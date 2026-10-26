"""Runs tools/merge_duplicate_characters.sql against a small made-up database.

    ENV_FILE=.env.local python -m unittest tools.tests.test_merge_duplicate_characters -v

Needs the local MariaDB; creates and drops the database `longbox_merge_test`.
"""
import unittest
from pathlib import Path

from tools.tests.test_linked_characters import mariadb

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "longbox_merge_test"
SCRIPT = (ROOT / "tools" / "merge_duplicate_characters.sql").read_text().replace("{{targetSchema}}", SCHEMA)

TABLES = """
CREATE TABLE m_character (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255) NOT NULL,
    alter_ego VARCHAR(255), publisher_id INT NOT NULL, gcd_character_id INT NULL,
    gcd_group_id INT NULL, UNIQUE KEY name_2 (name, alter_ego, publisher_id));
CREATE TABLE m_character_appearance (id INT PRIMARY KEY AUTO_INCREMENT, details VARCHAR(255),
    character_id INT NOT NULL, story_id INT NOT NULL, notes VARCHAR(255), membership LONGTEXT,
    issue_id INT NOT NULL DEFAULT 1, series_id INT NOT NULL DEFAULT 1, gcd_story_character_id INT NULL);
"""

# Publisher 1 is Marvel, 2 is DC
CHARACTERS = """
INSERT INTO m_character (id, name, alter_ego, publisher_id, gcd_character_id) VALUES
    -- Sunspot, three spellings of the name and one with name and alter ego the other way round
    (1, 'Roberto DaCosta', 'Sunspot', 1, NULL),
    (2, 'Roberto Da Costa', 'Sunspot', 1, NULL),
    (3, 'Roberto Da Costa]', 'Sunspot', 1, NULL),
    (4, 'Sunspot', 'Roberto DaCosta', 1, NULL),
    -- the same name and alter ego at another publisher
    (9, 'Roberto Da Costa', 'Sunspot', 2, NULL),
    -- two linked characters swapped, and a linked one with an extracted one swapped
    (5, 'Batgirl', 'Barbara Gordon', 2, 100),
    (6, 'Barbara Gordon', 'Batgirl', 2, 101),
    (7, 'Oracle', 'Barbara Gordon', 2, 102),
    (8, 'Barbara Gordon', 'Oracle', 2, NULL),
    -- near misses, and an alter ego against none
    (10, 'Damian', 'Robin', 1, NULL),
    (11, 'Damian Wayne', 'Robin', 1, NULL),
    (12, 'Robin', NULL, 1, NULL),
    (13, 'Robin', 'Dick Grayson', 1, NULL),
    (14, 'ROBIN!', NULL, 1, NULL),
    -- two linked characters with the same name: GCD's, so neither is removed
    (15, 'Maggie', NULL, 1, 200),
    (16, 'maggie', NULL, 1, 201);
-- a character and a team of one name, GCD's both, and an extracted one of that name
INSERT INTO m_character (id, name, alter_ego, publisher_id, gcd_character_id, gcd_group_id) VALUES
    (17, 'Fenris', NULL, 1, 300, NULL),
    (18, 'FENRIS!', NULL, 1, NULL, 5),
    (19, 'Fenris?', NULL, 1, NULL, NULL);
"""


def appearances(character_id, stories):
    return "".join(
        f"INSERT INTO m_character_appearance (details, character_id, story_id) VALUES ('', {character_id}, {s});\n"
        for s in stories)


APPEARANCES = (
    appearances(1, [10]) + appearances(2, [11, 12, 13]) + appearances(3, [14]) +
    appearances(4, [20, 21, 22, 23, 24, 25]) + appearances(8, [30, 31]) +
    appearances(7, [32]) + appearances(12, [40, 41]) + appearances(14, [41, 42]) +
    appearances(9, [50]) + appearances(5, [60]) + appearances(6, [61])
)


class MergeDuplicateCharactersTest(unittest.TestCase):
    def setUp(self):
        mariadb(f"DROP DATABASE IF EXISTS {SCHEMA}; CREATE DATABASE {SCHEMA};")
        mariadb(TABLES + CHARACTERS + APPEARANCES, SCHEMA)
        mariadb(SCRIPT, SCHEMA)

    def tearDown(self):
        mariadb(f"DROP DATABASE IF EXISTS {SCHEMA}")

    def ids(self):
        return [int(r[0]) for r in mariadb("SELECT id FROM m_character ORDER BY id", SCHEMA)]

    def stories(self, character_id):
        return [int(r[0]) for r in mariadb(
            f"SELECT story_id FROM m_character_appearance WHERE character_id = {character_id} ORDER BY story_id", SCHEMA)]

    def test_spellings_that_differ_only_in_spacing_and_punctuation_are_one_character(self):
        # 1, 2 and 3 are all Roberto Da Costa / Sunspot: none is left (the swapped 4 ends up with them)
        self.assertNotIn(1, self.ids())
        self.assertNotIn(2, self.ids())
        self.assertNotIn(3, self.ids())

    def test_name_and_alter_ego_swapped_are_one_character_and_the_better_known_orientation_stays(self):
        # 4 (Sunspot / Roberto DaCosta) has more appearances than the merged 2, so it is kept
        self.assertIn(4, self.ids())
        self.assertNotIn(2, self.ids())
        self.assertEqual(self.stories(4), [10, 11, 12, 13, 14, 20, 21, 22, 23, 24, 25])

    def test_the_same_name_and_alter_ego_at_another_publisher_is_left_alone(self):
        self.assertIn(9, self.ids())
        self.assertEqual(self.stories(9), [50])

    def test_a_linked_character_is_kept_over_an_extracted_one_it_is_swapped_with(self):
        self.assertIn(7, self.ids())
        self.assertNotIn(8, self.ids())
        self.assertEqual(self.stories(7), [30, 31, 32])

    def test_two_linked_characters_swapped_are_both_left_alone(self):
        self.assertTrue({5, 6} <= set(self.ids()))

    def test_near_misses_are_left_alone(self):
        self.assertTrue({10, 11} <= set(self.ids()))

    def test_a_character_with_an_alter_ego_is_not_merged_with_one_without(self):
        self.assertIn(13, self.ids())
        self.assertIn(12, self.ids())

    def test_characters_with_no_alter_ego_and_the_same_name_are_one_character_with_each_story_once(self):
        # 14 is 'ROBIN!' with no alter ego, as is 12; both are in story 41
        self.assertNotIn(14, self.ids())
        self.assertEqual(self.stories(12), [40, 41, 42])

    def test_linked_characters_are_never_removed(self):
        self.assertTrue({15, 16} <= set(self.ids()))

    def test_a_team_is_never_removed_or_merged_into_a_character_of_its_name(self):
        self.assertTrue({17, 18} <= set(self.ids()))
        self.assertNotIn(19, self.ids())

    def test_running_it_again_changes_nothing(self):
        before = (mariadb("SELECT id FROM m_character ORDER BY id", SCHEMA),
                  mariadb("SELECT COUNT(*) FROM m_character_appearance", SCHEMA))
        mariadb(SCRIPT, SCHEMA)
        after = (mariadb("SELECT id FROM m_character ORDER BY id", SCHEMA),
                 mariadb("SELECT COUNT(*) FROM m_character_appearance", SCHEMA))
        self.assertEqual(before, after)

    def test_helper_tables_are_cleaned_up(self):
        self.assertEqual(mariadb("SHOW TABLES LIKE '%\\_work'", SCHEMA), [])


if __name__ == "__main__":
    unittest.main()
