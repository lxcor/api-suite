from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from billa.backends import get_backend


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    """Handles incoming payment provider webhooks.

    provider kwarg (from URL) selects the correct backend. The generic
    /billing/webhook/ path falls back to BILLER_PAYMENT_BACKEND.
    """

    def post(self, request, provider=None):
        return get_backend(provider).handle_webhook(request)
