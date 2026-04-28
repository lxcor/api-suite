"""Model definition for UserTier — the tier assignment for a specific user."""

from django.conf import settings
from django.db import models


class UserTier(models.Model):
    """Assigns a membership tier to a user with an optional validity window.

    If a user has no ``UserTier`` record the default tier is applied.
    If ``valid_until`` is set and has passed, the default tier is applied
    as fallback.  The most recently created active record is used when
    multiple records exist.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kotta_tiers'
    )
    tier = models.ForeignKey('Tier', on_delete=models.PROTECT, related_name='user_assignments')
    valid_from = models.DateField()
    valid_until = models.DateField(
        null=True, blank=True,
        help_text='Leave blank for no expiry.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def save(self, *args, **kwargs):
        """Set valid_from to today if not provided."""
        if not self.valid_from:
            from django.utils import timezone
            self.valid_from = timezone.now().date()
        super().save(*args, **kwargs)

    def __str__(self):
        """Return user and tier name."""
        return '%s — %s' % (self.user, self.tier)
