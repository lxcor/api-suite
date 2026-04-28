"""Unit tests for ApiKey model — key generation, hashing, and validation logic."""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from reggi.models.api_key import generate_api_key, verify_api_key, ApiKey

User = get_user_model()


class GenerateApiKeyTests(TestCase):
    """Tests for the generate_api_key() function."""

    @override_settings(REGGI_KEY_PREFIX=None)
    def test_returns_four_values(self):
        """generate_api_key returns a 4-tuple."""
        result = generate_api_key()
        self.assertEqual(len(result), 4)

    @override_settings(REGGI_KEY_PREFIX='cal')
    def test_raw_key_includes_prefix(self):
        """Raw key starts with the configured prefix and underscore."""
        raw_key, _, _, _ = generate_api_key()
        self.assertTrue(raw_key.startswith('cal_'))

    @override_settings(REGGI_KEY_PREFIX=None)
    def test_raw_key_no_prefix(self):
        """Raw key has no underscore prefix when REGGI_KEY_PREFIX is None."""
        raw_key, _, _, _ = generate_api_key()
        self.assertFalse(raw_key.startswith('_'))

    @override_settings(REGGI_KEY_PREFIX=None)
    def test_lookup_prefix_is_8_chars(self):
        """Lookup prefix is exactly 8 characters."""
        _, lookup_prefix, _, _ = generate_api_key()
        self.assertEqual(len(lookup_prefix), 8)

    @override_settings(REGGI_KEY_PREFIX=None)
    def test_salt_is_32_hex_chars(self):
        """Salt is a 32-character hex string (16 bytes)."""
        _, _, _, salt_hex = generate_api_key()
        self.assertEqual(len(salt_hex), 32)
        int(salt_hex, 16)  # raises ValueError if not valid hex

    @override_settings(REGGI_KEY_PREFIX=None)
    def test_key_hash_is_hex(self):
        """Key hash is a non-empty hex string."""
        _, _, key_hash, _ = generate_api_key()
        self.assertTrue(len(key_hash) > 0)
        int(key_hash, 16)  # raises ValueError if not valid hex

    @override_settings(REGGI_KEY_PREFIX=None)
    def test_two_keys_are_unique(self):
        """Two generated keys produce different raw keys and hashes."""
        raw1, prefix1, hash1, salt1 = generate_api_key()
        raw2, prefix2, hash2, salt2 = generate_api_key()
        self.assertNotEqual(raw1, raw2)
        self.assertNotEqual(hash1, hash2)
        self.assertNotEqual(salt1, salt2)


class VerifyApiKeyTests(TestCase):
    """Tests for the verify_api_key() function."""

    @override_settings(REGGI_KEY_PREFIX=None)
    def test_correct_key_verifies(self):
        """A key verifies against its own stored hash and salt."""
        raw_key, _, key_hash, salt_hex = generate_api_key()
        self.assertTrue(verify_api_key(raw_key, key_hash, salt_hex))

    @override_settings(REGGI_KEY_PREFIX=None)
    def test_wrong_key_fails(self):
        """A different key does not verify against stored hash and salt."""
        raw_key, _, key_hash, salt_hex = generate_api_key()
        self.assertFalse(verify_api_key('wrongkey', key_hash, salt_hex))

    @override_settings(REGGI_KEY_PREFIX=None)
    def test_wrong_salt_fails(self):
        """The same raw key does not verify with a different salt."""
        raw_key, _, key_hash, salt_hex = generate_api_key()
        _, _, _, other_salt = generate_api_key()
        self.assertFalse(verify_api_key(raw_key, key_hash, other_salt))


class ApiKeyModelTests(TestCase):
    """Tests for the ApiKey model and its is_valid property."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')

    def _make_key(self, **kwargs):
        """Helper — create an ApiKey record from generate_api_key()."""
        _, lookup_prefix, key_hash, salt_hex = generate_api_key()
        defaults = dict(
            user=self.user,
            name='Test Key',
            prefix=lookup_prefix,
            key_hash=key_hash,
            salt=salt_hex,
            is_active=True,
        )
        defaults.update(kwargs)
        return ApiKey.objects.create(**defaults)

    def test_active_key_is_valid(self):
        """An active, non-revoked, non-expired key is valid."""
        key = self._make_key()
        self.assertTrue(key.is_valid)

    def test_inactive_key_is_not_valid(self):
        """A key with is_active=False is not valid."""
        key = self._make_key(is_active=False)
        self.assertFalse(key.is_valid)

    def test_revoked_key_is_not_valid(self):
        """A key with revoked_at set is not valid."""
        key = self._make_key(revoked_at=timezone.now())
        self.assertFalse(key.is_valid)

    def test_expired_key_is_not_valid(self):
        """A key whose expires_at is in the past is not valid."""
        past = timezone.now() - timezone.timedelta(seconds=1)
        key = self._make_key(expires_at=past)
        self.assertFalse(key.is_valid)

    def test_future_expiry_key_is_valid(self):
        """A key whose expires_at is in the future is still valid."""
        future = timezone.now() + timezone.timedelta(days=30)
        key = self._make_key(expires_at=future)
        self.assertTrue(key.is_valid)

    def test_str_representation(self):
        """__str__ includes username, key name, and prefix."""
        key = self._make_key()
        result = str(key)
        self.assertIn('testuser', result)
        self.assertIn('Test Key', result)
