"""Sitemaps for the calendula project."""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from docca.models import DocEndpoint


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'

    _pages = [
        ('romma.index',     1.0),
        ('romma.endpoints', 0.8),
        ('docca.portal',   0.8),
        ('billa.pricing', 0.7),
        ('billa.terms',   0.3),
    ]

    def items(self):
        return self._pages

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]


class DocEndpointSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return DocEndpoint.objects.filter(published=True, is_orphan=False)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('docca.endpoint_detail', args=[obj.slug])
