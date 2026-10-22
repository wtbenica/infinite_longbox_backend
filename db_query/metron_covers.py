"""Fetches a cover from Metron (metron.cloud) when the app asks for one.

Off unless METRON_TOKEN is set (a token from your Metron profile) and FETCH_COVERS=1. An issue is
looked up by its GCD id. Requests are spaced out to stay far inside Metron's limits (20 in a
burst, 5000 sustained).

For personal use: covers are copyrighted, so keep the server to yourself and credit Metron.
"""
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)

API = 'https://metron.cloud/api/issue/'
IMAGE_HOSTS = ('static.metron.cloud', 'metron.cloud')
MIN_INTERVAL = 0.6
TIMEOUT = 30
MAX_BYTES = 15 * 1024 * 1024

NO_COVER = object()  # what fetch() answers when Metron has no cover for the issue

_lock = threading.Lock()
_last_request = 0.0


def enabled() -> bool:
    return os.environ.get('FETCH_COVERS') == '1' and bool(os.environ.get('METRON_TOKEN'))


def _get(url: str, accept: str, auth: bool) -> bytes:
    global _last_request
    wait = _last_request + MIN_INTERVAL - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    headers = {'User-Agent': 'InfiniteLongbox-personal/1.0', 'Accept': accept}
    if auth:  # the token goes to the API only, never to the image host
        headers['Authorization'] = 'Bearer ' + os.environ['METRON_TOKEN']
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read(MAX_BYTES + 1)
    finally:
        _last_request = time.monotonic()


def fetch(issue_id: int, covers_dir: str, image_extension):
    """Looks the issue up on Metron and saves its cover (replacing any other format of it).

    Returns the file's path, NO_COVER if Metron has none, or None if it could not be got (off,
    unreachable, rate-limited, or not an image).

    image_extension(bytes) gives 'jpg', 'png', ... for image data and None for anything else.
    """
    if not enabled():
        return None
    with _lock:
        try:
            found = json.loads(_get(f'{API}?gcd_id={int(issue_id)}', 'application/json', auth=True))
            image = next((r.get('image') for r in found.get('results', []) if r.get('image')), None)
            if image is None:
                return NO_COVER
            if urllib.parse.urlparse(image).hostname not in IMAGE_HOSTS:
                log.warning('Metron cover for %s is on an unexpected host: %s', issue_id, image)
                return None
            data = _get(image, 'image/*', auth=False)
        except (OSError, ValueError, urllib.error.URLError) as e:
            log.warning('Metron lookup for %s failed: %s (%s)', issue_id, e, getattr(e, 'url', ''))
            return None

        ext = image_extension(data) if len(data) <= MAX_BYTES else None
        if ext is None:
            log.warning('Metron cover for %s is not an image we can store', issue_id)
            return None
        os.makedirs(covers_dir, exist_ok=True)
        # drop other formats of the same cover so the new one is the one that's served
        for other in ('jpg', 'jpeg', 'png', 'webp', 'gif', '_IMG'):
            old = os.path.join(covers_dir, f'{int(issue_id)}.{other}' if other != '_IMG' else f'{int(issue_id)}_IMG')
            if other != ext and os.path.isfile(old):
                os.remove(old)
        path = os.path.join(covers_dir, f'{int(issue_id)}.{ext}')
        tmp = path + '.part'
        with open(tmp, 'wb') as f:
            f.write(data)
        os.replace(tmp, path)
        log.info('Saved the Metron cover for %s (%d bytes)', issue_id, len(data))
        return path
