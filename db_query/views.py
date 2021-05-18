import json

from django.core.serializers import serialize
from django.db.models.query import RawQuerySet
from django.http import HttpResponse, JsonResponse

from db_query.models import *

ROWS_PER_PAGE = 2000
UNITED_STATES = 225


def index(request):
    return HttpResponse("Hello, world. You're at the polls index")


def all_series(request, page: int):
    series_list = GcdSeries.objects.all()[
    page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(series_list)


def series_by_id(request, series_id: int):
    series = GcdSeries.objects.filter(pk=series_id)

    return StandardResponse(series)


def issue_by_id(request, issue_id: int):
    issue = GcdIssue.objects.filter(pk=issue_id)

    return StandardResponse(issue)


def issues_by_series(request, series_id):
    issue_list = GcdIssue.objects.filter(series_id=series_id)

    return StandardResponse(issue_list)


def all_publishers(request) -> JsonResponse:
    publisher_list = GcdPublisher.objects.all()

    return StandardResponse(publisher_list)


def all_roles(request):
    role_list = GcdCreditType.objects.all()

    return StandardResponse(role_list)


def stories_by_issue(request, issue_id: int):
    story_list = GcdStory.objects.filter(issue=issue_id)

    return StandardResponse(story_list)


def credits_by_issue(request, issue_id: int):
    credit_list = GcdStoryCredit.objects.filter(story__issue=issue_id)

    return StandardResponse(credit_list)


def creator(request, creator_id: int):
    creator = GcdCreator.objects.filter(pk=creator_id)

    return StandardResponse(creator)


def all_story_types(request):
    story_type_list = GcdStoryType.objects.all()

    return StandardResponse(story_type_list)


def creators_by_issue(request, issue_id):
    creator_list: RawQuerySet = GcdCreator.objects.raw(
        """select distinct gc.* 
        from gcd_creator gc 
        join gcd_creator_name_detail gcnd on gc.id = gcnd.creator_id 
        join gcd_story_credit gsc on gcnd.id = gsc.creator_id 
        join gcd_story gs on gsc.story_id = gs.id 
        join gcd_issue gi on gs.issue_id = gi.id
        where gs.issue_id =  %s""", [issue_id])

    return StandardResponse(creator_list)


def creator_by_name(request, name):
    creator = GcdCreatorNameDetail.objects.filter(name=name)

    return StandardResponse(creator)


def stories_by_name_detail(request, name_detail_ids):
    ids = [int(id) for id in name_detail_ids.strip('[]').split(", ")]

    story_list = GcdStory.objects.raw("""
                                    select distinct gy.*
                                    from gcd_story gy
                                    join gcd_story_credit gsc on gy.id = gsc.story_id
                                    join gcd_creator_name_detail gcnd on gsc.creator_id = gcnd.id
                                    where gcnd.id in %s
                                    """, [ids])

    return StandardResponse(story_list)


def creator_credits(request, creator_ids: str):
    ids = [int(id) for id in creator_ids.strip('[]').split(', ')]
    story_credits = GcdStoryCredit.objects.filter(creator__creator__in=ids)

    return StandardResponse(story_credits)


def name_detail_list(request, name_detail_ids: str):
    ids = [int(id) for id in name_detail_ids.strip('[]').split(", ")]

    return StandardResponse(GcdCreatorNameDetail.objects.filter(pk__in=ids))


def creators_list(request, creator_ids: str):
    ids = [int(id) for id in creator_ids.strip('[]').split(", ")]

    return StandardResponse(GcdCreator.objects.filter(pk__in=ids))


def issues_by_ids(request, issue_ids: str):
    ids = [int(id) for id in issue_ids.strip('[]').split(", ")]

    return StandardResponse(GcdIssue.objects.filter(pk__in=ids))


def credits_by_stories(request, story_ids: str):
    ids = [int(id) for id in story_ids.strip('[]').split(", ")]

    return StandardResponse(GcdStoryCredit.objects.filter(story__in=ids))

def extracts_by_stories(request, story_ids: str):
    ids = [int(id) for id in story_ids.strip('[]').split(", ")]
    # TODO: add whatever model is needed for "my_credit"
    return StandardResponse(GcdStoryCredit.objects.filter(story__in=ids))

def name_detail_by_creator(request, creator_ids: str):
    ids = [int(id) for id in creator_ids.strip('[]').split(", ")]

    return StandardResponse(
        GcdCreatorNameDetail.objects.filter(creator__in=ids))


def stories_by_name(request, name: str):
    return StandardResponse(
        GcdStory.objects.filter(script__contains=name) |
        GcdStory.objects.filter(pencils__contains=name) |
        GcdStory.objects.filter(inks__contains=name) |
        GcdStory.objects.filter(colors__contains=name) |
        GcdStory.objects.filter(letters__contains=name) |
        GcdStory.objects.filter(editing__contains=name))


class StandardResponse(JsonResponse):
    def __init__(self, data, **kwargs):
        super().__init__(
            json.loads(serialize('json', data, use_natural_foreign_keys=True)),
            safe=False,
            json_dumps_params={'ensure_ascii': False}, **kwargs)


def story(request, story_ids: str):
    ids = [int(id) for id in story_ids.strip('[]').split(', ')]

    return StandardResponse(GcdStory.objects.filter(pk__in=ids))


def name_details_by_creator(request, creator_ids):
    ids = [int(id) for id in creator_ids.strip('[]').split(', ')]

    return StandardResponse(
        GcdCreatorNameDetail.objects.filter(creator__in=ids))
