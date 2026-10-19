"""Issue covers, kept as image files in a directory (COVERS_DIR, default <project>/covers).

  GET  /db_query/issue/id/<id>/cover          the cover, or 404
  POST /db_query/issue/id/<id>/cover/upload   store an image as the cover (needs ALLOW_COVER_UPLOAD=1)
  POST /db_query/issue/id/<id>/cover/remove   delete the cover (needs ALLOW_COVER_UPLOAD=1)
  GET  /db_query/covers/have                  ids of the issues that have a cover

Covers are named <issue id>.<ext> (jpg, jpeg, png, webp or gif) or <issue id>_IMG.
Nothing here touches the network: covers come from files you put there yourself, or from the app's
"pick a cover" / "upload covers to server" features.
"""
import json
import mimetypes
import os
import re
import tempfile

from django.conf import settings
from django.http import FileResponse, HttpResponse, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

EXTENSIONS = ('jpg', 'jpeg', 'png', 'webp', 'gif', '')
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
COVER_FILE = re.compile(r'^(\d+)(?:\.(?:jpe?g|png|webp|gif)|_IMG)$')


def covers_dir() -> str:
    return os.environ.get('COVERS_DIR') or os.path.join(settings.BASE_DIR, 'covers')


def _path(id: int, ext: str) -> str:
    return os.path.join(covers_dir(), f'{id}.{ext}' if ext else f'{id}_IMG')


def get_cover(request, id: int):
    for ext in EXTENSIONS:
        path = _path(id, ext)
        if os.path.isfile(path):
            content_type = mimetypes.guess_type(path)[0] or 'image/jpeg'
            return FileResponse(open(path, 'rb'), content_type=content_type)
    return HttpResponseNotFound()


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
