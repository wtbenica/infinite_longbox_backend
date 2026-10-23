"""Issue covers, kept as image files in a directory (COVERS_DIR, default <project>/covers).

  GET  /db_query/issue/id/<id>/cover          the cover, or 404
  POST /db_query/issue/id/<id>/cover/upload   store an image as the cover (needs ALLOW_COVER_UPLOAD=1)
  POST /db_query/issue/id/<id>/cover/remove   delete the cover (needs ALLOW_COVER_UPLOAD=1)
  POST /db_query/issue/id/<id>/cover/fetch    fetch the cover from Metron (needs FETCH_COVERS=1);
       for a variant: ?parent=<issue it varies>&name=<its variant name> or &choice=<id from options>
  GET  /db_query/issue/id/<id>/cover/metron/options   the covers Metron has for the issue (?parent=)
  GET  /db_query/issue/id/<id>/cover/metron/preview/<choice>   one of them, as an image
  GET  /db_query/covers/have                  ids of the issues that have a cover

Covers are named <issue id>.<ext> (jpg, jpeg, png, webp or gif) or <issue id>_IMG.
Covers come from files you put there yourself, from the app's "pick a cover" / "upload covers to
server" features, or, when FETCH_COVERS=1 and METRON_TOKEN are set, from Metron when the app asks
for it (POST /db_query/issue/id/<id>/cover/fetch; see metron_covers.py). Asking for a cover never
fetches one.
"""
import json
import mimetypes
from datetime import datetime, timezone
import os
import re
import tempfile

from django.conf import settings
from django.http import FileResponse, HttpResponse, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition, require_POST

from . import metron_covers

EXTENSIONS = ('jpg', 'jpeg', 'png', 'webp', 'gif', '')
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
COVER_FILE = re.compile(r'^(\d+)(?:\.(?:jpe?g|png|webp|gif)|_IMG)$')


def covers_dir() -> str:
    return os.environ.get('COVERS_DIR') or os.path.join(settings.BASE_DIR, 'covers')


def _path(id: int, ext: str) -> str:
    return os.path.join(covers_dir(), f'{id}.{ext}' if ext else f'{id}_IMG')


def _cover_path(id: int):
    for ext in EXTENSIONS:
        path = _path(id, ext)
        if os.path.isfile(path):
            return path
    return None


def _cover_modified(request, id: int):
    """When the cover file last changed, for conditional requests (None if there is none)."""
    path = _cover_path(id)
    if path is None:
        return None
    return datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)


@condition(last_modified_func=_cover_modified)
def get_cover(request, id: int):
    """The cover. With If-Modified-Since the answer is 304 and no image if it has not changed, so
    the phone can check its copy without downloading it again."""
    path = _cover_path(id)
    if path is None:
        return HttpResponseNotFound()
    content_type = mimetypes.guess_type(path)[0] or 'image/jpeg'
    return FileResponse(open(path, 'rb'), content_type=content_type)


def issue_ids_with_covers() -> set:
    """The ids of the issues that have a cover file here."""
    ids = set()
    if os.path.isdir(covers_dir()):
        for name in os.listdir(covers_dir()):
            match = COVER_FILE.match(name)
            if match:
                ids.add(int(match.group(1)))
    return ids


def covers_have(request) -> JsonResponse:
    return JsonResponse(sorted(issue_ids_with_covers()), safe=False)


def earliest_cover_ids(rows, per_series: int = 3) -> dict:
    """{series id: issue ids}, from rows of (series id, issue id, variant of, sort code).

    A series' issues with covers in the order a card wants them: regular issues before variants,
    then by sort code (the issue's place in the series), at most [per_series] of them.
    """
    ordered = {}
    for series_id, issue_id, variant_of, sort_code in rows:
        ordered.setdefault(series_id, []).append((variant_of is not None, sort_code, issue_id))
    return {
        series_id: [issue_id for _, _, issue_id in sorted(issues)[:per_series]]
        for series_id, issues in ordered.items()
    }


def series_covers(request, series_ids: str) -> JsonResponse:
    """For each of these series, which of its issues have covers here: the earliest few.

    A series card shows its first issue's cover, and falls back to the earliest cover the phone
    has for any issue of the series; this says which issues to fetch covers for.
    """
    from db_query.models import GcdIssue

    ids = [int(i) for i in series_ids.strip('[]').split(',') if i.strip()]
    have = issue_ids_with_covers()
    if not ids or not have:
        return JsonResponse({})
    rows = GcdIssue._base_manager.filter(series_id__in=ids, id__in=have).values_list(
        'series_id', 'id', 'variant_of_id', 'sort_code'
    )
    return JsonResponse({str(k): v for k, v in earliest_cover_ids(rows).items()})


def _image_extension(data: bytes):
    """File extension for the image type, from the file's magic bytes (not the client's say-so)."""
    if data.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
        return 'gif'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    return None


@csrf_exempt
@require_POST
def upload_cover(request, id: int):
    """Stores the request body (an image) as the cover for the issue, replacing any existing one.

    Off unless ALLOW_COVER_UPLOAD=1, because this dev server listens on the local network.
    """
    if os.environ.get('ALLOW_COVER_UPLOAD') != '1':
        return HttpResponse('Cover upload is disabled (set ALLOW_COVER_UPLOAD=1)', status=403)
    if len(request.body) > MAX_UPLOAD_BYTES:
        return HttpResponse('Image too large', status=413)

    ext = _image_extension(request.body)
    if ext is None:
        return HttpResponse('Not a JPEG, PNG, WebP or GIF image', status=415)

    os.makedirs(covers_dir(), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=covers_dir(), prefix='.upload_')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(request.body)
        # drop other formats of the same cover so the new one is the one that's served
        for other in EXTENSIONS:
            if os.path.isfile(_path(id, other)):
                os.remove(_path(id, other))
        os.replace(tmp, _path(id, ext))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return HttpResponse(json.dumps({'id': id, 'bytes': len(request.body), 'type': ext}),
                        content_type='application/json')


@csrf_exempt
@require_POST
def remove_cover(request, id: int):
    """Deletes the issue's cover, in whatever format it is stored. Same switch as uploads."""
    if os.environ.get('ALLOW_COVER_UPLOAD') != '1':
        return HttpResponse('Cover changes are disabled (set ALLOW_COVER_UPLOAD=1)', status=403)
    removed = 0
    for ext in EXTENSIONS:
        if os.path.isfile(_path(id, ext)):
            os.remove(_path(id, ext))
            removed += 1
    return JsonResponse({'id': id, 'removed': removed})


@csrf_exempt
@require_POST
def fetch_cover(request, id: int):
    """Fetches the issue's cover from Metron and stores it, replacing any existing one.

    200 {"id", "type"} when saved; 403 when fetching is off; 404 when Metron has no cover for the
    issue; 429 when Metron's rate limit means trying again shortly; 502 when Metron could not be reached or gave something that is not an image.
    """
    if not metron_covers.enabled():
        return HttpResponse('Fetching covers is off (set FETCH_COVERS=1 and METRON_TOKEN)', status=403)
    if not _issue_exists(id):
        # only issues the GCD has: the endpoint isn't a way to put files under any number
        return HttpResponseNotFound('No such issue')
    parent = request.GET.get('parent')
    parent = int(parent) if parent and parent.isdigit() else None
    result = metron_covers.fetch(
        id, covers_dir(), _image_extension,
        parent=parent,
        name=request.GET.get('name'),
        choice=request.GET.get('choice'),
        sole_variant=parent is not None and _variants_of(parent) == 1,
    )
    if result is metron_covers.NO_COVER:
        return HttpResponseNotFound('Metron has no cover for this issue')
    if result is metron_covers.RATE_LIMITED:
        return HttpResponse('Metron is busy, try again shortly', status=429)
    if result is None:
        return HttpResponse('Could not get the cover from Metron', status=502)
    return JsonResponse({'id': id, 'type': os.path.splitext(result)[1].lstrip('.')})


def _issue_exists(id: int) -> bool:
    from .models import GcdIssue
    return GcdIssue.objects.filter(pk=id).exists()


def _variants_of(parent: int) -> int:
    """How many variants of the issue the GCD knows."""
    from .models import GcdIssue
    return GcdIssue.objects.filter(variant_of=parent).count()


def _lookup_id(request, id: int) -> int:
    parent = request.GET.get('parent')
    return int(parent) if parent and parent.isdigit() else id


def metron_options(request, id: int):
    """The covers Metron has for the issue (or, with ?parent=, for the issue it is a variant of):
    [{"id", "name"}], the standard cover first (empty name), for the app to pick from. For a variant (?parent=) the
    standard cover is left out."""
    if not metron_covers.enabled():
        return HttpResponse('Fetching covers is off (set FETCH_COVERS=1 and METRON_TOKEN)', status=403)
    try:
        with metron_covers._lock:
            covers = metron_covers.candidates(_lookup_id(request, id))
    except metron_covers.RateLimited:
        return HttpResponse('Metron is busy, try again shortly', status=429)
    except (OSError, ValueError):
        return HttpResponse('Could not get the covers from Metron', status=502)
    if request.GET.get('parent'):
        covers = [c for c in covers if c.name]  # a variant is not the standard cover
    return JsonResponse([c.as_dict() for c in covers], safe=False)


def metron_preview(request, id: int, choice: str):
    data = metron_covers.preview(_lookup_id(request, id), choice)
    if data is None:
        return HttpResponseNotFound()
    return HttpResponse(data, content_type=mimetypes.guess_type('x.' + (_image_extension(data) or 'jpg'))[0])
