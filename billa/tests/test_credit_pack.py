"""Tests for CreditPack model — catalogue management."""

from django.test import TestCase

from billa.models import CreditPack


class CreditPackTests(TestCase):

    def setUp(self):
        CreditPack.objects.all().delete()

    def test_active_pack_included_in_filter(self):
        CreditPack.objects.create(name='Pro', credits=500, price='4.99')
        self.assertEqual(CreditPack.objects.filter(is_active=True).count(), 1)

    def test_inactive_pack_excluded_from_active_filter(self):
        CreditPack.objects.create(name='Pro', credits=500, price='4.99', is_active=False)
        self.assertEqual(CreditPack.objects.filter(is_active=True).count(), 0)

    def test_ordering_by_credits_ascending(self):
        CreditPack.objects.create(name='Big', credits=1000, price='9.99')
        CreditPack.objects.create(name='Small', credits=100, price='0.99')
        packs = list(CreditPack.objects.all())
        self.assertEqual(packs[0].credits, 100)
        self.assertEqual(packs[1].credits, 1000)

    def test_free_tier_flag_stored(self):
        pack = CreditPack.objects.create(name='Free', credits=50, price='0.00', is_free_tier=True)
        self.assertTrue(CreditPack.objects.get(pk=pack.pk).is_free_tier)

    def test_pack_without_tier_is_valid(self):
        pack = CreditPack.objects.create(name='Basic', credits=100, price='1.99')
        self.assertIsNone(pack.tier)

    def test_pack_with_tier_stores_tier(self):
        from kotta.models import Tier
        tier = Tier.objects.create(name='Pro')
        pack = CreditPack.objects.create(name='Pro Pack', credits=500, price='4.99', tier=tier)
        self.assertEqual(pack.tier, tier)

    def test_tier_nulled_on_tier_delete(self):
        from kotta.models import Tier
        tier = Tier.objects.create(name='Pro')
        pack = CreditPack.objects.create(name='Pro Pack', credits=500, price='4.99', tier=tier)
        tier.delete()
        pack.refresh_from_db()
        self.assertIsNone(pack.tier)

    def test_str_representation(self):
        pack = CreditPack.objects.create(name='Starter', credits=1000, price='2.99')
        self.assertEqual(str(pack), 'Starter (1,000 credits)')
