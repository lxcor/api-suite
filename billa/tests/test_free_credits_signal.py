"""Tests for attach_free_credits signal — free CreditBalance on ApiKey creation."""

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


class FreeCreditsSignalTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')
        self.free_pack = CreditPack.objects.create(
            name='Free', credits=100, price='0.00', is_free_tier=True, is_active=True,
        )

    def test_credit_balance_created_on_key_creation(self):
        _make_key(self.user)
        self.assertTrue(CreditBalance.objects.filter(api_key__user=self.user).exists())

    def test_balance_has_free_pack_credits(self):
        _make_key(self.user)
        balance = CreditBalance.objects.get(api_key__user=self.user)
        self.assertEqual(balance.credits_remaining, 100)

    def test_first_key_gets_is_default_true(self):
        _make_key(self.user)
        balance = CreditBalance.objects.get(api_key__user=self.user)
        self.assertTrue(balance.is_default)

    def test_second_key_gets_is_default_false(self):
        _make_key(self.user, 'Key1')
        _make_key(self.user, 'Key2')
        balances = list(CreditBalance.objects.filter(api_key__user=self.user).order_by('pk'))
        self.assertTrue(balances[0].is_default)
        self.assertFalse(balances[1].is_default)

    def test_skipped_when_from_purchase_flag_set(self):
        _, prefix, key_hash, salt = generate_api_key()
        key = ApiKey(
            user=self.user, name='PurchaseKey',
            prefix=prefix, key_hash=key_hash, salt=salt,
        )
        key._from_purchase = True
        key.save()
        self.assertFalse(CreditBalance.objects.filter(api_key=key).exists())

    def test_skipped_when_no_free_tier_pack_exists(self):
        CreditPack.objects.filter(is_free_tier=True).delete()
        _make_key(self.user)
        self.assertFalse(CreditBalance.objects.filter(api_key__user=self.user).exists())

    def test_skipped_when_free_pack_has_zero_credits(self):
        self.free_pack.credits = 0
        self.free_pack.save()
        _make_key(self.user)
        self.assertFalse(CreditBalance.objects.filter(api_key__user=self.user).exists())

    def test_not_triggered_on_key_update(self):
        key = _make_key(self.user)
        CreditBalance.objects.filter(api_key=key).delete()
        key.name = 'Updated'
        key.save()
        self.assertFalse(CreditBalance.objects.filter(api_key=key).exists())
