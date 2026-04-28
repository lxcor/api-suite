"""Tests for SetDefaultView — mark a CreditBalance as the default merge target."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from billa.models import CreditBalance
from reggi.models import ApiKey
from reggi.models.api_key import generate_api_key

User = get_user_model()


def _make_key(user, name='Key'):
    _, prefix, key_hash, salt = generate_api_key()
    return ApiKey.objects.create(
        user=user, name=name, prefix=prefix, key_hash=key_hash, salt=salt,
    )


class SetDefaultViewTests(TestCase):

    def setUp(self):
        from billa.models import CreditPack
        CreditPack.objects.filter(is_free_tier=True).delete()
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')
        self.client.force_login(self.user)
        key1 = _make_key(self.user, 'Key1')
        key2 = _make_key(self.user, 'Key2')
        self.bal1 = CreditBalance.objects.create(api_key=key1, is_default=True)
        self.bal2 = CreditBalance.objects.create(api_key=key2, is_default=False)

    def test_sets_is_default_true(self):
        self.client.post(f'/billing/default/{self.bal2.pk}/')
        self.bal2.refresh_from_db()
        self.assertTrue(self.bal2.is_default)

    def test_clears_previous_default(self):
        self.client.post(f'/billing/default/{self.bal2.pk}/')
        self.bal1.refresh_from_db()
        self.assertFalse(self.bal1.is_default)

    def test_redirects_to_dashboard(self):
        response = self.client.post(f'/billing/default/{self.bal2.pk}/')
        self.assertRedirects(response, '/reggi/keys/', fetch_redirect_response=False)

    def test_other_user_balance_returns_404(self):
        other_user = User.objects.create_user(username='u2', password='p', email='u2@x.com')
        other_key = _make_key(other_user, 'OtherKey')
        other_bal = CreditBalance.objects.create(api_key=other_key)
        response = self.client.post(f'/billing/default/{other_bal.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_redirects(self):
        self.client.logout()
        response = self.client.post(f'/billing/default/{self.bal2.pk}/')
        self.assertEqual(response.status_code, 302)
