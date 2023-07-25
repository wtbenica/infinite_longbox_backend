import os
from typing import Optional, Union

import google.auth
import google.auth.transport.requests as tr_requests
from bs4 import BeautifulSoup, ResultSet
from django.http import HttpResponse, HttpResponseNotFound, \
    HttpResponseServerError
from google.cloud import storage
from google.cloud.storage.blob import Blob
from google.resumable_media.requests import SimpleUpload
from ratelimit import limits, sleep_and_retry
from urllib3 import PoolManager
from urllib3.response import HTTPResponse

http = PoolManager()


def get_cover(request, id: int, recurse=False) -> HttpResponse:
    cover_path = get_cover_path(id)

    if os.path.exists(cover_path):  # cover is stored locally
        with open(cover_path, 'rb') as file:
            return HttpResponse(file.read(), content_type='image/jpeg')
    elif recurse:  # cover is not found locally and attempted download already
        return HttpResponseNotFound()
    else:  # cover is not found locally, see if it's available from gcd
        r = download_cover_from_gcd(id)
        if r is not None and isinstance(r, HTTPResponse) and r.status == 200:
            save_cover_locally(id, r)
            return get_cover(request, id)
        elif isinstance(r, HttpResponse):
            return r
        else:
            return HttpResponseServerError()


def get_cover_path(id: int) -> str:
    # Define the directory where covers will be stored locally
    cover_directory = '/home/wesley/Pictures/covers'

    # Create the directory if it doesn't exist
    os.makedirs(cover_directory, exist_ok=True)

    # Return the path of the cover file
    return os.path.join(cover_directory, f"{id}_IMG.jpg")


def save_cover_locally(id: int, r: HTTPResponse) -> None:
    cover_path = get_cover_path(id)

    with open(cover_path, 'wb') as file:
        file.write(r.data)


@sleep_and_retry
@limits(calls=5, period=1)
def download_cover_from_gcd(id) -> Optional[Union[HttpResponse, HTTPResponse]]:
    url = f"https://www.comics.org/issue/{id}/cover/4/"
    print('Getting page')

    page = resp(http.request('GET', url, timeout=4.0))
    print('Page was gotten')

    if not isinstance(page, HTTPResponse):
        print('Got an error')
        return page
    print(type(page.data))
    soup = BeautifulSoup(page.data, "html.parser")
    cover_image_links: ResultSet = soup.find_all("a", href=f"/issue/{id}/")
    imgs = [a.find('img') for a in cover_image_links if
            a.find('img') is not None]
    src = imgs[0]['src'] if len(imgs) > 0 else None

    if src is not None:
        headers = {
            'Referer': url
        }
        return resp(http.request('GET', src, headers=headers, timeout=2.0))
    else:
        return None


def resp(r) -> Union[HttpResponse, HTTPResponse]:
    print(f"Status: {r.status}")
    if r.status == 200:
        return r
    elif r.status == 404:
        return HttpResponseNotFound()
    else:
        return HttpResponseServerError()
