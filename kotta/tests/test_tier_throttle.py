"""Tests for TierThrottle — per-tier per-endpoint quota enforcement."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.utils import timezone

from kotta.models import Endpoint, Tier, TierEndpointLimit, UserTier
from kotta.throttle import TierThrottle
from reggi.models import ApiKey
from reggi.models.api_key import generate_api_key

User = get_user_model()


def _make_key(user, tier=None):
    _, prefix, key_hash, salt = generate_api_key()
    return ApiKey.objects.create(
        user=user, name='Key', prefix=prefix, key_hash=key_hash, salt=salt, tier=tier,
    )


def _auth_request(factory, user, api_key, path='api/data/'):
    request = factory.get('/' + path)
    request.user = user
    request.auth = api_key
    return request


def _anon_request(factory, path='api/data/'):
    request = factory.get('/' + path)
    request.user = AnonymousUser()
    request.auth = None
    return request


class TierThrottleTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')
        self.tier = Tier.objects.create(name='Pro')
        self.endpoint = Endpoint.objects.create(path='api/data/', method='GET')
        self.api_key = _make_key(self.user, tier=self.tier)
        self.limit = TierEndpointLimit.objects.create(
            tier=self.tier, endpoint=self.endpoint, limit=3, period='day',
        )

    def _request(self, path='api/data/'):
        return _auth_request(self.factory, self.user, self.api_key, path)

    def test_anonymous_request_always_allowed(self):
        request = _anon_request(self.factory)
        self.assertTrue(TierThrottle().allow_request(request, None))

    def test_no_endpoint_match_always_allowed(self):
        request = _auth_request(self.factory, self.user, self.api_key, path='api/unknown/')
        self.assertTrue(TierThrottle().allow_request(request, None))

    def test_no_tier_on_key_and_no_user_tier_allows_when_open(self):
        _, prefix, key_hash, salt = generate_api_key()
        key_no_tier = ApiKey.objects.create(
            user=self.user, name='NoTier', prefix=prefix, key_hash=key_hash, salt=salt,
        )
        request = _auth_request(self.factory, self.user, key_no_tier)
        self.assertTrue(TierThrottle().allow_request(request, None))

    def test_within_limit_allowed(self):
        for _ in range(3):
            result = TierThrottle().allow_request(self._request(), None)
        self.assertTrue(result)

    def test_over_limit_blocked(self):
        for _ in range(3):
            TierThrottle().allow_request(self._request(), None)
        self.assertFalse(TierThrottle().allow_request(self._request(), None))

    def test_throttle_info_set_on_blocked_request(self):
        for _ in range(3):
            TierThrottle().allow_request(self._request(), None)
        request = self._request()
        TierThrottle().allow_request(request, None)
        self.assertTrue(hasattr(request, 'kotta_throttle_info'))

    def test_different_keys_have_independent_counters(self):
        user2 = User.objects.create_user(username='u2', password='p', email='u2@x.com')
        key2 = _make_key(user2, tier=self.tier)
        for _ in range(3):
            TierThrottle().allow_request(self._request(), None)
        request2 = _auth_request(self.factory, user2, key2)
        self.assertTrue(TierThrottle().allow_request(request2, None))

    @patch('kotta.throttle.KOTTA_OPEN_BY_DEFAULT', False)
    def test_no_limit_configured_blocks_when_not_open_by_default(self):
        new_ep = Endpoint.objects.create(path='api/new/', method='GET')
        request = _auth_request(self.factory, self.user, self.api_key, path='api/new/')
        self.assertFalse(TierThrottle().allow_request(request, None))

    @patch('kotta.throttle.KOTTA_OPEN_BY_DEFAULT', True)
    def test_no_limit_configured_allows_when_open_by_default(self):
        new_ep = Endpoint.objects.create(path='api/new/', method='GET')
        request = _auth_request(self.factory, self.user, self.api_key, path='api/new/')
        self.assertTrue(TierThrottle().allow_request(request, None))

    def test_wait_returns_positive_after_block(self):
        for _ in range(4):
            throttle = TierThrottle()
            throttle.allow_request(self._request(), None)
        self.assertIsNotNone(throttle.wait())
        self.assertGreater(throttle.wait(), 0)

    def test_user_tier_assignment_used_when_key_has_no_tier(self):
        tier2 = Tier.objects.create(name='Basic')
        TierEndpointLimit.objects.create(tier=tier2, endpoint=self.endpoint, limit=1, period='day')
        UserTier.objects.create(user=self.user, tier=tier2, valid_from=timezone.now().date())
        _, prefix, key_hash, salt = generate_api_key()
        key_no_tier = ApiKey.objects.create(
            user=self.user, name='K2', prefix=prefix, key_hash=key_hash, salt=salt,
        )
        request = _auth_request(self.factory, self.user, key_no_tier)
        TierThrottle().allow_request(request, None)
        # Second request should be blocked (limit=1 for tier2)
        request2 = _auth_request(self.factory, self.user, key_no_tier)
        self.assertFalse(TierThrottle().allow_request(request2, None))
