import json

from django.core import serializers
from django.core.serializers import serialize
from django.db.models import QuerySet
from django.http import HttpResponse, JsonResponse

# Create your views here.
from db_query.models import *
from db_query.models import GcdStory

ROWS_PER_PAGE = 1000

UNITED_STATES = 225


def index(request):
    return HttpResponse("Hello, world. You're at the polls index")


def series_list(request, page: int):
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


def series(request, series_id: int):
    return JsonResponse(json.loads(serialize('json', GcdSeries.objects.filter(pk_id=series_id))),
                        safe=False, json_dumps_params={'ensure_ascii': False})


def issue(request, issue_id: int):
    issue = GcdIssue.objects.filter(pk=issue_id)

    return JsonResponse(json.loads(serialize('json', issue)), safe=False,
                        json_dumps_params={'ensure_ascii': False})


def issues_by_series(request, series_id):
    issues = GcdIssue.objects.filter(series_id=series_id)

    return JsonResponse(json.loads(serialize('json', issues)), safe=False,
                        json_dumps_params={'ensure_ascii': False})


def publishers_list(request) -> JsonResponse:
    pub_list = GcdPublisher.objects.filter(country=UNITED_STATES,
                                           year_began__gte=1900,
                                           series_count__gte=200)

    return JsonResponse(json.loads(serialize('json', pub_list)),
                        safe=False,
                        json_dumps_params={'ensure_ascii': False})


def roles_list(request):
    roles = GcdCreditType.objects.all()
    return JsonResponse(json.loads(serialize('json', roles)), safe=False,
                        json_dumps_params={'ensure_ascii': False})


def credits(request, issue_id: int):
    stories: QuerySet[GcdStory] = GcdStory.objects.filter(issue_id=issue_id)
    story_credits: QuerySet[GcdStoryCredit] = GcdStoryCredit.objects.filter(story__issue=issue_id)
    return JsonResponse(json.loads(
            "[" + serialize('json', story_credits) + ", " + serialize('json', stories) + "]"),
            safe=False,
            json_dumps_params={'ensure_ascii': False})
