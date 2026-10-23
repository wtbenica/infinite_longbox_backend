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
        metron_covers._candidates_cache.clear()
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        patcher = mock.patch.dict(os.environ, {'FETCH_COVERS': '1', 'METRON_TOKEN': 't'})
        patcher.start()
        self.addCleanup(patcher.stop)

    def fetch(self, answers, **kwargs):
        with mock.patch.object(metron_covers, '_get', side_effect=answers) as get:
            path = metron_covers.fetch(7, self.dir.name, local_covers._image_extension, **kwargs)
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


def issue_answers(*variants):
    """What Metron answers for a lookup by GCD id and then for the issue itself."""
    base = 'https://static.metron.cloud/base.jpg'
    return [
        json.dumps({'results': [{'id': 99, 'image': base}]}).encode(),
        json.dumps({'id': 99, 'image': base, 'variants': [
            {'name': n, 'image': f'https://static.metron.cloud/{i}.jpg'} for i, n in enumerate(variants)
        ]}).encode(),
    ]


class MetronVariantsTest(MetronCoversTest):
    def test_the_candidates_are_the_standard_cover_then_the_variants(self):
        with mock.patch.object(metron_covers, '_get', side_effect=issue_answers('Second Printing Cover', 'Variant Cover')):
            covers = metron_covers.candidates(5)
        self.assertEqual([c.name for c in covers], [None, 'Second Printing Cover', 'Variant Cover'])

    def test_a_variant_is_matched_by_name(self):
        path, get = self.fetch(issue_answers('Variant Cover', 'Second Printing Cover') + [JPEG], parent=5, name='Second Printing')
        self.assertEqual(os.path.basename(path), '7.jpg')
        self.assertEqual(get.call_args_list[-1].args[0], 'https://static.metron.cloud/1.jpg')

    def test_generic_and_ambiguous_names_do_not_match(self):
        self.assertIs(self.fetch(issue_answers('Variant Cover'), parent=5, name='Tim Sale Cover')[0], metron_covers.NO_COVER)
        metron_covers._candidates_cache.clear()
        self.assertIs(self.fetch(issue_answers('Foil Cover', 'Foil Variant'), parent=5, name='Foil')[0], metron_covers.NO_COVER)

    def test_the_only_variant_is_it_when_the_gcd_knows_only_one(self):
        path, get = self.fetch(issue_answers('Variant Cover') + [JPEG], parent=5, name='Tim Sale Cover', sole_variant=True)
        self.assertEqual(get.call_args_list[-1].args[0], 'https://static.metron.cloud/0.jpg')
        self.assertIsNotNone(path)

    def test_one_metron_variant_is_not_guessed_when_the_gcd_has_more(self):
        path, _ = self.fetch(issue_answers('Variant Cover'), parent=5, name='Tim Sale Cover', sole_variant=False)
        self.assertIs(path, metron_covers.NO_COVER)

    def test_two_metron_variants_are_not_guessed_either(self):
        path, _ = self.fetch(issue_answers('A', 'B'), parent=5, name='Tim Sale Cover', sole_variant=True)
        self.assertIs(path, metron_covers.NO_COVER)

    def test_a_picked_cover_is_the_one_saved(self):
        with mock.patch.object(metron_covers, '_get', side_effect=issue_answers('A', 'B')):
            choice = metron_covers.candidates(5)[2].id
        path, get = self.fetch([JPEG], parent=5, choice=choice)
        self.assertIsNotNone(path)
        self.assertEqual(get.call_args_list[-1].args[0], 'https://static.metron.cloud/1.jpg')


class FetchCoverViewTest(SimpleTestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        for patcher in (
            mock.patch.dict(os.environ, {'FETCH_COVERS': '1', 'METRON_TOKEN': 't', 'COVERS_DIR': self.dir.name}),
            mock.patch.object(local_covers, '_issue_exists', return_value=True),
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


class FetchCoverGuardsTest(SimpleTestCase):
    def test_an_issue_the_gcd_does_not_have_is_not_fetched_for(self):
        with mock.patch.dict(os.environ, {'FETCH_COVERS': '1', 'METRON_TOKEN': 't'}), \
                mock.patch.object(local_covers, '_issue_exists', return_value=False), \
                mock.patch.object(metron_covers, 'fetch') as fetch:
            response = self.client.post('/db_query/issue/id/987654321/cover/fetch')
        self.assertEqual(response.status_code, 404)
        fetch.assert_not_called()

    def test_redirects_stay_on_metron(self):
        handler = metron_covers._SameFamilyRedirects()
        request = mock.Mock(full_url='https://metron.cloud/x', headers={}, origin_req_host='metron.cloud', unverifiable=False)
        with self.assertRaises(metron_covers.urllib.error.URLError):
            handler.redirect_request(request, None, 302, 'Found', {}, 'https://evil.example/x.jpg')
