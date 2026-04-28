"""Tests for romma view helper functions."""

from django.test import TestCase, override_settings

from romma.views import _app_badge_class, _card_title, _path_segments


class PathSegmentsTests(TestCase):

    def test_basic_path(self):
        segs = _path_segments('astra/sun/rise-set/')
        labels = [s['label'] for s in segs]
        self.assertEqual(labels, ['astra', 'sun', 'rise-set'])

    def test_params_excluded(self):
        segs = _path_segments('locci/geo/city/{city_id}/')
        labels = [s['label'] for s in segs]
        self.assertNotIn('{city_id}', labels)
        self.assertEqual(labels, ['locci', 'geo', 'city'])

    def test_empty_path(self):
        self.assertEqual(_path_segments('/'), [])


class CardTitleTests(TestCase):

    def test_hyphen_replaced_and_titled(self):
        self.assertEqual(_card_title('astra/sun/rise-set/'), 'Rise Set')

    def test_underscore_replaced(self):
        self.assertEqual(_card_title('some/app/my_view/'), 'My View')

    def test_param_only_path_returns_empty(self):
        self.assertEqual(_card_title('{pk}/'), '')

    def test_uses_last_non_param_segment(self):
        self.assertEqual(_card_title('locci/geo/city/{city_id}/'), 'City')


class AppBadgeClassTests(TestCase):

    @override_settings(DOCCA_APP_COLORS={'myapp': 'primary'})
    def test_color_map_used_when_present(self):
        cls = _app_badge_class('myapp')
        self.assertIn('bg-primary', cls)

    def test_hash_fallback_is_consistent(self):
        cls1 = _app_badge_class('astra')
        cls2 = _app_badge_class('astra')
        self.assertEqual(cls1, cls2)

    def test_dark_bg_gets_text_white(self):
        # Force a dark-bg color via DOCCA_APP_COLORS
        with override_settings(DOCCA_APP_COLORS={'x': 'danger'}):
            cls = _app_badge_class('x')
        self.assertIn('text-white', cls)

    def test_light_bg_gets_text_dark(self):
        with override_settings(DOCCA_APP_COLORS={'x': 'warning'}):
            cls = _app_badge_class('x')
        self.assertIn('text-dark', cls)
