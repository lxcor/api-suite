"""Signal handlers for biller — attaches a free CreditBalance on ApiKey creation."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from reggi.models import ApiKey


@receiver(post_save, sender=ApiKey)
def attach_free_credits(sender, instance, created, **kwargs):
    """Attach a free CreditBalance when a new ApiKey is created.

    Skipped when:
    - The key was not just created (update path)
    - No active free-tier CreditPack exists
    - The key is flagged _from_purchase=True (set by the webhook before
      saving so the signal doesn't double-create a balance for paid keys)
    """
    if not created:
        return
    if getattr(instance, '_from_purchase', False):
        return

    from billa.models import CreditBalance, CreditPack
    free_pack = CreditPack.objects.filter(is_free_tier=True).first()
    if not free_pack or free_pack.credits <= 0:
        return

    has_default = CreditBalance.objects.filter(
        api_key__user=instance.user,
        is_default=True,
    ).exists()
    CreditBalance.objects.create(
        api_key=instance,
        credits_remaining=free_pack.credits,
        is_default=not has_default,
    )
