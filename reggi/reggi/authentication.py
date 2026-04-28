"""DRF authentication class that validates API keys issued by reggi."""

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from reggi.models import ApiKey
from reggi.models.api_key import verify_api_key


class ApiKeyAuthentication(BaseAuthentication):
    """Authenticate incoming requests using a reggi-issued API key.

    Supports two header styles, configured via ``REGGI_AUTH_HEADER_STYLE``:

    - ``'bearer'`` (default): ``Authorization: Bearer <key>``
    - ``'apikey'``: ``X-Api-Key: <key>``

    Returns ``(user, api_key)`` on success, ``None`` if no key is present,
    or raises ``AuthenticationFailed`` if the key is invalid or expired.
    """

    def authenticate(self, request):
        """Extract and validate the API key from the request."""
        raw_key = self._extract_key(request)
        if raw_key is None:
            return None

        project_prefix = getattr(settings, 'REGGI_KEY_PREFIX', None)
        if project_prefix and raw_key.startswith(f'{project_prefix}_'):
            token_portion = raw_key[len(project_prefix) + 1:]
        else:
            token_portion = raw_key

        lookup_prefix = token_portion[:8]

        candidates = ApiKey.objects.filter(
            prefix=lookup_prefix,
            is_active=True,
            revoked_at__isnull=True,
        ).select_related('user')

        for candidate in candidates:
            if not verify_api_key(raw_key, candidate.key_hash, candidate.salt):
                continue
            if candidate.expires_at is not None and candidate.expires_at < timezone.now():
                continue
            candidate.last_used_at = timezone.now()
            candidate.save(update_fields=['last_used_at'])
            return (candidate.user, candidate)

        raise AuthenticationFailed('Invalid or expired API key.')

    def _extract_key(self, request):
        """Return the raw API key string from the request, or None if absent."""
        style = getattr(settings, 'REGGI_AUTH_HEADER_STYLE', 'bearer')

        if style == 'apikey':
            return request.META.get('HTTP_X_API_KEY') or None

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:] or None

        return None
