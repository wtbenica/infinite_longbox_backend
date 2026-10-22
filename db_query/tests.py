import json
import os
import tempfile
from unittest import mock

from django.test import SimpleTestCase

from . import local_covers, metron_covers

JPEG = b'\xff\xd8\xff\xe0' + b'0' * 20


def api_answer(image):
    return json.dumps({'results': [{'image': image}] if image else []}).encode()


class MetronCoversTest(SimpleTestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        patcher = mock.patch.dict(os.environ, {'FETCH_COVERS': '1', 'METRON_TOKEN': 't'})
        patcher.start()
        self.addCleanup(patcher.stop)

    def fetch(self, answers):
        with mock.patch.object(metron_covers, '_get', side_effect=answers) as get:
            path = metron_covers.fetch(7, self.dir.name, local_covers._image_extension)
        return path, get

    def test_saves_the_cover_the_lookup_points_to(self):
        path, get = self.fetch([api_answer('https://static.metron.cloud/a.jpg'), JPEG])
        self.assertEqual(os.path.basename(path), '7.jpg')
        self.assertEqual(open(path, 'rb').read(), JPEG)
        # the token goes to the API and not the image host
        self.assertTrue(get.call_args_list[0].kwargs['auth'])
        self.assertFalse(get.call_args_list[1].kwargs['auth'])

    def test_a_missing_cover_is_remembered(self):
        self.assertIsNone(self.fetch([api_answer(None)])[0])
        path, get = self.fetch([])
        self.assertIsNone(path)
        get.assert_not_called()

    def test_a_failed_request_is_not_remembered(self):
        self.assertIsNone(self.fetch([OSError('offline')])[0])
        path, _ = self.fetch([api_answer('https://static.metron.cloud/a.jpg'), JPEG])
        self.assertIsNotNone(path)

    def test_an_image_on_another_host_is_not_fetched(self):
        path, get = self.fetch([api_answer('https://example.com/a.jpg')])
        self.assertIsNone(path)
        self.assertEqual(get.call_count, 1)

    def test_something_that_is_not_an_image_is_not_stored(self):
        path, _ = self.fetch([api_answer('https://static.metron.cloud/a.jpg'), b'<html>'])
        self.assertIsNone(path)
        self.assertEqual(os.listdir(self.dir.name), [])

    def test_off_without_the_switch(self):
        with mock.patch.dict(os.environ, {'FETCH_COVERS': '0'}):
            path, get = self.fetch([])
        self.assertIsNone(path)
        get.assert_not_called()
