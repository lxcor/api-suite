"""Template context processors for biller."""

from django.conf import settings


def billa_settings(request):
    """Inject biller settings into every template context.

    Makes ``pricing_url`` available in all templates without requiring
    each view to pass it explicitly — mirrors the reggi_settings pattern.
    Set BILLA_UPGRADE_URL = None in settings to hide the pricing nav link.
    """
    return {
        'pricing_url': getattr(settings, 'BILLA_UPGRADE_URL', None),
    }
