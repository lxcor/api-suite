"""Tests for MergeView — credit transfer between tokens."""

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


class MergeViewTests(TestCase):

    def setUp(self):
        from billa.models import CreditPack
        CreditPack.objects.filter(is_free_tier=True).delete()
        self.user = User.objects.create_user(username='u', password='p', email='u@x.com')
        self.client.force_login(self.user)
        key1 = _make_key(self.user, 'Key1')
        key2 = _make_key(self.user, 'Key2')
        self.source = CreditBalance.objects.create(api_key=key1, credits_remaining=30)
        self.target = CreditBalance.objects.create(
            api_key=key2, credits_remaining=70, is_default=True,
        )

    def test_post_transfers_credits_to_default_target(self):
        self.client.post(f'/billing/merge/{self.source.pk}/')
        self.target.refresh_from_db()
        self.assertEqual(self.target.credits_remaining, 100)

    def test_post_with_explicit_target_pk(self):
        key3 = _make_key(self.user, 'Key3')
        other = CreditBalance.objects.create(api_key=key3, credits_remaining=0)
        self.client.post(
            f'/billing/merge/{self.source.pk}/',
            {'target_pk': other.pk},
        )
        other.refresh_from_db()
        self.assertEqual(other.credits_remaining, 30)

    def test_source_key_revoked_after_merge(self):
        self.client.post(f'/billing/merge/{self.source.pk}/')
        self.source.api_key.refresh_from_db()
        self.assertFalse(self.source.api_key.is_active)

    def test_merge_into_self_returns_400(self):
        response = self.client.post(
            f'/billing/merge/{self.target.pk}/',
            {'target_pk': self.target.pk},
        )
        self.assertEqual(response.status_code, 400)

    def test_no_default_target_returns_400(self):
        self.target.is_default = False
        self.target.save(update_fields=['is_default'])
        response = self.client.post(f'/billing/merge/{self.source.pk}/')
        self.assertEqual(response.status_code, 400)

    def test_other_user_source_returns_404(self):
        other_user = User.objects.create_user(username='u2', password='p', email='u2@x.com')
        other_key = _make_key(other_user, 'OtherKey')
        other_balance = CreditBalance.objects.create(api_key=other_key, credits_remaining=50)
        response = self.client.post(f'/billing/merge/{other_balance.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_redirects(self):
        self.client.logout()
        response = self.client.post(f'/billing/merge/{self.source.pk}/')
        self.assertEqual(response.status_code, 302)

    def test_redirects_to_dashboard_after_merge(self):
        response = self.client.post(f'/billing/merge/{self.source.pk}/')
        self.assertRedirects(response, '/reggi/keys/', fetch_redirect_response=False)
