"""Tests for ApiKey tier FK — assignment, null default, cascade on tier delete."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from kotta.models import Tier
from reggi.models import ApiKey
from reggi.models.api_key import generate_api_key

User = get_user_model()


def _make_key(user, name='Key'):
    _, prefix, key_hash, salt = generate_api_key()
    return ApiKey.objects.create(
        user=user, name=name, prefix=prefix, key_hash=key_hash, salt=salt,
    )


class ApiKeyTierTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='tieruser', password='pass', email='t@example.com',
        )

    def test_tier_defaults_to_none(self):
        key = _make_key(self.user)
        self.assertIsNone(key.tier)

    def test_tier_can_be_assigned(self):
        tier = Tier.objects.create(name='Pro', slug='pro')
        key = _make_key(self.user)
        key.tier = tier
        key.save(update_fields=['tier'])
        key.refresh_from_db()
        self.assertEqual(key.tier, tier)

    def test_tier_set_to_null_on_tier_delete(self):
        tier = Tier.objects.create(name='Basic', slug='basic')
        key = _make_key(self.user)
        key.tier = tier
        key.save()
        tier.delete()
        key.refresh_from_db()
        self.assertIsNone(key.tier)

    def test_key_is_valid_with_tier_assigned(self):
        tier = Tier.objects.create(name='Pro', slug='pro')
        key = _make_key(self.user)
        key.tier = tier
        key.save()
        self.assertTrue(key.is_valid)

    def test_two_keys_can_share_same_tier(self):
        tier = Tier.objects.create(name='Free', slug='free')
        key_a = _make_key(self.user, name='A')
        key_b = _make_key(self.user, name='B')
        key_a.tier = tier
        key_b.tier = tier
        key_a.save()
        key_b.save()
        self.assertEqual(ApiKey.objects.filter(tier=tier).count(), 2)
