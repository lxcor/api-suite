"""Admin configuration for the Endpoint model."""

from django.contrib import admin

from kotta.models import Endpoint


@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    """Admin configuration for the Endpoint model.

    Provides list display with active/orphan status indicators, search
    by path and name, and filtering by method, active state, and orphan
    flag.  Anon limits and description are editable inline.
    """

    list_display = ['method', 'path', 'name', 'anonymous_limit', 'anonymous_period', 'is_active', 'is_orphan']
    list_filter = ['method', 'is_active', 'is_orphan', 'anonymous_period']
    search_fields = ['path', 'name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        (None, {
            'fields': ['path', 'method', 'name', 'description', 'is_active']
        }),
        ('Anonymous access', {
            'fields': ['anonymous_limit', 'anonymous_period'],
            'description': 'Leave anonymous_limit blank to block anonymous access to this endpoint entirely.'
        }),
        ('Sync status', {
            'fields': ['is_orphan', 'created_at', 'updated_at'],
        }),
    ]
