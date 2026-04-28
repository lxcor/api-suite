from django.conf import settings
from django.utils.module_loading import import_string

_DEFAULT = 'billa.backends.stub.StubPaymentBackend'

_PROVIDER_MAP = {
    'stripe': 'billa.backends.stripe_backend.StripePaymentBackend',
    'paypal': 'billa.backends.paypal_backend.PayPalPaymentBackend',
    'stub': 'billa.backends.stub.StubPaymentBackend',
}


def get_backend(provider=None):
    """Return an instantiated payment backend.

    When provider is given ('stripe', 'paypal', 'stub') the matching backend
    is returned directly. When omitted, falls back to BILLER_PAYMENT_BACKEND.
    """
    if provider:
        path = _PROVIDER_MAP.get(provider, _DEFAULT)
    else:
        path = getattr(settings, 'BILLER_PAYMENT_BACKEND', _DEFAULT)
    return import_string(path)()
