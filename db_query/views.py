import json

from django.core import serializers
from django.core.serializers import serialize
from django.http import HttpResponse, JsonResponse

# Create your views here.
from db_query.models import GcdSeries, GcdIssue


def index(request):
    return HttpResponse("Hello, world. You're at the polls index")


def series(request):
    series = GcdSeries.objects.filter(country_id=225,
        name__contains='Doom Patrol').order_by(
        'sort_name')
    series_list = serializers.serialize('json', series,
        use_natural_foreign_keys=True)
    return JsonResponse(json.loads(series_list), safe=False,
        json_dumps_params={'ensure_ascii': False})


def issue(request, pk_id):
    issue = GcdIssue.objects.filter(pk=pk_id)
    return JsonResponse(json.loads(serialize('json', issue)), safe=False,
        json_dumps_params={'ensure_ascii': False})
