# billa

Credit-based billing for Django APIs.

`billa` provides a pluggable payment backend (Stripe, PayPal, or a local stub for development), a credit pack catalogue, per-key balance tracking, and a `BillerThrottle` that enforces credit limits on API requests.

Part of the [lxcor/api-suite](https://github.com/lxcor/api-suite).

## Install

```bash
pip install lxcor-billa           # core + stub backend
pip install lxcor-billa[stripe]   # include Stripe
pip install lxcor-billa[paypal]   # include PayPal
```

## Setup

```python
# settings.py
INSTALLED_APPS = [
    ...
    'reggi',  # required
    'kotta',  # required
    'billa',
]

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'kotta.throttle.AnonEndpointThrottle',
        'kotta.throttle.TierThrottle',
        'billa.throttle.BillerThrottle',
    ],
}
```

```python
# urls.py
urlpatterns = [
    path('', include('billa.urls')),
]
```

## Settings

| Setting | Default | Description |
|---|---|---|
| `BILLA_PAYMENT_BACKEND` | `'billa.backends.stub.StubPaymentBackend'` | Active payment backend |
| `BILLA_MERCHANT_NAME` | `''` | Merchant name shown on terms and pricing pages |
| `BILLA_CONTACT_EMAIL` | `''` | Contact email shown on terms page |
| `BILLA_CURRENCY` | `'USD'` | Currency code for all transactions |
| `BILLA_SUCCESS_URL` | `''` | Redirect URL after successful checkout |
| `BILLA_CANCEL_URL` | `''` | Redirect URL after cancelled checkout |
| `BILLA_UPGRADE_URL` | `''` | URL appended to 402 responses when credits are exhausted |
| `BILLA_STRIPE_MODE` | `'test'` | `'test'` or `'live'` |
| `BILLA_PAYPAL_MODE` | `'sandbox'` | `'sandbox'` or `'live'` |

## Navbar and footer fragments

```django
{% include "billa/_navbar_links.html" %}   {# Pricing link #}
{% include "billa/_footer_links.html" %}   {# Terms link #}
```

## License

MIT
