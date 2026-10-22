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

    def test_no_cover_on_metron_is_said_so(self):
        path, _ = self.fetch([api_answer(None)])
        self.assertIs(path, metron_covers.NO_COVER)

    def test_a_rate_limit_is_reported(self):
        path, _ = self.fetch([metron_covers.RateLimited(), metron_covers.RateLimited()])
        self.assertIs(path, metron_covers.RATE_LIMITED)

    def test_a_rate_limit_is_tried_once_more(self):
        path, _ = self.fetch([metron_covers.RateLimited(), api_answer('https://static.metron.cloud/a.jpg'), JPEG])
        self.assertEqual(os.path.basename(path), '7.jpg')

    def test_a_failed_request_gives_nothing(self):
        self.assertIsNone(self.fetch([OSError('offline')])[0])

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


class FetchCoverViewTest(SimpleTestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        for patcher in (
            mock.patch.dict(os.environ, {'FETCH_COVERS': '1', 'METRON_TOKEN': 't', 'COVERS_DIR': self.dir.name}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def post(self, result):
        with mock.patch.object(metron_covers, 'fetch', return_value=result):
            return self.client.post('/db_query/issue/id/7/cover/fetch')

    def test_saved(self):
        response = self.post(os.path.join(self.dir.name, '7.jpg'))
        self.assertEqual((response.status_code, response.json()), (200, {'id': 7, 'type': 'jpg'}))

    def test_none_on_metron(self):
        self.assertEqual(self.post(metron_covers.NO_COVER).status_code, 404)

    def test_rate_limited(self):
        self.assertEqual(self.post(metron_covers.RATE_LIMITED).status_code, 429)

    def test_could_not_get_it(self):
        self.assertEqual(self.post(None).status_code, 502)

    def test_off(self):
        with mock.patch.dict(os.environ, {'FETCH_COVERS': '0'}):
            self.assertEqual(self.post(None).status_code, 403)

    def test_asking_for_a_cover_never_fetches(self):
        with mock.patch.object(metron_covers, 'fetch') as fetch:
            self.assertEqual(self.client.get('/db_query/issue/id/7/cover').status_code, 404)
        fetch.assert_not_called()
