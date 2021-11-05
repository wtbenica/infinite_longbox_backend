import json
from typing import Type

from django.core.serializers import serialize
from django.db.models.query import RawQuerySet
from django.http import HttpResponse, JsonResponse

from db_query.models import *

ROWS_PER_PAGE = 500
UNITED_STATES = 225


def index(request) -> HttpResponse:
    return HttpResponse("Hello, world. You're at the polls index")


# Get number of pages
def get_num_pages(model: Type[models.Model]) -> JsonResponse:
    num_pages = model.objects.all().count() // ROWS_PER_PAGE + 1
    return JsonResponse({'count': num_pages}, safe=False)


def num_series_pages(request) -> JsonResponse:
    return get_num_pages(GcdSeries)


def num_publisher_pages(request) -> JsonResponse:
    return get_num_pages(GcdPublisher)


def num_character_pages(request) -> JsonResponse:
    return get_num_pages(GcdCharacter)


def num_creator_pages(request) -> JsonResponse:
    return get_num_pages(GcdCreator)


def num_name_detail_pages(request) -> JsonResponse:
    return get_num_pages(GcdCreatorNameDetail)


# Get items by page
def get_all_by_page(model: Type[models.Model], page: int) -> JsonResponse:
    query_set = model.objects.all().order_by('id')[
    page * ROWS_PER_PAGE:(page + 1) * ROWS_PER_PAGE]
    return StandardResponse(query_set)


def get_all_series_by_page(request, page: int) -> JsonResponse:
    return get_all_by_page(GcdSeries, page)


def get_all_publishers_by_page(request, page: int) -> JsonResponse:
    return get_all_by_page(GcdPublisher, page)


def get_all_credits_by_page(request, page: int) -> JsonResponse:
    return get_all_by_page(GcdStoryCredit, page)


def get_all_excredits_by_page(request, page: int) -> JsonResponse:
    return get_all_by_page(GcdExtractedStoryCredit, page)


def get_all_appearances_by_page(request, page: int) -> JsonResponse:
    return get_all_by_page(GcdCharacterAppearance, page)


def get_all_name_details_by_page(request, page: int) -> JsonResponse:
    return get_all_by_page(GcdCreatorNameDetail, page)


def get_all_creators_by_page(request, page: int) -> JsonResponse:
    return get_all_by_page(GcdCreator, page)


def get_all_characters_by_page(request, page: int) -> JsonResponse:
    return get_all_by_page(GcdCharacter, page)


# Get items by id list
def get_items_by_id_list(id_list: str, model: Type[models.Model]) -> \
        JsonResponse:
    ids = str_to_int_list(id_list)
    query_set = model.objects.filter(pk__in=ids)
    return StandardResponse(query_set)


def series_by_id_list(request, series_ids: str) -> JsonResponse:
    return get_items_by_id_list(series_ids, GcdSeries)


def name_details_by_id_list(request, name_detail_ids: str) -> JsonResponse:
    return get_items_by_id_list(name_detail_ids, GcdCreatorNameDetail)


def creators_by_id_list(request, creator_ids: str) -> JsonResponse:
    return get_items_by_id_list(creator_ids, GcdCreator)


def publishers_by_id_list(request, pub_ids: str) -> JsonResponse:
    return get_items_by_id_list(pub_ids, GcdPublisher)


def stories_by_id_list(request, story_ids: str) -> JsonResponse:
    return get_items_by_id_list(story_ids, GcdStory)


def characters_by_id_list(request, char_ids: str) -> JsonResponse:
    return get_items_by_id_list(char_ids, GcdCharacter)


def issues_by_id_list(request, issue_ids: str) -> JsonResponse:
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
        ;""", [ids, ids]
    )

    return StandardResponse(rawSet)


# Get item by id
def get_item_by_id(issue_id: int, model: Type[models.Model]) -> JsonResponse:
    issue = model.objects.filter(pk=issue_id)
    return StandardResponse(issue)


def issue_by_id(request, issue_id: int) -> JsonResponse:
    return get_item_by_id(issue_id, GcdIssue)


def creator_by_id(request, creator_id: int) -> JsonResponse:
    return get_item_by_id(creator_id, GcdCreator)


def issues_by_series(request, series_id) -> JsonResponse:
    issue_list: RawQuerySet = GcdIssue.objects.raw(
        """select distinct gi. *
        from gcd_issue gi
        where gi.series_id = %s
        or gi.id in (
            select gi2.variant_of_id
            from gcd_issue gi2
            where gi2.series_id = %s
        );""", [series_id, series_id]
    )

    return StandardResponse(issue_list)


# Get all
def get_all(model: Type[models.Model]) -> JsonResponse:
    query_set = model.objects.all()
    return StandardResponse(query_set)


def all_publishers(request) -> JsonResponse:
    return get_all(GcdPublisher)


def all_roles(request) -> JsonResponse:
    return get_all(GcdCreditType)


def all_story_types(request) -> JsonResponse:
    return get_all(GcdStoryType)


def series_bonds(request) -> JsonResponse:
    return get_all(GcdSeriesBond)


def series_bond_types(request) -> JsonResponse:
    return get_all(GcdSeriesBondType)


# Get stories by _
def stories_by_issue_id(request, issue_id: int) -> JsonResponse:
    story_list = GcdStory.objects.filter(issue_id=issue_id)

    return StandardResponse(story_list)


def stories_by_issue_id_list(request, issue_ids: str) -> JsonResponse:
    ids = str_to_int_list(issue_ids)

    return StandardResponse(GcdStory.objects.filter(issue_id__in=ids))


def stories_by_name_detail_id_list(request, name_detail_ids: str) -> \
        JsonResponse:
    ids = [int(id) for id in name_detail_ids.strip('[]').split(", ")]

    story_list = GcdStory.objects.raw(
        """select distinct gy.*
           from gcd_story gy
           join gcd_story_credit gsc on gy.id = gsc.story_id
           join gcd_creator_name_detail gcnd on gsc.creator_id = gcnd.id
           where gcnd.id in %s
           """, [ids]
    )

    return StandardResponse(story_list)


def stories_by_name(request, name: str) -> JsonResponse:
    return StandardResponse(
        GcdStory.objects.filter(script__contains=name) |
        GcdStory.objects.filter(pencils__contains=name) |
        GcdStory.objects.filter(inks__contains=name) |
        GcdStory.objects.filter(colors__contains=name) |
        GcdStory.objects.filter(letters__contains=name) |
        GcdStory.objects.filter(editing__contains=name)
    )


# Get credits by _
def credits_by_issue_id(request, issue_id: int) -> JsonResponse:
    credit_list = GcdStoryCredit.objects.filter(issue_id=issue_id)

    return StandardResponse(credit_list)


def credits_by_name_detail_id_list(request, name_detail_ids: str) -> \
        JsonResponse:
    ids = str_to_int_list(name_detail_ids)
    story_credits = GcdStoryCredit.objects.filter(creator__in=ids)

    return StandardResponse(story_credits)


def credits_by_story_id_list(request, story_ids: str) -> JsonResponse:
    ids = str_to_int_list(story_ids)

    return StandardResponse(GcdStoryCredit.objects.filter(story__in=ids))


# Get extracted credits by _
def ex_credits_by_name_detail_id_list(request,
        name_detail_ids: str) -> JsonResponse:
    ids = [int(id) for id in name_detail_ids.strip('[]').split(', ')]
    story_credits = GcdExtractedStoryCredit.objects.filter(creator__in=ids)

    return StandardResponse(story_credits)


def ex_credits_by_story_id_list(request, story_ids: str) -> JsonResponse:
    ids = str_to_int_list(story_ids)

    return StandardResponse(
        GcdExtractedStoryCredit.objects.filter(story__in=ids)
    )


# Get creators by _
def creators_by_issue_id(request, issue_id: int) -> JsonResponse:
    creator_list: RawQuerySet = GcdCreator.objects.raw(
        """select distinct gc.* 
        from gcd_creator gc 
        join gcd_creator_name_detail gcnd on gc.id = gcnd.creator_id 
        join gcd_story_credit gsc on gcnd.id = gsc.creator_id 
        join gcd_story gs on gsc.story_id = gs.id 
        join gcd_issue gi on gs.issue_id = gi.id
        where gs.issue_id =  %s""", [issue_id]
    )

    return StandardResponse(creator_list)


# Get appearances by _
def appearances_by_story_id_list(request, story_ids: str) -> JsonResponse:
    ids = str_to_int_list(story_ids)

    return StandardResponse(
        GcdCharacterAppearance.objects.filter(story_id__in=ids)
    )


def appearances_by_character_id(request, character_ids: str) -> JsonResponse:
    ids = str_to_int_list(character_ids)

    return StandardResponse(
        GcdCharacterAppearance.objects.filter(character_id__in=ids)
    )


def str_to_int_list(ids_string) -> [int]:
    return [int(id) for id in ids_string.strip('[]').split(", ")]


class StandardResponse(JsonResponse):
    def __init__(self, data, **kwargs):
        super().__init__(
            json.loads(serialize('json', data, use_natural_foreign_keys=True)),
            safe=False,
            json_dumps_params={'ensure_ascii': False}, **kwargs
        )
