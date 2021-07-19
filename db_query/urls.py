from django.urls import path

from . import views

series_urls = [
    path('series_list/<int:page>', views.all_series, name='series_list'),
    path('series/<str:series_ids>', views.series_by_ids, name='series'),
    path('series/<int:series_id>/issues', views.issues_by_series,
        name='issues'),
    path('series/<int:series_id>/series_bond', views.series_bond,
        name='series_bond'),
]

issue_urls = [
    path('issue/<int:issue_id>', views.issue_by_id, name='issue'),
    path('issue/<int:issue_id>/stories', views.stories_by_issue,
        name='stories'),
    path('issue/<int:issue_id>/credits', views.credits_by_issue,
        name='credits'),
    path('issue/<int:issue_id>/creators', views.creators_by_issue,
        name='creators'),
    path('issues/<str:issue_ids>', views.issues_by_ids, name='issues_by_ids'),
    path('issue/<int:series_id>/issue_bond', views.issue_bond,
        name='issue_bond')
]

creator_urls = [
    path('creator/<int:creator_id>', views.creator, name='creator'),
    # path('creator/<int:creator_id>/stories', views.creator_stories,
    #      name='creator_series'),
    path('creators/all/<int:page>', views.all_creators, name='all_creators'),
    path('creators/<str:creator_ids>/name_details',
        views.name_detail_by_creator,
        name='name_detail_by_creator'),
    path('creator_list/<str:creator_ids>', views.creators_list,
        name='creators_list'),
    path('creator_name/<str:name>/stories', views.stories_by_name,
        name='stories_by_name'),
    path('creator_name/<str:name>', views.creator)
]

name_detail_urls = [
    path('name_detail/name/<str:name>', views.namedetail_by_name,
        name='name_detail_by_name'),
    path('name_detail/<str:name_detail_ids>', views.name_detail_list,
        name='name_detail_list'),
    path('name_detail/<str:name_detail_ids>/stories',
        views.stories_by_name_detail, name='stories_by_name_detail'),
    path('name_details/creator_ids/<str:creator_ids>',
        views.name_details_by_creator, name='name_details_by_creator'),
    path('name_detail/<str:name_detail_ids>/credits',
        views.credits_by_name_detail, name='creator_credits'),
    path('name_detail/<str:name_detail_ids>/extracts',
        views.excredits_by_name_detail, name='creator_extracts'),
]

story_urls = [
    path('stories/<str:story_ids>/credits', views.credits_by_stories,
        name='credits_by_stories'),
    path('stories/<str:story_ids>/extracts',
        views.extracts_by_stories, name='extracts_by_stories'),
    path('story/<str:story_ids>', views.story, name='story')
]

static_urls = [
    path('', views.index, name='index'),
    path('role', views.all_roles, name='role'),
    path('publisher', views.all_publishers, name='publisher'),
    path('story_types', views.all_story_types,        name='story_types'),
    path('story_bond_types', views.story_bond_types, name='story_bond_types')
]

urlpatterns = series_urls + issue_urls + creator_urls + name_detail_urls + story_urls + static_urls
