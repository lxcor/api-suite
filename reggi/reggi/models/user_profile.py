"""User profile model for reggi — stores per-user state not in AUTH_USER_MODEL."""

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """One-to-one extension of the auth user model.

    Currently stores email verification status.  Created automatically on
    user registration when ``REGGI_EMAIL_VERIFICATION`` is enabled.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reggi_profile',
    )
    email_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'user profile'
        verbose_name_plural = 'user profiles'

    def __str__(self):
        return f'Profile({self.user})'
