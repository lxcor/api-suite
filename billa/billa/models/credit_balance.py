"""CreditBalance — attaches a request credit counter to a reggi ApiKey."""

from django.db import models, transaction
from django.utils import timezone


class CreditBalance(models.Model):
    """Credit counter bound to one reggi ApiKey.

    One CreditBalance per ApiKey (OneToOne). Credits are decremented
    atomically per authenticated request by BillerThrottle. When
    credits_remaining reaches zero the next request returns 402.

    Exactly one CreditBalance per user is flagged is_default=True — the
    designated merge target. Enforced in save() via an UPDATE on siblings.
    """

    api_key = models.OneToOneField(
        'reggi.ApiKey',
        on_delete=models.CASCADE,
        related_name='credit_balance',
    )
    credits_remaining = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(
        default=False,
        help_text='Designated merge target. Only one per user.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.api_key.user} — {self.api_key.name} ({self.credits_remaining} credits)'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            CreditBalance.objects.filter(
                api_key__user=self.api_key.user,
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)

    def merge_into(self, target):
        """Transfer all credits to target atomically and revoke this key.

        Parameters
        ----------
        target : CreditBalance
            The destination balance. Must belong to the same user.
        """
        with transaction.atomic():
            source = CreditBalance.objects.select_for_update().get(pk=self.pk)
            tgt = CreditBalance.objects.select_for_update().get(pk=target.pk)
            tgt.credits_remaining += source.credits_remaining
            source.credits_remaining = 0
            tgt.save(update_fields=['credits_remaining', 'updated_at'])
            source.save(update_fields=['credits_remaining', 'updated_at'])
            source.api_key.revoked_at = timezone.now()
            source.api_key.is_active = False
            source.api_key.save(update_fields=['revoked_at', 'is_active'])
