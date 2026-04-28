"""Purchase — provider-agnostic audit record for a completed credit-pack payment."""

from django.conf import settings
from django.db import models

PROVIDER_CHOICES = [
    ('stripe', 'Stripe'),
    ('paypal', 'PayPal'),
    ('stub', 'Stub (development)'),
]


class Purchase(models.Model):
    """Records a completed payment from any supported provider.

    (provider, provider_session_id) is the unique deduplication key used
    to prevent double-granting of credits when webhook events are replayed.
    credit_balance always points to the originally issued balance regardless
    of subsequent merges, preserving a complete audit trail.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='biller_purchases',
    )
    credit_balance = models.OneToOneField(
        'billa.CreditBalance',
        on_delete=models.PROTECT,
        related_name='purchase',
    )
    provider = models.CharField(max_length=16, choices=PROVIDER_CHOICES)
    provider_session_id = models.CharField(max_length=255)
    credits_granted = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        unique_together = ('provider', 'provider_session_id')

    def __str__(self):
        return f'{self.user} — {self.credits_granted} credits via {self.provider} ({self.provider_session_id[:20]}…)'
