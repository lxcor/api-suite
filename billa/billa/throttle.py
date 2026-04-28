"""BillerThrottle — credit check and atomic decrement for credit-bearing API keys."""

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import APIException
from rest_framework.throttling import BaseThrottle


class PaymentRequired(APIException):
    """Raised when a credit-bearing key has exhausted its balance (HTTP 402)."""
    status_code = 402
    default_detail = 'Credit balance exhausted.'
    default_code = 'payment_required'


class BillerThrottle(BaseThrottle):
    """DRF throttle that enforces per-key credit limits.

    Runs after kotta throttles. For each authenticated request:
    - Skips deduction if kotta already blocked the request (kotta_throttle_info set)
    - Resolves the ApiKey from request.auth (set by reggi.ApiKeyAuthentication)
    - Looks up its CreditBalance
    - If no CreditBalance exists, passes through unchanged
    - If credits_remaining == 0, raises PaymentRequired (HTTP 402)
    - Otherwise decrements credits_remaining atomically and allows the request
    """

    def allow_request(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True

        # Don't deduct credits for requests kotta has already blocked
        if getattr(request, 'kotta_throttle_info', None):
            return True

        api_key = getattr(request, 'auth', None)
        if not hasattr(api_key, 'pk'):
            return True

        from billa.models import CreditBalance
        try:
            with transaction.atomic():
                balance = CreditBalance.objects.select_for_update().get(api_key=api_key)
                if balance.credits_remaining == 0:
                    detail = {'detail': 'Credit balance exhausted.'}
                    upgrade_url = getattr(settings, 'BILLER_UPGRADE_URL', None)
                    if upgrade_url:
                        detail['upgrade_url'] = upgrade_url
                    raise PaymentRequired(detail=detail)
                balance.credits_remaining -= 1
                balance.save(update_fields=['credits_remaining', 'updated_at'])
        except CreditBalance.DoesNotExist:
            return True

        return True

    def wait(self):
        return None
