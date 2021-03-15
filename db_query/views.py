import json

from django.core import serializers
from django.core.serializers import serialize
from django.http import HttpResponse, JsonResponse

# Create your views here.
from db_query.models import GcdSeries, GcdIssue, GcdCreditType, GcdPublisher

ROWS_PER_PAGE = 1000

UNITED_STATES = 225


def index(request):
    return HttpResponse("Hello, world. You're at the polls index")


def series(request, page: int):
    series = GcdSeries.objects.filter(country_id=UNITED_STATES,
                                      dimensions__iregex='standard modern|standard '
                                                                 'silver|standard gold',
                                      publisher__country_id=UNITED_STATES,
                                      publisher__year_began__gte=1900,
                                      publisher__series_count__gte=200).order_by('sort_name')[
             page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    series_list = serializers.serialize('json', series,
                                        use_natural_foreign_keys=True)

    return JsonResponse(json.loads(series_list), safe=False,
                        json_dumps_params={'ensure_ascii': False})


def issue(request, pk_id):
    issue = GcdIssue.objects.filter(pk=pk_id)

    return JsonResponse(json.loads(serialize('json', issue)), safe=False,
                        json_dumps_params={'ensure_ascii': False})


def issues(request, pk_id):
    issues = GcdIssue.objects.filter(series_id=pk_id)

    return JsonResponse(json.loads(serialize('json', issues)), safe=False,
                        json_dumps_params={'ensure_ascii': False})


def publishers(request):
    pub_list = GcdPublisher.objects.filter(country=UNITED_STATES,
                                           year_began__gte=1900,
                                           series_count__gte=200)

    return JsonResponse(json.loads(serialize('json', pub_list)),
                        safe=False,
                        json_dumps_params={'ensure_ascii': False})


def role(request):
    roles = GcdCreditType.objects.all()
    return JsonResponse(json.loads(serialize('json', roles)), safe=False,
                        json_dumps_params={'ensure_ascii': False})
