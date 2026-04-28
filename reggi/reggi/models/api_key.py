"""Model definition for ApiKey — a hashed API key issued to a user."""

import hashlib
import os
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


def _get_key_prefix():
    """Return the configured project prefix string, or empty string if not set."""
    return getattr(settings, 'REGGI_KEY_PREFIX', None)


def generate_api_key():
    """Generate a new raw API key and return (raw_key, lookup_prefix, key_hash, salt).

    The raw key is never stored — only the lookup prefix, hash, and salt are
    persisted.  The raw key must be shown to the user immediately and cannot
    be recovered after that point.

    Returns
    -------
    tuple
        (raw_key, lookup_prefix, key_hash, salt_hex)
    """
    token = secrets.token_urlsafe(30)
    project_prefix = _get_key_prefix()

    if project_prefix:
        raw_key = f'{project_prefix}_{token}'
    else:
        raw_key = token

    lookup_prefix = token[:8]
    salt = os.urandom(16)
    salt_hex = salt.hex()
    key_hash = hashlib.pbkdf2_hmac(
        'sha256',
        raw_key.encode('utf-8'),
        salt,
        260000,
    ).hex()

    return raw_key, lookup_prefix, key_hash, salt_hex


def verify_api_key(raw_key, key_hash, salt_hex):
    """Return True if the raw key matches the stored hash and salt.

    Parameters
    ----------
    raw_key : str
        The raw key string as submitted by the client.
    key_hash : str
        The hex-encoded PBKDF2 hash stored in the database.
    salt_hex : str
        The hex-encoded salt stored in the database.

    Returns
    -------
    bool
    """
    salt = bytes.fromhex(salt_hex)
    candidate_hash = hashlib.pbkdf2_hmac(
        'sha256',
        raw_key.encode('utf-8'),
        salt,
        260000,
    ).hex()
    return candidate_hash == key_hash


class ApiKey(models.Model):
    """An API key issued to a user.

    The raw key is never stored.  Only the first 8 characters of the token
    portion (``prefix``) are stored in plaintext for efficient DB lookup.
    The full key is hashed with PBKDF2-SHA256 and a unique per-key salt.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='api_keys',
    )
    name = models.CharField(
        max_length=255,
        help_text='A label to identify this key (e.g. Production, Testing).',
    )
    prefix = models.CharField(
        max_length=8,
        help_text='First 8 characters of the token — stored for lookup only.',
    )
    key_hash = models.CharField(max_length=128)
    salt = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Updated on every authenticated request.',
    )
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Leave blank for no expiry.',
    )
    revoked_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Set when the key is revoked. Null means the key is active.',
    )
    tier = models.ForeignKey(
        'kotta.Tier',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='api_keys',
        help_text='Rate-limit tier for this key. Overrides the user-level tier when set.',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Disable without deleting.',
    )

    class Meta:
        unique_together = ('user', 'name')
        ordering = ('-created_at',)

    def __str__(self):
        """Return a readable identifier for the key."""
        return f'{self.user} — {self.name} ({self.prefix}...)'

    @property
    def is_valid(self):
        """Return True if the key is active, not revoked, and not expired."""
        if not self.is_active or self.revoked_at is not None:
            return False
        if self.expires_at is not None and self.expires_at < timezone.now():
            return False
        return True
