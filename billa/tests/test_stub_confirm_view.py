"""Tests for StubConfirmView — development checkout flow."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from billa.models import CreditPack, Purchase

User = get_user_model()


class StubConfirmViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')
        self.pack = CreditPack.objects.create(name='Starter', credits=500, price='4.99')

    def test_unauthenticated_get_redirects(self):
        response = self.client.get('/billing/stub/confirm/')
        self.assertEqual(response.status_code, 302)

    def test_authenticated_get_renders_200(self):
        self.client.force_login(self.user)
        response = self.client.get(f'/billing/stub/confirm/?pack_pk={self.pack.pk}')
        self.assertEqual(response.status_code, 200)

    def test_get_with_pack_pk_passes_correct_pack(self):
        self.client.force_login(self.user)
        response = self.client.get(f'/billing/stub/confirm/?pack_pk={self.pack.pk}')
        self.assertEqual(response.context['pack'], self.pack)

    def test_get_without_pack_pk_falls_back_to_first_active(self):
        self.client.force_login(self.user)
        response = self.client.get('/billing/stub/confirm/')
        self.assertEqual(response.context['pack'], self.pack)

    def test_get_with_inactive_pack_pk_falls_back_to_first_active(self):
        inactive = CreditPack.objects.create(
            name='Old', credits=100, price='0.99', is_active=False,
        )
        self.client.force_login(self.user)
        response = self.client.get(f'/billing/stub/confirm/?pack_pk={inactive.pk}')
        self.assertEqual(response.context['pack'], self.pack)

    def test_post_creates_purchase(self):
        self.client.force_login(self.user)
        self.client.post(f'/billing/stub/confirm/', {'pack_pk': self.pack.pk})
        self.assertEqual(Purchase.objects.filter(user=self.user, provider='stub').count(), 1)

    def test_post_redirects_to_key_reveal(self):
        self.client.force_login(self.user)
        response = self.client.post('/billing/stub/confirm/', {'pack_pk': self.pack.pk})
        self.assertRedirects(response, '/billing/key/', fetch_redirect_response=False)

    def test_post_stores_raw_key_in_session(self):
        self.client.force_login(self.user)
        self.client.post('/billing/stub/confirm/', {'pack_pk': self.pack.pk})
        self.assertIn('billa_new_raw_key', self.client.session)

    def test_unauthenticated_post_redirects(self):
        response = self.client.post('/billing/stub/confirm/', {'pack_pk': self.pack.pk})
        self.assertEqual(response.status_code, 302)
