from __future__ import absolute_import
from django.conf.urls import url

from pombola.map.views import home


urlpatterns = [
    url(r'^$', home, name='map-home'),
]
