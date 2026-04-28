"""Tests for tier resolution: _get_tier_for_key and _get_active_tier."""

import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from kotta.models import Tier, UserTier
from kotta.throttle import _get_active_tier, _get_tier_for_key
from reggi.models import ApiKey
from reggi.models.api_key import generate_api_key

User = get_user_model()


def _make_key(user, tier=None):
    _, prefix, key_hash, salt = generate_api_key()
    return ApiKey.objects.create(
        user=user, name='Key', prefix=prefix, key_hash=key_hash, salt=salt, tier=tier,
    )


def _make_tier(name, is_default=False):
    return Tier.objects.create(name=name, is_default=is_default)


class GetTierForKeyTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')

    def test_key_with_explicit_tier_returns_that_tier(self):
        tier = _make_tier('Pro')
        key = _make_key(self.user, tier=tier)
        self.assertEqual(_get_tier_for_key(key), tier)

    def test_key_without_tier_falls_back_to_user_tier(self):
        tier = _make_tier('Basic')
        UserTier.objects.create(user=self.user, tier=tier, valid_from=timezone.now().date())
        key = _make_key(self.user)
        self.assertEqual(_get_tier_for_key(key), tier)

    def test_key_without_tier_no_user_tier_returns_default(self):
        default_tier = _make_tier('Free', is_default=True)
        key = _make_key(self.user)
        self.assertEqual(_get_tier_for_key(key), default_tier)

    def test_none_api_key_returns_none(self):
        self.assertIsNone(_get_tier_for_key(None))


class GetActiveTierTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')
        self.today = timezone.now().date()

    def test_indefinite_user_tier_returned(self):
        tier = _make_tier('Pro')
        UserTier.objects.create(user=self.user, tier=tier, valid_from=self.today, valid_until=None)
        self.assertEqual(_get_active_tier(self.user), tier)

    def test_time_bounded_active_tier_returned(self):
        tier = _make_tier('Basic')
        future = self.today + datetime.timedelta(days=30)
        UserTier.objects.create(user=self.user, tier=tier, valid_from=self.today, valid_until=future)
        self.assertEqual(_get_active_tier(self.user), tier)

    def test_expired_user_tier_falls_back_to_default(self):
        expired_tier = _make_tier('Old')
        default_tier = _make_tier('Free', is_default=True)
        yesterday = self.today - datetime.timedelta(days=1)
        UserTier.objects.create(
            user=self.user, tier=expired_tier,
            valid_from=self.today - datetime.timedelta(days=10),
            valid_until=yesterday,
        )
        self.assertEqual(_get_active_tier(self.user), default_tier)

    def test_no_user_tier_returns_default_tier(self):
        default_tier = _make_tier('Free', is_default=True)
        self.assertEqual(_get_active_tier(self.user), default_tier)

    def test_no_user_tier_no_default_returns_none(self):
        self.assertIsNone(_get_active_tier(self.user))

    def test_inactive_default_tier_not_returned(self):
        inactive = _make_tier('Free', is_default=True)
        inactive.is_active = False
        inactive.save()
        self.assertIsNone(_get_active_tier(self.user))

    def test_most_recent_active_usertier_wins(self):
        tier_old = _make_tier('Old')
        tier_new = _make_tier('New')
        UserTier.objects.create(user=self.user, tier=tier_old, valid_from=self.today)
        UserTier.objects.create(user=self.user, tier=tier_new, valid_from=self.today)
        self.assertEqual(_get_active_tier(self.user), tier_new)
