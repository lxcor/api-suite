"""Unit tests for kotta throttle helper functions."""

import datetime

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from kotta.models import Endpoint
from kotta.throttle import _get_window_start, _match_endpoint, _seconds_until_reset


class GetWindowStartTests(SimpleTestCase):

    def test_day_returns_today(self):
        self.assertEqual(_get_window_start('day'), timezone.now().date())

    def test_month_returns_first_of_month(self):
        result = _get_window_start('month')
        today = timezone.now().date()
        self.assertEqual(result.day, 1)
        self.assertEqual(result.month, today.month)
        self.assertEqual(result.year, today.year)

    def test_day_and_month_differ_unless_first_of_month(self):
        today = timezone.now().date()
        if today.day != 1:
            self.assertNotEqual(_get_window_start('day'), _get_window_start('month'))


class SecondsUntilResetTests(SimpleTestCase):

    def test_day_reset_is_positive(self):
        self.assertGreater(_seconds_until_reset('day'), 0)

    def test_month_reset_is_positive(self):
        self.assertGreater(_seconds_until_reset('month'), 0)

    def test_day_reset_is_less_than_one_day(self):
        self.assertLessEqual(_seconds_until_reset('day'), 86400)

    def test_month_reset_is_less_than_32_days(self):
        self.assertLessEqual(_seconds_until_reset('month'), 32 * 86400)

    def test_month_reset_longer_than_day_reset(self):
        today = timezone.now().date()
        if today.day != 1:
            self.assertGreater(_seconds_until_reset('month'), _seconds_until_reset('day'))


class MatchEndpointTests(TestCase):

    def setUp(self):
        self.ep = Endpoint.objects.create(
            path='api/items/', method='GET', anonymous_limit=10,
        )

    def test_exact_path_match(self):
        result = _match_endpoint('api/items/', 'GET')
        self.assertEqual(result, self.ep)

    def test_wrong_method_returns_none(self):
        self.assertIsNone(_match_endpoint('api/items/', 'POST'))

    def test_unknown_path_returns_none(self):
        self.assertIsNone(_match_endpoint('api/unknown/', 'GET'))

    def test_inactive_endpoint_not_matched(self):
        self.ep.is_active = False
        self.ep.save()
        self.assertIsNone(_match_endpoint('api/items/', 'GET'))

    def test_regex_path_matches_parameterised_url(self):
        Endpoint.objects.create(
            path=r'api/items/(?P<pk>[^/.]+)/',
            method='GET',
        )
        result = _match_endpoint('api/items/42/', 'GET')
        self.assertIsNotNone(result)
        self.assertEqual(result.path, r'api/items/(?P<pk>[^/.]+)/')
