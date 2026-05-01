"""PayPalReturnView — captures the PayPal order when the buyer returns from PayPal."""

import requests
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from billa.backends.paypal_backend import PayPalPaymentBackend, _auth_headers, _base_url
from billa.models import CreditPack
from billa.services import fulfill_purchase
from reggi.decorators import reggi_login_required


@method_decorator(reggi_login_required, name='dispatch')
class PayPalReturnView(View):
    """GET /billing/return/paypal/

    PayPal redirects here after the buyer approves the payment. The view
    captures the order, fulfills the purchase immediately, then redirects
    to BILLER_SUCCESS_URL. The webhook is a fallback (fulfill_purchase is
    idempotent so double-fire is harmless).
    """

    def get(self, request):
        cancel_url = getattr(settings, 'BILLER_CANCEL_URL', '/pricing/')
        success_url = getattr(settings, 'BILLER_SUCCESS_URL', '/reggi/keys/')

        order_id = request.GET.get('token')
        if not order_id:
            return redirect(cancel_url)

        try:
            resp = requests.post(
                f'{_base_url()}/v2/checkout/orders/{order_id}/capture',
                json={},
                headers=_auth_headers(),
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException:
            # Capture failed — webhook will retry; redirect user to success anyway
            return redirect(success_url)

        data = resp.json()

        try:
            purchase_unit = data['purchase_units'][0]
            capture_id = purchase_unit['payments']['captures'][0]['id']
            custom_id = purchase_unit.get('custom_id', '')
        except (KeyError, IndexError):
            return redirect(success_url)

        raw_key = PayPalPaymentBackend._fulfill_from_custom_id(custom_id, capture_id)
        if raw_key:
            request.session['billa_new_raw_key'] = raw_key
            return redirect(reverse('billa.key_reveal'))

        return redirect(success_url)
