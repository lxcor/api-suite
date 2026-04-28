"""Custom DRF exception handler for kotta — humanises the throttle wait time."""

from django.conf import settings
from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler

ANON_BLOCKED_MESSAGE = getattr(
    settings,
    'KOTTA_ANONYMOUS_BLOCKED_MESSAGE',
    'This endpoint is not available for anonymous access. Sign up to get access.',
)


def _humanize_seconds(seconds):
    """Convert a raw seconds count into a human-readable string.

    Examples
    --------
    >>> _humanize_seconds(26997)
    '7 hours, 29 minutes'
    >>> _humanize_seconds(45)
    '45 seconds'
    """
    seconds = int(seconds)
    parts = []

    if seconds >= 3600:
        hours = seconds // 3600
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        seconds %= 3600

    if seconds >= 60:
        minutes = seconds // 60
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

    if not parts:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return ', '.join(parts)


def kotta_exception_handler(exc, context):
    """DRF exception handler that replaces the raw throttle wait with a human-readable message."""
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled) and response is not None:
        request = context.get('request')
        retry_after = exc.wait
        humanized = _humanize_seconds(retry_after) if retry_after else 'some time'

        user = request.user if request else None
        if user and user.is_authenticated:
            user_label = user.username
        else:
            user_label = 'anonymous'

        ip_address = getattr(request, 'kotta_ip', None) or (
            request.META.get('REMOTE_ADDR') if request else None
        )

        endpoint = f'{request.method} {request.path}' if request else None

        throttle_info = getattr(request, 'kotta_throttle_info', {})
        limit = throttle_info.get('limit')
        period = throttle_info.get('period')
        anon_blocked = 'limit' in throttle_info and limit is None

        if anon_blocked:
            detail = ANON_BLOCKED_MESSAGE
        else:
            detail = f'Request limit reached. Available in {humanized}.'

        data = {
            'detail': detail,
            'retry_after': None if anon_blocked else (int(retry_after) if retry_after else None),
            'user': user_label,
            'ip_address': ip_address,
            'endpoint': endpoint,
            'limit': limit,
            'period': period,
        }

        upgrade_message = getattr(settings, 'KOTTA_UPGRADE_MESSAGE', None)
        if upgrade_message:
            data['upgrade'] = upgrade_message

        response.data = data

    return response
