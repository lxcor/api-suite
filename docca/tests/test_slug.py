"""Unit tests for make_endpoint_slug — no database required."""

from django.test import SimpleTestCase

from docca.models.doc_endpoint import make_endpoint_slug


class MakeEndpointSlugTests(SimpleTestCase):

    def test_simple_path(self):
        self.assertEqual(make_endpoint_slug('v1/items/', 'GET'), 'v1-items-get')

    def test_method_appended_lowercase(self):
        self.assertEqual(make_endpoint_slug('v1/items/', 'POST'), 'v1-items-post')

    def test_pk_regex_group_becomes_id(self):
        self.assertEqual(
            make_endpoint_slug('v1/items/(?P<pk>[^/.]+)/', 'GET'),
            'v1-items-id-get',
        )

    def test_named_regex_group_preserved(self):
        self.assertEqual(
            make_endpoint_slug('v1/items/(?P<slug>[^/.]+)/', 'GET'),
            'v1-items-slug-get',
        )

    def test_angle_bracket_with_type_converter(self):
        self.assertEqual(make_endpoint_slug('v1/items/<int:pk>/', 'GET'), 'v1-items-pk-get')

    def test_angle_bracket_without_type_converter(self):
        self.assertEqual(make_endpoint_slug('v1/items/<pk>/', 'GET'), 'v1-items-pk-get')

    def test_underscore_in_path_segment_becomes_dash(self):
        self.assertEqual(make_endpoint_slug('v1/my_items/', 'GET'), 'v1-my-items-get')

    def test_nested_path_with_pk_group(self):
        self.assertEqual(
            make_endpoint_slug('v1/users/(?P<pk>[^/.]+)/keys/', 'GET'),
            'v1-users-id-keys-get',
        )

    def test_delete_method(self):
        self.assertEqual(make_endpoint_slug('v1/items/<int:pk>/', 'DELETE'), 'v1-items-pk-delete')

    def test_two_different_paths_produce_different_slugs(self):
        a = make_endpoint_slug('v1/alpha/', 'GET')
        b = make_endpoint_slug('v1/beta/', 'GET')
        self.assertNotEqual(a, b)

    def test_same_path_different_method_produces_different_slugs(self):
        get_slug = make_endpoint_slug('v1/items/', 'GET')
        post_slug = make_endpoint_slug('v1/items/', 'POST')
        self.assertNotEqual(get_slug, post_slug)
