from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('series_list/<int:page>', views.series_list, name='series_list'),
    path('series/<int:series_id>', views.series, name='series'),
    path('series/<int:series_id>/issues', views.issues_by_series, name='issues'),
    path('issue/<int:issue_id>', views.issue, name='issue'),
    path('issue/<int:issue_id>/stories', views.stories, name='stories'),
    path('issue/<int:issue_id>/credits', views.credits, name='credits'),
    path('issue/<int:issue_id>/creators', views.creators, name='creators'),
    path('role', views.roles_list, name='role'),
    path('publisher', views.publishers_list, name='publisher'),
    path('creator/<int:creator_id>', views.creator, name='creator'),
    path('creator/name/<str:name>', views.name, name='creator_by_name'),
    path('story_types', views.story_types, name='story_types'),
]
