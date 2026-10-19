"""db_query/local_covers.py get_cover: a conditional request for a cover the phone already has.

    python -m unittest tools.tests.test_cover_download -v
"""
import email.utils
import os
import tempfile
import time
import unittest

import django
from django.test import RequestFactory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gcd_server.settings')
django.setup()

from db_query import local_covers  # noqa: E402


class GetCover(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.environ['COVERS_DIR'] = self.dir
        self.path = os.path.join(self.dir, '42.jpg')
        with open(self.path, 'wb') as f:
            f.write(b'\xff\xd8\xff not really a jpeg')
        os.utime(self.path, (1_700_000_000, 1_700_000_000))

    def tearDown(self):
        os.environ.pop('COVERS_DIR', None)

    def get(self, id=42, **headers):
        request = RequestFactory().get(f'/x/{id}/cover', **headers)
        return local_covers.get_cover(request, id)

    def test_a_cover_comes_with_the_time_it_last_changed(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Last-Modified'], email.utils.formatdate(1_700_000_000, usegmt=True))
        b''.join(response.streaming_content)

    def test_a_copy_that_is_current_is_not_sent_again(self):
        stamp = email.utils.formatdate(1_700_000_000, usegmt=True)
        response = self.get(HTTP_IF_MODIFIED_SINCE=stamp)
        self.assertEqual(response.status_code, 304)

    def test_a_copy_older_than_the_server_s_is_sent(self):
        stamp = email.utils.formatdate(1_600_000_000, usegmt=True)
        response = self.get(HTTP_IF_MODIFIED_SINCE=stamp)
        self.assertEqual(response.status_code, 200)
        b''.join(response.streaming_content)

    def test_a_cover_replaced_on_the_server_is_sent_to_a_phone_that_has_the_old_one(self):
        stamp = email.utils.formatdate(1_700_000_000, usegmt=True)
        now = time.time()
        os.utime(self.path, (now, now))
        response = self.get(HTTP_IF_MODIFIED_SINCE=stamp)
        self.assertEqual(response.status_code, 200)
        b''.join(response.streaming_content)

    def test_no_cover_is_a_404_even_when_asked_conditionally(self):
        stamp = email.utils.formatdate(1_700_000_000, usegmt=True)
        self.assertEqual(self.get(id=99).status_code, 404)
        self.assertEqual(self.get(id=99, HTTP_IF_MODIFIED_SINCE=stamp).status_code, 404)


if __name__ == '__main__':
    unittest.main()
