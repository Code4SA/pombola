from __future__ import absolute_import
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^in/(?P<slug>[-\w]+)/', views.in_place, name='project_in_place'),
]
