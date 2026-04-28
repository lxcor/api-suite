"""Management command to export docca endpoint overviews to a JSON file."""

import json
import os

from django.core.management.base import BaseCommand
from django.utils import timezone

from docca.models import DocEndpoint, DocParameterDef, DocResponseField

DEFAULT_OUTPUT_DIR = 'fixtures'
DEFAULT_FILENAME_TEMPLATE = 'docca_overviews_{timestamp}.json'


class Command(BaseCommand):
    """Export DocEndpoint manager-controlled fields to a JSON file.

    Produces a file keyed by (path, method) — not pk — so it is portable
    across environments and survives database resets.  Only the fields that
    managers own are exported:

        overview, tag (slug), published

    syncdocs-managed fields (summary, description, app_label, view_name)
    are excluded — they are always re-derived from code.

    Safe to run at any time without affecting live data.
    """

    help = 'Export docca endpoint overviews and visibility settings to JSON.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help=(
                'Path to write the JSON file. '
                'Defaults to fixtures/docca_overviews_<timestamp>.json.'
            ),
        )
        parser.add_argument(
            '--app',
            type=str,
            default=None,
            help='Limit export to endpoints belonging to a specific app label.',
        )

    def handle(self, **options):
        output_path = options['output']
        app_label = options['app']

        if output_path is None:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = DEFAULT_FILENAME_TEMPLATE.format(timestamp=timestamp)
            output_path = os.path.join(DEFAULT_OUTPUT_DIR, filename)

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        qs = DocEndpoint.objects.select_related('tag').order_by('path', 'method')
        if app_label:
            qs = qs.filter(app_label=app_label)

        # Endpoint overviews
        endpoints = []
        for ep in qs:
            params = []
            for p in ep.parameters.select_related('param_def').all():
                params.append({
                    'name': p.param_def.name,
                    'location': p.location,
                    'description_override': p.description_override,
                    'example': p.example,
                })
            response_fields = []
            for f in ep.response_fields.all():
                response_fields.append({
                    'name': f.name,
                    'data_type': f.data_type,
                    'nullable': f.nullable,
                    'description': f.description,
                    'example': f.example,
                })
            endpoints.append({
                'path': ep.path,
                'method': ep.method,
                'app_label': ep.app_label,
                'overview': ep.overview,
                'tag': ep.tag.slug if ep.tag else None,
                'published': ep.published,
                'parameters': params,
                'response_fields': response_fields,
            })

        # Parameter definition registry
        param_defs = [
            {
                'name': d.name,
                'param_type': d.param_type,
                'description': d.description,
            }
            for d in DocParameterDef.objects.order_by('name')
        ]

        output = {
            'param_defs': param_defs,
            'endpoints': endpoints,
        }

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        total_response_fields = sum(len(e['response_fields']) for e in endpoints)
        self.stdout.write(self.style.SUCCESS('docca config exported to %s' % output_path))
        self.stdout.write('  Endpoints:        %d' % len(endpoints))
        self.stdout.write('  Parameter defs:   %d' % len(param_defs))
        self.stdout.write('  Response fields:  %d' % total_response_fields)
