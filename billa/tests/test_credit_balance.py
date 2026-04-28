"""Tests for CreditBalance — single-default invariant and merge_into."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from billa.models import CreditBalance, CreditPack
from reggi.models import ApiKey
from reggi.models.api_key import generate_api_key

User = get_user_model()


def _make_key(user, name='Key'):
    _, prefix, key_hash, salt = generate_api_key()
    return ApiKey.objects.create(
        user=user, name=name, prefix=prefix, key_hash=key_hash, salt=salt,
    )


class SingleDefaultTests(TestCase):

    def setUp(self):
        CreditPack.objects.filter(is_free_tier=True).delete()
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')

    def test_setting_default_clears_sibling(self):
        key1 = _make_key(self.user, 'Key1')
        key2 = _make_key(self.user, 'Key2')
        bal1 = CreditBalance.objects.create(api_key=key1, is_default=True)
        CreditBalance.objects.create(api_key=key2, is_default=True)
        bal1.refresh_from_db()
        self.assertFalse(bal1.is_default)

    def test_non_default_save_leaves_existing_default(self):
        key1 = _make_key(self.user, 'Key1')
        key2 = _make_key(self.user, 'Key2')
        bal1 = CreditBalance.objects.create(api_key=key1, is_default=True)
        CreditBalance.objects.create(api_key=key2, is_default=False)
        bal1.refresh_from_db()
        self.assertTrue(bal1.is_default)

    def test_different_users_each_have_independent_defaults(self):
        user2 = User.objects.create_user(username='u2', password='p', email='u2@x.com')
        key1 = _make_key(self.user, 'Key1')
        key2 = _make_key(user2, 'Key2')
        bal1 = CreditBalance.objects.create(api_key=key1, is_default=True)
        bal2 = CreditBalance.objects.create(api_key=key2, is_default=True)
        bal1.refresh_from_db()
        bal2.refresh_from_db()
        self.assertTrue(bal1.is_default)
        self.assertTrue(bal2.is_default)


class MergeIntoTests(TestCase):

    def setUp(self):
        CreditPack.objects.filter(is_free_tier=True).delete()
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')
        key1 = _make_key(self.user, 'Key1')
        key2 = _make_key(self.user, 'Key2')
        self.source = CreditBalance.objects.create(api_key=key1, credits_remaining=30)
        self.target = CreditBalance.objects.create(
            api_key=key2, credits_remaining=70, is_default=True,
        )

    def test_target_receives_source_credits(self):
        self.source.merge_into(self.target)
        self.target.refresh_from_db()
        self.assertEqual(self.target.credits_remaining, 100)

    def test_source_credits_zeroed(self):
        self.source.merge_into(self.target)
        self.source.refresh_from_db()
        self.assertEqual(self.source.credits_remaining, 0)

    def test_source_key_revoked(self):
        self.source.merge_into(self.target)
        self.source.api_key.refresh_from_db()
        self.assertFalse(self.source.api_key.is_active)
        self.assertIsNotNone(self.source.api_key.revoked_at)

    def test_target_key_not_revoked(self):
        self.source.merge_into(self.target)
        self.target.api_key.refresh_from_db()
        self.assertTrue(self.target.api_key.is_active)
        self.assertIsNone(self.target.api_key.revoked_at)

    def test_zero_source_credits_merge_leaves_target_unchanged(self):
        self.source.credits_remaining = 0
        self.source.save()
        self.source.merge_into(self.target)
        self.target.refresh_from_db()
        self.assertEqual(self.target.credits_remaining, 70)
