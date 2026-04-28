"""CreditPack — a purchasable credit bundle with optional tier upgrade."""

from django.db import models


class CreditPack(models.Model):
    """Defines a purchasable credit bundle.

    Replaces the BILLER_PACK_CREDITS setting for admin-editable pricing.
    A single price field is used by all payment providers — Stripe receives it
    via price_data (inline), PayPal directly in the order amount. tier is
    optional — when set, fulfill_purchase creates a UserTier assignment for
    the buyer so they bypass free-tier rate limits.
    """

    name = models.CharField(max_length=100)
    credits = models.PositiveIntegerField(help_text='Number of API request credits granted.')
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text='Price charged to the buyer (e.g. 4.99). Used by all payment providers.',
    )
    tier = models.ForeignKey(
        'kotta.Tier',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='credit_packs',
        help_text='Tier assigned to the buyer on purchase. Leave blank for no tier upgrade.',
    )
    is_active = models.BooleanField(default=True)
    is_free_tier = models.BooleanField(
        default=False,
        help_text='Mark this pack as the free-tier grant issued on account creation. '
                  'Set is_active=False to hide it from the pricing page.',
    )

    class Meta:
        ordering = ('credits',)

    def __str__(self):
        return f'{self.name} ({self.credits:,} credits)'
