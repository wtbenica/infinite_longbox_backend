"""db_query/character_info.py: what the character page shows.

    python -m unittest tools.tests.test_character_info -v
"""
import unittest

from db_query import character_info


class AlternateNames(unittest.TestCase):
    def test_official_names_come_first_then_alphabetical(self):
        rows = [('Zed', False), ('Batgirl II', True), ('Alpha', False)]
        self.assertEqual(character_info.alternate_names('Batgirl', rows), ['Batgirl II', 'Alpha', 'Zed'])

    def test_the_characters_own_name_is_not_an_alternate(self):
        self.assertEqual(character_info.alternate_names('Batgirl', [('batgirl', True), ('Oracle', False)]), ['Oracle'])

    def test_a_name_is_listed_once_whatever_its_case_or_spacing(self):
        rows = [('Oracle', False), ('ORACLE', True), (' Oracle ', False)]
        self.assertEqual(character_info.alternate_names('Barbara Gordon', rows), ['ORACLE'])

    def test_blank_names_are_dropped(self):
        self.assertEqual(character_info.alternate_names('X', [('', True), ('  ', False)]), [])


class Teams(unittest.TestCase):
    def test_earliest_joined_first_and_undated_last(self):
        rows = [(2, 'Outsiders', None, None, 'formal', ''), (1, 'JLA', 1960, 1970, 'formal', ''),
                (3, 'Birds of Prey', 1996, None, 'associated', 'on and off')]
        self.assertEqual([t['name'] for t in character_info.teams(rows)], ['JLA', 'Birds of Prey', 'Outsiders'])

    def test_a_team_two_records_belong_to_is_listed_once_with_the_widest_years(self):
        rows = [(1, 'JLA', 1965, 1970, 'formal', ''), (1, 'JLA', 1960, 1968, 'formal', '')]
        self.assertEqual(character_info.teams(rows), [
            {'groupId': 1, 'name': 'JLA', 'yearJoined': 1960, 'yearLeft': 1970, 'membership': 'formal', 'notes': ''}])

    def test_two_groups_with_one_name_are_one_team(self):
        rows = [(5, 'Batman Incorporated', 2011, None, 'formal', ''), (9, 'Batman Incorporated', 2012, None, 'formal', '')]
        self.assertEqual([t['groupId'] for t in character_info.teams(rows)], [5])

    def test_a_missing_year_does_not_hide_a_known_one(self):
        rows = [(1, 'JLA', None, None, 'formal', ''), (1, 'JLA', 1960, 1970, 'formal', '')]
        team = character_info.teams(rows)[0]
        self.assertEqual((team['yearJoined'], team['yearLeft']), (1960, 1970))


class RelationLabel(unittest.TestCase):
    def test_from_side_reads_the_relation_and_to_side_its_reverse(self):
        self.assertEqual(character_info.relation_label('alias of', 'secret identity of', True), 'alias of')
        self.assertEqual(character_info.relation_label('alias of', 'secret identity of', False), 'secret identity of')

    def test_a_relation_with_no_reverse_reads_the_same_both_ways(self):
        self.assertEqual(character_info.relation_label('x', '', False), 'x')


class OneEach(unittest.TestCase):
    def item(self, id, name='Barbara Gordon', relation='alias of', ego=''):
        return {'relation': relation, 'characterId': id, 'name': name, 'alterEgo': ego, 'detail': ''}

    def test_records_of_one_identity_are_listed_once_preferring_the_one_the_app_has(self):
        got = character_info.one_each([self.item(None), self.item(110957), self.item(None)])
        self.assertEqual([i['characterId'] for i in got], [110957])

    def test_different_relations_or_alter_egos_stay_separate(self):
        got = character_info.one_each([self.item(1), self.item(2, relation='secret identity of'), self.item(3, ego='x')])
        self.assertEqual(len(got), 3)


class Issue(unittest.TestCase):
    def test_the_year_comes_from_the_key_date(self):
        self.assertEqual(character_info._issue((1, 2, 'Batman', '27', '1940-04-00'))['year'], 1940)

    def test_no_date_no_year(self):
        self.assertIsNone(character_info._issue((1, 2, 'Batman', '27', ''))['year'])
        self.assertIsNone(character_info._issue((1, 2, 'Batman', '27', None))['year'])

    def test_no_row_no_issue(self):
        self.assertIsNone(character_info._issue(None))


class OnlyListedStories(unittest.TestCase):
    """Needs the database; skipped without one."""

    def test_the_story_filter_is_the_one_the_app_lists(self):
        self.assertIn('IN (6, 19)', character_info.STORY_JOIN)

    def test_first_appearance_is_in_a_story_the_app_lists(self):
        try:
            import django
            import os
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gcd_server.settings')
            django.setup()
            rows = character_info._run(
                'SELECT a.character_id FROM m_character_appearance a '
                'JOIN gcd_story st ON st.id = a.story_id AND st.type_id NOT IN (6, 19) LIMIT 1')
        except Exception as e:  # no database here
            self.skipTest(str(e))
        if not rows:
            self.skipTest('no appearances in other story types')
        first = character_info._first_issue(rows[0][0])
        if first is None:
            return
        listed = character_info._run(
            'SELECT 1 FROM m_character_appearance a ' + character_info.STORY_JOIN +
            'WHERE a.character_id = %s AND a.issue_id = %s', [rows[0][0], first['issueId']])
        self.assertTrue(listed)
