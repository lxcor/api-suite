"""Admin configuration for the UserTier model."""

from django.contrib import admin

from kotta.models import UserTier


@admin.register(UserTier)
class UserTierAdmin(admin.ModelAdmin):
    """Admin configuration for the UserTier model.

    Allows managers to assign or change a user's membership tier and
    set the validity window.
    """

    list_display = ['user', 'tier', 'valid_from', 'valid_until', 'created_at']
    list_filter = ['tier', 'valid_until']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']
