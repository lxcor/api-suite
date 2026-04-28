"""Management command to discover API endpoints from the URL configuration and sync the Endpoint table."""

import re

from django.core.management.base import BaseCommand
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

from kotta.models import Endpoint

HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete']

SKIP_CLASSES = {'APIRootView'}
SKIP_PATH_PATTERNS = [
    re.compile(r'format'),   # format suffix variants
    re.compile(r'^static/'), # static files
    re.compile(r'^admin/'),  # Django admin
]


def _clean_path(raw):
    """Strip regex anchors from a URL pattern string and return a clean path."""
    return raw.lstrip('^').rstrip('$')


def _get_methods(cls, actions):
    """Return the list of uppercase HTTP methods for a DRF view.

    For ViewSets ``actions`` is a dict whose keys are the HTTP methods.
    For plain APIView subclasses ``actions`` is None — the methods defined
    directly on the class are inspected instead.
    """
    if actions:
        return [m.upper() for m in actions.keys()]
    return [m.upper() for m in HTTP_METHODS if m in cls.__dict__]


def _collect_endpoints(patterns, prefix=''):
    """Recursively walk URL patterns and yield (path, method, name, cls_name) tuples."""
    for p in patterns:
        full = prefix + str(p.pattern)

        if isinstance(p, URLResolver):
            yield from _collect_endpoints(p.url_patterns, full)
            continue

        if not isinstance(p, URLPattern):
            continue

        cb = p.callback
        cls = getattr(cb, 'cls', None)

        if cls is None:
            continue

        if cls.__name__ in SKIP_CLASSES:
            continue

        clean = _clean_path(full)

        if any(pat.search(clean) for pat in SKIP_PATH_PATTERNS):
            continue

        actions = getattr(cb, 'actions', None)
        methods = _get_methods(cls, actions)

        for method in methods:
            raw_name = p.name or ''
            name = raw_name[:-5] if raw_name.endswith('-list') else raw_name
            yield clean, method, name, cls.__name__


class Command(BaseCommand):
    """Discover all DRF endpoints from the URL configuration and sync the Endpoint table.

    Creates a new ``Endpoint`` record for each path + method combination
    not already present in the database.  Existing records are not
    modified so manager-configured values (limits, descriptions) are
    preserved.  Endpoint records whose path + method no longer appears in
    the URL configuration are flagged as orphans by default, or deleted
    when ``--prune`` is supplied.

    Safe to run repeatedly — fully idempotent.
    """

    help = 'Sync Endpoint records from the project URL configuration.'

    def add_arguments(self, parser):
        """Add the --check and --prune flags."""
        parser.add_argument(
            '--check',
            action='store_true',
            help='Exit with code 1 if any unsynced endpoints exist without writing to the database.',
        )
        parser.add_argument(
            '--prune',
            action='store_true',
            help='Delete orphaned Endpoint records instead of flagging them.',
        )

    def handle(self, **options):
        """Walk all URL patterns, sync the Endpoint table, and report results."""
        check_mode = options['check']
        prune_mode = options['prune']

        discovered = list(_collect_endpoints(get_resolver().url_patterns))
        discovered_keys = {(path, method) for path, method, *_ in discovered}

        created = []
        existing = []

        for path, method, name, _ in discovered:
            endpoint, was_created = Endpoint.objects.get_or_create(
                path=path,
                method=method,
                defaults={'name': name},
            )
            if was_created:
                created.append(endpoint)
            else:
                existing.append(endpoint)
                update_fields = []
                if endpoint.is_orphan:
                    endpoint.is_orphan = False
                    update_fields.append('is_orphan')
                if name and endpoint.name != name:
                    endpoint.name = name
                    update_fields.append('name')
                if update_fields:
                    endpoint.save(update_fields=update_fields)

        db_keys = set(Endpoint.objects.values_list('path', 'method'))
        orphan_keys = db_keys - discovered_keys
        orphan_count = 0
        for path, method in orphan_keys:
            if prune_mode:
                Endpoint.objects.filter(path=path, method=method).delete()
                self.stdout.write(
                    self.style.WARNING('Pruned:  %s %s (deleted)' % (method, path))
                )
            else:
                Endpoint.objects.filter(path=path, method=method).update(is_orphan=True)
                self.stdout.write(
                    self.style.WARNING('Orphan:  %s %s (in DB but not in URL config)' % (method, path))
                )
            orphan_count += 1

        if check_mode:
            if created:
                for ep in created:
                    self.stdout.write(self.style.ERROR('Unsynced: %s' % ep))
                raise SystemExit(1)
            self.stdout.write(self.style.SUCCESS('OK: all endpoints are synced.'))
            return

        for ep in created:
            self.stdout.write(self.style.SUCCESS('Created: %s' % ep))

        orphan_label = 'Pruned:  ' if prune_mode else 'Orphans: '
        self.stdout.write('\nSummary:')
        self.stdout.write('  Created:  %d' % len(created))
        self.stdout.write('  Existing: %d' % len(existing))
        self.stdout.write('  %s %d' % (orphan_label, orphan_count))
