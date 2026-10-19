"""db_query/page_index.py: the cached page counts and pages the sync endpoints answer from.

    python -m unittest tools.tests.test_page_index -v
"""
import os
import tempfile
import time
import unittest

from db_query import page_index


class FakeManager:
    def __init__(self, rows):
        self.rows = rows

    def count(self):
        return self.rows


class FakeModel:
    def __init__(self, rows):
        self._base_manager = FakeManager(rows)


class Paging(unittest.TestCase):
    def test_the_last_page_counts_even_when_it_is_empty_or_partly_filled(self):
        # what the app has always been told: rows // 500 + 1
        self.assertEqual(page_index.num_pages(0), 1)
        self.assertEqual(page_index.num_pages(499), 1)
        self.assertEqual(page_index.num_pages(500), 2)
        self.assertEqual(page_index.num_pages(578025), 1157)

    def test_a_page_is_500_ids_in_order(self):
        ids = list(range(10, 2010, 2))  # 1000 ids
        self.assertEqual(page_index.page_ids(ids, 0), ids[:500])
        self.assertEqual(page_index.page_ids(ids, 1), ids[500:])

    def test_a_page_past_the_end_is_empty(self):
        self.assertEqual(page_index.page_ids([1, 2, 3], 1), [])
        self.assertEqual(page_index.page_ids([], 0), [])


class Index(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.environ['SEED_DIR'] = self.dir
        page_index._loaded.update(mtime=None, data=None)
        page_index._checked.clear()

    def tearDown(self):
        os.environ.pop('SEED_DIR', None)

    def write(self, ids, rows):
        page_index.write({'character': {'rows': rows, 'ids': ids}}, self.dir)

    def test_no_index_means_no_ids(self):
        self.assertIsNone(page_index.ids_for('character', FakeModel(3)))

    def test_an_index_that_fits_the_table_is_used(self):
        self.write([1, 2, 3], rows=5)
        self.assertEqual(page_index.ids_for('character', FakeModel(5)), [1, 2, 3])

    def test_an_index_made_from_a_different_table_is_not(self):
        self.write([1, 2, 3], rows=5)
        self.assertIsNone(page_index.ids_for('character', FakeModel(6)))

    def test_a_model_the_index_does_not_have_is_not_in_it(self):
        self.write([1, 2, 3], rows=5)
        self.assertIsNone(page_index.ids_for('series', FakeModel(5)))

    def test_a_new_index_is_picked_up_without_a_restart(self):
        self.write([1, 2, 3], rows=5)
        self.assertEqual(page_index.ids_for('character', FakeModel(5)), [1, 2, 3])
        time.sleep(0.02)
        self.write([1, 2, 3, 4], rows=7)
        os.utime(page_index.index_path(), (time.time() + 5, time.time() + 5))
        self.assertEqual(page_index.ids_for('character', FakeModel(7)), [1, 2, 3, 4])

    def test_the_row_count_is_not_asked_for_on_every_request(self):
        self.write([1, 2, 3], rows=5)
        model = FakeModel(5)
        calls = []
        original = model._base_manager.count
        model._base_manager.count = lambda: calls.append(1) or original()
        for _ in range(5):
            page_index.ids_for('character', model)
        self.assertEqual(len(calls), 1)

    def test_writing_leaves_no_half_written_file(self):
        self.write([1], rows=1)
        self.assertEqual(sorted(os.listdir(self.dir)), ['page_index.json'])


if __name__ == '__main__':
    unittest.main()
