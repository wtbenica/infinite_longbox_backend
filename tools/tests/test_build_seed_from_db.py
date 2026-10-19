"""The conversions in tools/build_seed_from_db.py, which have to match what the app does with a row
(database/models/GcdJson.kt, Issue.formatDate): the seed is only as good as they are.

    python -m unittest tools.tests.test_build_seed_from_db -v
"""
import importlib.util
import os
import unittest

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build_seed_from_db.py')
spec = importlib.util.spec_from_file_location('build_seed_from_db', path)
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)

TODAY = '2026-10-19'


class YearDates(unittest.TestCase):
    def test_a_year_is_its_first_of_january(self):
        self.assertEqual(seed.year_date(1939), '1939-01-01')
        self.assertEqual(seed.year_date(987), '0987-01-01')

    def test_years_past_9999_are_written_with_a_plus_as_java_does(self):
        self.assertEqual(seed.year_date(99999), '+99999-01-01')
        self.assertEqual(seed.year_date(20110), '+20110-01-01')

    def test_the_year_a_series_gets_when_it_has_none_is_localdate_min(self):
        self.assertEqual(seed.year_date(seed.MIN_YEAR), '-999999999-01-01')


class IssueDates(unittest.TestCase):
    def test_a_full_date(self):
        self.assertEqual(seed.issue_date('1907-04-11'), '1907-04-11')

    def test_zero_months_and_days_become_the_first(self):
        self.assertEqual(seed.issue_date('1935-10-00'), '1935-10-01')
        self.assertEqual(seed.issue_date('1935-00-00'), '1935-01-01')

    def test_a_month_without_a_day_gets_the_first(self):
        self.assertEqual(seed.issue_date('1935-10'), '1935-10-01')

    def test_a_day_that_does_not_exist_falls_back_to_the_year(self):
        self.assertEqual(seed.issue_date('1935-02-31'), '1935-01-01')

    def test_nothing_is_nothing(self):
        self.assertIsNone(seed.issue_date(''))
        self.assertIsNone(seed.issue_date(None))
        self.assertIsNone(seed.issue_date('not a date'))


class IssueNumbers(unittest.TestCase):
    def test_the_number_is_what_comes_before_a_space_or_bracket(self):
        self.assertEqual(seed.int_from_string('18'), 18)
        self.assertEqual(seed.int_from_string('9 [Direct]'), 9)
        self.assertEqual(seed.int_from_string('12(a)'), 12)
        self.assertEqual(seed.int_from_string('7[b]'), 7)

    def test_something_that_is_not_a_number_is_one(self):
        self.assertEqual(seed.int_from_string('Annual'), 1)
        self.assertEqual(seed.int_from_string(''), 1)


class Barcodes(unittest.TestCase):
    def test_digits_are_a_number(self):
        self.assertEqual(seed.long_or_none('75960606123400111'), 75960606123400111)

    def test_anything_else_is_nothing(self):
        for text in ('', None, '7596 0606', 'n/a', '9' * 30):
            self.assertIsNone(seed.long_or_none(text), text)


class ContentHash(unittest.TestCase):
    def database(self, rows, extra=''):
        import sqlite3
        con = sqlite3.connect(':memory:')
        con.execute('CREATE TABLE T (id INTEGER PRIMARY KEY, name TEXT)')
        con.executemany('INSERT INTO T VALUES (?, ?)', rows)
        if extra:
            con.execute(extra)
        return con

    def test_the_same_rows_give_the_same_fingerprint_whatever_order_they_went_in(self):
        a = self.database([(1, 'a'), (2, 'b'), (3, 'c')])
        b = self.database([(3, 'c'), (1, 'a'), (2, 'b')])
        self.assertEqual(seed.content_hash(a), seed.content_hash(b))

    def test_a_changed_row_changes_it(self):
        a = self.database([(1, 'a'), (2, 'b')])
        b = self.database([(1, 'a'), (2, 'B')])
        self.assertNotEqual(seed.content_hash(a), seed.content_hash(b))

    def test_a_missing_row_changes_it(self):
        self.assertNotEqual(seed.content_hash(self.database([(1, 'a'), (2, 'b')])),
                            seed.content_hash(self.database([(1, 'a')])))

    def test_a_changed_table_layout_changes_it(self):
        a = self.database([(1, 'a')])
        b = self.database([(1, 'a')], 'CREATE INDEX byname ON T (name)')
        self.assertNotEqual(seed.content_hash(a), seed.content_hash(b))


class Rows(unittest.TestCase):
    def test_a_series_with_no_year_began_and_blank_text(self):
        row = seed.series_row(5, {
            'name': 'Doom Patrol', 'sort_name': 'Doom Patrol', 'year_began': None, 'year_ended': 1995,
            'publisher': 54, 'tracking_notes': '', 'publishing_format': '', 'first_issue': None,
            'notes': '', 'issue_count': 22}, TODAY)
        self.assertEqual(row['startDate'], '-999999999-01-01')
        self.assertEqual(row['endDate'], '1995-01-01')
        self.assertIsNone(row['description'])
        self.assertIsNone(row['publishingFormat'])
        self.assertIsNone(row['notes'])
        self.assertEqual((row['volume'], row['lastUpdated']), (1, TODAY))

    def test_a_publisher_flags_are_zero_or_one(self):
        row = seed.publisher_row(54, {
            'name': 'DC', 'year_began': 1934, 'year_began_uncertain': 1, 'year_ended': None,
            'year_ended_uncertain': 0, 'url': ''}, TODAY)
        self.assertEqual((row['yearBeganUncertain'], row['yearEndedUncertain']), (1, 0))
        self.assertIsNone(row['url'])
        self.assertIsNone(row['yearEnded'])

    def test_an_issue(self):
        row = seed.issue_row(212404, {
            'number': '18 [Direct]', 'series': 7533, 'sort_code': 17, 'on_sale_date': '1986-00-00',
            'on_sale_date_uncertain': 1, 'key_date': '1986-05-00', 'publication_date': 'May 1986',
            'notes': '', 'barcode': '', 'variant_name': '', 'variant_of': None}, TODAY)
        self.assertEqual(row['issueNum'], 18)
        self.assertEqual(row['issueNumRaw'], '18 [Direct]')
        self.assertEqual((row['releaseDate'], row['coverDate']), ('1986-01-01', '1986-05-01'))
        self.assertEqual(row['onSaleDateUncertain'], 1)
        self.assertEqual(row['coverDateLong'], 'May 1986')
        self.assertIsNone(row['upc'])
        self.assertIsNone(row['notes'])

    def test_a_creator_and_a_name_detail(self):
        creator = seed.creator_row(1, {'gcd_official_name': 'Will Eisner', 'sort_name': 'Eisner, Will', 'bio': ''}, TODAY)
        self.assertEqual((creator['name'], creator['bio']), ('Will Eisner', None))
        detail = seed.name_detail_row(2, {'creator': 1, 'name': 'Will Eisner', 'sort_name': ''}, TODAY)
        self.assertEqual((detail['creator'], detail['sortName']), (1, None))


if __name__ == '__main__':
    unittest.main()
