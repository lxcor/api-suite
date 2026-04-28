"""TokenUsageView — credit balance per active API key for the current user."""

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from billa.models import CreditBalance, CreditPack
from reggi.decorators import reggi_login_required


@method_decorator(reggi_login_required, name='dispatch')
class TokenUsageView(View):
    def get(self, request):
        free_pack = CreditPack.objects.filter(is_free_tier=True).first()
        free_credits = free_pack.credits if free_pack else 0

        balances = (
            CreditBalance.objects
            .filter(
                api_key__user=request.user,
                api_key__is_active=True,
                api_key__revoked_at__isnull=True,
            )
            .select_related('api_key', 'purchase')
            .order_by('-is_default', '-created_at')
        )

        from kotta.throttle import _get_active_tier

        rows = []
        for balance in balances:
            try:
                granted = balance.purchase.credits_granted
                is_paid = True
            except ObjectDoesNotExist:
                granted = free_credits
                is_paid = False

            key = balance.api_key
            tier = key.tier if key.tier_id else _get_active_tier(request.user)

            rows.append({
                'balance': balance,
                'key': key,
                'granted': granted,
                'is_paid': is_paid,
                'tier': tier,
            })

        return render(request, 'billa/token_usage.html', {
            'rows': rows,
            'today': timezone.now().date(),
        })
