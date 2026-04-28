"""Tests for AnonEndpointThrottle."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from kotta.models import Endpoint
from kotta.throttle import AnonEndpointThrottle

User = get_user_model()


def _anon_request(factory, path='api/data/', ip='1.2.3.4'):
    request = factory.get('/' + path)
    request.user = AnonymousUser()
    request.META['REMOTE_ADDR'] = ip
    return request


def _auth_request(factory, user, path='api/data/'):
    request = factory.get('/' + path)
    request.user = user
    return request


class AnonEndpointThrottleTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.endpoint = Endpoint.objects.create(
            path='api/data/', method='GET', anonymous_limit=3, anonymous_period='day',
        )

    def test_authenticated_request_always_allowed(self):
        user = User.objects.create_user(username='u', password='p', email='u@x.com')
        request = _auth_request(self.factory, user)
        self.assertTrue(AnonEndpointThrottle().allow_request(request, None))

    def test_anonymous_first_request_allowed(self):
        request = _anon_request(self.factory)
        self.assertTrue(AnonEndpointThrottle().allow_request(request, None))

    def test_anonymous_within_limit_allowed(self):
        for _ in range(3):
            result = AnonEndpointThrottle().allow_request(_anon_request(self.factory), None)
        self.assertTrue(result)

    def test_anonymous_over_limit_blocked(self):
        for _ in range(3):
            AnonEndpointThrottle().allow_request(_anon_request(self.factory), None)
        result = AnonEndpointThrottle().allow_request(_anon_request(self.factory), None)
        self.assertFalse(result)

    def test_different_ips_have_independent_limits(self):
        for _ in range(3):
            AnonEndpointThrottle().allow_request(_anon_request(self.factory, ip='1.1.1.1'), None)
        # Different IP is not exhausted
        result = AnonEndpointThrottle().allow_request(_anon_request(self.factory, ip='2.2.2.2'), None)
        self.assertTrue(result)

    def test_no_endpoint_match_always_allowed(self):
        request = _anon_request(self.factory, path='api/unknown/')
        self.assertTrue(AnonEndpointThrottle().allow_request(request, None))

    def test_inactive_endpoint_treated_as_no_match(self):
        self.endpoint.is_active = False
        self.endpoint.save()
        request = _anon_request(self.factory)
        self.assertTrue(AnonEndpointThrottle().allow_request(request, None))

    @patch('kotta.throttle.KOTTA_BLOCK_ANONYMOUS_BY_DEFAULT', True)
    def test_null_limit_blocks_when_default_block_enabled(self):
        ep = Endpoint.objects.create(path='api/locked/', method='GET', anonymous_limit=None)
        request = _anon_request(self.factory, path='api/locked/')
        self.assertFalse(AnonEndpointThrottle().allow_request(request, None))

    @patch('kotta.throttle.KOTTA_BLOCK_ANONYMOUS_BY_DEFAULT', False)
    @patch('kotta.throttle.KOTTA_DEFAULT_ANONYMOUS_LIMIT', 2)
    def test_null_limit_uses_default_when_block_disabled(self):
        ep = Endpoint.objects.create(path='api/open/', method='GET', anonymous_limit=None)
        for _ in range(2):
            AnonEndpointThrottle().allow_request(_anon_request(self.factory, path='api/open/'), None)
        result = AnonEndpointThrottle().allow_request(_anon_request(self.factory, path='api/open/'), None)
        self.assertFalse(result)

    def test_wait_returns_positive_after_block(self):
        for _ in range(4):
            throttle = AnonEndpointThrottle()
            throttle.allow_request(_anon_request(self.factory), None)
        self.assertIsNotNone(throttle.wait())
        self.assertGreater(throttle.wait(), 0)
