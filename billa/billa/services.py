"""Shared purchase fulfillment — called by all payment backends."""

from django.utils import timezone

from reggi.models import ApiKey
from reggi.models.api_key import generate_api_key


def fulfill_purchase(user, provider, provider_session_id, credit_pack):
    """Create ApiKey + CreditBalance + Purchase for a completed payment.

    Idempotent: silently returns if (provider, provider_session_id) already
    exists. credit_pack is required — its credits count and tier are used.
    """
    from billa.models import CreditBalance, Purchase

    if Purchase.objects.filter(provider=provider, provider_session_id=provider_session_id).exists():
        return

    is_first_purchase = not Purchase.objects.filter(user=user).exists()
    pack_credits = credit_pack.credits
    pack_name = credit_pack.name
    date_label = timezone.now().strftime('%Y-%m-%d')
    raw_key, lookup_prefix, key_hash, salt_hex = generate_api_key()

    api_key = ApiKey(
        user=user,
        name=f'{pack_name} — {date_label} ({lookup_prefix})',
        prefix=lookup_prefix,
        key_hash=key_hash,
        salt=salt_hex,
    )
    api_key._from_purchase = True
    api_key.save()

    balance = CreditBalance.objects.create(
        api_key=api_key,
        credits_remaining=pack_credits,
        is_default=is_first_purchase,
    )

    Purchase.objects.create(
        user=user,
        credit_balance=balance,
        provider=provider,
        provider_session_id=provider_session_id,
        credits_granted=pack_credits,
    )

    if credit_pack and credit_pack.tier:
        api_key.tier = credit_pack.tier
        api_key.save(update_fields=['tier'])
