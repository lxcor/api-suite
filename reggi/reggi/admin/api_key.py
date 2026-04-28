"""Admin configuration for the ApiKey model."""

from django.contrib import admin
from django.utils import timezone

from reggi.models import ApiKey


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    """Admin configuration for the ApiKey model.

    The raw key is never stored and never shown here.  The prefix field
    allows managers to identify a key without exposing the full value.
    """

    list_display = ['user', 'name', 'prefix', 'is_active', 'created_at', 'last_used_at', 'revoked_at']
    list_filter = ['is_active', 'revoked_at']
    search_fields = ['user__username', 'user__email', 'name', 'prefix']
    readonly_fields = ['prefix', 'key_hash', 'salt', 'created_at', 'last_used_at']
    fields = ['user', 'name', 'prefix', 'key_hash', 'salt', 'is_active', 'expires_at', 'revoked_at', 'created_at', 'last_used_at']
    actions = ['revoke_selected_keys']

    def revoke_selected_keys(self, request, queryset):
        """Set revoked_at and is_active=False on all selected keys."""
        now = timezone.now()
        updated = queryset.filter(revoked_at__isnull=True).update(revoked_at=now, is_active=False)
        self.message_user(request, '%d key(s) revoked.' % updated)

    revoke_selected_keys.short_description = 'Revoke selected API keys'
