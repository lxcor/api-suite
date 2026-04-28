"""Tests for romma endpoints catalog view."""

from django.test import TestCase

from docca.models import DocEndpoint, DocTag
from docca.models.doc_endpoint import make_endpoint_slug


def _make_ep(path, method='GET', app_label='testapp', tag=None):
    slug = make_endpoint_slug(path, method)
    return DocEndpoint.objects.create(
        path=path, method=method, app_label=app_label,
        slug=slug, published=True, tag=tag,
    )


class EndpointsViewTests(TestCase):

    def test_renders_200(self):
        response = self.client.get('/endpoints/')
        self.assertEqual(response.status_code, 200)

    def test_manifest_in_context(self):
        response = self.client.get('/endpoints/')
        self.assertIn('manifest', response.context)
        self.assertIn('groups', response.context['manifest'])

    def test_app_labels_in_context(self):
        tag = DocTag.objects.create(name='Geo')
        _make_ep('/api/geo/cities/', tag=tag, app_label='locci')
        response = self.client.get('/endpoints/')
        self.assertIn('locci', response.context['app_labels'])

    def test_romma_sorted_last_in_app_labels(self):
        tag = DocTag.objects.create(name='Mix')
        _make_ep('/api/astra/sun/', tag=tag, app_label='astra')
        _make_ep('/api/romma/home/', tag=tag, app_label='romma')
        response = self.client.get('/endpoints/')
        labels = response.context['app_labels']
        self.assertEqual(labels[-1], 'romma')

    def test_enriched_endpoints_have_path_segments(self):
        tag = DocTag.objects.create(name='Planets')
        _make_ep('/api/planets/', tag=tag, app_label='astra')
        response = self.client.get('/endpoints/')
        group = response.context['manifest']['groups'][0]
        ep = group['endpoints'][0]
        self.assertIn('path_segments', ep)
        self.assertIn('card_title', ep)
        self.assertIn('app_badge_class', ep)

    def test_untagged_endpoints_enriched(self):
        _make_ep('/api/misc/', app_label='astra', tag=None)
        response = self.client.get('/endpoints/')
        untagged = response.context['manifest']['untagged']
        self.assertEqual(len(untagged), 1)
        self.assertIn('path_segments', untagged[0])
