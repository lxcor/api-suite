from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class SuiteSitemap(Sitemap):
    """The public pages of the sandbox (the login-gated ones are left out on purpose)."""
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return ['home', 'romma.index', 'romma.endpoints', 'docca.portal', 'billa.pricing', 'billa.terms',
                'reggi.register', 'reggi.login']

    def location(self, item):
        return reverse(item)
