"""Tests for fulfill_purchase service."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from billa.models import CreditBalance, CreditPack, Purchase
from billa.services import fulfill_purchase
from reggi.models import ApiKey

User = get_user_model()


class FulfillPurchaseTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')
        self.pack = CreditPack.objects.create(name='Starter', credits=500, price='4.99')

    def test_creates_api_key(self):
        fulfill_purchase(self.user, 'stub', 'sess_1', self.pack)
        self.assertEqual(ApiKey.objects.filter(user=self.user).count(), 1)

    def test_creates_credit_balance_with_pack_credits(self):
        fulfill_purchase(self.user, 'stub', 'sess_1', self.pack)
        balance = CreditBalance.objects.get(api_key__user=self.user)
        self.assertEqual(balance.credits_remaining, 500)

    def test_creates_purchase_record(self):
        fulfill_purchase(self.user, 'stub', 'sess_1', self.pack)
        self.assertTrue(
            Purchase.objects.filter(user=self.user, provider_session_id='sess_1').exists()
        )

    def test_purchase_records_correct_provider(self):
        fulfill_purchase(self.user, 'stub', 'sess_1', self.pack)
        purchase = Purchase.objects.get(provider_session_id='sess_1')
        self.assertEqual(purchase.provider, 'stub')

    def test_first_purchase_balance_is_default(self):
        fulfill_purchase(self.user, 'stub', 'sess_1', self.pack)
        balance = CreditBalance.objects.get(api_key__user=self.user)
        self.assertTrue(balance.is_default)

    def test_second_purchase_balance_not_default(self):
        fulfill_purchase(self.user, 'stub', 'sess_1', self.pack)
        fulfill_purchase(self.user, 'stub', 'sess_2', self.pack)
        # Ordered by -created_at, so the newest is first
        balances = list(CreditBalance.objects.filter(api_key__user=self.user).order_by('pk'))
        self.assertTrue(balances[0].is_default)
        self.assertFalse(balances[1].is_default)

    def test_idempotent_on_duplicate_session_id(self):
        fulfill_purchase(self.user, 'stub', 'sess_1', self.pack)
        fulfill_purchase(self.user, 'stub', 'sess_1', self.pack)
        self.assertEqual(Purchase.objects.count(), 1)

    def test_assigns_tier_to_api_key_when_pack_has_tier(self):
        from kotta.models import Tier
        tier = Tier.objects.create(name='Pro')
        pack_with_tier = CreditPack.objects.create(
            name='ProPack', credits=1000, price='9.99', tier=tier,
        )
        fulfill_purchase(self.user, 'stub', 'sess_3', pack_with_tier)
        key = ApiKey.objects.get(user=self.user)
        self.assertEqual(key.tier, tier)

    def test_no_tier_on_api_key_when_pack_has_none(self):
        fulfill_purchase(self.user, 'stub', 'sess_1', self.pack)
        key = ApiKey.objects.get(user=self.user)
        self.assertIsNone(key.tier)

    def test_api_key_name_includes_pack_name_and_prefix(self):
        fulfill_purchase(self.user, 'stub', 'sess_1', self.pack)
        key = ApiKey.objects.get(user=self.user)
        self.assertIn('Starter', key.name)
        self.assertIn(key.prefix, key.name)
