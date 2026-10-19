"""Page counts and page contents for the paged sync, from a list of ids made once.

The sync endpoints page through models whose managers filter with subqueries (a character is only
listed if it has appearances, a name detail only if it has credits). Counting those, or taking a
page of them, costs 15-30 seconds on every request. The ids that make up each model are the same
until the data changes, so tools/build_seed_from_db.py writes them to page_index.json, beside the
seed, and these endpoints read the counts and pages from that.

The index only counts while the table it was made from has the same number of rows. If it is
missing or out of date (the data changed and the index was not made again) the endpoints fall
back to asking the database, slowly but correctly.
"""
import hashlib
import json
import os
import time
from typing import Optional

from django.conf import settings

ROWS_PER_PAGE = 500
CHECK_SECONDS = 30  # how long a row count is trusted before it is looked at again

_loaded = {'mtime': None, 'data': None}
_checked = {}  # model name -> (when, whether the index matched)


def index_path() -> str:
    return os.path.join(
        os.environ.get('SEED_DIR') or os.path.join(settings.BASE_DIR, 'seed'), 'page_index.json'
    )


def hash_page(rows) -> str:
    """A fingerprint of a page's rows: it changes when any of them does."""
    return hashlib.sha1(repr(list(rows)).encode()).hexdigest()[:12]


def make(models: dict) -> dict:
    """The index for {name: model}: the ids the model's endpoints list, in order, the number of
    rows in its table, which says whether the index still fits, and a fingerprint of each page.

    The fingerprints are the manifest: a phone that has the pages as of one version asks which
    changed in the next and fetches only those."""
    index = {}
    for name, model in models.items():
        ids = list(model.objects.order_by('pk').values_list('pk', flat=True))
        hashes = []
        for page in range(num_pages(len(ids))):
            chunk = page_ids(ids, page)
            rows = model._base_manager.filter(pk__in=chunk).order_by('pk').values_list() if chunk else []
            hashes.append(hash_page(rows))
        index[name] = {'rows': model._base_manager.count(), 'ids': ids, 'hashes': hashes}
    return index


def write(index: dict, directory: str) -> None:
    os.makedirs(directory, exist_ok=True)
    tmp = os.path.join(directory, 'page_index.json.tmp')
    with open(tmp, 'w') as f:
        json.dump(index, f, separators=(',', ':'))
    os.replace(tmp, os.path.join(directory, 'page_index.json'))


def num_pages(count: int) -> int:
    """Pages the app expects: a partly or not at all filled last page counts."""
    return count // ROWS_PER_PAGE + 1


def page_ids(ids: list, page: int) -> list:
    return ids[page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]


def _data() -> Optional[dict]:
    path = index_path()
    try:
        mtime = os.stat(path).st_mtime
    except OSError:
        _loaded.update(mtime=None, data=None)
        return None
    if _loaded['mtime'] != mtime:
        with open(path) as f:
            _loaded.update(mtime=mtime, data=json.load(f))
        _checked.clear()
    return _loaded['data']


def manifest(models: dict) -> dict:
    """{name: {"pages": n, "hashes": [...]}} for each model whose index still fits its table."""
    out = {}
    data = _data() or {}
    for name, model in models.items():
        ids = ids_for(name, model)
        if ids is not None and 'hashes' in data[name]:
            out[name] = {'pages': len(data[name]['hashes']), 'hashes': data[name]['hashes']}
    return out


def ids_for(name: str, model) -> Optional[list]:
    """The ids the model's endpoints list, if there is an index that still fits the table."""
    data = _data()
    if not data or name not in data:
        return None
    now = time.monotonic()
    checked = _checked.get(name)
    if checked is None or now - checked[0] > CHECK_SECONDS:
        checked = (now, model._base_manager.count() == data[name]['rows'])
        _checked[name] = checked
    return data[name]['ids'] if checked[1] else None
