-- Adds the characters GCD links to stories (gcd_story_character) to the extracted ones.
--
-- GCD now records most characters as links to its own character records; the free-text field
-- the extractor reads only holds those nobody has linked. This is not a copy of GCD's records:
-- a character is a name, an alter ego and a publisher, and records are merged when nothing
-- tells them apart.
--
--  * A linked character belongs to the publisher of the series it appears in, so the same
--    character at two publishers is two characters.
--  * A record GCD says was 'republished as' another (a reprint or foreign edition) counts as
--    that other one, so Robin (Dick Grayson) is not four characters. Alternate universe versions
--    and the like are left separate.
--  * A character that is the 'alias of' exactly one other (Starman, Jack Knight, is the alias of
--    Jack Knight) has that one's name as its alter ego; that is what keeps the Starmen, Robins
--    and Batgirls apart.
--  * Records with the same name, alter ego and publisher are one character, whatever GCD's
--    disambiguation says: with no alter ego to tell them apart, nothing else can.
--  * An extracted character is taken over by the linked one whose name matches (ignoring case
--    and punctuation) any name GCD has for it, with the same alter ego and publisher. Extracted
--    characters that match the same linked one are the same character spelled differently, and
--    are folded into it with their appearances. A name that belongs to two linked characters
--    matches neither.
--
-- Safe to run again: it adds what is missing and changes nothing else.
-- Placeholder: {{targetSchema}}, the database holding the gcd_* and m_* tables.

ALTER TABLE `{{targetSchema}}`.m_character
    ADD COLUMN IF NOT EXISTS gcd_character_id INT NULL,
    ADD INDEX IF NOT EXISTS m_character_gcd_character (gcd_character_id, publisher_id);

ALTER TABLE `{{targetSchema}}`.m_character_appearance
    ADD COLUMN IF NOT EXISTS gcd_story_character_id INT NULL,
    ADD UNIQUE INDEX IF NOT EXISTS m_appearance_gcd_story_character (gcd_story_character_id);

DROP TABLE IF EXISTS `{{targetSchema}}`.canonical_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.alias_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.linked_appearance_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.linked_character_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.linked_group_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.linked_name_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.match_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.claim_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.duplicate_work;
DROP TABLE IF EXISTS `{{targetSchema}}`.extracted_key_work;

-- Which record each character counts as: the one it was republished from, and so on up the chain
CREATE TABLE `{{targetSchema}}`.canonical_work AS
SELECT id AS gcd_character_id, id AS canonical_id
FROM `{{targetSchema}}`.gcd_character
WHERE deleted = 0;

ALTER TABLE `{{targetSchema}}`.canonical_work
    ADD PRIMARY KEY (gcd_character_id),
    ADD INDEX (canonical_id);

CREATE TABLE `{{targetSchema}}`.republished_work AS
SELECT r.to_character_id AS copy_id, MIN(r.from_character_id) AS original_id
FROM `{{targetSchema}}`.gcd_character_relation r
         JOIN `{{targetSchema}}`.gcd_character_relation_type t
              ON t.id = r.relation_type_id AND t.type = 'republished as'
         JOIN `{{targetSchema}}`.gcd_character o ON o.id = r.from_character_id AND o.deleted = 0
WHERE r.from_character_id <> r.to_character_id
  -- GCD has pairs that are each other's reprint: the higher id counts as the copy of the lower
  AND (r.from_character_id < r.to_character_id
    OR NOT EXISTS (SELECT 1
                   FROM `{{targetSchema}}`.gcd_character_relation back
                            JOIN `{{targetSchema}}`.gcd_character_relation_type bt
                                 ON bt.id = back.relation_type_id AND bt.type = 'republished as'
                   WHERE back.from_character_id = r.to_character_id
                     AND back.to_character_id = r.from_character_id))
GROUP BY r.to_character_id;

ALTER TABLE `{{targetSchema}}`.republished_work ADD PRIMARY KEY (copy_id);

UPDATE `{{targetSchema}}`.canonical_work c
    JOIN `{{targetSchema}}`.republished_work r ON r.copy_id = c.canonical_id
SET c.canonical_id = r.original_id;
UPDATE `{{targetSchema}}`.canonical_work c
    JOIN `{{targetSchema}}`.republished_work r ON r.copy_id = c.canonical_id
SET c.canonical_id = r.original_id;
UPDATE `{{targetSchema}}`.canonical_work c
    JOIN `{{targetSchema}}`.republished_work r ON r.copy_id = c.canonical_id
SET c.canonical_id = r.original_id;
UPDATE `{{targetSchema}}`.canonical_work c
    JOIN `{{targetSchema}}`.republished_work r ON r.copy_id = c.canonical_id
SET c.canonical_id = r.original_id;

DROP TABLE `{{targetSchema}}`.republished_work;

-- The one character a character is the alias of, if there is exactly one
CREATE TABLE `{{targetSchema}}`.alias_work AS
SELECT r.from_character_id AS gcd_character_id,
       MIN(person.name) AS alter_ego,
       COUNT(DISTINCT r.to_character_id) AS n
FROM `{{targetSchema}}`.gcd_character_relation r
         JOIN `{{targetSchema}}`.gcd_character_relation_type t
              ON t.id = r.relation_type_id AND t.type = 'alias of'
         JOIN `{{targetSchema}}`.gcd_character person ON person.id = r.to_character_id AND person.deleted = 0
GROUP BY r.from_character_id;

ALTER TABLE `{{targetSchema}}`.alias_work ADD PRIMARY KEY (gcd_character_id);

-- Every link, with where its story is published and which character it counts as
CREATE TABLE `{{targetSchema}}`.linked_appearance_work AS
SELECT sc.id AS gcd_story_character_id,
       sc.story_id,
       s.issue_id,
       i.series_id,
       ser.publisher_id,
       c.id AS gcd_character_id,
       r.name AS role_name,
       sc.is_flashback,
       sc.is_origin,
       sc.is_death,
       sc.notes
FROM `{{targetSchema}}`.gcd_story_character sc
         JOIN `{{targetSchema}}`.gcd_story s ON s.id = sc.story_id AND s.deleted = 0
         JOIN `{{targetSchema}}`.gcd_issue i ON i.id = s.issue_id AND i.deleted = 0
         JOIN `{{targetSchema}}`.gcd_series ser ON ser.id = i.series_id AND ser.deleted = 0
         JOIN `{{targetSchema}}`.gcd_character_name_detail nd ON nd.id = sc.character_id
         JOIN `{{targetSchema}}`.canonical_work cw ON cw.gcd_character_id = nd.character_id
         JOIN `{{targetSchema}}`.gcd_character c ON c.id = cw.canonical_id AND c.deleted = 0
         LEFT JOIN `{{targetSchema}}`.gcd_character_role r ON r.id = sc.role_id
WHERE sc.deleted = 0;

ALTER TABLE `{{targetSchema}}`.linked_appearance_work
    ADD COLUMN group_id INT NULL,
    ADD INDEX (gcd_character_id, publisher_id);

-- One row per linked record per publisher, with the keys characters are matched and merged by:
-- name and alter ego without case or punctuation. The key columns are plain fixed-size text in
-- one character set, or the indexes on them could not be used.
CREATE TABLE `{{targetSchema}}`.linked_character_work AS
SELECT la.gcd_character_id,
       la.publisher_id,
       LEFT(MIN(c.name), 255) AS character_name,
       LEFT(MIN(al.alter_ego), 255) AS alter_ego
FROM `{{targetSchema}}`.linked_appearance_work la
         JOIN `{{targetSchema}}`.gcd_character c ON c.id = la.gcd_character_id
         LEFT JOIN `{{targetSchema}}`.alias_work al ON al.gcd_character_id = la.gcd_character_id AND al.n = 1
GROUP BY la.gcd_character_id, la.publisher_id;

ALTER TABLE `{{targetSchema}}`.linked_character_work
    ADD COLUMN name_key VARCHAR(255) CHARACTER SET utf8mb4,
    ADD COLUMN alter_key VARCHAR(255) CHARACTER SET utf8mb4,
    ADD COLUMN group_id INT NULL;

UPDATE `{{targetSchema}}`.linked_character_work
SET name_key  = LEFT(LOWER(REGEXP_REPLACE(character_name, '[^[:alnum:]]+', '')), 255),
    alter_key = LEFT(LOWER(REGEXP_REPLACE(IFNULL(alter_ego, ''), '[^[:alnum:]]+', '')), 255);

ALTER TABLE `{{targetSchema}}`.linked_character_work
    ADD INDEX (publisher_id, name_key, alter_key),
    ADD INDEX (gcd_character_id, publisher_id);

-- Records with the same name, alter ego and publisher are one character: the lowest id stands
-- for them all
CREATE TABLE `{{targetSchema}}`.linked_group_work AS
SELECT lc.publisher_id,
       lc.name_key,
       lc.alter_key,
       MIN(lc.gcd_character_id) AS group_id
FROM `{{targetSchema}}`.linked_character_work lc
GROUP BY lc.publisher_id, lc.name_key, lc.alter_key;

ALTER TABLE `{{targetSchema}}`.linked_group_work
    ADD PRIMARY KEY (publisher_id, name_key, alter_key),
    ADD INDEX (group_id, publisher_id);

UPDATE `{{targetSchema}}`.linked_character_work lc
    JOIN `{{targetSchema}}`.linked_group_work g
    ON g.publisher_id = lc.publisher_id AND g.name_key = lc.name_key AND g.alter_key = lc.alter_key
SET lc.group_id = g.group_id;

UPDATE `{{targetSchema}}`.linked_appearance_work la
    JOIN `{{targetSchema}}`.linked_character_work lc
    ON lc.gcd_character_id = la.gcd_character_id AND lc.publisher_id = la.publisher_id
SET la.group_id = lc.group_id;

ALTER TABLE `{{targetSchema}}`.linked_appearance_work
    ADD INDEX (story_id, group_id, gcd_story_character_id);

-- Every name GCD has for the characters in a group (the official one, spellings, titles,
-- translations), as keys, with the group's alter ego. A name two groups have at a publisher
-- belongs to the one it is the official name of, if there is just one; otherwise it says nothing
-- about which an extracted character is, and is dropped.
CREATE TABLE `{{targetSchema}}`.linked_name_work AS
SELECT DISTINCT lc.publisher_id,
                lc.group_id,
                LEFT(LOWER(REGEXP_REPLACE(nd.name, '[^[:alnum:]]+', '')), 255) AS name_key,
                lc.alter_key,
                (LEFT(LOWER(REGEXP_REPLACE(nd.name, '[^[:alnum:]]+', '')), 255) = lc.name_key) AS official
FROM `{{targetSchema}}`.linked_character_work lc
         JOIN `{{targetSchema}}`.canonical_work cw ON cw.canonical_id = lc.gcd_character_id
         JOIN `{{targetSchema}}`.gcd_character_name_detail nd
              ON nd.character_id = cw.gcd_character_id AND nd.deleted = 0;

ALTER TABLE `{{targetSchema}}`.linked_name_work
    MODIFY name_key VARCHAR(255) CHARACTER SET utf8mb4,
    MODIFY alter_key VARCHAR(255) CHARACTER SET utf8mb4,
    ADD INDEX (publisher_id, name_key, alter_key);

DELETE n
FROM `{{targetSchema}}`.linked_name_work n
         JOIN (SELECT publisher_id, name_key, alter_key, SUM(official) AS officials
               FROM `{{targetSchema}}`.linked_name_work
               GROUP BY publisher_id, name_key, alter_key
               HAVING COUNT(*) > 1) shared
              ON shared.publisher_id = n.publisher_id
                  AND shared.name_key = n.name_key
                  AND shared.alter_key = n.alter_key
WHERE NOT (n.official = 1 AND shared.officials = 1);

-- Extracted characters not yet linked, by the same keys
CREATE TABLE `{{targetSchema}}`.extracted_key_work
(
    id           INT NOT NULL,
    publisher_id INT NULL,
    name_key     VARCHAR(255) CHARACTER SET utf8mb4 NULL,
    alter_key    VARCHAR(255) CHARACTER SET utf8mb4 NULL,
    INDEX (publisher_id, name_key, alter_key)
);

INSERT INTO `{{targetSchema}}`.extracted_key_work (id, publisher_id, name_key, alter_key)
SELECT m.id,
       m.publisher_id,
       LEFT(LOWER(REGEXP_REPLACE(m.name, '[^[:alnum:]]+', '')), 255),
       LEFT(LOWER(REGEXP_REPLACE(IFNULL(m.alter_ego, ''), '[^[:alnum:]]+', '')), 255)
FROM `{{targetSchema}}`.m_character m
WHERE m.gcd_character_id IS NULL;

-- Which extracted characters are which linked character, for linked characters that do not have
-- a row yet
CREATE TABLE `{{targetSchema}}`.match_work AS
SELECT n.group_id, n.publisher_id, e.id AS extracted_id
FROM `{{targetSchema}}`.linked_name_work n
         JOIN `{{targetSchema}}`.extracted_key_work e
              ON e.publisher_id = n.publisher_id AND e.name_key = n.name_key AND e.alter_key = n.alter_key
WHERE NOT EXISTS (SELECT 1
                  FROM `{{targetSchema}}`.m_character done
                  WHERE done.gcd_character_id = n.group_id
                    AND done.publisher_id = n.publisher_id)
GROUP BY n.group_id, n.publisher_id, e.id;

-- The oldest takes over
CREATE TABLE `{{targetSchema}}`.claim_work AS
SELECT group_id, publisher_id, MIN(extracted_id) AS extracted_id
FROM `{{targetSchema}}`.match_work
GROUP BY group_id, publisher_id;

ALTER TABLE `{{targetSchema}}`.claim_work ADD PRIMARY KEY (extracted_id);

-- The others are the same character spelled differently: folded into it, with their appearances
CREATE TABLE `{{targetSchema}}`.duplicate_work AS
SELECT m.extracted_id AS duplicate_id, c.extracted_id AS keep_id
FROM `{{targetSchema}}`.match_work m
         JOIN `{{targetSchema}}`.claim_work c ON c.group_id = m.group_id AND c.publisher_id = m.publisher_id
WHERE m.extracted_id <> c.extracted_id;

ALTER TABLE `{{targetSchema}}`.duplicate_work ADD PRIMARY KEY (duplicate_id), ADD INDEX (keep_id);

UPDATE `{{targetSchema}}`.m_character_appearance a
    JOIN `{{targetSchema}}`.duplicate_work d ON d.duplicate_id = a.character_id
SET a.character_id = d.keep_id;

DELETE a
FROM `{{targetSchema}}`.m_character_appearance a
         JOIN `{{targetSchema}}`.m_character_appearance b
              ON b.story_id = a.story_id AND b.character_id = a.character_id AND b.id < a.id
WHERE a.character_id IN (SELECT keep_id FROM `{{targetSchema}}`.duplicate_work);

DELETE m
FROM `{{targetSchema}}`.m_character m
         JOIN `{{targetSchema}}`.duplicate_work d ON d.duplicate_id = m.id;

-- The linked character takes over the extracted one, and GCD's spelling of its name
UPDATE IGNORE `{{targetSchema}}`.m_character m
    JOIN `{{targetSchema}}`.claim_work c ON c.extracted_id = m.id
    JOIN `{{targetSchema}}`.linked_character_work lc
    ON lc.gcd_character_id = c.group_id AND lc.publisher_id = c.publisher_id
SET m.gcd_character_id = c.group_id,
    m.name             = lc.character_name,
    m.alter_ego        = IFNULL(lc.alter_ego, m.alter_ego);

-- An extracted character spelled exactly as a linked one, whatever the keys say, is that one too
UPDATE IGNORE `{{targetSchema}}`.m_character m
    JOIN `{{targetSchema}}`.linked_character_work lc
    ON lc.publisher_id = m.publisher_id
        AND lc.character_name = m.name
        AND IFNULL(lc.alter_ego, '') = IFNULL(m.alter_ego, '')
        AND lc.gcd_character_id = lc.group_id
SET m.gcd_character_id = lc.gcd_character_id
WHERE m.gcd_character_id IS NULL
  AND NOT EXISTS (SELECT 1
                  FROM `{{targetSchema}}`.m_character done
                  WHERE done.gcd_character_id = lc.gcd_character_id
                    AND done.publisher_id = lc.publisher_id);

-- The rest are new characters
INSERT IGNORE INTO `{{targetSchema}}`.m_character (name, alter_ego, publisher_id, gcd_character_id)
SELECT lc.character_name, lc.alter_ego, lc.publisher_id, lc.gcd_character_id
FROM `{{targetSchema}}`.linked_character_work lc
WHERE lc.gcd_character_id = lc.group_id
  AND NOT EXISTS (SELECT 1
                  FROM `{{targetSchema}}`.m_character m
                  WHERE m.gcd_character_id = lc.gcd_character_id
                    AND m.publisher_id = lc.publisher_id);

-- Appearances, unless the extractor already found that character in that story. A story that links
-- a character twice (by two names, or two records that count as one) gets one appearance, from the
-- first link.
-- details holds what the story says about the appearance, notes the character's role.
INSERT IGNORE INTO `{{targetSchema}}`.m_character_appearance
(details, character_id, story_id, notes, membership, issue_id, series_id, gcd_story_character_id)
SELECT LEFT(CONCAT_WS(', ',
                      NULLIF(la.notes, ''),
                      IF(la.is_flashback, 'flashback', NULL),
                      IF(la.is_origin, 'origin', NULL),
                      IF(la.is_death, 'death', NULL)), 255),
       m.id,
       la.story_id,
       la.role_name,
       NULL,
       la.issue_id,
       la.series_id,
       la.gcd_story_character_id
FROM `{{targetSchema}}`.linked_appearance_work la
         JOIN `{{targetSchema}}`.m_character m
              ON m.gcd_character_id = la.group_id AND m.publisher_id = la.publisher_id
WHERE NOT EXISTS (SELECT 1
                  FROM `{{targetSchema}}`.m_character_appearance a
                  WHERE a.story_id = la.story_id
                    AND a.character_id = m.id
                    AND a.gcd_story_character_id IS NULL)
  AND NOT EXISTS (SELECT 1
                  FROM `{{targetSchema}}`.linked_appearance_work first_link
                  WHERE first_link.story_id = la.story_id
                    AND first_link.group_id = la.group_id
                    AND first_link.publisher_id = la.publisher_id
                    AND first_link.gcd_story_character_id < la.gcd_story_character_id);

DROP TABLE `{{targetSchema}}`.canonical_work;
DROP TABLE `{{targetSchema}}`.alias_work;
DROP TABLE `{{targetSchema}}`.linked_appearance_work;
DROP TABLE `{{targetSchema}}`.linked_character_work;
DROP TABLE `{{targetSchema}}`.linked_group_work;
DROP TABLE `{{targetSchema}}`.linked_name_work;
DROP TABLE `{{targetSchema}}`.match_work;
DROP TABLE `{{targetSchema}}`.claim_work;
DROP TABLE `{{targetSchema}}`.duplicate_work;
DROP TABLE `{{targetSchema}}`.extracted_key_work;
