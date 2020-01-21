from __future__ import absolute_import
from django import template
import six

register = template.Library()

NO_PLACE_ORGS = ('parliament', 'national-assembly', )
MEMBER_ORGS = ('parliament', 'national-assembly', )


@register.assignment_tag()
def should_display_place(organisation):
    if not organisation:
        return True
    return organisation.slug not in NO_PLACE_ORGS


@register.assignment_tag()
def should_display_position(organisation, position_title):
    should_display = True

    if organisation.slug in MEMBER_ORGS and six.text_type(position_title) in (u'Member',):
        should_display = False

    if 'ncop' == organisation.slug and six.text_type(position_title) in (u'Delegate',):
        should_display = False

    return should_display
