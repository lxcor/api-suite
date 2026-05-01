import json

import requests
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect

from billa.services import fulfill_purchase


def _paypal_setting(name):
    """Return the mode-specific PayPal setting (SANDBOX or LIVE)."""
    mode = getattr(settings, 'BILLER_PAYPAL_MODE', 'sandbox').upper()
    return getattr(settings, f'BILLER_PAYPAL_{mode}_{name}', '')


def _base_url():
    mode = getattr(settings, 'BILLER_PAYPAL_MODE', 'sandbox')
    return (
        'https://api-m.sandbox.paypal.com'
        if mode == 'sandbox'
        else 'https://api-m.paypal.com'
    )


def get_paypal_access_token():
    """Return a cached PayPal Bearer token, fetching a fresh one if expired."""
    cached = cache.get('biller_paypal_access_token')
    if cached:
        return cached

    resp = requests.post(
        f'{_base_url()}/v1/oauth2/token',
        auth=(_paypal_setting('CLIENT_ID'), _paypal_setting('SECRET')),
        data={'grant_type': 'client_credentials'},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data['access_token']
    expires_in = data.get('expires_in', 32400)
    cache.set('biller_paypal_access_token', token, timeout=expires_in - 60)
    return token


def _auth_headers():
    return {
        'Authorization': f'Bearer {get_paypal_access_token()}',
        'Content-Type': 'application/json',
    }


class PayPalPaymentBackend:
    def create_checkout(self, request, credit_pack=None):
        currency = getattr(settings, 'BILLER_CURRENCY', 'USD')
        cancel_url = getattr(
            settings, 'BILLER_CANCEL_URL',
            request.build_absolute_uri('/pricing/'),
        )
        return_url = request.build_absolute_uri('/billing/return/paypal/')

        price = str(credit_pack.price) if credit_pack else '0.00'
        custom_id = f'{request.user.pk}:{credit_pack.pk}' if credit_pack else str(request.user.pk)

        payload = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'custom_id': custom_id,
                'amount': {'currency_code': currency, 'value': price},
            }],
            'application_context': {
                'return_url': return_url,
                'cancel_url': cancel_url,
                'user_action': 'PAY_NOW',
            },
        }

        resp = requests.post(
            f'{_base_url()}/v2/checkout/orders',
            json=payload,
            headers=_auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        order = resp.json()

        approval_url = next(
            link['href'] for link in order['links'] if link['rel'] == 'approve'
        )
        return redirect(approval_url)

    def handle_webhook(self, request):
        try:
            event = json.loads(request.body)
        except (ValueError, TypeError):
            return HttpResponse(status=400)

        # Verify PayPal webhook signature
        verify_payload = {
            'auth_algo': request.META.get('HTTP_PAYPAL_AUTH_ALGO', ''),
            'cert_url': request.META.get('HTTP_PAYPAL_CERT_URL', ''),
            'transmission_id': request.META.get('HTTP_PAYPAL_TRANSMISSION_ID', ''),
            'transmission_sig': request.META.get('HTTP_PAYPAL_TRANSMISSION_SIG', ''),
            'transmission_time': request.META.get('HTTP_PAYPAL_TRANSMISSION_TIME', ''),
            'webhook_id': _paypal_setting('WEBHOOK_ID'),
            'webhook_event': event,
        }
        verify_resp = requests.post(
            f'{_base_url()}/v1/notifications/verify-webhook-signature',
            json=verify_payload,
            headers=_auth_headers(),
            timeout=10,
        )
        if (
            verify_resp.status_code != 200
            or verify_resp.json().get('verification_status') != 'SUCCESS'
        ):
            return HttpResponse(status=400)

        if event.get('event_type') == 'PAYMENT.CAPTURE.COMPLETED':
            resource = event.get('resource', {})
            capture_id = resource.get('id', '')
            custom_id = resource.get('custom_id', '')
            self._fulfill_from_custom_id(custom_id, capture_id)

        return HttpResponse(status=200)

    @staticmethod
    def _fulfill_from_custom_id(custom_id, capture_id):
        from django.contrib.auth import get_user_model
        from billa.models import CreditPack

        parts = custom_id.split(':')
        user_pk = parts[0]
        pack_pk = parts[1] if len(parts) > 1 else None

        User = get_user_model()
        try:
            user = User.objects.get(pk=user_pk)
        except (User.DoesNotExist, ValueError, TypeError):
            return

        credit_pack = None
        if pack_pk:
            credit_pack = CreditPack.objects.filter(pk=pack_pk, is_active=True).first()

        return fulfill_purchase(user, 'paypal', capture_id, credit_pack=credit_pack)
