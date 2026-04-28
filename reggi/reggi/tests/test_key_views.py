"""Tests for ApiKeyCreateView and ApiKeyRevokeView (key rotation flow)."""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from reggi.models import ApiKey
from reggi.models.api_key import generate_api_key

User = get_user_model()


def _make_key(user, name='Test Key'):
    _, prefix, key_hash, salt = generate_api_key()
    return ApiKey.objects.create(
        user=user, name=name, prefix=prefix, key_hash=key_hash, salt=salt,
    )


class ApiKeyCreateViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='creator', password='pass', email='c@example.com',
        )
        self.client.force_login(self.user)

    def test_get_renders_form(self):
        response = self.client.get(reverse('reggi.key_create'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_get_redirects(self):
        self.client.logout()
        response = self.client.get(reverse('reggi.key_create'))
        self.assertEqual(response.status_code, 302)

    def test_post_creates_key_record(self):
        self.client.post(reverse('reggi.key_create'), {'name': 'Prod Key'})
        self.assertTrue(ApiKey.objects.filter(user=self.user, name='Prod Key').exists())

    def test_post_shows_raw_key_in_context(self):
        response = self.client.post(reverse('reggi.key_create'), {'name': 'Prod Key'})
        self.assertIn('raw_key', response.context)
        self.assertTrue(len(response.context['raw_key']) > 0)

    def test_raw_key_not_stored_in_db(self):
        response = self.client.post(reverse('reggi.key_create'), {'name': 'Prod Key'})
        raw_key = response.context['raw_key']
        key = ApiKey.objects.get(user=self.user, name='Prod Key')
        self.assertNotEqual(raw_key, key.key_hash)
        self.assertNotEqual(raw_key, key.salt)

    def test_duplicate_name_rejected(self):
        _make_key(self.user, name='Existing')
        response = self.client.post(reverse('reggi.key_create'), {'name': 'Existing'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ApiKey.objects.filter(user=self.user, name='Existing').count(), 1)

    @override_settings(REGGI_KEY_EXPIRY_DAYS=30)
    def test_expiry_days_setting_applied(self):
        self.client.post(reverse('reggi.key_create'), {'name': 'Expiring'})
        key = ApiKey.objects.get(user=self.user, name='Expiring')
        self.assertIsNotNone(key.expires_at)
        delta = key.expires_at - timezone.now()
        self.assertAlmostEqual(delta.days, 29, delta=1)

    @override_settings(REGGI_KEY_EXPIRY_DAYS=None)
    def test_no_expiry_when_setting_absent(self):
        self.client.post(reverse('reggi.key_create'), {'name': 'No Expiry'})
        key = ApiKey.objects.get(user=self.user, name='No Expiry')
        self.assertIsNone(key.expires_at)


class ApiKeyRevokeViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='owner', password='pass', email='o@example.com',
        )
        self.client.force_login(self.user)
        self.key = _make_key(self.user)

    def test_post_sets_revoked_at(self):
        self.client.post(reverse('reggi.key_revoke', kwargs={'pk': self.key.pk}))
        self.key.refresh_from_db()
        self.assertIsNotNone(self.key.revoked_at)

    def test_post_sets_is_active_false(self):
        self.client.post(reverse('reggi.key_revoke', kwargs={'pk': self.key.pk}))
        self.key.refresh_from_db()
        self.assertFalse(self.key.is_active)

    def test_post_redirects_to_dashboard(self):
        response = self.client.post(
            reverse('reggi.key_revoke', kwargs={'pk': self.key.pk}),
        )
        self.assertRedirects(response, reverse('reggi.dashboard'), fetch_redirect_response=False)

    def test_revoked_key_absent_from_dashboard(self):
        self.client.post(reverse('reggi.key_revoke', kwargs={'pk': self.key.pk}))
        response = self.client.get(reverse('reggi.dashboard'))
        self.assertNotIn(self.key, response.context['keys'])

    def test_cannot_revoke_another_users_key(self):
        other = User.objects.create_user(
            username='other', password='pass', email='other@example.com',
        )
        self.client.force_login(other)
        response = self.client.post(
            reverse('reggi.key_revoke', kwargs={'pk': self.key.pk}),
        )
        self.assertEqual(response.status_code, 403)
        self.key.refresh_from_db()
        self.assertIsNone(self.key.revoked_at)

    def test_unauthenticated_revoke_redirects(self):
        self.client.logout()
        response = self.client.post(
            reverse('reggi.key_revoke', kwargs={'pk': self.key.pk}),
        )
        self.assertEqual(response.status_code, 302)

    def test_key_rotation_old_revoked_new_created(self):
        """Rotate: revoke old key then create new one — both in DB, old revoked."""
        self.client.post(reverse('reggi.key_revoke', kwargs={'pk': self.key.pk}))
        self.client.post(reverse('reggi.key_create'), {'name': 'New Key'})

        self.key.refresh_from_db()
        self.assertFalse(self.key.is_active)
        self.assertTrue(ApiKey.objects.filter(user=self.user, name='New Key', is_active=True).exists())
