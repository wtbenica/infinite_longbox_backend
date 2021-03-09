import json

from django.core.serializers import serialize
from django.http import HttpResponse, JsonResponse

# Create your views here.
from db_query.models import GcdSeries


def index(request):
    return HttpResponse("Hello, world. You're at the polls index")


def series(request):
    series = GcdSeries.objects.filter(country_id=225, name__contains='Doom Patrol').order_by(
            'sort_name')
    series_list = serialize('json', series, fields=('name', 'publication_dates'))
    return JsonResponse(json.loads(series_list), safe=False,
                        json_dumps_params={'ensure_ascii': False})
