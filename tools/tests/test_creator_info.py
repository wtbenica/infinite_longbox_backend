"""db_query/creator_info.py: what the creator page shows.

    python -m unittest tools.tests.test_creator_info -v
"""
import unittest

from db_query import creator_info as ci


class DateText(unittest.TestCase):
    def test_full_partial_and_missing_dates(self):
        self.assertEqual(ci.date_text('1917', '08', '28'), 'Aug 28, 1917')
        self.assertEqual(ci.date_text('1917', '08', ''), 'Aug 1917')
        self.assertEqual(ci.date_text('1917', '', ''), '1917')
        self.assertEqual(ci.date_text('', '', ''), '')
        self.assertEqual(ci.date_text('0', '0', '0'), '')
        self.assertEqual(ci.date_text(None, None, None), '')

    def test_a_nonsense_month_or_day_is_ignored(self):
        self.assertEqual(ci.date_text('1917', '13', '28'), '1917')
        self.assertEqual(ci.date_text('1917', '02', '00'), 'Feb 1917')


class PlaceText(unittest.TestCase):
    def test_parts_in_order_without_blanks_or_repeats(self):
        self.assertEqual(ci.place_text('Thousand Oaks', '', 'California', 'United States'),
                         'Thousand Oaks, California, United States')
        self.assertEqual(ci.place_text('New York', 'New York', None), 'New York')
        self.assertEqual(ci.place_text('', None), '')


class RoleCounts(unittest.TestCase):
    def test_combined_credits_count_toward_each_role(self):
        got = ci.role_counts([('pencils and inks', 10), ('pencils', 5), ('script', 3)])
        self.assertEqual(got, [{'role': 'Penciler', 'count': 15}, {'role': 'Inker', 'count': 10},
                               {'role': 'Writer', 'count': 3}])

    def test_ties_keep_the_usual_order(self):
        got = ci.role_counts([('letters', 4), ('script', 4)])
        self.assertEqual([r['role'] for r in got], ['Writer', 'Letterer'])

    def test_no_credits_no_roles(self):
        self.assertEqual(ci.role_counts([]), [])


class OtherNames(unittest.TestCase):
    def test_kinds_are_labelled_and_misspellings_dropped(self):
        rows = [('Jacob Kurtzberg', 0, 'Name at Birth'), ('Jolly Jack', 0, 'Pen Name'),
                ('Jack Kirbi', 0, 'Misspelled Name'), ('Jack Kirby', 1, None), ('J. Kirby', 0, 'Common Alternative Name')]
        self.assertEqual(ci.other_names('Jack Kirby', rows), [
            {'name': 'J. Kirby', 'kind': ''}, {'name': 'Jacob Kurtzberg', 'kind': 'birth name'},
            {'name': 'Jolly Jack', 'kind': 'pen name'}])


class Links(unittest.TestCase):
    TEXT = 'with [gcd_link_creator](6805) he made [gcd_link_feature](1211) at [gcd_link_publisher](78).'

    def test_ids_by_kind(self):
        self.assertEqual(ci.link_ids(self.TEXT), {'creator': {6805}, 'feature': {1211}, 'publisher': {78}})

    def test_known_names_replace_links_and_unknown_ones_vanish_cleanly(self):
        names = {('creator', 6805): 'Joe Simon', ('publisher', 78): 'DC'}
        self.assertEqual(ci.resolve_links(self.TEXT, names), 'with Joe Simon he made at DC.')

    def test_a_run_of_unknown_links_does_not_leave_commas(self):
        text = 'including [gcd_link_feature](1), [gcd_link_feature](2), [gcd_link_feature](3), among others'
        self.assertEqual(ci.resolve_links(text, {}), 'including, among others')

    def test_text_without_links_is_unchanged(self):
        self.assertEqual(ci.resolve_links('A plain bio.', {}), 'A plain bio.')
        self.assertEqual(ci.resolve_links(None, {}), '')
