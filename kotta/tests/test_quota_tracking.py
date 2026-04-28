"""Tests for _check_and_increment — the atomic usage counter logic."""

import datetime

from django.test import TestCase
from django.utils import timezone

from kotta.models import Endpoint, UsageCounter
from kotta.throttle import _check_and_increment


def _today():
    return timezone.now().date()


def _yesterday():
    return _today() - datetime.timedelta(days=1)


class CheckAndIncrementTests(TestCase):

    def setUp(self):
        self.endpoint = Endpoint.objects.create(path='api/data/', method='GET')
        self.kwargs = {
            'ip_address': '10.0.0.1',
            'endpoint': self.endpoint,
            'window_start': _today(),
        }

    def test_first_call_returns_true(self):
        self.assertTrue(_check_and_increment(self.kwargs, limit=5))

    def test_first_call_creates_counter_with_count_one(self):
        _check_and_increment(self.kwargs, limit=5)
        counter = UsageCounter.objects.get(**self.kwargs)
        self.assertEqual(counter.count, 1)

    def test_repeated_calls_increment_counter(self):
        for _ in range(3):
            _check_and_increment(self.kwargs, limit=10)
        counter = UsageCounter.objects.get(**self.kwargs)
        self.assertEqual(counter.count, 3)

    def test_returns_true_up_to_limit(self):
        results = [_check_and_increment(self.kwargs, limit=3) for _ in range(3)]
        self.assertTrue(all(results))

    def test_returns_false_when_limit_exceeded(self):
        for _ in range(3):
            _check_and_increment(self.kwargs, limit=3)
        self.assertFalse(_check_and_increment(self.kwargs, limit=3))

    def test_counter_not_incremented_past_limit(self):
        for _ in range(5):
            _check_and_increment(self.kwargs, limit=3)
        counter = UsageCounter.objects.get(**self.kwargs)
        self.assertEqual(counter.count, 3)

    def test_new_window_start_creates_fresh_counter(self):
        for _ in range(3):
            _check_and_increment(self.kwargs, limit=3)

        new_kwargs = {**self.kwargs, 'window_start': _yesterday()}
        # Yesterday's window is separate — starts fresh
        self.assertTrue(_check_and_increment(new_kwargs, limit=3))
        self.assertEqual(UsageCounter.objects.filter(endpoint=self.endpoint).count(), 2)

    def test_different_ips_have_independent_counters(self):
        kwargs_a = {**self.kwargs, 'ip_address': '1.1.1.1'}
        kwargs_b = {**self.kwargs, 'ip_address': '2.2.2.2'}
        for _ in range(3):
            _check_and_increment(kwargs_a, limit=3)
        # IP B is not exhausted
        self.assertTrue(_check_and_increment(kwargs_b, limit=3))
