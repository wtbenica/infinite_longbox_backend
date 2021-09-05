from typing import Optional, Union

import google.auth
import google.auth.transport.requests as tr_requests
from bs4 import BeautifulSoup, ResultSet
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from google.cloud import storage
from google.cloud.storage.blob import Blob
from google.resumable_media.requests import SimpleUpload
from urllib3 import PoolManager
from urllib3.contrib.appengine import AppEngineManager, is_appengine_sandbox
from urllib3.response import HTTPResponse

global http

if is_appengine_sandbox():
    http = AppEngineManager()
else:
    http = PoolManager()


def get_cover(request, id: int, recurse=False) -> HttpResponse:
    res = get_cover_from_storage(id)

    if res is not None:  # cover is in storage
        return HttpResponse(res.download_as_bytes(), content_type=res.content_type)
    elif recurse:  # cover is not in storage and attempted download already
        return HttpResponseNotFound()
    else:  # cover is not in storage, see if it's available from gcd
        r = download_cover_from_gcd(id)
        print(type(r))
        if r is not None and isinstance(r, HTTPResponse) and r.status == 200:
            upload_cover_to_storage(id, r)
            return get_cover(request, id)
        elif isinstance(r, HttpResponse):
            return r
        else:
            return HttpResponseServerError()


def get_cover_from_storage(id: int) -> Optional[Blob]:
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('longbox.appspot.com')
    return bucket.get_blob(f"{id}_IMG")


def upload_cover_to_storage(id, r) -> None:
    url_template = (
        f'https://www.googleapis.com/upload/storage/v1/b/longbox.appspot.com/o?uploadType'
        f'=media'
        f'&name={id}_IMG'
    )
    upload_url = url_template.format(bucket="longbox.appspot.com")
    upload = SimpleUpload(upload_url)
    ro_scope = 'https://www.googleapis.com/auth/devstorage.read_write'
    credentials, _ = google.auth.default(scopes=(ro_scope,))
    transport = tr_requests.AuthorizedSession(credentials)
    content_type = r.headers['content-type']

    upload.transmit(transport, r.data, content_type)


def download_cover_from_gcd(id) -> Optional[Union[HttpResponse, HTTPResponse]]:
    URL = f"https://www.comics.org/issue/{id}/cover/4/"
    print('Getting page')

    page = resp(http.request('GET', URL, timeout=4.0))
    print('Page was gotten')

    if not isinstance(page, HTTPResponse):
        print('Got an error')
        return page
    print(type(page.data))
    soup = BeautifulSoup(page.data, "html.parser")
    cover_image_links: ResultSet = soup.find_all("a", href=f"/issue/{id}/")
    imgs = [a.find('img') for a in cover_image_links if a.find('img') is not None]
    src = imgs[0]['src'] if len(imgs) > 0 else None

    if src is not None:
        headers = {
            'Referer': URL
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
