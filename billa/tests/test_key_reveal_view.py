"""Tests for PurchaseKeyRevealView."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

User = get_user_model()


class PurchaseKeyRevealViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')

    def tearDown(self):
        cache.delete(f'billa_new_key_{self.user.pk}')

    def test_unauthenticated_redirects(self):
        response = self.client.get('/billing/key/')
        self.assertEqual(response.status_code, 302)

    def test_no_key_redirects_to_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get('/billing/key/')
        self.assertRedirects(response, '/reggi/keys/', fetch_redirect_response=False)

    def test_session_key_renders_page(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['billa_new_raw_key'] = 'test_raw_key_value'
        session.save()
        response = self.client.get('/billing/key/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_raw_key_value')

    def test_session_key_consumed_after_view(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['billa_new_raw_key'] = 'test_raw_key_value'
        session.save()
        self.client.get('/billing/key/')
        self.assertNotIn('billa_new_raw_key', self.client.session)

    def test_cache_key_renders_page(self):
        self.client.force_login(self.user)
        cache.set(f'billa_new_key_{self.user.pk}', 'cached_key_value', 300)
        response = self.client.get('/billing/key/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cached_key_value')

    def test_cache_key_consumed_after_view(self):
        self.client.force_login(self.user)
        cache.set(f'billa_new_key_{self.user.pk}', 'cached_key_value', 300)
        self.client.get('/billing/key/')
        self.assertIsNone(cache.get(f'billa_new_key_{self.user.pk}'))

    def test_session_takes_precedence_over_cache(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['billa_new_raw_key'] = 'session_key'
        session.save()
        cache.set(f'billa_new_key_{self.user.pk}', 'cache_key', 300)
        response = self.client.get('/billing/key/')
        self.assertContains(response, 'session_key')
        self.assertNotContains(response, 'cache_key')
