import json

from django.core import serializers
from django.core.serializers import serialize
from django.http import HttpResponse, JsonResponse

# Create your views here.
from db_query.models import GcdSeries, GcdIssue, GcdCreditType, GcdPublisher

UNITED_STATES = 225


def index(request):
    return HttpResponse("Hello, world. You're at the polls index")


def series(request):
    series = GcdSeries.objects.filter(country_id=225,
                                      publisher__year_began__gte=1900,
                                      publisher__series_count__gte=50).order_by('sort_name')[
             1000:1050]

    series_list = serializers.serialize('json', series,
                                        use_natural_foreign_keys=True)

    return JsonResponse(json.loads(series_list), safe=False,
                        json_dumps_params={'ensure_ascii': False})


def issue(request, pk_id):
    issue = GcdIssue.objects.filter(pk=pk_id)

    return JsonResponse(json.loads(serialize('json', issue)), safe=False,
                        json_dumps_params={'ensure_ascii': False})


def publishers(request):
    pub_list = GcdPublisher.objects.filter(country=UNITED_STATES,
                                           year_began__gte=1900,
                                           series_count__gte=50)

    return JsonResponse(json.loads(serialize('json', pub_list)),
                        safe=False,
                        json_dumps_params={'ensure_ascii': False})

def role(request):
    roles = GcdCreditType.objects.all()
    return JsonResponse(json.loads(serialize('json', roles)), safe=False,
        json_dumps_params={'ensure_ascii': False})