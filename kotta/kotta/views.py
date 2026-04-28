"""Views for the kotta usage dashboard."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from kotta.models import Endpoint, Tier, TierEndpointLimit, UserTier, UsageCounter
from kotta.throttle import _get_active_tier


def _get_user_tier(user):
    """Return the active Tier for the user, falling back to the default tier."""
    today = timezone.now().date()
    record = (
        UserTier.objects
        .filter(user=user, valid_from__lte=today)
        .filter(valid_until__isnull=True)
        .select_related('tier')
        .first()
    ) or (
        UserTier.objects
        .filter(user=user, valid_from__lte=today, valid_until__gte=today)
        .select_related('tier')
        .first()
    )
    if record:
        return record.tier
    return Tier.objects.filter(is_default=True, is_active=True).first()


@login_required
def usage(request):
    """Display the current user's API usage against their tier limits."""
    from reggi.models import ApiKey

    # Collect all active keys for this user
    user_keys = list(
        ApiKey.objects
        .filter(user=request.user, is_active=True, revoked_at__isnull=True)
        .select_related('tier')
        .order_by('-created_at')
    )

    # Determine selected key (query param ?key=<pk>, default first)
    selected_key = None
    key_pk = request.GET.get('key')
    if key_pk:
        selected_key = next((k for k in user_keys if str(k.pk) == key_pk), None)
    if selected_key is None and user_keys:
        selected_key = user_keys[0]

    # Tier for the selected key
    if selected_key is not None:
        tier = selected_key.tier or _get_active_tier(selected_key.user)
    else:
        tier = _get_user_tier(request.user)

    today = timezone.now().date()
    month_start = today.replace(day=1)

    day_counters = {}
    month_counters = {}
    if selected_key is not None:
        day_counters = {
            uc.endpoint_id: uc.count
            for uc in UsageCounter.objects.filter(
                api_key=selected_key,
                window_start=today,
            )
        }
        month_counters = {
            uc.endpoint_id: uc.count
            for uc in UsageCounter.objects.filter(
                api_key=selected_key,
                window_start=month_start,
            )
        }

    limits = {}
    if tier:
        for tel in TierEndpointLimit.objects.filter(tier=tier).select_related('endpoint'):
            limits[tel.endpoint_id] = tel

    endpoints = Endpoint.objects.filter(is_active=True, is_orphan=False).order_by('path', 'method')

    rows = []
    for ep in endpoints:
        tel = limits.get(ep.id)
        day_count = day_counters.get(ep.id, 0)
        month_count = month_counters.get(ep.id, 0)
        rows.append({
            'endpoint': ep,
            'limit': tel,
            'day_count': day_count,
            'month_count': month_count,
        })

    return render(request, 'kotta/usage.html', {
        'tier': tier,
        'rows': rows,
        'today': today,
        'user_keys': user_keys,
        'selected_key': selected_key,
    })
