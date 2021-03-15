from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('series', views.series, name='series'),
    path('series/<int:page>', views.series, name='seriesList'),
    path('issue/<int:pk_id>', views.issue, name='issue'),
    path('role', views.role, name='role'),
    path('publisher', views.publishers, name='publisher'),
    path('series/<int:pk_id>/issues', views.issues, name='issues')
]
