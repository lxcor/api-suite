"""Tests for romma.context_processors.home_settings."""

from django.test import RequestFactory, TestCase, override_settings

from romma.context_processors import home_settings


class HomeSettingsProcessorTests(TestCase):

    def setUp(self):
        self.request = RequestFactory().get('/')

    def test_all_keys_present_with_defaults(self):
        ctx = home_settings(self.request)
        self.assertIn('site_name', ctx)
        self.assertIn('site_tagline', ctx)
        self.assertIn('site_description', ctx)
        self.assertIn('site_free_tier_requests', ctx)
        self.assertIn('docs_url', ctx)

    @override_settings(SITE_NAME='My API')
    def test_site_name_from_setting(self):
        ctx = home_settings(self.request)
        self.assertEqual(ctx['site_name'], 'My API')

    @override_settings(SITE_TAGLINE='Fast and reliable')
    def test_site_tagline_from_setting(self):
        ctx = home_settings(self.request)
        self.assertEqual(ctx['site_tagline'], 'Fast and reliable')

    @override_settings(DOCS_URL='/docs/')
    def test_docs_url_from_setting(self):
        ctx = home_settings(self.request)
        self.assertEqual(ctx['docs_url'], '/docs/')

    @override_settings(SITE_FREE_TIER_REQUESTS='1,000')
    def test_site_free_tier_requests_from_setting(self):
        ctx = home_settings(self.request)
        self.assertEqual(ctx['site_free_tier_requests'], '1,000')

    def test_docs_url_default_is_none(self):
        ctx = home_settings(self.request)
        self.assertIsNone(ctx['docs_url'])
