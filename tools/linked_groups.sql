-- Adds the groups (teams) GCD links to stories (gcd_group_character) to the extracted characters.
--
-- GCD records a team in a story as a link to its own group record, and who appeared as part of it
-- as links from the story's characters to that group (gcd_story_character_group). The free text
-- the extractor reads can't say which a name is: "Superman [Clark Kent; Kal-El]" and
-- "Challengers of the Unknown [Ace Morgan; Rocky Davis]" look alike. These links can.
--
--  * A team is a character record with no alter ego, as the extractor makes them, and a
--    gcd_group_id. It belongs to the publisher of the series it appears in.
--  * A group GCD says was 'republished as' another counts as that other one.
--  * An extracted character with no alter ego is taken over by the group whose name matches
--    (ignoring case and punctuation) any name GCD has for it, unless that name is also a
--    character's or belongs to two groups. Extracted characters taken over by the same group are
--    folded into it with their appearances.
--  * A team's appearance keeps the roster of its story: the names its member characters were
--    credited as, in the order GCD links them. That replaces what the extractor guessed from the
--    brackets.
--
-- Run it after linked_characters.sql. Safe to run again: it adds what is missing.
-- Placeholder: {{targetSchema}}, the database holding the gcd_* and m_* tables.

ALTER TABLE `{{targetSchema}}`.m_character
    ADD COLUMN IF NOT EXISTS gcd_group_id INT NULL,
    ADD INDEX IF NOT EXISTS m_character_gcd_group (gcd_group_id, publisher_id);

ALTER TABLE `{{targetSchema}}`.m_character_appearance
    ADD COLUMN IF NOT EXISTS gcd_group_character_id INT NULL,
    ADD UNIQUE INDEX IF NOT EXISTS m_appearance_gcd_group_character (gcd_group_character_id);

DROP TABLE IF EXISTS `{{targetSchema}}`.team_canonical_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_republished_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_appearance_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_first_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_roster_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_character_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_name_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_character_key_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_extracted_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_match_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_claim_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.team_duplicate_work;

-- Every group, standing for itself
CREATE TABLE `{{targetSchema}}`.team_canonical_work AS
SELECT id AS gcd_group_id, id AS canonical_id
FROM `{{targetSchema}}`.gcd_group
WHERE deleted = 0;
ALTER TABLE `{{targetSchema}}`.team_canonical_work
    ADD PRIMARY KEY (gcd_group_id),
    ADD INDEX (canonical_id);

-- A republished group stands for the one it republishes (two groups that are each other's
-- reprint go by the lower id)
CREATE TABLE `{{targetSchema}}`.team_republished_work AS
SELECT r.to_group_id AS copy_id, MIN(r.from_group_id) AS original_id
FROM `{{targetSchema}}`.gcd_group_relation r
         JOIN `{{targetSchema}}`.gcd_group_relation_type t
              ON t.id = r.relation_type_id AND t.type = 'republished as'
         JOIN `{{targetSchema}}`.gcd_group o ON o.id = r.from_group_id AND o.deleted = 0
WHERE r.from_group_id <> r.to_group_id
  AND (r.from_group_id < r.to_group_id
    OR NOT EXISTS (SELECT 1
                   FROM `{{targetSchema}}`.gcd_group_relation back
                            JOIN `{{targetSchema}}`.gcd_group_relation_type bt
                                 ON bt.id = back.relation_type_id AND bt.type = 'republished as'
                   WHERE back.from_group_id = r.to_group_id
                     AND back.to_group_id = r.from_group_id))
GROUP BY r.to_group_id;
ALTER TABLE `{{targetSchema}}`.team_republished_work ADD PRIMARY KEY (copy_id);

-- Follow republished chains up to their original, a few steps being as many as there are
UPDATE `{{targetSchema}}`.team_canonical_work c
    JOIN `{{targetSchema}}`.team_republished_work r ON r.copy_id = c.canonical_id
SET c.canonical_id = r.original_id;
UPDATE `{{targetSchema}}`.team_canonical_work c
    JOIN `{{targetSchema}}`.team_republished_work r ON r.copy_id = c.canonical_id
SET c.canonical_id = r.original_id;
UPDATE `{{targetSchema}}`.team_canonical_work c
    JOIN `{{targetSchema}}`.team_republished_work r ON r.copy_id = c.canonical_id
SET c.canonical_id = r.original_id;
UPDATE `{{targetSchema}}`.team_canonical_work c
    JOIN `{{targetSchema}}`.team_republished_work r ON r.copy_id = c.canonical_id
SET c.canonical_id = r.original_id;
DROP TABLE `{{targetSchema}}`.team_republished_work;

-- Each link of a group to a story of a kept series
CREATE TABLE `{{targetSchema}}`.team_appearance_work AS
SELECT gc.id AS gcd_group_character_id,
       gc.story_id,
       s.issue_id,
       i.series_id,
       ser.publisher_id,
       cw.canonical_id AS gcd_group_id,
       gc.notes
FROM `{{targetSchema}}`.gcd_group_character gc
         JOIN `{{targetSchema}}`.gcd_story s ON s.id = gc.story_id AND s.deleted = 0
         JOIN `{{targetSchema}}`.gcd_issue i ON i.id = s.issue_id AND i.deleted = 0
         JOIN `{{targetSchema}}`.gcd_series ser ON ser.id = i.series_id AND ser.deleted = 0
         JOIN `{{targetSchema}}`.gcd_group_name_detail nd ON nd.id = gc.group_name_id
         JOIN `{{targetSchema}}`.team_canonical_work cw ON cw.gcd_group_id = nd.group_id
         JOIN `{{targetSchema}}`.gcd_group g ON g.id = cw.canonical_id AND g.deleted = 0
WHERE gc.deleted = 0;
ALTER TABLE `{{targetSchema}}`.team_appearance_work
    ADD INDEX (story_id, gcd_group_id, publisher_id, gcd_group_character_id),
    ADD INDEX (gcd_group_id, publisher_id);

-- A story links a group once, whatever else it says: the first link
CREATE TABLE `{{targetSchema}}`.team_first_work AS
SELECT MIN(gcd_group_character_id) AS gcd_group_character_id
FROM `{{targetSchema}}`.team_appearance_work
GROUP BY story_id, gcd_group_id, publisher_id;
ALTER TABLE `{{targetSchema}}`.team_first_work ADD PRIMARY KEY (gcd_group_character_id);

-- Who appeared as part of each group in each story, by the names they were credited as
CREATE TABLE `{{targetSchema}}`.team_roster_work AS
SELECT sc.story_id,
       cw.canonical_id AS gcd_group_id,
       GROUP_CONCAT(nd.name ORDER BY sc.id SEPARATOR '; ') AS roster
FROM `{{targetSchema}}`.gcd_story_character_group sg
         JOIN `{{targetSchema}}`.gcd_story_character sc ON sc.id = sg.storycharacter_id AND sc.deleted = 0
         JOIN `{{targetSchema}}`.gcd_character_name_detail nd ON nd.id = sc.character_id
         JOIN `{{targetSchema}}`.team_canonical_work cw ON cw.gcd_group_id = sg.group_id
GROUP BY sc.story_id, cw.canonical_id;
ALTER TABLE `{{targetSchema}}`.team_roster_work ADD PRIMARY KEY (story_id, gcd_group_id);

-- The teams to have, a group at a publisher being one
CREATE TABLE `{{targetSchema}}`.team_character_work AS
SELECT ta.gcd_group_id,
       ta.publisher_id,
       LEFT(MIN(g.name), 255) AS group_name
FROM `{{targetSchema}}`.team_appearance_work ta
         JOIN `{{targetSchema}}`.gcd_group g ON g.id = ta.gcd_group_id
GROUP BY ta.gcd_group_id, ta.publisher_id;
ALTER TABLE `{{targetSchema}}`.team_character_work
    ADD PRIMARY KEY (gcd_group_id, publisher_id);

-- Every name a group goes by, as it is compared
CREATE TABLE `{{targetSchema}}`.team_name_work
(
    publisher_id INT NOT NULL,
    gcd_group_id INT NOT NULL,
    name_key     VARCHAR(255) CHARACTER SET utf8mb4 NOT NULL,
    INDEX (publisher_id, name_key)
);
INSERT INTO `{{targetSchema}}`.team_name_work (publisher_id, gcd_group_id, name_key)
SELECT DISTINCT tc.publisher_id,
                tc.gcd_group_id,
                LEFT(LOWER(REGEXP_REPLACE(nd.name, '[^[:alnum:]]+', '')), 255)
FROM `{{targetSchema}}`.team_character_work tc
         JOIN `{{targetSchema}}`.team_canonical_work cw ON cw.canonical_id = tc.gcd_group_id
         JOIN `{{targetSchema}}`.gcd_group_name_detail nd ON nd.group_id = cw.gcd_group_id AND nd.deleted = 0;
INSERT INTO `{{targetSchema}}`.team_name_work (publisher_id, gcd_group_id, name_key)
SELECT tc.publisher_id, tc.gcd_group_id, LEFT(LOWER(REGEXP_REPLACE(tc.group_name, '[^[:alnum:]]+', '')), 255)
FROM `{{targetSchema}}`.team_character_work tc;

-- A name two groups have at one publisher belongs to neither
DELETE n
FROM `{{targetSchema}}`.team_name_work n
         JOIN (SELECT publisher_id, name_key
               FROM `{{targetSchema}}`.team_name_work
               GROUP BY publisher_id, name_key
               HAVING COUNT(DISTINCT gcd_group_id) > 1) shared
              ON shared.publisher_id = n.publisher_id AND shared.name_key = n.name_key;

-- Nor does a name that is also a character's: nothing says which the text means
CREATE TABLE `{{targetSchema}}`.team_character_key_work
(
    name_key VARCHAR(255) CHARACTER SET utf8mb4 NOT NULL,
    PRIMARY KEY (name_key)
);
INSERT IGNORE INTO `{{targetSchema}}`.team_character_key_work (name_key)
SELECT LEFT(LOWER(REGEXP_REPLACE(cn.name, '[^[:alnum:]]+', '')), 255)
FROM `{{targetSchema}}`.gcd_character_name_detail cn
WHERE cn.deleted = 0;
DELETE n
FROM `{{targetSchema}}`.team_name_work n
         JOIN `{{targetSchema}}`.team_character_key_work ck ON ck.name_key = n.name_key;

-- What the extractor made of names that have no alter ego and aren't taken yet
CREATE TABLE `{{targetSchema}}`.team_extracted_work
(
    id           INT NOT NULL,
    publisher_id INT NULL,
    name_key     VARCHAR(255) CHARACTER SET utf8mb4 NULL,
    INDEX (publisher_id, name_key)
);
INSERT INTO `{{targetSchema}}`.team_extracted_work (id, publisher_id, name_key)
SELECT m.id,
       m.publisher_id,
       LEFT(LOWER(REGEXP_REPLACE(m.name, '[^[:alnum:]]+', '')), 255)
FROM `{{targetSchema}}`.m_character m
WHERE m.gcd_character_id IS NULL
  AND m.gcd_group_id IS NULL
  AND (m.alter_ego IS NULL OR m.alter_ego = '');

CREATE TABLE `{{targetSchema}}`.team_match_work AS
SELECT n.gcd_group_id, n.publisher_id, e.id AS extracted_id
FROM `{{targetSchema}}`.team_name_work n
         JOIN `{{targetSchema}}`.team_extracted_work e
              ON e.publisher_id = n.publisher_id AND e.name_key = n.name_key
WHERE NOT EXISTS (SELECT 1
                  FROM `{{targetSchema}}`.m_character done
                  WHERE done.gcd_group_id = n.gcd_group_id
                    AND done.publisher_id = n.publisher_id)
GROUP BY n.gcd_group_id, n.publisher_id, e.id;

CREATE TABLE `{{targetSchema}}`.team_claim_work AS
SELECT gcd_group_id, publisher_id, MIN(extracted_id) AS extracted_id
FROM `{{targetSchema}}`.team_match_work
GROUP BY gcd_group_id, publisher_id;
ALTER TABLE `{{targetSchema}}`.team_claim_work ADD PRIMARY KEY (extracted_id);

CREATE TABLE `{{targetSchema}}`.team_duplicate_work AS
SELECT m.extracted_id AS duplicate_id, c.extracted_id AS keep_id
FROM `{{targetSchema}}`.team_match_work m
         JOIN `{{targetSchema}}`.team_claim_work c
              ON c.gcd_group_id = m.gcd_group_id AND c.publisher_id = m.publisher_id
WHERE m.extracted_id <> c.extracted_id;
ALTER TABLE `{{targetSchema}}`.team_duplicate_work ADD PRIMARY KEY (duplicate_id), ADD INDEX (keep_id);

-- Characters taken over by the same group are one: their appearances go to the one kept
UPDATE `{{targetSchema}}`.m_character_appearance a
    JOIN `{{targetSchema}}`.team_duplicate_work d ON d.duplicate_id = a.character_id
SET a.character_id = d.keep_id;

DELETE a
FROM `{{targetSchema}}`.m_character_appearance a
         JOIN `{{targetSchema}}`.m_character_appearance b
              ON b.story_id = a.story_id AND b.character_id = a.character_id AND b.id < a.id
WHERE a.character_id IN (SELECT keep_id FROM `{{targetSchema}}`.team_duplicate_work);

DELETE m
FROM `{{targetSchema}}`.m_character m
         JOIN `{{targetSchema}}`.team_duplicate_work d ON d.duplicate_id = m.id;

-- The one kept becomes the group, spelled as GCD spells it
UPDATE IGNORE `{{targetSchema}}`.m_character m
    JOIN `{{targetSchema}}`.team_claim_work c ON c.extracted_id = m.id
    JOIN `{{targetSchema}}`.team_character_work tc
    ON tc.gcd_group_id = c.gcd_group_id AND tc.publisher_id = c.publisher_id
SET m.gcd_group_id = c.gcd_group_id,
    m.name         = tc.group_name,
    m.alter_ego    = NULL;

-- Groups nothing was extracted for
INSERT IGNORE INTO `{{targetSchema}}`.m_character (name, alter_ego, publisher_id, gcd_group_id)
SELECT tc.group_name, NULL, tc.publisher_id, tc.gcd_group_id
FROM `{{targetSchema}}`.team_character_work tc
WHERE NOT EXISTS (SELECT 1
                  FROM `{{targetSchema}}`.m_character m
                  WHERE m.gcd_group_id = tc.gcd_group_id
                    AND m.publisher_id = tc.publisher_id);

-- A team the extractor already found in a story gets its link, GCD's notes if it had none, and the roster
UPDATE IGNORE `{{targetSchema}}`.m_character_appearance a
    JOIN `{{targetSchema}}`.m_character m ON m.id = a.character_id AND m.gcd_group_id IS NOT NULL
    JOIN `{{targetSchema}}`.team_appearance_work ta
    ON ta.story_id = a.story_id
        AND ta.gcd_group_id = m.gcd_group_id
        AND ta.publisher_id = m.publisher_id
    JOIN `{{targetSchema}}`.team_first_work f ON f.gcd_group_character_id = ta.gcd_group_character_id
    LEFT JOIN `{{targetSchema}}`.team_roster_work r ON r.story_id = ta.story_id AND r.gcd_group_id = ta.gcd_group_id
SET a.gcd_group_character_id = ta.gcd_group_character_id,
    a.details                = IF(IFNULL(a.details, '') = '', COALESCE(LEFT(NULLIF(ta.notes, ''), 255), a.details), a.details),
    a.membership             = COALESCE(r.roster, a.membership)
WHERE a.gcd_group_character_id IS NULL;

-- And one it didn't find is added
INSERT IGNORE INTO `{{targetSchema}}`.m_character_appearance
(details, character_id, story_id, notes, membership, issue_id, series_id, gcd_group_character_id)
SELECT LEFT(NULLIF(ta.notes, ''), 255),
       m.id,
       ta.story_id,
       NULL,
       r.roster,
       ta.issue_id,
       ta.series_id,
       ta.gcd_group_character_id
FROM `{{targetSchema}}`.team_appearance_work ta
         JOIN `{{targetSchema}}`.team_first_work f ON f.gcd_group_character_id = ta.gcd_group_character_id
         JOIN `{{targetSchema}}`.m_character m
              ON m.gcd_group_id = ta.gcd_group_id AND m.publisher_id = ta.publisher_id
         LEFT JOIN `{{targetSchema}}`.team_roster_work r ON r.story_id = ta.story_id AND r.gcd_group_id = ta.gcd_group_id
WHERE NOT EXISTS (SELECT 1
                  FROM `{{targetSchema}}`.m_character_appearance a
                  WHERE a.story_id = ta.story_id
                    AND a.character_id = m.id);

DROP TABLE `{{targetSchema}}`.team_canonical_work;
DROP TABLE `{{targetSchema}}`.team_appearance_work;
DROP TABLE `{{targetSchema}}`.team_first_work;
DROP TABLE `{{targetSchema}}`.team_roster_work;
DROP TABLE `{{targetSchema}}`.team_character_work;
DROP TABLE `{{targetSchema}}`.team_name_work;
DROP TABLE `{{targetSchema}}`.team_character_key_work;
DROP TABLE `{{targetSchema}}`.team_extracted_work;
DROP TABLE `{{targetSchema}}`.team_match_work;
DROP TABLE `{{targetSchema}}`.team_claim_work;
DROP TABLE `{{targetSchema}}`.team_duplicate_work;
