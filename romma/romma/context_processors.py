"""Template context processor for the home app."""

from django.conf import settings


def home_settings(request):
    """Inject site-level display settings into every template context.

    All keys have safe defaults so the app works without any configuration.
    Override in settings.py:

        SITE_NAME = 'My API'
        SITE_TAGLINE = 'Short hero headline'
        SITE_DESCRIPTION = 'Longer hero subtitle shown below the headline.'
        SITE_FREE_TIER_REQUESTS = '1,000'
        DOCS_URL = '/docs/'
    """
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'API'),
        'site_tagline': getattr(settings, 'SITE_TAGLINE', 'API'),
        'site_description': getattr(settings, 'SITE_DESCRIPTION', ''),
        'site_free_tier_requests': getattr(settings, 'SITE_FREE_TIER_REQUESTS', ''),
        'docs_url': getattr(settings, 'DOCS_URL', None),
    }
