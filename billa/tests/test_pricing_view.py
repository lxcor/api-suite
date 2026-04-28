"""Tests for PricingView — credit pack catalogue page."""

from django.test import TestCase

from billa.models import CreditPack


class PricingViewTests(TestCase):

    def setUp(self):
        CreditPack.objects.all().delete()

    def test_renders_200(self):
        response = self.client.get('/pricing/')
        self.assertEqual(response.status_code, 200)

    def test_active_packs_in_context(self):
        CreditPack.objects.create(name='Pro', credits=500, price='4.99')
        response = self.client.get('/pricing/')
        self.assertEqual(len(list(response.context['packs'])), 1)

    def test_inactive_packs_excluded(self):
        CreditPack.objects.create(name='Pro', credits=500, price='4.99', is_active=False)
        response = self.client.get('/pricing/')
        self.assertEqual(len(list(response.context['packs'])), 0)

    def test_free_credits_from_free_tier_pack(self):
        CreditPack.objects.create(name='Free', credits=100, price='0.00', is_free_tier=True)
        response = self.client.get('/pricing/')
        self.assertEqual(response.context['free_credits'], 100)

    def test_free_credits_zero_when_no_free_pack(self):
        response = self.client.get('/pricing/')
        self.assertEqual(response.context['free_credits'], 0)

    def test_free_tier_pack_not_shown_when_inactive(self):
        CreditPack.objects.create(
            name='Free', credits=100, price='0.00', is_free_tier=True, is_active=False,
        )
        CreditPack.objects.create(name='Pro', credits=500, price='4.99')
        response = self.client.get('/pricing/')
        packs = list(response.context['packs'])
        names = [p.name for p in packs]
        self.assertNotIn('Free', names)
        self.assertIn('Pro', names)
