from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('series', views.series, name='series'),
    path('issue/<int:pk_id>', views.issue, name='issue'),
    path('role', views.role, name='role'),
    path('publisher', views.publishers, name='publisher')
]