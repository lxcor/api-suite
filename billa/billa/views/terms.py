"""Payment terms page."""

from django.conf import settings
from django.shortcuts import render
from django.views import View


class TermsView(View):
    def get(self, request):
        context = {
            'merchant_name': getattr(settings, 'BILLER_MERCHANT_NAME', settings.REGGI_SITE_NAME),
            'contact_email': getattr(settings, 'BILLER_CONTACT_EMAIL', ''),
            'upgrade_url': getattr(settings, 'BILLER_UPGRADE_URL', '/pricing/'),
        }
        return render(request, 'billa/terms.html', context)
