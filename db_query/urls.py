from django.urls import path

from . import views

series_urls = [
    path('series_list/<int:page>', views.all_series, name='series_list'),
    path('series/<int:series_id>', views.series_by_id, name='series'),
    path('series/<int:series_id>/issues', views.issues_by_series,
        name='issues'),
]

issue_urls = [
    path('issue/<int:issue_id>', views.issue_by_id, name='issue'),
    path('issue/<int:issue_id>/stories', views.stories_by_issue,
        name='stories'),
    path('issue/<int:issue_id>/credits', views.credits_by_issue,
        name='credits'),
    path('issue/<int:issue_id>/creators', views.creators_by_issue,
        name='creators'),
]

creator_urls = [
    path('creator/<int:creator_id>', views.creator, name='creator'),
    path('creator/<int:creator_id>/stories', views.creator_stories,
        name='creator_series'),
    path('creator/<int:creator_id>/credits', views.creator_credits,
        name='creator_credits'),
    path('creator_list/<str:bob>', views.creators_list,
        name='creators_list')
]

name_detail_urls = [
    path('name_detail/name/<str:name>', views.creator_by_name,
        name='creator_by_name'),
    path('name_detail/<str:bob>', views.name_detail_list,
        name='name_detail_list')
]

urlpatterns = [
                  path('', views.index, name='index'),
                  path('role', views.all_roles, name='role'),
                  path('publisher', views.all_publishers, name='publisher'),
                  path('story_types', views.all_story_types,
                      name='story_types'),
              ] + series_urls + issue_urls + creator_urls
