from django.contrib import admin
from django.core import urlresolvers
from django.utils.safestring import mark_safe  

from pombola.za_hansard import models
from .filters import SuccessfullyParsedFilter

@admin.register(models.SourceParsingLog)
class SourceParsingLogAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'linked_source',
        'source_url',
        'error',
        'success',
        ]

    list_filter = ['error', 'success', 'date',]
    readonly_fields = [
        'date',
        'source',
        'error',
        'success', 
        'log',
        'source',
        'linked_source'
        ]
    actions = []
    date_hierarchy = 'date'

    def source_url(self, obj):
        return mark_safe('<a href="{}">{}</a>'.format(
            obj.source.url,
            obj.source.url
        ))

    def linked_source(self, obj):
        return mark_safe('<a href="{}">{}</a>'.format(
            urlresolvers.reverse("admin:za_hansard_source_change", args=(obj.source.pk,)),
            obj.source
        ))

@admin.register(models.Source)
class ZAHansardSourceAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'pmg_hansard',
        'url',
        'is404',
        'last_processing_success',
        'last_processing_attempt',
        ]

    readonly_fields = [
        'pmg_hansard',
        ]
    date_hierarchy = 'date'

    def pmg_hansard(self, obj):
        return mark_safe('<a href="https://api.pmg.org.za/hansard/{}/">{}</a>'.format(
            obj.pmg_id,
            obj.pmg_id
        ))

    list_filter = [SuccessfullyParsedFilter, 'is404', 'date']