"""Runs tools/linked_characters.sql against a small made-up database.

    ENV_FILE=.env.local python -m unittest tools.tests.test_linked_characters -v

Needs the local MariaDB (the script runs with its database selected, as CreditUpdater runs it); creates and drops the database `longbox_linked_test`.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "longbox_linked_test"
SCRIPT = (ROOT / "tools" / "linked_characters.sql").read_text().replace("{{targetSchema}}", SCHEMA)

TABLES = """
CREATE TABLE gcd_series (id INT PRIMARY KEY, publisher_id INT NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_issue (id INT PRIMARY KEY, series_id INT NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_story (id INT PRIMARY KEY, issue_id INT NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_character (id INT PRIMARY KEY, name VARCHAR(255) NOT NULL,
    disambiguation VARCHAR(255) NOT NULL DEFAULT '', deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_character_name_detail (id INT PRIMARY KEY, character_id INT NOT NULL,
    name VARCHAR(255) NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_character_role (id INT PRIMARY KEY, name VARCHAR(255) NOT NULL);
CREATE TABLE gcd_character_relation_type (id INT PRIMARY KEY, type VARCHAR(50) NOT NULL, reverse_type VARCHAR(50) NOT NULL);
CREATE TABLE gcd_character_relation (id INT PRIMARY KEY, from_character_id INT NOT NULL,
    relation_type_id INT NOT NULL, to_character_id INT NOT NULL);
CREATE TABLE gcd_story_character (id INT PRIMARY KEY, story_id INT NOT NULL, character_id INT NOT NULL,
    role_id INT NULL, is_flashback TINYINT NOT NULL DEFAULT 0, is_origin TINYINT NOT NULL DEFAULT 0,
    is_death TINYINT NOT NULL DEFAULT 0, notes LONGTEXT NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE m_character (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255) NOT NULL,
    alter_ego VARCHAR(255), publisher_id INT NOT NULL, UNIQUE KEY name_2 (name, alter_ego, publisher_id));
CREATE TABLE m_character_appearance (id INT PRIMARY KEY AUTO_INCREMENT, details VARCHAR(255),
    character_id INT NOT NULL, story_id INT NOT NULL, notes VARCHAR(255), membership LONGTEXT,
    issue_id INT NOT NULL, series_id INT NOT NULL);
"""

# Series 1 is Fantagraphics (publisher 10), series 2 is DC (publisher 20); one issue and story
# in each, and a second story in series 1
DATA = """
INSERT INTO gcd_series VALUES (1, 10, 0), (2, 20, 0);
INSERT INTO gcd_issue VALUES (100, 1, 0), (200, 2, 0);
INSERT INTO gcd_story VALUES (1000, 100, 0), (1001, 100, 0), (2000, 200, 0), (1002, 100, 1),
    (2001, 200, 0), (2002, 200, 0), (1003, 100, 0), (2003, 200, 0);
INSERT INTO gcd_character VALUES
    (1, 'Hopey Glass', '', 0),
    (2, 'Maggie Chascarrillo', '', 0),
    (3, 'Maggie', 'Weaver', 0),
    (4, 'Maggie', 'Bringing Up Father', 0),
    (5, 'Esperanza', 'Lady Zorro', 0),
    (6, 'Deleted Person', '', 1);
INSERT INTO gcd_character_name_detail VALUES (11, 1, 'Hopey Glass', 0), (12, 2, 'Maggie Chascarrillo', 0),
    (13, 2, 'Maggie', 0), (14, 3, 'Maggie', 0), (15, 4, 'Maggie', 0), (16, 5, 'Esperanza', 0),
    (17, 6, 'Deleted Person', 0);
INSERT INTO gcd_character_role VALUES (1, 'featured'), (2, 'villain');

-- Robin, as GCD records him: Dick Grayson's Robin, a reprint record of it and a foreign edition
-- of that reprint, Tim Drake's Robin, the people behind them, a character that is the alias of
-- two others, and a reprint of a record that was deleted
INSERT INTO gcd_character VALUES
    (7, 'Robin', 'Dick Grayson', 0),
    (8, 'Dick Grayson', 'Robin', 0),
    (9, 'Robin', 'DC, Dick Grayson', 0),
    (10, 'Robin', 'Dick Grayson, German edition', 0),
    (11, 'Robin', 'Tim Drake', 0),
    (12, 'Mystery Man', '', 0),
    (13, 'Alpha Person', '', 0),
    (14, 'Beta Person', '', 0),
    (15, 'Orphan Copy', '', 0),
    (16, 'Tim Drake', 'Robin', 0),
    (17, 'Twin A', '', 0),
    (18, 'Twin B', '', 0),
    (19, 'Barbara Gordon', 'Batgirl / Oracle', 0),
    (20, 'Batgirl', 'first record', 0),
    (21, 'Batgirl', 'second record', 0),
    (22, 'Spirit A', '', 0),
    (23, 'Spirit B', '', 0),
    (24, 'Barbara Gordon Wayne', '', 0);
INSERT INTO gcd_character_name_detail VALUES (21, 7, 'Robin', 0), (22, 9, 'Robin', 0), (23, 10, 'Robin', 0),
    (24, 11, 'Robin', 0), (25, 12, 'Mystery Man', 0), (26, 15, 'Orphan Copy', 0), (27, 17, 'Twin A', 0),
    (28, 18, 'Twin B', 0),
    (31, 19, 'Barbara Gordon', 0), (32, 19, 'Commissioner Barbara Gordon', 0), (33, 19, 'Barbara Gourdon', 0),
    (34, 20, 'Batgirl', 0), (35, 21, 'Batgirl', 0),
    (36, 22, 'Spirit A', 0), (37, 22, 'The Spirit', 0), (38, 23, 'Spirit B', 0), (39, 23, 'The Spirit', 0),
    (40, 24, 'Barbara Gordon Wayne', 0), (41, 24, 'Barbara Gordon', 0);
INSERT INTO gcd_character_relation_type VALUES
    (1, 'republished as', 'originally published as'),
    (2, 'alias of', 'secret identity of'),
    (3, 'alternate universe version of', 'alternate universe version of');
INSERT INTO gcd_character_relation VALUES
    (1, 7, 1, 9), (2, 9, 1, 10), (3, 7, 2, 8), (4, 12, 2, 13), (5, 12, 2, 14),
    (6, 6, 1, 15), (7, 11, 3, 7), (8, 11, 2, 16),
    -- two records that are each other's reprint
    (9, 17, 1, 18), (10, 18, 1, 17);

-- story 1000: Hopey, and Maggie Chascarrillo under her short name in a dream sequence
INSERT INTO gcd_story_character VALUES
    (1, 1000, 11, 1, 1, 0, 0, '', 0),
    (2, 1000, 13, NULL, 0, 0, 0, 'dream sequence', 0),
    (3, 1001, 11, 2, 0, 1, 1, 'cameo', 0),
    -- the same Hopey in a DC story is a different character
    (4, 2000, 11, NULL, 0, 0, 0, '', 0),
    -- two characters named Maggie in one publisher's story
    (5, 1001, 14, NULL, 0, 0, 0, '', 0),
    (6, 1001, 15, NULL, 0, 0, 0, '', 0),
    -- left out: link deleted, story deleted, character deleted
    (7, 1001, 12, NULL, 0, 0, 0, '', 1),
    (8, 1002, 12, NULL, 0, 0, 0, '', 0),
    (9, 1001, 17, NULL, 0, 0, 0, '', 0),
    -- Esperanza, featured in a flashback; the extractor has one with an alter ego
    (10, 1000, 16, 1, 1, 0, 0, '', 0),
    -- Robin at DC: the original record, a reprint record of it, a foreign edition of that, and
    -- Tim Drake's Robin; a character that is the alias of two; a copy of a deleted original
    (20, 2000, 21, NULL, 0, 0, 0, '', 0),
    (21, 2001, 22, NULL, 0, 0, 0, '', 0),
    (22, 2002, 23, NULL, 0, 0, 0, '', 0),
    (23, 2000, 24, NULL, 0, 0, 0, '', 0),
    (24, 2001, 25, NULL, 0, 0, 0, '', 0),
    (25, 2001, 26, NULL, 0, 0, 0, '', 0),
    (26, 2001, 27, NULL, 0, 0, 0, '', 0),
    (27, 2002, 28, NULL, 0, 0, 0, '', 0),
    -- one story linking Robin and his reprint record: one appearance, from the first link
    (28, 2003, 21, NULL, 0, 0, 0, 'first', 0),
    (29, 2003, 22, NULL, 0, 0, 0, 'second', 0),
    -- Barbara Gordon by her official name; two Batgirl records with nothing to tell them apart
    (30, 2001, 31, NULL, 0, 0, 0, '', 0),
    (31, 2000, 34, NULL, 0, 0, 0, '', 0),
    (32, 2001, 35, NULL, 0, 0, 0, '', 0),
    -- two characters that both have 'The Spirit' as another name
    (33, 1000, 36, NULL, 0, 0, 0, '', 0),
    (34, 1001, 38, NULL, 0, 0, 0, '', 0),
    -- another record that lists 'Barbara Gordon' as one of its other names
    (35, 2002, 40, NULL, 0, 0, 0, '', 0);

-- what the extractor found: Hopey spelled sloppily, Esperanza with an alter ego, and Maggie
-- Chascarrillo under her full name with a stray period
INSERT INTO m_character (id, name, alter_ego, publisher_id) VALUES
    (500, 'hopey  glass!', NULL, 10),
    (501, 'Esperanza', 'Lady Z', 10),
    (502, 'Maggie Chascarrillo.', NULL, 10),
    -- DC's Robin written with the alter ego sloppily, and one with no alter ego at all
    (503, 'Robin', 'dick  grayson', 20),
    (504, 'Robin', NULL, 20),
    -- Barbara Gordon as GCD's other names for her, and a bare Maggie that could be either linked one
    (507, 'Commissioner Barbara Gordon', NULL, 20),
    (508, 'Barbara Gourdon', NULL, 20),
    (509, 'Maggie', NULL, 10),
    (510, 'The Spirit', NULL, 10),
    (511, 'Barbara Gordon', NULL, 20),
    -- the same two again spelled as GCD spells them (so renaming the first would collide with it)
    (506, 'Robin', 'Dick Grayson', 20),
    (505, 'Hopey Glass', NULL, 10);
INSERT INTO m_character_appearance (details, character_id, story_id, notes, membership, issue_id, series_id)
VALUES ('', 500, 1000, NULL, NULL, 100, 1),
       ('', 505, 1000, NULL, NULL, 100, 1),
       ('', 505, 1003, NULL, NULL, 100, 1),
       ('', 503, 2002, NULL, NULL, 200, 2),
       ('', 506, 2002, NULL, NULL, 200, 2),
       ('', 506, 2000, NULL, NULL, 200, 2),
       ('', 507, 2000, NULL, NULL, 200, 2),
       ('', 508, 2002, NULL, NULL, 200, 2),
       ('', 511, 2003, NULL, NULL, 200, 2);
"""


def mariadb(sql=None, database=None):
    env = {}
    for line in (ROOT / os.environ.get("ENV_FILE", ".env.local")).read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("'\"")
    with tempfile.NamedTemporaryFile("w", suffix=".cnf") as cnf:
        cnf.write(f"[client]\nuser={env['SQL_USER']}\npassword={env['PASSWORD']}\nhost={env.get('HOST', '127.0.0.1')}\n")
        cnf.flush()
        cmd = ["mariadb", f"--defaults-extra-file={cnf.name}", "-N", "-B"]
        if database:
            cmd.append(database)
        done = subprocess.run(cmd, input=sql, text=True, capture_output=True)
    if done.returncode != 0:
        raise RuntimeError(done.stderr)
    return [line.split("\t") for line in done.stdout.splitlines()]


class LinkedCharactersTest(unittest.TestCase):
    def setUp(self):
        mariadb(f"DROP DATABASE IF EXISTS {SCHEMA}; CREATE DATABASE {SCHEMA};")
        mariadb(TABLES + DATA, SCHEMA)
        mariadb(SCRIPT, SCHEMA)

    def tearDown(self):
        mariadb(f"DROP DATABASE IF EXISTS {SCHEMA}")

    def characters(self):
        return {(r[0], r[1]): r for r in mariadb(
            "SELECT name, publisher_id, alter_ego, gcd_character_id, id FROM m_character", SCHEMA)}

    def appearances(self, story_id):
        return mariadb(
            f"SELECT m.name, a.details, a.notes FROM m_character_appearance a "
            f"JOIN m_character m ON m.id = a.character_id WHERE a.story_id = {story_id} ORDER BY m.name", SCHEMA)

    def test_matching_extracted_character_is_taken_over_not_duplicated(self):
        chars = self.characters()
        # 'hopey  glass!' at Fantagraphics is Hopey Glass: same row, now linked to GCD's record
        self.assertEqual(sum(1 for (n, p) in chars if n.lower().startswith("hopey")), 2)
        taken = [r for r in chars.values() if r[4] == "500"][0]
        self.assertEqual(taken[3], "1")

    def test_same_character_at_another_publisher_is_a_separate_character(self):
        chars = self.characters()
        self.assertIn(("Hopey Glass", "20"), chars)
        self.assertNotEqual(chars[("Hopey Glass", "20")][4], "500")

    def test_extracted_character_with_alter_ego_is_left_alone(self):
        rows = mariadb("SELECT alter_ego, gcd_character_id FROM m_character WHERE name = 'Esperanza' ORDER BY id", SCHEMA)
        # the extractor's Esperanza keeps her alter ego and stays unlinked; GCD's is a new character
        self.assertEqual(rows, [["Lady Z", "NULL"], ["NULL", "5"]])

    def test_records_with_the_same_name_alter_ego_and_publisher_are_one_character(self):
        # GCD has Maggie (Weaver) and Maggie (Bringing Up Father) at one publisher, neither with
        # an alter ego: nothing tells them apart, so they are one Maggie, under the lower id
        self.assertEqual(self.row("name = 'Maggie' AND publisher_id = 10 AND gcd_character_id IS NOT NULL"),
                         [[self.row("gcd_character_id = 3")[0][0], "Maggie", "NULL", "3"]])
        self.assertEqual(self.row("gcd_character_id = 4"), [])
        self.assertNotIn("Maggie (Weaver)", {r[0] for r in self.characters().values()})

    def test_two_records_with_nothing_to_tell_them_apart_are_one_batgirl(self):
        batgirl = self.row("name = 'Batgirl' AND publisher_id = 20")
        self.assertEqual(len(batgirl), 1)
        self.assertEqual(
            mariadb(f"SELECT story_id FROM m_character_appearance WHERE character_id = {batgirl[0][0]} ORDER BY story_id", SCHEMA),
            [["2000"], ["2001"]])

    def test_extracted_characters_with_other_names_gcd_has_for_a_character_are_folded_into_it(self):
        # 507 is GCD's 'Commissioner Barbara Gordon', 508 a misspelling GCD lists and 511 her official
        # name, which another record lists as one of its other names: all are Barbara Gordon
        self.assertEqual(self.row("id IN (507, 508, 511)"), [["507", "Barbara Gordon", "NULL", "19"]])
        self.assertEqual(len(self.row("gcd_character_id = 19")), 1)
        stories = mariadb("SELECT story_id FROM m_character_appearance WHERE character_id = 507 ORDER BY story_id", SCHEMA)
        self.assertEqual(stories, [["2000"], ["2001"], ["2002"], ["2003"]])
        # and the record that only lists her name as another of its own is a character of its own
        self.assertEqual(self.row("gcd_character_id = 24")[0][1], "Barbara Gordon Wayne")

    def test_a_character_spelled_as_gcd_spells_its_official_name_beats_another_one_having_that_name_as_an_alias(self):
        # GCD lists 'Maggie' as another name of Maggie Chascarrillo too, but an extracted 'Maggie'
        # is the one whose official name it is
        self.assertEqual(self.row("id = 509")[0][3], "3")

    def test_a_name_that_two_linked_characters_have_as_another_name_matches_neither(self):
        # Spirit A and Spirit B are both also called 'The Spirit': an extracted 'The Spirit' is left alone
        self.assertEqual(self.row("id = 510"), [["510", "The Spirit", "NULL", "NULL"]])

    def test_linked_character_is_listed_by_its_real_name_not_the_alias_it_was_credited_as(self):
        # the dream-sequence link is to name detail 13, an alias of Maggie Chascarrillo
        self.assertIn(["Maggie Chascarrillo", "dream sequence", "NULL"], self.appearances(1000))

    def test_details_hold_notes_and_flags_and_notes_hold_the_role(self):
        # link 3: a villain's cameo, with the origin and death flags
        self.assertEqual(
            mariadb("SELECT details, notes FROM m_character_appearance WHERE gcd_story_character_id = 3", SCHEMA),
            [["cameo, origin, death", "villain"]])
        # link 10: a featured flashback
        self.assertEqual(
            mariadb("SELECT details, notes FROM m_character_appearance WHERE gcd_story_character_id = 10", SCHEMA),
            [["flashback", "featured"]])
        # no notes, flags or role at all
        self.assertEqual(
            mariadb("SELECT details, notes FROM m_character_appearance WHERE gcd_story_character_id = 4", SCHEMA),
            [["", "NULL"]])

    def test_existing_appearance_is_kept_and_nothing_is_added_beside_it(self):
        # the extractor found Hopey in story 1000; GCD's link 1 says the same, so it adds nothing
        self.assertEqual(
            mariadb("SELECT COUNT(*) FROM m_character_appearance WHERE gcd_story_character_id = 1", SCHEMA),
            [["0"]])
        # Hopey, Maggie in a dream, Esperanza in a flashback, and Spirit A
        self.assertEqual(len(self.appearances(1000)), 4)

    def test_character_already_found_in_a_story_is_not_listed_twice(self):
        hopey = [r for r in self.appearances(1000) if r[0].lower().startswith("hopey")]
        self.assertEqual(len(hopey), 1)

    def test_deleted_links_stories_and_characters_are_ignored(self):
        self.assertEqual(self.appearances(1002), [])
        names = {r[0] for r in self.characters().values()}
        self.assertNotIn("Deleted Person", names)
        count = mariadb("SELECT COUNT(*) FROM m_character_appearance WHERE gcd_story_character_id IN (7, 8, 9)", SCHEMA)
        self.assertEqual(count, [["0"]])

    def test_extracted_name_with_stray_punctuation_matches_and_takes_gcds_spelling(self):
        chars = self.characters()
        self.assertEqual(chars[("Maggie Chascarrillo", "10")][3], "2")
        self.assertEqual(chars[("Maggie Chascarrillo", "10")][4], "502")
        self.assertNotIn(("Maggie Chascarrillo.", "10"), chars)
        # and the sloppy 'hopey  glass!' too
        self.assertEqual(chars[("Hopey Glass", "10")][4], "500")

    def test_running_it_again_changes_nothing(self):
        before = (mariadb("SELECT COUNT(*) FROM m_character", SCHEMA),
                  mariadb("SELECT COUNT(*) FROM m_character_appearance", SCHEMA))
        mariadb(SCRIPT, SCHEMA)
        after = (mariadb("SELECT COUNT(*) FROM m_character", SCHEMA),
                 mariadb("SELECT COUNT(*) FROM m_character_appearance", SCHEMA))
        self.assertEqual(before, after)

    def row(self, where):
        return mariadb(f"SELECT id, name, alter_ego, gcd_character_id FROM m_character WHERE {where} ORDER BY id", SCHEMA)

    def test_alter_ego_comes_from_the_one_character_it_is_the_alias_of(self):
        self.assertEqual(self.row("gcd_character_id = 7 AND publisher_id = 20"),
                         [["503", "Robin", "Dick Grayson", "7"]])

    def test_a_character_that_is_the_alias_of_two_has_no_alter_ego(self):
        self.assertEqual(self.row("gcd_character_id = 12")[0][2:], ["NULL", "12"])

    def test_extracted_character_whose_alter_ego_matches_is_taken_over_and_spelled_as_gcd_does(self):
        # 503 was written 'dick grayson'; it is now Dick Grayson's Robin, in GCD's spelling
        self.assertEqual(self.row("id = 503"), [["503", "Robin", "Dick Grayson", "7"]])

    def test_extracted_character_with_no_alter_ego_is_not_taken_by_a_robin_who_has_one(self):
        self.assertEqual(self.row("id = 504"), [["504", "Robin", "NULL", "NULL"]])

    def test_a_reprint_record_counts_as_the_character_it_reprints_all_the_way_up_the_chain(self):
        # records 9 (a reprint of 7) and 10 (a reprint of 9) get no characters of their own...
        self.assertEqual(self.row("gcd_character_id IN (9, 10)"), [])
        # ...their appearances are Dick Grayson's Robin's
        self.assertIn(["Robin", "", "NULL"], self.appearances(2001))
        self.assertEqual([r for r in self.appearances(2002) if r[0] == "Robin"], [["Robin", "", "NULL"]])
        self.assertEqual(
            mariadb("SELECT COUNT(*) FROM m_character_appearance WHERE character_id = 503", SCHEMA), [["4"]])

    def test_extracted_duplicates_of_a_linked_character_are_folded_into_it(self):
        # 505 is another Hopey Glass at Fantagraphics; 506 is another Robin (Dick Grayson) at DC,
        # spelled exactly as GCD spells him
        self.assertEqual(self.row("id IN (505, 506)"), [])
        # their appearances are the survivors', and a story that had both has one
        hopey = mariadb("SELECT story_id FROM m_character_appearance WHERE character_id = 500 ORDER BY story_id", SCHEMA)
        self.assertEqual(hopey, [["1000"], ["1001"], ["1003"]])  # 1001 is the linked cameo
        robin = mariadb("SELECT story_id FROM m_character_appearance WHERE character_id = 503 ORDER BY story_id", SCHEMA)
        self.assertEqual(robin, [["2000"], ["2001"], ["2002"], ["2003"]])

    def test_a_story_that_links_a_character_twice_gets_one_appearance_from_the_first_link(self):
        self.assertEqual(
            mariadb("SELECT details FROM m_character_appearance WHERE story_id = 2003 AND character_id = 503", SCHEMA),
            [["first"]])

    def test_an_alternate_universe_version_stays_a_character_of_its_own(self):
        tim = self.row("gcd_character_id = 11")
        self.assertEqual(len(tim), 1)
        self.assertEqual(tim[0][2], "Tim Drake")
        self.assertNotEqual(tim[0][0], "503")

    def test_two_records_that_are_each_others_reprint_are_one_character_under_the_lower_id(self):
        self.assertEqual(self.row("gcd_character_id = 18"), [])
        twin = self.row("gcd_character_id = 17")
        self.assertEqual(len(twin), 1)
        self.assertEqual(
            mariadb(f"SELECT COUNT(*) FROM m_character_appearance WHERE character_id = {twin[0][0]}", SCHEMA), [["2"]])

    def test_a_reprint_of_a_deleted_record_stands_alone(self):
        self.assertEqual(self.row("gcd_character_id = 15")[0][1:], ["Orphan Copy", "NULL", "15"])

    def test_helper_tables_are_cleaned_up(self):
        left = mariadb(f"SHOW TABLES LIKE '%\\_work'", SCHEMA)
        self.assertEqual(left, [])


if __name__ == "__main__":
    unittest.main()
