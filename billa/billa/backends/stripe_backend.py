import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from billa.services import fulfill_purchase

User = get_user_model()


def _stripe_setting(name):
    """Return the mode-specific Stripe setting (TEST or LIVE)."""
    mode = getattr(settings, 'BILLER_STRIPE_MODE', 'test').upper()
    return getattr(settings, f'BILLER_STRIPE_{mode}_{name}', '')


class StripePaymentBackend:
    def create_checkout(self, request, credit_pack=None):
        stripe.api_key = _stripe_setting('SECRET_KEY')
        currency = getattr(settings, 'BILLER_CURRENCY', 'USD')
        success_url = request.build_absolute_uri(reverse('billa.key_reveal'))
        cancel_url = getattr(
            settings, 'BILLER_CANCEL_URL',
            request.build_absolute_uri('/pricing/'),
        )
        metadata = {'pack_pk': str(credit_pack.pk)} if credit_pack else {}

        price_data = {
            'currency': currency,
            'product_data': {'name': credit_pack.name if credit_pack else 'Credits'},
            'unit_amount': int(credit_pack.price * 100) if credit_pack else 0,
        }

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price_data': price_data, 'quantity': 1}],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(request.user.pk),
            metadata=metadata,
        )

        return redirect(session.url)

    def handle_webhook(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        webhook_secret = _stripe_setting('WEBHOOK_SECRET')

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return HttpResponse(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_pk = session.get('client_reference_id')
            try:
                user = User.objects.get(pk=user_pk)
            except (User.DoesNotExist, ValueError, TypeError):
                return HttpResponse(status=200)

            pack_pk = session.get('metadata', {}).get('pack_pk')
            credit_pack = None
            if pack_pk:
                from billa.models import CreditPack
                credit_pack = CreditPack.objects.filter(pk=pack_pk, is_active=True).first()

            raw_key = fulfill_purchase(user, 'stripe', session['id'], credit_pack=credit_pack)
            if raw_key:
                cache.set(f'billa_new_key_{user.pk}', raw_key, 300)

        return HttpResponse(status=200)
