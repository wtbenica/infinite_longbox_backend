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
MAX_WAIT = 45  # seconds a request will wait for Metron's burst window; longer and it says so
TIMEOUT = 30
MAX_BYTES = 15 * 1024 * 1024

RATE_LIMITED = object()  # what fetch() answers when Metron's limit would make the request wait too long
NO_COVER = object()  # what fetch() answers when Metron has no cover for the issue

_lock = threading.Lock()
_last_request = 0.0


def enabled() -> bool:
    return os.environ.get('FETCH_COVERS') == '1' and bool(os.environ.get('METRON_TOKEN'))


class RateLimited(Exception):
    pass


# Metron's burst limit (20 requests a minute) as its answers last reported it
_remaining = None
_reset_at = 0.0


def _note_limits(headers) -> None:
    global _remaining, _reset_at
    try:
        _remaining = int(headers['X-Ratelimit-Burst-Remaining'])
        _reset_at = float(headers['X-Ratelimit-Burst-Reset'])
    except (KeyError, TypeError, ValueError):
        pass


def _wait_for_window() -> None:
    """Sleeps until the burst window has room, or raises RateLimited if that is too long."""
    if _remaining is not None and _remaining <= 1 and _reset_at > time.time():
        wait = _reset_at - time.time() + 0.5
        if wait > MAX_WAIT:
            raise RateLimited()
        time.sleep(wait)


def _get(url: str, accept: str, auth: bool) -> bytes:
    headers = {'User-Agent': 'InfiniteLongbox-personal/1.0', 'Accept': accept}
    if auth:  # the token goes to the API only, never to the image host
        headers['Authorization'] = 'Bearer ' + os.environ['METRON_TOKEN']
        _wait_for_window()
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            if auth:
                _note_limits(response.headers)
            return response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        if auth and e.code == 429:
            global _remaining, _reset_at
            _remaining, _reset_at = 0, time.time() + 20  # in case the answer says nothing more
            _note_limits(e.headers)
            raise RateLimited() from e
        raise


def fetch(issue_id: int, covers_dir: str, image_extension):
    """Looks the issue up on Metron and saves its cover (replacing any other format of it).

    Returns the file's path, NO_COVER if Metron has none, RATE_LIMITED if its limit means trying
    again shortly, or None if it could not be got (off, unreachable, or not an image).

    image_extension(bytes) gives 'jpg', 'png', ... for image data and None for anything else.
    """
    if not enabled():
        return None
    with _lock:
        try:
            try:
                found = json.loads(_get(f'{API}?gcd_id={int(issue_id)}', 'application/json', auth=True))
            except RateLimited:
                # another worker may have used the window up: wait for the next one and try once more
                found = json.loads(_get(f'{API}?gcd_id={int(issue_id)}', 'application/json', auth=True))
            image = next((r.get('image') for r in found.get('results', []) if r.get('image')), None)
            if image is None:
                return NO_COVER
            if urllib.parse.urlparse(image).hostname not in IMAGE_HOSTS:
                log.warning('Metron cover for %s is on an unexpected host: %s', issue_id, image)
                return None
            data = _get(image, 'image/*', auth=False)
        except RateLimited:
            log.warning('Metron rate limit reached; not fetching %s now', issue_id)
            return RATE_LIMITED
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
