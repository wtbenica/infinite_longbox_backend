"""db_query/local_covers.py: which issues of a series have covers, for the series card.

    python -m unittest tools.tests.test_series_covers -v
"""
import os
import tempfile
import unittest

from db_query import local_covers


class EarliestCoverIds(unittest.TestCase):
    def test_the_earliest_regular_issues_come_first(self):
        rows = [(7, 30, None, 30), (7, 10, None, 10), (7, 20, None, 20), (7, 40, None, 40)]
        self.assertEqual(local_covers.earliest_cover_ids(rows), {7: [10, 20, 30]})

    def test_regular_issues_come_before_variants_even_when_the_variant_is_earlier(self):
        rows = [(7, 11, 10, 10), (7, 20, None, 20)]
        self.assertEqual(local_covers.earliest_cover_ids(rows), {7: [20, 11]})

    def test_each_series_gets_its_own_list(self):
        rows = [(1, 5, None, 5), (2, 6, None, 1), (1, 4, None, 4)]
        self.assertEqual(local_covers.earliest_cover_ids(rows), {1: [4, 5], 2: [6]})

    def test_a_different_limit(self):
        rows = [(1, i, None, i) for i in range(1, 8)]
        self.assertEqual(local_covers.earliest_cover_ids(rows, per_series=2), {1: [1, 2]})

    def test_no_rows_no_series(self):
        self.assertEqual(local_covers.earliest_cover_ids([]), {})


class IssueIdsWithCovers(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.environ['COVERS_DIR'] = self.dir

    def tearDown(self):
        os.environ.pop('COVERS_DIR', None)

    def touch(self, *names):
        for name in names:
            open(os.path.join(self.dir, name), 'wb').close()

    def test_cover_files_by_issue_id(self):
        self.touch('100.jpg', '200.png', '300.webp', '400_IMG')
        self.assertEqual(local_covers.issue_ids_with_covers(), {100, 200, 300, 400})

    def test_other_files_are_not_covers(self):
        self.touch('100.jpg', 'notes.txt', '.DS_Store', 'abc.jpg', '5.pdf')
        self.assertEqual(local_covers.issue_ids_with_covers(), {100})

    def test_no_folder_no_covers(self):
        os.environ['COVERS_DIR'] = os.path.join(self.dir, 'missing')
        self.assertEqual(local_covers.issue_ids_with_covers(), set())


if __name__ == '__main__':
    unittest.main()
