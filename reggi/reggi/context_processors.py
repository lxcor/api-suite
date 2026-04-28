"""Template context processors for reggi."""

from django.conf import settings


def reggi_settings(request):
    """Inject reggi settings into every template context.

    Makes ``site_name`` available in all reggi templates without
    requiring each view to pass it explicitly.
    """
    return {
        'site_name': getattr(settings, 'REGGI_SITE_NAME', 'API'),
        'docs_url': getattr(settings, 'REGGI_DOCS_URL', None),
        'usage_url': getattr(settings, 'REGGI_USAGE_URL', None),
    }
