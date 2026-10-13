"""Serves the starter-database seed built by tools/build_seed.py.

/db_query/seed/meta  -> meta.json (version, size, schema identity hash, sync-progress markers)
/db_query/seed/db    -> seed.db.gz (a pre-synced Room database, gzipped)

Both 404 if no seed has been built, and the app falls back to its normal paged sync.
"""
import os

from django.conf import settings
from django.http import FileResponse, HttpResponseNotFound


def _seed_path(name: str) -> str:
    return os.path.join(
        os.environ.get('SEED_DIR') or os.path.join(settings.BASE_DIR, 'seed'), name
    )


def _serve(name: str, content_type: str):
    path = _seed_path(name)
    if not os.path.isfile(path):
        return HttpResponseNotFound()
    return FileResponse(open(path, 'rb'), content_type=content_type)


def seed_meta(request):
    return _serve('meta.json', 'application/json')


def seed_db(request):
    return _serve('seed.db.gz', 'application/gzip')
