from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('series', views.series, name='series'),
    path('series_list/<int:page>', views.series_list, name='series_list'),
    path('series/<int:series_id>', views.series, name='series'),
    path('series/<int:series_id>/issues', views.issues_by_series, name='issues'),
    path('issue/<int:issue_id>', views.issue, name='issue'),
    path('issue/<int:issue_id>/credits', views.credits, name='credits'),
    path('role', views.roles_list, name='role'),
    path('publisher', views.publishers_list, name='publisher'),
]
