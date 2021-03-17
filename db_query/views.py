import json

from django.core.serializers import serialize
from django.db.models.query import RawQuerySet
from django.http import HttpResponse, JsonResponse

# Create your views here.
from db_query.models import *
from db_query.models import GcdStory

ROWS_PER_PAGE = 1000

UNITED_STATES = 225


def index(request):
    return HttpResponse("Hello, world. You're at the polls index")


def series_list(request, page: int):
    series_list = GcdSeries.objects.filter(country_id=UNITED_STATES,
                                           dimensions__iregex='standard modern|standard '
                                                              'silver|standard gold',
                                           publisher__country_id=UNITED_STATES,
                                           publisher__year_began__gte=1900,
                                           publisher__series_count__gte=200).order_by('sort_name')[
                  page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return JsonResponse(json.loads(serialize('json', series_list, use_natural_foreign_keys=True)),
                        safe=False, json_dumps_params={'ensure_ascii': False})


def series(request, series_id: int):
    return JsonResponse(json.loads(serialize('json', GcdSeries.objects.filter(pk_id=series_id))),
                        safe=False, json_dumps_params={'ensure_ascii': False})


def issue(request, issue_id: int):
    return JsonResponse(json.loads(serialize('json', GcdIssue.objects.filter(pk=issue_id))),
                        safe=False, json_dumps_params={'ensure_ascii': False})


def issues_by_series(request, series_id):
    return JsonResponse(json.loads(serialize('json', GcdIssue.objects.filter(series_id=series_id))),
                        safe=False, json_dumps_params={'ensure_ascii': False})


def publishers_list(request) -> JsonResponse:
    return JsonResponse(
            json.loads(serialize('json',
                                 GcdPublisher.objects.filter(country=UNITED_STATES,
                                                             year_began__gte=1900,
                                                             series_count__gte=200))),
            safe=False,
            json_dumps_params={'ensure_ascii': False})


def roles_list(request):
    return JsonResponse(json.loads(serialize('json', GcdCreditType.objects.all())), safe=False,
                        json_dumps_params={'ensure_ascii': False})


def stories(request, issue_id: int):
    story_list = GcdStory.objects.filter(issue_id=issue_id)

    return JsonResponse(
            json.loads(serialize('json', story_list)),
            safe=False,
            json_dumps_params={'ensure_ascii': False})


def credits(request, issue_id: int):
    story_credits = GcdStoryCredit.objects.filter(story__issue=issue_id)

    js = JsonResponse(
            json.loads(serialize('json', story_credits)),
            safe=False,
            json_dumps_params={'ensure_ascii': False})

    return js


def creator(request, creator_id: int):
    return JsonResponse(json.loads(serialize('json', GcdCreator.objects.filter(pk=creator_id))),
                        safe=False,
                        json_dumps_params={'ensure_ascii': False})


def story_types(request):
    return JsonResponse(json.loads(serialize('json', GcdStoryType.objects.all())),
                        safe=False,
                        json_dumps_params={'ensure_ascii': False})


def creators(request, issue_id):
    story_list: RawQuerySet = GcdCreator.objects.raw(f"""
        select *
        from gcd_creator gc
        where gc.id in (
            select gsc.creator_id
            from gcd_story_credit gsc
            where gsc.story_id in (
                select gs.id
                from gcd_story gs
                where gs.issue_id = {issue_id}))""")

    return JsonResponse(
            json.loads(serialize('json', story_list)),
            safe=False,
            json_dumps_params={'ensure_ascii': False})
