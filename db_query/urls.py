from django.urls import path

from . import views, get_covers

page_count_urls = [
    path(
        'publisher/page_count',
        views.num_publisher_pages,
        name='publisher_count'
    ),
    path(
        'series/page_count',
        views.num_series_pages,
        name='series_count'
    ),
    path(
        'name_detail/page_count',
        views.num_name_detail_pages,
        name='name_detail_count'
    ),
    path(
        'character/page_count',
        views.num_character_pages,
        name='character_count'
    ),
]

get_by_page_urls = [
    path(
        'publisher/page/<int:page>',
        views.get_all_publishers_by_page,
        name='publishers_list'
    ),
    path(
        'series/page/<int:page>',
        views.get_all_series_by_page,
        name='series_list'
    ),
    path(
        'name_detail/page/<int:page>',
        views.get_all_name_details_by_page,
        name='name_details_list'
    ),
    path(
        'character/page/<int:page>',
        views.get_all_characters_by_page,
        name='characters_list'
    ),
]

get_by_ids_urls = [
    path(
        'publishers/ids/<str:pub_ids>',
        views.publishers_by_id_list,
        name='publisher_by_ids'
    ),
    path(
        'series/ids/<str:series_ids>',
        views.series_by_id_list,
        name='series_by_ids'
    ),
    path(
        'issue/ids/<str:issue_ids>',
        views.issues_by_id_list,
        name='issues_by_ids'
    ),
    path(
        'story/ids/<str:story_ids>',
        views.stories_by_id_list,
        name='stories_by_ids'
    ),
    path(
        'creator/ids/<str:creator_ids>',
        views.creators_by_id_list,
        name='creators_by_ids'
    ),
    path(
        'name_detail/ids/<str:name_detail_ids>',
        views.name_details_by_id_list,
        name='name_detail_by_ids'
    ),
    path(
        'character/ids/<str:char_ids>',
        views.characters_by_id_list,
        name='characters_by_ids'
    ),
]

series_urls = [
    path(
        'series/id/<int:series_id>/issues',
        views.issues_by_series,
        name='issues'
    ),
]

issue_urls = [
    path(
        'issue/ids/<str:issue_ids>/stories',
        views.stories_by_issue_id_list,
        name='stories_by_issues'
    ),
    # This is used, but not in Webservice.kt, so be careful before deleting
    path(
        'issue/id/<int:id>/cover', get_covers.get_cover,
        name='issue_cover'
    )
]

story_urls = [
    path(
        'story/ids/<str:story_ids>/credits',
        views.credits_by_story_id_list,
        name='credits_by_stories'
    ),
    path(
        'story/ids/<str:story_ids>/extracts',
        views.ex_credits_by_story_id_list,
        name='extracts_by_stories'
    ),
    path(
        'story/ids/<str:story_ids>/appearances',
        views.appearances_by_story_id_list,
        name='story appearances'
    ),
]

name_detail_urls = [
    path(
        'name_detail/ids/<str:name_detail_ids>/credits',
        views.credits_by_name_detail_id_list,
        name='creator_credits'
    ),
    path(
        'name_detail/ids/<str:name_detail_ids>/extracts',
        views.ex_credits_by_name_detail_id_list,
        name='creator_extracts'
    ),
]

character_urls = [
    path(
        'character/ids/<str:character_ids>/appearances',
        views.appearances_by_character_id,
        name='character_appearances'
    ),
]

static_urls = [
    path(
        '',
        views.index,
        name='index'
    ),
    path(
        'role/all',
        views.all_roles,
        name='roles'
    ),
    path(
        'story_type/all',
        views.all_story_types,
        name='story_types'
    ),
    path(
        'series_bond_type/all',
        views.series_bond_types,
        name='series_bond_types'
    ),
    path(
        'series_bond/all',
        views.series_bonds,
        name='series_bonds'
    ),
]

urlpatterns = page_count_urls + get_by_page_urls + series_urls + issue_urls \
              + story_urls + name_detail_urls + character_urls + static_urls \
              + get_by_ids_urls
