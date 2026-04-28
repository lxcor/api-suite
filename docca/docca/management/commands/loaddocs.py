"""Management command to import dokks configuration from a JSON file."""

import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from docca.models import DocEndpoint, DocParameter, DocParameterDef, DocResponseField, DocTag


class Command(BaseCommand):
    """Import manager-controlled fields into dokks models from a JSON file.

    Reads a file produced by ``dumpdocs``.  The file contains two sections:

    ``param_defs``
        Canonical parameter definitions — name, type, and description.
        Matched by name.  Only ``param_type`` and ``description`` are
        written; existing records are updated.

    ``endpoints``
        Matched by (path, method).  Only manager-owned fields are written:
        ``overview``, ``tag``, ``published``.  For each endpoint's
        ``parameters`` list, ``description_override`` and ``example`` are
        updated; syncdocs-managed fields (``required``, ``location``) are
        never touched here.

    Runs inside a transaction — rolled back entirely on any error unless
    ``--dry-run`` is used.
    """

    help = 'Import dokks configuration from a JSON file produced by dumpdocs.'

    def add_arguments(self, parser):
        parser.add_argument('input', type=str)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, **options):
        input_path = options['input']
        dry_run = options['dry_run']

        if not os.path.exists(input_path):
            raise CommandError('File not found: %s' % input_path)

        with open(input_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as exc:
                raise CommandError('Failed to parse JSON: %s' % exc)

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run — no changes will be written.'))

        counts = {
            'param_defs': 0,
            'endpoints_updated': 0,
            'endpoints_skipped': 0,
            'params_updated': 0,
            'response_fields_updated': 0,
        }

        try:
            with transaction.atomic():
                # --- Parameter definition registry ---
                for record in data.get('param_defs', []):
                    name = record.get('name')
                    if not name:
                        continue
                    obj, _ = DocParameterDef.objects.get_or_create(name=name)
                    obj.param_type = record.get('param_type', obj.param_type)
                    obj.description = record.get('description', obj.description)
                    if not dry_run:
                        obj.save(update_fields=['param_type', 'description'])
                    counts['param_defs'] += 1

                # --- Endpoint overviews ---
                for record in data.get('endpoints', []):
                    path = record.get('path')
                    method = record.get('method')
                    if not path or not method:
                        continue

                    try:
                        ep = DocEndpoint.objects.get(path=path, method=method)
                    except DocEndpoint.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING('Not in DB, skipped: %s %s' % (method, path))
                        )
                        counts['endpoints_skipped'] += 1
                        continue

                    ep.overview = record.get('overview') or ''
                    ep.published = record.get('published', True)

                    tag_slug = record.get('tag')
                    if tag_slug:
                        try:
                            ep.tag = DocTag.objects.get(slug=tag_slug)
                        except DocTag.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    'Tag "%s" not found, skipped for %s %s' % (tag_slug, method, path)
                                )
                            )
                    else:
                        ep.tag = None

                    if not dry_run:
                        ep.save(update_fields=['overview', 'published', 'tag'])
                    counts['endpoints_updated'] += 1

                    # Per-endpoint parameter overrides (and creation for manually documented params)
                    for p_record in record.get('parameters', []):
                        p_name = p_record.get('name')
                        p_location = p_record.get('location')
                        if not p_name or not p_location:
                            continue
                        try:
                            param_def, _ = DocParameterDef.objects.get_or_create(
                                name=p_name,
                                defaults={'param_type': 'string'},
                            )
                            if not dry_run:
                                param, created = DocParameter.objects.get_or_create(
                                    endpoint=ep,
                                    param_def=param_def,
                                    location=p_location,
                                    defaults={'required': p_record.get('required', False)},
                                )
                            else:
                                created = False
                                param = DocParameter(
                                    endpoint=ep, param_def=param_def, location=p_location
                                )
                            param.description_override = p_record.get('description_override', '')
                            param.example = p_record.get('example', '')
                            if not dry_run:
                                param.save(update_fields=['description_override', 'example'])
                            counts['params_updated'] += 1
                        except Exception as exc:
                            self.stdout.write(
                                self.style.WARNING(
                                    'Parameter "%s" error for %s %s: %s' % (p_name, method, path, exc)
                                )
                            )

                    # Response field descriptions and examples
                    for f_record in record.get('response_fields', []):
                        f_name = f_record.get('name')
                        if not f_name:
                            continue
                        try:
                            rf = DocResponseField.objects.get(endpoint=ep, name=f_name)
                            rf.description = f_record.get('description', rf.description)
                            rf.example = f_record.get('example', rf.example)
                            if not dry_run:
                                rf.save(update_fields=['description', 'example'])
                            counts['response_fields_updated'] += 1
                        except DocResponseField.DoesNotExist:
                            # Field not yet in DB (e.g. manually documented endpoint)
                            # Create it with manager-owned fields only
                            if not dry_run:
                                DocResponseField.objects.create(
                                    endpoint=ep,
                                    name=f_name,
                                    data_type=f_record.get('data_type', 'string'),
                                    nullable=f_record.get('nullable', False),
                                    description=f_record.get('description', ''),
                                    example=f_record.get('example', ''),
                                )
                            counts['response_fields_updated'] += 1

                if dry_run:
                    raise _DryRunRollback()

        except _DryRunRollback:
            pass

        action = 'Would update' if dry_run else 'Updated'
        self.stdout.write(self.style.SUCCESS('%s dokks config from %s' % (action, input_path)))
        self.stdout.write('  Parameter defs:    %d' % counts['param_defs'])
        self.stdout.write('  Endpoints:         %d' % counts['endpoints_updated'])
        self.stdout.write('  Skipped:           %d' % counts['endpoints_skipped'])
        self.stdout.write('  Param overrides:   %d' % counts['params_updated'])
        self.stdout.write('  Response fields:   %d' % counts['response_fields_updated'])


class _DryRunRollback(Exception):
    pass
