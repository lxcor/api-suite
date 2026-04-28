"""Tests for docca portal views — ordering, tag grouping, and untagged collection."""

from django.test import TestCase, override_settings

from docca.models import DocEndpoint, DocTag


def _make_endpoint(path, method='GET', slug=None, tag=None, published=True, is_orphan=False):
    slug = slug or (path.strip('/').replace('/', '-') + '-' + method.lower())
    return DocEndpoint.objects.create(
        path=path,
        method=method,
        app_label='test',
        slug=slug,
        tag=tag,
        published=published,
        is_orphan=is_orphan,
    )


@override_settings(ROOT_URLCONF='tests.urls_test')
class PortalViewOrderingTests(TestCase):
    """PortalView renders tag groups in tag.order, untagged endpoints last."""

    def test_tag_groups_ordered_by_tag_order_field(self):
        tag_z = DocTag.objects.create(name='Zzz', order=2)
        tag_a = DocTag.objects.create(name='Aaa', order=1)
        _make_endpoint('v1/z/', tag=tag_z)
        _make_endpoint('v1/a/', tag=tag_a)

        response = self.client.get('/docs/')
        tag_groups = response.context['tag_groups']
        self.assertEqual(tag_groups[0]['tag'], tag_a)  # order=1 first
        self.assertEqual(tag_groups[1]['tag'], tag_z)  # order=2 second

    def test_untagged_endpoints_excluded_from_tag_groups(self):
        _make_endpoint('v1/x/')
        response = self.client.get('/docs/')
        tag_groups = response.context['tag_groups']
        self.assertEqual(len(tag_groups), 0)

    def test_untagged_endpoints_present_in_untagged_context(self):
        _make_endpoint('v1/x/')
        response = self.client.get('/docs/')
        self.assertEqual(response.context['untagged'].count(), 1)

    def test_unpublished_endpoints_excluded_from_portal(self):
        _make_endpoint('v1/secret/', published=False)
        response = self.client.get('/docs/')
        slugs = list(response.context['untagged'].values_list('path', flat=True))
        self.assertNotIn('v1/secret/', slugs)

    def test_orphan_endpoints_excluded_from_portal(self):
        _make_endpoint('v1/gone/', is_orphan=True)
        response = self.client.get('/docs/')
        slugs = list(response.context['untagged'].values_list('path', flat=True))
        self.assertNotIn('v1/gone/', slugs)

    def test_tag_group_omitted_when_all_endpoints_unpublished(self):
        tag = DocTag.objects.create(name='Hidden', order=1)
        _make_endpoint('v1/h/', tag=tag, published=False)
        response = self.client.get('/docs/')
        self.assertEqual(len(response.context['tag_groups']), 0)

    def test_app_labels_list_excludes_unpublished(self):
        _make_endpoint('v1/pub/', slug='v1-pub-get')
        _make_endpoint('v1/priv/', slug='v1-priv-get', published=False)
        response = self.client.get('/docs/')
        app_labels = response.context['app_labels']
        self.assertIn('test', app_labels)


@override_settings(ROOT_URLCONF='tests.urls_test')
class EndpointDetailViewTests(TestCase):
    """EndpointDetailView resolves prev/next navigation correctly."""

    def setUp(self):
        tag = DocTag.objects.create(name='Nav', order=1)
        _make_endpoint('v1/a/', slug='v1-a-get', tag=tag)
        _make_endpoint('v1/b/', slug='v1-b-get', tag=tag)
        _make_endpoint('v1/c/', slug='v1-c-get', tag=tag)

    def test_middle_endpoint_has_prev_and_next(self):
        response = self.client.get('/docs/endpoint/v1-b-get/')
        self.assertIsNotNone(response.context['prev_ep'])
        self.assertIsNotNone(response.context['next_ep'])

    def test_first_endpoint_has_no_prev(self):
        response = self.client.get('/docs/endpoint/v1-a-get/')
        self.assertIsNone(response.context['prev_ep'])

    def test_last_endpoint_has_no_next(self):
        response = self.client.get('/docs/endpoint/v1-c-get/')
        self.assertIsNone(response.context['next_ep'])

    def test_unpublished_endpoint_returns_404(self):
        _make_endpoint('v1/hidden/', slug='v1-hidden-get', published=False)
        response = self.client.get('/docs/endpoint/v1-hidden-get/')
        self.assertEqual(response.status_code, 404)
