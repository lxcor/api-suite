"""Management command to discover API endpoints and sync the DocEndpoint table."""

import inspect
import re

from django.core.management.base import BaseCommand, CommandError
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver
from rest_framework import serializers as drf_serializers

from docca.models import DocEndpoint, DocParameter, DocParameterDef, DocResponseField, DocTag
from docca.models.doc_endpoint import make_endpoint_slug

HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete']

SKIP_CLASSES = {'APIRootView'}
SKIP_PATH_PATTERNS = [
    re.compile(r'format'),
    re.compile(r'^static/'),
    re.compile(r'^admin/'),
    re.compile(r'^reggi/'),
]

VIEWSET_ACTION_METHODS = {
    'list': 'get',
    'create': 'post',
    'retrieve': 'get',
    'update': 'put',
    'partial_update': 'patch',
    'destroy': 'delete',
}

# Map DRF serializer field class → param_type string (shared by request and response)
FIELD_TYPE_MAP = {
    drf_serializers.DecimalField: 'float',
    drf_serializers.FloatField: 'float',
    drf_serializers.IntegerField: 'integer',
    drf_serializers.BooleanField: 'boolean',
    drf_serializers.DateField: 'date',
    drf_serializers.DateTimeField: 'datetime',
    drf_serializers.ChoiceField: 'choice',
    drf_serializers.CharField: 'string',
    drf_serializers.EmailField: 'string',
    drf_serializers.URLField: 'string',
    drf_serializers.HyperlinkedRelatedField: 'string',
    drf_serializers.ManyRelatedField: 'array',
    drf_serializers.ListSerializer: 'array',
    drf_serializers.Serializer: 'object',
}

# Map param_type strings → DocResponseField.data_type choices
RESPONSE_TYPE_MAP = {
    'float': DocResponseField.TYPE_FLOAT,
    'integer': DocResponseField.TYPE_INTEGER,
    'boolean': DocResponseField.TYPE_BOOLEAN,
    'date': DocResponseField.TYPE_STRING,
    'datetime': DocResponseField.TYPE_DATETIME,
    'choice': DocResponseField.TYPE_STRING,
    'string': DocResponseField.TYPE_STRING,
    'array': DocResponseField.TYPE_ARRAY,
    'object': DocResponseField.TYPE_OBJECT,
}

PATH_PARAM_RE = re.compile(r'\(\?P<(\w+)>[^)]+\)')


_NAMED_GROUP_RE = re.compile(r'\(\?P<(\w+)>[^)]+\)')


def _clean_path(raw):
    return raw.lstrip('^').rstrip('$')


def _display_path(path):
    """Convert Django URL regex groups to human-readable {resource_id} tokens.

    ``(?P<pk>[^/.]+)`` uses the preceding segment to infer the resource name
    (e.g. ``timezone/{timezone_id}/``).  Other named groups map to ``{name}``.
    """
    def _replace(m):
        group_name = m.group(1)
        if group_name == 'pk':
            preceding = path[:m.start()].rstrip('/')
            segment = preceding.rsplit('/', 1)[-1] if '/' in preceding else preceding
            return '{%s_id}' % segment
        return '{%s}' % group_name

    return _NAMED_GROUP_RE.sub(_replace, path)


def _first_line(text):
    if not text:
        return ''
    for line in text.strip().splitlines():
        line = line.strip()
        if line:
            return line
    return ''


def _get_docca_meta(cls):
    """Read docca_tag and docca_overview class attributes if present."""
    return {
        'tag_name': getattr(cls, 'docca_tag', None),
        'overview': getattr(cls, 'docca_overview', ''),
    }


def _get_docstring(cls, method_name):
    handler = getattr(cls, method_name, None)
    doc = inspect.getdoc(handler) if handler else None
    if not doc:
        doc = inspect.getdoc(cls) or ''
    return _first_line(doc), doc


def _get_app_label(cls):
    return cls.__module__.split('.')[0]


def _field_type(field):
    for cls, type_str in FIELD_TYPE_MAP.items():
        if isinstance(field, cls):
            return type_str
    return 'string'


def _get_serializer_params(cls):
    """Return list of dicts for each field in the view's serializer_class."""
    serializer_cls = getattr(cls, 'serializer_class', None)
    if serializer_cls is None:
        return []

    try:
        instance = serializer_cls()
        fields = instance.fields
    except Exception:
        return []

    params = []
    for name, field in fields.items():
        params.append({
            'name': name,
            'param_type': _field_type(field),
            'required': field.required,
            'location': DocParameter.LOCATION_BODY,
        })
    return params


def _get_path_params(path):
    """Extract named groups from a URL pattern string as path parameters."""
    return [
        {
            'name': name,
            'param_type': 'string',
            'required': True,
            'location': DocParameter.LOCATION_PATH,
        }
        for name in PATH_PARAM_RE.findall(path)
    ]


def _get_response_fields(cls):
    """Return response field descriptors from a ModelSerializer serializer_class.

    Only introspects when the serializer is a ModelSerializer subclass —
    plain Serializers and manually constructed dict responses are skipped
    and return an empty list (manager fills these via loaddocs).
    """
    serializer_cls = getattr(cls, 'serializer_class', None)
    if serializer_cls is None:
        return []

    if not issubclass(serializer_cls, drf_serializers.ModelSerializer):
        return []

    try:
        instance = serializer_cls()
        fields = instance.fields
    except Exception:
        return []

    result = []
    for name, field in fields.items():
        raw_type = _field_type(field)
        data_type = RESPONSE_TYPE_MAP.get(raw_type, DocResponseField.TYPE_STRING)
        nullable = getattr(field, 'allow_null', False)
        result.append({
            'name': name,
            'data_type': data_type,
            'nullable': nullable,
        })
    return result


def _sync_response_fields(endpoint, fields):
    """Upsert DocResponseField records for an endpoint.

    Creates missing records.  Refreshes ``data_type`` and ``nullable``
    on existing records.  Never touches ``description`` or ``example``.
    """
    for f in fields:
        obj, created = DocResponseField.objects.get_or_create(
            endpoint=endpoint,
            name=f['name'],
            defaults={
                'data_type': f['data_type'],
                'nullable': f['nullable'],
            },
        )
        if not created:
            update_fields = []
            if obj.data_type != f['data_type']:
                obj.data_type = f['data_type']
                update_fields.append('data_type')
            if obj.nullable != f['nullable']:
                obj.nullable = f['nullable']
                update_fields.append('nullable')
            if update_fields:
                obj.save(update_fields=update_fields)


def _collect_endpoints(patterns, prefix=''):
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

        path_params = _get_path_params(clean)
        actions = getattr(cb, 'actions', None)
        meta = _get_docca_meta(cls)

        if actions:
            for http_method, action_name in actions.items():
                summary, description = _get_docstring(cls, action_name)
                if path_params:
                    params = path_params
                else:
                    params = _get_serializer_params(cls) if http_method in ('post', 'put', 'patch') else []
                # Response fields only meaningful on GET endpoints
                response_fields = _get_response_fields(cls) if http_method == 'get' else []
                yield {
                    'path': clean,
                    'method': http_method.upper(),
                    'view_name': p.name or '',
                    'app_label': _get_app_label(cls),
                    'summary': summary,
                    'description': description,
                    'params': params,
                    'response_fields': response_fields,
                    'tag_name': meta['tag_name'],
                    'overview': meta['overview'],
                }
        else:
            for http_method in HTTP_METHODS:
                if not hasattr(cls, http_method):
                    continue
                summary, description = _get_docstring(cls, http_method)
                if path_params:
                    params = path_params
                else:
                    params = _get_serializer_params(cls) if http_method in ('post', 'put', 'patch') else []
                response_fields = _get_response_fields(cls) if http_method == 'get' else []
                yield {
                    'path': clean,
                    'method': http_method.upper(),
                    'view_name': p.name or '',
                    'app_label': _get_app_label(cls),
                    'summary': summary,
                    'description': description,
                    'params': params,
                    'response_fields': response_fields,
                    'tag_name': meta['tag_name'],
                    'overview': meta['overview'],
                }


def _sync_parameters(endpoint, params):
    """Upsert DocParameter records for an endpoint.

    - Creates DocParameterDef if the name is new (blank description shell).
    - Creates DocParameter link if it doesn't exist.
    - Refreshes ``required`` and ``location`` on existing links.
    - Never touches ``description_override`` or ``example``.
    """
    for p in params:
        param_def, _ = DocParameterDef.objects.get_or_create(
            name=p['name'],
            defaults={'param_type': p['param_type']},
        )
        # Refresh param_type if we have a more specific type from code
        if param_def.param_type == 'string' and p['param_type'] != 'string':
            param_def.param_type = p['param_type']
            param_def.save(update_fields=['param_type'])

        doc_param, created = DocParameter.objects.get_or_create(
            endpoint=endpoint,
            param_def=param_def,
            location=p['location'],
            defaults={'required': p['required']},
        )
        if not created and doc_param.required != p['required']:
            doc_param.required = p['required']
            doc_param.save(update_fields=['required'])


class Command(BaseCommand):
    """Discover API endpoints and sync DocEndpoint + DocParameter tables.

    Requires either one or more app names or the ``--all`` flag.

    Examples::

        python manage.py syncdocs astra
        python manage.py syncdocs locci astra
        python manage.py syncdocs --all
    """

    help = 'Sync DocEndpoint and DocParameter records from the project URL configuration.'

    def add_arguments(self, parser):
        parser.add_argument('apps', nargs='*', metavar='app')
        parser.add_argument('--all', action='store_true', dest='all_apps')
        parser.add_argument('--prune', action='store_true')
        parser.add_argument('--check', action='store_true')

    def handle(self, **options):
        app_labels = options['apps']
        all_apps = options['all_apps']
        prune_mode = options['prune']
        check_mode = options['check']

        if not app_labels and not all_apps:
            raise CommandError(
                'Provide at least one app label or use --all.\n'
                'Examples:\n'
                '  python manage.py syncdocs astra\n'
                '  python manage.py syncdocs --all'
            )

        all_discovered = list(_collect_endpoints(get_resolver().url_patterns))

        if not all_apps:
            discovered = [e for e in all_discovered if e['app_label'] in app_labels]
            unknown = set(app_labels) - {e['app_label'] for e in all_discovered}
            if unknown:
                self.stdout.write(
                    self.style.WARNING('Warning: no endpoints found for: %s' % ', '.join(sorted(unknown)))
                )
        else:
            discovered = all_discovered

        discovered_keys = {(e['path'], e['method']) for e in discovered}
        created = []
        existing = []
        _tag_cache = {}

        for ep in discovered:
            tag = None
            if ep['tag_name']:
                if ep['tag_name'] not in _tag_cache:
                    _tag_cache[ep['tag_name']], _ = DocTag.objects.get_or_create(name=ep['tag_name'])
                tag = _tag_cache[ep['tag_name']]

            obj, was_created = DocEndpoint.objects.get_or_create(
                path=ep['path'],
                method=ep['method'],
                defaults={
                    'slug': make_endpoint_slug(ep['path'], ep['method']),
                    'view_name': ep['view_name'],
                    'app_label': ep['app_label'],
                    'summary': ep['summary'],
                    'description': ep['description'],
                    'tag': tag,
                    'overview': ep['overview'],
                },
            )
            if was_created:
                created.append(obj)
            else:
                existing.append(obj)
                update_fields = []
                if obj.is_orphan:
                    obj.is_orphan = False
                    update_fields.append('is_orphan')
                if ep['view_name'] and obj.view_name != ep['view_name']:
                    obj.view_name = ep['view_name']
                    update_fields.append('view_name')
                if obj.app_label != ep['app_label']:
                    obj.app_label = ep['app_label']
                    update_fields.append('app_label')
                if obj.summary != ep['summary']:
                    obj.summary = ep['summary']
                    update_fields.append('summary')
                if obj.description != ep['description']:
                    obj.description = ep['description']
                    update_fields.append('description')
                if update_fields:
                    obj.save(update_fields=update_fields)

            _sync_parameters(obj, ep['params'])
            _sync_response_fields(obj, ep['response_fields'])

        if all_apps:
            scope_filter = DocEndpoint.objects.all()
        else:
            scope_filter = DocEndpoint.objects.filter(app_label__in=app_labels)

        db_keys = set(scope_filter.values_list('path', 'method'))
        orphan_keys = db_keys - discovered_keys
        orphan_count = 0

        for path, method in orphan_keys:
            orphan_count += 1
            if prune_mode:
                DocEndpoint.objects.filter(path=path, method=method).delete()
                self.stdout.write(self.style.WARNING('Pruned:  %s %s' % (method, _display_path(path))))
            else:
                DocEndpoint.objects.filter(path=path, method=method).update(is_orphan=True)
                self.stdout.write(self.style.WARNING('Orphan:  %s %s' % (method, _display_path(path))))

        if check_mode:
            if created:
                for obj in created:
                    self.stdout.write(self.style.ERROR('Unsynced: %s' % obj))
                raise SystemExit(1)
            self.stdout.write(self.style.SUCCESS('OK: all endpoints are synced.'))
            return

        for obj in created:
            self.stdout.write(self.style.SUCCESS('Created: %s %s' % (obj.method, _display_path(obj.path))))

        # Endpoints with no response fields after sync need manual loaddocs work.
        # This covers two silent cases: POST/PUT/PATCH endpoints (response fields
        # never attempted) and GET endpoints whose serializer_class is not a
        # ModelSerializer (discovery attempted but skipped).
        no_fields = [
            obj for obj in (created + existing)
            if not DocResponseField.objects.filter(endpoint=obj).exists()
        ]

        self.stdout.write('\nSummary:')
        self.stdout.write('  Created:  %d' % len(created))
        self.stdout.write('  Existing: %d' % len(existing))
        self.stdout.write('  Orphans:  %d' % orphan_count)

        if no_fields:
            self.stdout.write(
                self.style.WARNING(
                    '\n  %d endpoint(s) have no response fields (auto-discovery not possible).\n'
                    '  Add them manually to the fixture and run loaddocs:' % len(no_fields)
                )
            )
            for obj in sorted(no_fields, key=lambda o: (o.path, o.method)):
                self.stdout.write(self.style.WARNING('    %s %s' % (obj.method, _display_path(obj.path))))
