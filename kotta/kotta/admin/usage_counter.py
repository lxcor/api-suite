"""Admin configuration for the UsageCounter model."""

from django.contrib import admin

from kotta.models import UsageCounter


@admin.register(UsageCounter)
class UsageCounterAdmin(admin.ModelAdmin):
    """Admin configuration for the UsageCounter model.

    Read-only monitoring view — no editing permitted.  Useful for
    debugging throttle behaviour and reviewing per-user usage.
    """

    list_display = ['user', 'ip_address', 'endpoint', 'count', 'window_start', 'updated_at']
    list_filter = ['endpoint', 'window_start']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'ip_address', 'endpoint', 'count', 'window_start', 'updated_at']

    def has_add_permission(self, request):
        """Disable manual creation — counters are managed by the throttle classes only."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing — counters are managed by the throttle classes only."""
        return False
