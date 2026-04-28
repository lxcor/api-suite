"""Tests for romma home view."""

from django.test import TestCase, override_settings

from docca.models import DocEndpoint, DocTag
from docca.models.doc_endpoint import make_endpoint_slug


def _make_ep(path, method='GET', app_label='testapp', tag=None, published=True):
    slug = make_endpoint_slug(path, method)
    return DocEndpoint.objects.create(
        path=path, method=method, app_label=app_label,
        slug=slug, published=published, tag=tag,
    )


class HomeViewTests(TestCase):

    def test_renders_200_with_empty_manifest(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_total_endpoints_in_context(self):
        tag = DocTag.objects.create(name='Planets')
        _make_ep('/api/planets/', tag=tag, app_label='astra')
        _make_ep('/api/planets/<int:pk>/', tag=tag, app_label='astra')
        response = self.client.get('/')
        self.assertEqual(response.context['total_endpoints'], 2)

    def test_apps_list_in_context(self):
        tag = DocTag.objects.create(name='Stars')
        _make_ep('/api/stars/', tag=tag, app_label='astra')
        response = self.client.get('/')
        app_labels = [a['app_label'] for a in response.context['apps']]
        self.assertIn('astra', app_labels)

    def test_romma_sorted_last_among_apps(self):
        tag = DocTag.objects.create(name='Mixed')
        _make_ep('/api/astra/', tag=tag, app_label='astra')
        _make_ep('/api/romma/', tag=tag, app_label='romma')
        response = self.client.get('/')
        app_labels = [a['app_label'] for a in response.context['apps']]
        self.assertEqual(app_labels[-1], 'romma')

    @override_settings(DOCCA_APP_DESCRIPTIONS={'astra': 'Astronomical data'})
    def test_app_description_from_setting(self):
        tag = DocTag.objects.create(name='Astro')
        _make_ep('/api/astro/', tag=tag, app_label='astra')
        response = self.client.get('/')
        apps = {a['app_label']: a for a in response.context['apps']}
        self.assertEqual(apps['astra']['description'], 'Astronomical data')

    def test_unpublished_endpoints_excluded_from_count(self):
        tag = DocTag.objects.create(name='Hidden')
        _make_ep('/api/public/', tag=tag, app_label='astra', published=True)
        _make_ep('/api/hidden/', tag=tag, app_label='astra', published=False)
        response = self.client.get('/')
        self.assertEqual(response.context['total_endpoints'], 1)
