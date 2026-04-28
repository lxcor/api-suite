"""Tests for BillerThrottle — credit deduction and PaymentRequired gating."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase, override_settings

from billa.models import CreditBalance
from billa.throttle import BillerThrottle, PaymentRequired
from reggi.models import ApiKey
from reggi.models.api_key import generate_api_key

User = get_user_model()


def _make_key(user, name='Key'):
    _, prefix, key_hash, salt = generate_api_key()
    return ApiKey.objects.create(
        user=user, name=name, prefix=prefix, key_hash=key_hash, salt=salt,
    )


def _auth_request(factory, user, api_key):
    request = factory.get('/api/data/')
    request.user = user
    request.auth = api_key
    return request


class BillerThrottleTests(TestCase):

    def setUp(self):
        from billa.models import CreditPack
        CreditPack.objects.filter(is_free_tier=True).delete()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')
        self.api_key = _make_key(self.user)
        self.balance = CreditBalance.objects.create(
            api_key=self.api_key, credits_remaining=10,
        )

    def _request(self):
        return _auth_request(self.factory, self.user, self.api_key)

    def test_anonymous_request_always_allowed(self):
        request = self.factory.get('/api/data/')
        request.user = AnonymousUser()
        self.assertTrue(BillerThrottle().allow_request(request, None))

    def test_no_credit_balance_passes_through(self):
        self.balance.delete()
        self.assertTrue(BillerThrottle().allow_request(self._request(), None))

    def test_request_with_credits_allowed(self):
        self.assertTrue(BillerThrottle().allow_request(self._request(), None))

    def test_credits_decremented_after_allowed_request(self):
        BillerThrottle().allow_request(self._request(), None)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.credits_remaining, 9)

    def test_zero_credits_raises_payment_required(self):
        self.balance.credits_remaining = 0
        self.balance.save()
        with self.assertRaises(PaymentRequired):
            BillerThrottle().allow_request(self._request(), None)

    def test_kotta_throttle_info_skips_deduction(self):
        request = self._request()
        request.kotta_throttle_info = {'blocked': True}
        BillerThrottle().allow_request(request, None)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.credits_remaining, 10)

    @override_settings(BILLER_UPGRADE_URL='https://example.com/pricing')
    def test_payment_required_includes_upgrade_url_when_setting_present(self):
        self.balance.credits_remaining = 0
        self.balance.save()
        try:
            BillerThrottle().allow_request(self._request(), None)
            self.fail('PaymentRequired not raised')
        except PaymentRequired as exc:
            self.assertIn('upgrade_url', exc.detail)
            self.assertEqual(exc.detail['upgrade_url'], 'https://example.com/pricing')

    def test_payment_required_has_no_upgrade_url_without_setting(self):
        self.balance.credits_remaining = 0
        self.balance.save()
        try:
            BillerThrottle().allow_request(self._request(), None)
            self.fail('PaymentRequired not raised')
        except PaymentRequired as exc:
            self.assertNotIn('upgrade_url', exc.detail)

    def test_wait_returns_none(self):
        self.assertIsNone(BillerThrottle().wait())

    def test_request_without_api_key_auth_passes_through(self):
        request = self.factory.get('/api/data/')
        request.user = self.user
        request.auth = None
        self.assertTrue(BillerThrottle().allow_request(request, None))
