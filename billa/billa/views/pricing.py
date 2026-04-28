"""Public pricing page — shows available credit packs and buy buttons."""

from django.shortcuts import render
from django.views import View

from billa.models import CreditPack


class PricingView(View):
    def get(self, request):
        packs = CreditPack.objects.filter(is_active=True).select_related('tier')
        free_pack = CreditPack.objects.filter(is_free_tier=True).first()
        context = {
            'packs': packs,
            'free_credits': free_pack.credits if free_pack else 0,
        }
        return render(request, 'billa/pricing.html', context)
