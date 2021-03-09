from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('series', views.series, name='series')
]