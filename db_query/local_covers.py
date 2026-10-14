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


def covers_have(request) -> JsonResponse:
    ids = set()
    if os.path.isdir(covers_dir()):
        for name in os.listdir(covers_dir()):
            match = COVER_FILE.match(name)
            if match:
                ids.add(int(match.group(1)))
    return JsonResponse(sorted(ids), safe=False)


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
