"""Runs tools/linked_groups.sql against a small made-up database.

    ENV_FILE=.env.local python -m unittest tools.tests.test_linked_groups -v

Needs the local MariaDB; creates and drops the database `longbox_groups_test`.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "longbox_groups_test"
SCRIPT = (ROOT / "tools" / "linked_groups.sql").read_text().replace("{{targetSchema}}", SCHEMA)

TABLES = """
CREATE TABLE gcd_series (id INT PRIMARY KEY, publisher_id INT NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_issue (id INT PRIMARY KEY, series_id INT NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_story (id INT PRIMARY KEY, issue_id INT NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_character_name_detail (id INT PRIMARY KEY, character_id INT NOT NULL,
    name VARCHAR(255) NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_group (id INT PRIMARY KEY, name VARCHAR(255) NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_group_name_detail (id INT PRIMARY KEY, group_id INT NOT NULL,
    name VARCHAR(255) NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_group_relation_type (id INT PRIMARY KEY, type VARCHAR(50) NOT NULL, reverse_type VARCHAR(50) NOT NULL);
CREATE TABLE gcd_group_relation (id INT PRIMARY KEY, from_group_id INT NOT NULL,
    relation_type_id INT NOT NULL, to_group_id INT NOT NULL);
CREATE TABLE gcd_story_character (id INT PRIMARY KEY, story_id INT NOT NULL, character_id INT NOT NULL,
    deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE gcd_story_character_group (id INT PRIMARY KEY, storycharacter_id INT NOT NULL, group_id INT NOT NULL);
CREATE TABLE gcd_group_character (id INT PRIMARY KEY, story_id INT NOT NULL, group_name_id INT NOT NULL,
    notes LONGTEXT NOT NULL, deleted TINYINT NOT NULL DEFAULT 0);
CREATE TABLE m_character (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255) NOT NULL,
    alter_ego VARCHAR(255), publisher_id INT NOT NULL, gcd_character_id INT NULL,
    UNIQUE KEY name_2 (name, alter_ego, publisher_id));
CREATE TABLE m_character_appearance (id INT PRIMARY KEY AUTO_INCREMENT, details VARCHAR(255),
    character_id INT NOT NULL, story_id INT NOT NULL, notes VARCHAR(255), membership LONGTEXT,
    issue_id INT NOT NULL, series_id INT NOT NULL);
"""

# Series 1 is Fantagraphics-ish (publisher 10), series 2 is DC (publisher 20); one issue each
DATA = """
INSERT INTO gcd_series VALUES (1, 10, 0), (2, 20, 0);
INSERT INTO gcd_issue VALUES (100, 1, 0), (200, 2, 0);
INSERT INTO gcd_story VALUES (1000, 100, 0), (1001, 100, 0), (1002, 100, 1), (2000, 200, 0), (2001, 200, 0);

-- Challengers of the Unknown, also called Challengers; the Justice League, which JLA republishes;
-- Fenris, a group whose name is also a character's; a deleted group
INSERT INTO gcd_group VALUES (1, 'Challengers of the Unknown', 0), (2, 'Justice League', 0), (3, 'JLA', 0),
    (4, 'Fenris', 0), (5, 'Deleted Team', 1);
INSERT INTO gcd_group_name_detail VALUES (21, 1, 'Challengers of the Unknown', 0), (22, 1, 'Challengers', 0),
    (23, 2, 'Justice League', 0), (24, 3, 'JLA', 0), (25, 4, 'Fenris', 0), (26, 5, 'Deleted Team', 0);
INSERT INTO gcd_group_relation_type VALUES (1, 'republished as', 'originally published as'),
    (2, 'alternate universe version of', 'alternate universe version of');
INSERT INTO gcd_group_relation VALUES (1, 2, 1, 3);

INSERT INTO gcd_character_name_detail VALUES (11, 1, 'Superman', 0), (12, 2, 'Ace Morgan', 0),
    (13, 3, 'Rocky Davis', 0), (14, 4, 'Fenris', 0);
-- Ace Morgan and Rocky Davis appeared in story 1000 as part of the Challengers; Superman alone
INSERT INTO gcd_story_character VALUES (1, 1000, 12, 0), (2, 1000, 13, 0), (3, 2000, 11, 0), (4, 1000, 14, 1);
INSERT INTO gcd_story_character_group VALUES (1, 1, 1), (2, 2, 1), (3, 4, 1);

INSERT INTO gcd_group_character VALUES
    (1, 1000, 21, '', 0),
    (2, 1001, 22, '', 0),
    (3, 2000, 24, 'cameo', 0),
    (4, 1002, 21, '', 0),
    (5, 1000, 25, '', 0),
    (6, 2001, 21, 'cameo', 0),
    (7, 1001, 21, '', 1),
    (8, 1000, 26, '', 0);

-- what the extractor found: the Challengers by two names, with the roster guessed from the text,
-- the Justice League at DC, Fenris (also a character), and Superman
INSERT INTO m_character (id, name, alter_ego, publisher_id) VALUES
    (500, 'Challengers of the Unknown', NULL, 10),
    (501, 'challengers', NULL, 10),
    (502, 'Justice League', NULL, 20),
    (503, 'Fenris', NULL, 10),
    (504, 'Superman', NULL, 10);
INSERT INTO m_character_appearance (details, character_id, story_id, notes, membership, issue_id, series_id)
VALUES ('', 500, 1000, NULL, 'Ace Morgan; Rocky Davis; Guessed', 100, 1),
       ('', 501, 1001, NULL, 'Ace Morgan', 100, 1),
       ('', 502, 2000, NULL, 'from the text', 200, 2),
       ('', 503, 1000, NULL, NULL, 100, 1),
       ('', 504, 1000, NULL, NULL, 100, 1);
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


class LinkedGroupsTest(unittest.TestCase):
    def setUp(self):
        mariadb(f"DROP DATABASE IF EXISTS {SCHEMA}; CREATE DATABASE {SCHEMA};")
        mariadb(TABLES + DATA, SCHEMA)
        mariadb(SCRIPT, SCHEMA)

    def tearDown(self):
        mariadb(f"DROP DATABASE IF EXISTS {SCHEMA}")

    def teams(self):
        return mariadb("SELECT id, name, publisher_id, gcd_group_id FROM m_character "
                       "WHERE gcd_group_id IS NOT NULL ORDER BY publisher_id, name", SCHEMA)

    def appearance(self, story_id, character_name, publisher_id):
        return mariadb(
            f"SELECT a.details, a.membership, a.gcd_group_character_id FROM m_character_appearance a "
            f"JOIN m_character m ON m.id = a.character_id WHERE a.story_id = {story_id} "
            f"AND m.name = '{character_name}' AND m.publisher_id = {publisher_id}", SCHEMA)

    def test_an_extracted_name_matching_a_group_is_taken_over_and_spelled_as_gcd_does(self):
        self.assertIn(["500", "Challengers of the Unknown", "10", "1"], self.teams())

    def test_extracted_names_of_the_same_group_are_folded_into_one_team(self):
        names = [t[1] for t in self.teams() if t[2] == "10"]
        self.assertEqual(names.count("Challengers of the Unknown"), 1)
        self.assertEqual(mariadb("SELECT COUNT(*) FROM m_character WHERE id = 501", SCHEMA), [["0"]])
        # the appearance of the one folded in belongs to the one kept, with the link of its story
        self.assertEqual(self.appearance(1001, "Challengers of the Unknown", 10), [["", "Ace Morgan", "2"]])

    def test_the_roster_is_who_gcd_says_appeared_as_part_of_the_group(self):
        self.assertEqual(self.appearance(1000, "Challengers of the Unknown", 10),
                         [["", "Ace Morgan; Rocky Davis", "1"]])

    def test_a_republished_group_counts_as_the_original_and_keeps_the_text_without_a_roster(self):
        self.assertIn(["502", "Justice League", "20", "2"], self.teams())
        self.assertEqual(self.appearance(2000, "Justice League", 20), [["cameo", "from the text", "3"]])

    def test_a_group_nothing_was_extracted_for_is_added_with_its_appearance(self):
        self.assertEqual(self.appearance(2001, "Challengers of the Unknown", 20), [["cameo", "NULL", "6"]])

    def test_a_name_that_is_also_a_characters_is_not_taken_from_the_text_but_the_group_is_added(self):
        fenris = mariadb("SELECT id, gcd_group_id FROM m_character WHERE name = 'Fenris' ORDER BY id", SCHEMA)
        self.assertEqual(fenris[0], ["503", "NULL"])
        self.assertEqual(len(fenris), 2)
        self.assertEqual(fenris[1][1], "4")

    def test_a_character_that_is_no_group_is_left_alone(self):
        self.assertEqual(mariadb("SELECT gcd_group_id FROM m_character WHERE id = 504", SCHEMA), [["NULL"]])

    def test_deleted_links_stories_and_groups_are_ignored(self):
        self.assertEqual(mariadb("SELECT COUNT(*) FROM m_character WHERE name = 'Deleted Team'", SCHEMA), [["0"]])
        self.assertEqual(mariadb("SELECT COUNT(*) FROM m_character_appearance WHERE story_id = 1002", SCHEMA), [["0"]])
        self.assertEqual(mariadb(
            "SELECT COUNT(*) FROM m_character_appearance WHERE gcd_group_character_id IN (4, 7, 8)", SCHEMA), [["0"]])

    def test_running_it_again_changes_nothing(self):
        before = (mariadb("SELECT COUNT(*) FROM m_character", SCHEMA),
                  mariadb("SELECT COUNT(*) FROM m_character_appearance", SCHEMA),
                  mariadb("SELECT id, membership FROM m_character_appearance ORDER BY id", SCHEMA))
        mariadb(SCRIPT, SCHEMA)
        after = (mariadb("SELECT COUNT(*) FROM m_character", SCHEMA),
                 mariadb("SELECT COUNT(*) FROM m_character_appearance", SCHEMA),
                 mariadb("SELECT id, membership FROM m_character_appearance ORDER BY id", SCHEMA))
        self.assertEqual(before, after)

    def test_helper_tables_are_cleaned_up(self):
        self.assertEqual(mariadb("SHOW TABLES LIKE '%\\_work'", SCHEMA), [])


if __name__ == "__main__":
    unittest.main()
