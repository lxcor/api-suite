"""Admin configuration for the Tier and TierEndpointLimit models."""

from django.contrib import admin

from kotta.models import Tier, TierEndpointLimit


class TierEndpointLimitInline(admin.TabularInline):
    """Inline for editing per-endpoint limits directly on the Tier admin page."""

    model = TierEndpointLimit
    extra = 1
    fields = ['endpoint', 'limit', 'period']
    autocomplete_fields = ['endpoint']


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    """Admin configuration for the Tier model.

    Shows all per-endpoint limits as a tabular inline so a tier and its
    full limit set are managed on a single screen.
    """

    list_display = ['name', 'slug', 'is_default', 'is_active', 'created_at']
    list_filter = ['is_default', 'is_active']
    search_fields = ['name']
    readonly_fields = ['slug', 'created_at']
    inlines = [TierEndpointLimitInline]
