"""Tests for ApiKeyAuthentication — bearer/apikey header styles, expiry, prefix."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from reggi.authentication import ApiKeyAuthentication
from reggi.models import ApiKey
from reggi.models.api_key import generate_api_key

User = get_user_model()


class ApiKeyAuthenticationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser', password='pass', email='api@example.com',
        )
        self.factory = RequestFactory()
        self.auth = ApiKeyAuthentication()

        raw_key, prefix, key_hash, salt = generate_api_key()
        self.raw_key = raw_key
        self.key = ApiKey.objects.create(
            user=self.user, name='Main', prefix=prefix, key_hash=key_hash, salt=salt,
        )

    def _bearer(self, key):
        return self.factory.get('/', HTTP_AUTHORIZATION=f'Bearer {key}')

    def _apikey_header(self, key):
        return self.factory.get('/', HTTP_X_API_KEY=key)

    def test_valid_bearer_token_returns_user_and_key(self):
        user, api_key = self.auth.authenticate(self._bearer(self.raw_key))
        self.assertEqual(user, self.user)
        self.assertEqual(api_key, self.key)

    def test_no_auth_header_returns_none(self):
        request = self.factory.get('/')
        self.assertIsNone(self.auth.authenticate(request))

    def test_invalid_key_raises_authentication_failed(self):
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(self._bearer('totally-wrong-key'))

    def test_revoked_key_raises_authentication_failed(self):
        self.key.revoked_at = timezone.now()
        self.key.save(update_fields=['revoked_at'])
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(self._bearer(self.raw_key))

    def test_inactive_key_raises_authentication_failed(self):
        self.key.is_active = False
        self.key.save(update_fields=['is_active'])
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(self._bearer(self.raw_key))

    def test_expired_key_raises_authentication_failed(self):
        self.key.expires_at = timezone.now() - timedelta(seconds=1)
        self.key.save(update_fields=['expires_at'])
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(self._bearer(self.raw_key))

    def test_future_expiry_key_authenticates(self):
        self.key.expires_at = timezone.now() + timedelta(days=30)
        self.key.save(update_fields=['expires_at'])
        user, _ = self.auth.authenticate(self._bearer(self.raw_key))
        self.assertEqual(user, self.user)

    def test_last_used_at_updated_on_success(self):
        self.assertIsNone(self.key.last_used_at)
        self.auth.authenticate(self._bearer(self.raw_key))
        self.key.refresh_from_db()
        self.assertIsNotNone(self.key.last_used_at)

    @override_settings(REGGI_AUTH_HEADER_STYLE='apikey')
    def test_x_api_key_header_style_authenticates(self):
        user, api_key = self.auth.authenticate(self._apikey_header(self.raw_key))
        self.assertEqual(user, self.user)

    @override_settings(REGGI_AUTH_HEADER_STYLE='apikey')
    def test_bearer_ignored_when_apikey_style_set(self):
        # Bearer header present but style is 'apikey' — no key found → None
        result = self.auth.authenticate(self._bearer(self.raw_key))
        self.assertIsNone(result)

    @override_settings(REGGI_KEY_PREFIX='proj')
    def test_prefixed_key_authenticates(self):
        raw_key, prefix, key_hash, salt = generate_api_key()
        ApiKey.objects.create(
            user=self.user, name='Prefixed', prefix=prefix, key_hash=key_hash, salt=salt,
        )
        user, _ = self.auth.authenticate(self._bearer(raw_key))
        self.assertEqual(user, self.user)

    def test_empty_bearer_value_returns_none(self):
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer ')
        self.assertIsNone(self.auth.authenticate(request))
