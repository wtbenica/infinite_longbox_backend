"""Serve issue covers from a local directory (COVERS_DIR).

Looks for <issue id>.<ext> (jpg, jpeg, png, webp, gif) or <issue id>_IMG.
Never touches the network, so nothing is scraped or uploaded.
"""
import mimetypes
import os

from django.http import FileResponse, HttpResponseNotFound

EXTENSIONS = ('jpg', 'jpeg', 'png', 'webp', 'gif', '')


def get_cover(request, id: int):
    covers_dir = os.environ['COVERS_DIR']
    for ext in EXTENSIONS:
        name = f'{id}.{ext}' if ext else f'{id}_IMG'
        path = os.path.join(covers_dir, name)
        if os.path.isfile(path):
            content_type = mimetypes.guess_type(path)[0] or 'image/jpeg'
            return FileResponse(open(path, 'rb'), content_type=content_type)
    return HttpResponseNotFound()
