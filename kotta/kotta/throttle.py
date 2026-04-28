"""DRF throttle classes for kotta — AnonEndpointThrottle and TierThrottle."""

import datetime
import re

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.throttling import BaseThrottle

from kotta.models import Endpoint, Tier, TierEndpointLimit, UserTier, UsageCounter

# --- kotta settings with defaults ---

KOTTA_DEFAULT_ANONYMOUS_LIMIT = getattr(settings, 'KOTTA_DEFAULT_ANONYMOUS_LIMIT', 50)
KOTTA_DEFAULT_PERIOD = getattr(settings, 'KOTTA_DEFAULT_PERIOD', 'month')
KOTTA_OPEN_BY_DEFAULT = getattr(settings, 'KOTTA_OPEN_BY_DEFAULT', True)
KOTTA_BLOCK_ANONYMOUS_BY_DEFAULT = getattr(settings, 'KOTTA_BLOCK_ANONYMOUS_BY_DEFAULT', False)


def _get_window_start(period):
    """Return the start date of the current throttle window for the given period.

    Parameters
    ----------
    period : str
        ``'day'`` or ``'month'``.

    Returns
    -------
    datetime.date
        The first date of the current window.
    """
    today = timezone.now().date()
    if period == 'month':
        return today.replace(day=1)
    return today


def _seconds_until_reset(period):
    """Return the number of seconds until the current throttle window resets.

    Parameters
    ----------
    period : str
        ``'day'`` or ``'month'``.

    Returns
    -------
    float
        Seconds remaining in the current window.
    """
    now = timezone.now()
    today = now.date()

    if period == 'month':
        if today.month == 12:
            reset_date = today.replace(year=today.year + 1, month=1, day=1)
        else:
            reset_date = today.replace(month=today.month + 1, day=1)
    else:
        reset_date = today + datetime.timedelta(days=1)

    reset_dt = timezone.make_aware(
        datetime.datetime.combine(reset_date, datetime.time.min)
    )
    return max(0.0, (reset_dt - now).total_seconds())


def _match_endpoint(request_path, method):
    """Return the active Endpoint matching the given path and method, or None.

    Attempts an exact match first.  If that fails, iterates active
    Endpoint records and tries regex matching to handle parameterised
    paths (e.g. ``locci/geo/continent/(?P<pk>[^/.]+)/``).

    Parameters
    ----------
    request_path : str
        The request path with the leading slash stripped.
    method : str
        Uppercase HTTP method string (e.g. ``'GET'``).

    Returns
    -------
    Endpoint or None
    """
    try:
        return Endpoint.objects.get(path=request_path, method=method, is_active=True)
    except Endpoint.DoesNotExist:
        pass

    for endpoint in Endpoint.objects.filter(method=method, is_active=True):
        try:
            if re.fullmatch(endpoint.path, request_path):
                return endpoint
        except re.error:
            pass

    return None


def _get_tier_for_key(api_key):
    """Return the rate-limit Tier for an API key.

    Uses the key's own tier when set; otherwise falls back to the
    user-level UserTier assignment, then the system default tier.

    Parameters
    ----------
    api_key : reggi.ApiKey instance
        The authenticated API key (``request.auth``).

    Returns
    -------
    Tier or None
    """
    if api_key is not None and getattr(api_key, 'tier_id', None):
        return api_key.tier
    user = getattr(api_key, 'user', None)
    if user is not None:
        return _get_active_tier(user)
    return None


def _get_active_tier(user):
    """Return the user's active Tier via UserTier, falling back to the default tier.

    Used as a fallback when a key carries no explicit tier.  The most
    recently created UserTier record whose validity window includes today
    is used.  If none exists the Tier marked ``is_default=True`` is
    returned.  Returns ``None`` if no default tier is configured.

    Parameters
    ----------
    user : AUTH_USER_MODEL instance
        The authenticated user.

    Returns
    -------
    Tier or None
    """
    today = timezone.now().date()

    assignment = (
        UserTier.objects
        .filter(
            user=user,
            valid_from__lte=today,
        )
        .filter(
            valid_until__isnull=True
        )
        .order_by('-created_at')
        .select_related('tier')
        .first()
    )

    if assignment is None:
        assignment = (
            UserTier.objects
            .filter(
                user=user,
                valid_from__lte=today,
                valid_until__gte=today,
            )
            .order_by('-created_at')
            .select_related('tier')
            .first()
        )

    if assignment:
        return assignment.tier

    return Tier.objects.filter(is_default=True, is_active=True).first()


def _check_and_increment(counter_kwargs, limit):
    """Check the usage counter against the limit and increment if allowed.

    Uses ``select_for_update()`` to prevent race conditions under
    concurrent requests.  Resets the counter lazily if the stored
    ``window_start`` is earlier than the current window.

    Parameters
    ----------
    counter_kwargs : dict
        Lookup kwargs identifying the UsageCounter record.
    limit : int
        Maximum allowed requests for the current window.

    Returns
    -------
    bool
        ``True`` if the request is within the limit and the counter
        was incremented.  ``False`` if the limit has been reached.
    """
    window_start = counter_kwargs['window_start']

    with transaction.atomic():
        counter, _ = UsageCounter.objects.select_for_update().get_or_create(
            **counter_kwargs,
            defaults={'count': 0},
        )

        if counter.window_start < window_start:
            counter.count = 0
            counter.window_start = window_start

        if counter.count >= limit:
            return False

        counter.count += 1
        counter.save(update_fields=['count', 'window_start', 'updated_at'])
        return True


class AnonEndpointThrottle(BaseThrottle):
    """Throttle anonymous requests by IP address using per-endpoint limits.

    Reads ``Endpoint.anonymous_limit`` and ``Endpoint.anonymous_period`` for
    the matched endpoint.  If ``anonymous_limit`` is null the request is
    blocked unless ``KOTTA_BLOCK_ANONYMOUS_BY_DEFAULT`` is False (the default),
    in which case ``KOTTA_DEFAULT_ANONYMOUS_LIMIT`` is used as the fallback.
    Authenticated requests are passed through immediately — they are handled
    by ``TierThrottle``.
    """

    def __init__(self):
        """Initialise the period store used by ``wait()``."""
        self._period = None

    def allow_request(self, request, view):
        """Return True if the anonymous request is within the endpoint limit."""
        if request.user and request.user.is_authenticated:
            return True

        request_path = request.path.lstrip('/')
        endpoint = _match_endpoint(request_path, request.method)

        if endpoint is None:
            return True

        period = endpoint.anonymous_period
        limit = endpoint.anonymous_limit

        if limit is None:
            if KOTTA_BLOCK_ANONYMOUS_BY_DEFAULT:
                self._period = period
                request.kotta_throttle_info = {'limit': None, 'period': period}
                return False
            limit = KOTTA_DEFAULT_ANONYMOUS_LIMIT

        self._period = period
        window_start = _get_window_start(period)

        allowed = _check_and_increment(
            {
                'ip_address': getattr(request, 'kotta_ip', request.META.get('REMOTE_ADDR', '')),
                'endpoint': endpoint,
                'window_start': window_start,
            },
            limit,
        )

        if not allowed:
            request.kotta_throttle_info = {
                'limit': limit,
                'period': period,
            }

        return allowed

    def wait(self):
        """Return seconds until the anonymous throttle window resets."""
        if self._period:
            return _seconds_until_reset(self._period)
        return None


class TierThrottle(BaseThrottle):
    """Throttle authenticated requests using per-endpoint limits defined on the user's tier.

    Resolves the user's active ``Tier`` via ``UserTier``, looks up the
    ``TierEndpointLimit`` for that tier and endpoint, and enforces the
    limit using a database-backed ``UsageCounter``.

    Requests are allowed by default when no ``TierEndpointLimit`` record
    exists for the user's tier and the matched endpoint, preventing
    accidental lockout after ``syncendpoints`` discovers new endpoints
    before limits are configured.
    """

    def __init__(self):
        """Initialise the period store used by ``wait()``."""
        self._period = None

    def allow_request(self, request, view):
        """Return True if the authenticated request is within the tier limit."""
        if not request.user or not request.user.is_authenticated:
            return True

        api_key = getattr(request, 'auth', None)
        request_path = request.path.lstrip('/')
        endpoint = _match_endpoint(request_path, request.method)

        if endpoint is None:
            return True

        tier = _get_tier_for_key(api_key)

        if tier is None:
            return True

        counter_kwargs = {
            'api_key': api_key,
            'endpoint': endpoint,
        }

        try:
            limit_obj = TierEndpointLimit.objects.get(tier=tier, endpoint=endpoint)
        except TierEndpointLimit.DoesNotExist:
            if not KOTTA_OPEN_BY_DEFAULT:
                return False
            # No limit configured — record usage without enforcing a cap
            _check_and_increment(
                {**counter_kwargs, 'window_start': _get_window_start('month')},
                2_147_483_647,
            )
            return True

        self._period = limit_obj.period
        window_start = _get_window_start(limit_obj.period)

        allowed = _check_and_increment(
            {**counter_kwargs, 'window_start': window_start},
            limit_obj.limit,
        )

        if not allowed:
            request.kotta_throttle_info = {
                'limit': limit_obj.limit,
                'period': limit_obj.period,
            }

        return allowed

    def wait(self):
        """Return seconds until the tier throttle window resets."""
        if self._period:
            return _seconds_until_reset(self._period)
        return None
