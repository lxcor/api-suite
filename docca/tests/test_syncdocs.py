"""Tests for the syncdocs management command."""

from django.core.management import call_command
from django.test import TestCase, override_settings

from docca.models import DocEndpoint, DocTag


@override_settings(ROOT_URLCONF='tests.urls_test')
class SyncDocsCreateTests(TestCase):
    """syncdocs creates DocEndpoint rows for newly discovered URL patterns."""

    def test_creates_endpoint_for_discovered_url(self):
        call_command('syncdocs', '--all', verbosity=0)
        self.assertTrue(DocEndpoint.objects.filter(path='api/alpha/', method='GET').exists())

    def test_creates_endpoint_for_each_method_on_view(self):
        call_command('syncdocs', '--all', verbosity=0)
        self.assertTrue(DocEndpoint.objects.filter(path='api/alpha/', method='POST').exists())

    def test_creates_endpoint_for_path_param_url(self):
        call_command('syncdocs', '--all', verbosity=0)
        self.assertTrue(
            DocEndpoint.objects.filter(path__contains='api/beta/', method='GET').exists()
        )

    def test_slug_set_on_creation(self):
        call_command('syncdocs', '--all', verbosity=0)
        ep = DocEndpoint.objects.get(path='api/alpha/', method='GET')
        self.assertEqual(ep.slug, 'api-alpha-get')

    def test_tag_created_from_docca_tag_attribute(self):
        call_command('syncdocs', '--all', verbosity=0)
        self.assertTrue(DocTag.objects.filter(name='Alpha').exists())

    def test_endpoint_linked_to_tag(self):
        call_command('syncdocs', '--all', verbosity=0)
        ep = DocEndpoint.objects.get(path='api/alpha/', method='GET')
        self.assertIsNotNone(ep.tag)
        self.assertEqual(ep.tag.name, 'Alpha')

    def test_summary_populated_from_class_docstring(self):
        call_command('syncdocs', '--all', verbosity=0)
        ep = DocEndpoint.objects.get(path='api/alpha/', method='GET')
        self.assertIn('alpha', ep.summary.lower())

    def test_second_run_does_not_duplicate_endpoints(self):
        call_command('syncdocs', '--all', verbosity=0)
        call_command('syncdocs', '--all', verbosity=0)
        count = DocEndpoint.objects.filter(path='api/alpha/', method='GET').count()
        self.assertEqual(count, 1)


@override_settings(ROOT_URLCONF='tests.urls_test')
class SyncDocsUpdateTests(TestCase):
    """syncdocs updates mutable fields on re-run without touching manager edits."""

    def setUp(self):
        call_command('syncdocs', '--all', verbosity=0)
        self.ep = DocEndpoint.objects.get(path='api/alpha/', method='GET')

    def test_is_orphan_cleared_when_endpoint_reappears(self):
        self.ep.is_orphan = True
        self.ep.save(update_fields=['is_orphan'])
        call_command('syncdocs', '--all', verbosity=0)
        self.ep.refresh_from_db()
        self.assertFalse(self.ep.is_orphan)

    def test_overview_not_overwritten_by_resync(self):
        self.ep.overview = 'Manager-written overview.'
        self.ep.save(update_fields=['overview'])
        call_command('syncdocs', '--all', verbosity=0)
        self.ep.refresh_from_db()
        self.assertEqual(self.ep.overview, 'Manager-written overview.')


@override_settings(ROOT_URLCONF='tests.urls_test')
class SyncDocsOrphanTests(TestCase):
    """syncdocs marks removed endpoints as orphans; --prune deletes them."""

    def setUp(self):
        # Seed an endpoint that will no longer appear in the URL conf.
        DocEndpoint.objects.create(
            path='api/gone/',
            method='GET',
            app_label='tests',
            slug='api-gone-get',
        )

    def test_missing_endpoint_marked_as_orphan(self):
        call_command('syncdocs', '--all', verbosity=0)
        ep = DocEndpoint.objects.get(path='api/gone/', method='GET')
        self.assertTrue(ep.is_orphan)

    def test_prune_deletes_missing_endpoint(self):
        call_command('syncdocs', '--all', '--prune', verbosity=0)
        self.assertFalse(DocEndpoint.objects.filter(path='api/gone/', method='GET').exists())

    def test_non_orphan_endpoint_not_deleted_by_prune(self):
        call_command('syncdocs', '--all', '--prune', verbosity=0)
        self.assertTrue(DocEndpoint.objects.filter(path='api/alpha/', method='GET').exists())
