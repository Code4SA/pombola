from __future__ import unicode_literals

from __future__ import absolute_import
from django import template

register = template.Library()


@register.filter
def absolute_url(abs_path, request):
    return request.build_absolute_uri(abs_path)
