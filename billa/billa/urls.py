"""URL configuration for biller."""

from django.urls import path

from billa.views.checkout import CheckoutView
from billa.views.key_reveal import PurchaseKeyRevealView
from billa.views.token_usage import TokenUsageView
from billa.views.merge import MergeView
from billa.views.paypal_return import PayPalReturnView
from billa.views.pricing import PricingView
from billa.views.set_default import SetDefaultView
from billa.views.stub_confirm import StubConfirmView
from billa.views.terms import TermsView
from billa.views.webhook import WebhookView

urlpatterns = [
    path('usage/tokens/', TokenUsageView.as_view(), name='billa.token_usage'),
    path('pricing/', PricingView.as_view(), name='billa.pricing'),
    path('terms/', TermsView.as_view(), name='billa.terms'),
    path('billing/checkout/', CheckoutView.as_view(), name='billa.checkout'),
    path('billing/key/', PurchaseKeyRevealView.as_view(), name='billa.key_reveal'),
    path('billing/stub/confirm/', StubConfirmView.as_view(), name='billa.stub_confirm'),
    path('billing/return/paypal/', PayPalReturnView.as_view(), name='billa.paypal_return'),
    path('billing/merge/<int:source_pk>/', MergeView.as_view(), name='billa.merge'),
    path('billing/default/<int:pk>/', SetDefaultView.as_view(), name='billa.set_default'),
    # Provider-specific webhook endpoints
    path('billing/webhook/stripe/', WebhookView.as_view(), {'provider': 'stripe'}, name='billa.webhook.stripe'),
    path('billing/webhook/paypal/', WebhookView.as_view(), {'provider': 'paypal'}, name='billa.webhook.paypal'),
    # Generic fallback — routes to BILLER_PAYMENT_BACKEND
    path('billing/webhook/', WebhookView.as_view(), name='billa.webhook'),
]
