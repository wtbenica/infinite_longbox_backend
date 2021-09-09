import json

from django.core.serializers import serialize
from django.db.models.query import RawQuerySet
from django.http import HttpResponse, JsonResponse

from db_query.models import *

ROWS_PER_PAGE = 500
UNITED_STATES = 225


def index(request):
    return HttpResponse("Hello, world. You're at the polls index")


def all_series(request, page: int):
    series_list = GcdSeries.objects.all()[
                  page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(series_list)


def num_series_pages(request):
    num_pages = GcdSeries.objects.all().count() // ROWS_PER_PAGE + 1
    return JsonResponse({'count': num_pages}, safe=False)


def num_publisher_pages(request):
    num_pages = GcdPublisher.objects.all().count() // ROWS_PER_PAGE + 1
    return JsonResponse({'count': num_pages}, safe=False)


def num_character_pages(request):
    num_pages = GcdCharacter.objects.all().count() // ROWS_PER_PAGE + 1
    return JsonResponse({'count': num_pages}, safe=False)


def num_creator_pages(request):
    num_pages = GcdCreator.objects.all().count() // ROWS_PER_PAGE + 1
    return JsonResponse({'count': num_pages}, safe=False)


def num_name_detail_pages(request):
    num_pages = GcdCreatorNameDetail.objects.all().count() // ROWS_PER_PAGE + 1
    return JsonResponse({'count': num_pages}, safe=False)


def pubs_by_page(request, page: int):
    pubs_list = GcdPublisher.objects.all()[
                page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(pubs_list)


def issues_list(request, page: int):
    series_list = GcdIssue.objects.all()[
                  page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(series_list)


def stories_list(request, page: int):
    series_list = GcdStory.objects.all()[
                  page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(series_list)


def credits_list(request, page: int):
    series_list = GcdStoryCredit.objects.all()[
                  page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(series_list)


def excredits_list(request, page: int):
    series_list = GcdExtractedStoryCredit.objects.all()[
                  page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(series_list)


def appearances_list(request, page: int):
    series_list = GcdCharacterAppearance.objects.all()[
                  page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(series_list)


def name_details_list(request, page: int):
    series_list = GcdCreatorNameDetail.objects.all()[
                  page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(series_list)


def all_creators(request, page: int):
    creators_list = GcdCreator.objects.all()[page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(creators_list)


def all_characters(request, page: int):
    character_list = GcdCharacter.objects.all()[page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]

    return StandardResponse(character_list)


def series_by_ids(request, series_ids: str):
    ids = str_to_int_list(series_ids)
    series = GcdSeries.objects.filter(pk__in=ids)

    return StandardResponse(series)


def issue_by_id(request, issue_id: int):
    issue = GcdIssue.objects.filter(pk=issue_id)

    return StandardResponse(issue)


def issues_by_series(request, series_id):
    issue_list: RawQuerySet = GcdIssue.objects.raw(
            """select distinct gi. *
            from gcd_issue gi
            where gi.series_id = %s
            or gi.id in (
                select gi2.variant_of_id
                from gcd_issue gi2
                where gi2.series_id = %s
            );""", [series_id, series_id])

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
    credit_list = GcdStoryCredit.objects.filter(issue=issue_id)

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


def namedetail_by_name(request, name):
    namedetail = GcdCreatorNameDetail.objects.filter(name=name)

    return StandardResponse(namedetail)


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


def credits_by_name_detail(request, name_detail_ids: str):
    ids = str_to_int_list(name_detail_ids)
    story_credits = GcdStoryCredit.objects.filter(creator__in=ids)

    return StandardResponse(story_credits)


def excredits_by_name_detail(request, name_detail_ids: str):
    ids = [int(id) for id in name_detail_ids.strip('[]').split(', ')]
    story_credits = GcdExtractedStoryCredit.objects.filter(creator__in=ids)

    return StandardResponse(story_credits)


def name_details_by_ids(request, name_detail_ids: str):
    ids = str_to_int_list(name_detail_ids)

    return StandardResponse(GcdCreatorNameDetail.objects.filter(pk__in=ids))


def publisher_by_id(request, pub_ids: str):
    ids = str_to_int_list(pub_ids)

    return StandardResponse(GcdPublisher.objects.filter(pk__in=ids))


def creators_list(request, creator_ids: str):
    ids = [int(id) for id in creator_ids.strip('[]').split(", ")]

    return StandardResponse(GcdCreator.objects.filter(pk__in=ids))


def issues_by_ids(request, issue_ids: str):
    ids = str_to_int_list(issue_ids)

    rawSet: RawQuerySet = GcdIssue.objects.raw(
            """select distinct gi.*
            from gcd_issue gi
            where gi.id in (
                select gi2.variant_of_id
                from gcd_issue gi2
                join gcd_series gs2 on gi2.series_id = gs2.id
                where gi2.id in %s 
            )
            union
            select distinct gi. *
            from gcd_issue gi
            where gi.id in %s
            ;""", [ids, ids])

    return StandardResponse(rawSet)


def stories_by_issues(request, issue_ids: str):
    ids = str_to_int_list(issue_ids)

    return StandardResponse(GcdStory.objects.filter(issue_id__in=ids))


def credits_by_stories(request, story_ids: str):
    ids = str_to_int_list(story_ids)

    return StandardResponse(GcdStoryCredit.objects.filter(story_id__in=ids))


def extracts_by_stories(request, story_ids: str):
    ids = str_to_int_list(story_ids)

    return StandardResponse(
            GcdExtractedStoryCredit.objects.filter(story_id__in=ids))


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


def story(request, story_ids: str):
    ids = str_to_int_list(story_ids)

    return StandardResponse(GcdStory.objects.filter(pk__in=ids))


def story_characters(request, story_ids: str):
    ids = str_to_int_list(story_ids)

    return StandardResponse(
            GcdCharacterAppearance.objects.filter(story_id__in=ids))


def character_appearances(request, character_id: int):
    return StandardResponse(GcdCharacterAppearance.objects.filter(character_id=character_id))


def characters_by_id(request, ids: str):
    ids = str_to_int_list(ids)

    return StandardResponse(
            GcdCharacter.objects.filter(pk__in=ids)
    )


def name_details_by_creator(request, creator_ids):
    ids = [int(id) for id in creator_ids.strip('[]').split(', ')]

    return StandardResponse(
            GcdCreatorNameDetail.objects.filter(creator__in=ids))


def series_bonds(request):
    return StandardResponse(GcdSeriesBond.objects.all())


def series_bond_types(request):
    return StandardResponse(GcdSeriesBondType.objects.all())


def str_to_int_list(ids_string):
    return [int(id) for id in ids_string.strip('[]').split(", ")]


class StandardResponse(JsonResponse):
    def __init__(self, data, **kwargs):
        super().__init__(
                json.loads(serialize('json', data, use_natural_foreign_keys=True)),
                safe=False,
                json_dumps_params={'ensure_ascii': False}, **kwargs)
