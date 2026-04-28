"""Management command to import biller CreditPack configuration from a JSON fixture file."""

import os

from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from billa.models import CreditPack


class Command(BaseCommand):
    """Import CreditPack records from a JSON fixture file produced by dumppacks.

    Performs an upsert — existing records are updated with values from the
    fixture, new records are created. Records present in the DB but absent
    from the fixture are left untouched.

    Purchase and CreditBalance records are never touched by this command.

    Load order: run loadconfig (kotta) before loadpacks so that Tier FKs
    resolve correctly.

    Run inside a transaction — the entire import is rolled back if any
    record fails to save.
    """

    help = 'Import biller CreditPack catalogue from a JSON fixture file.'

    def add_arguments(self, parser):
        parser.add_argument(
            'input',
            type=str,
            help='Path to the JSON fixture file produced by dumppacks.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and validate the fixture without writing to the database.',
        )

    def handle(self, **options):
        input_path = options['input']
        dry_run = options['dry_run']

        if not os.path.exists(input_path):
            raise CommandError('File not found: %s' % input_path)

        with open(input_path, 'r') as f:
            raw = f.read()

        try:
            deserialized = list(serializers.deserialize('json', raw))
        except Exception as exc:
            raise CommandError('Failed to parse fixture: %s' % exc)

        allowed_models = {CreditPack}
        counts = {'created': 0, 'updated': 0, 'skipped': 0}

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run — no changes will be written.'))

        try:
            with transaction.atomic():
                for obj in deserialized:
                    model = type(obj.object)

                    if model not in allowed_models:
                        self.stdout.write(
                            self.style.WARNING('Skipped unsupported model: %s' % model.__name__)
                        )
                        counts['skipped'] += 1
                        continue

                    exists = model.objects.filter(pk=obj.object.pk).exists()

                    if not dry_run:
                        obj.save()

                    if exists:
                        counts['updated'] += 1
                    else:
                        counts['created'] += 1

                if dry_run:
                    raise _DryRunRollback()

        except _DryRunRollback:
            pass

        action = 'Would import' if dry_run else 'Imported'
        self.stdout.write(self.style.SUCCESS('%s biller packs from %s' % (action, input_path)))
        self.stdout.write('\nRecords %s:' % ('to be processed' if dry_run else 'processed'))
        self.stdout.write('  Created: %d' % counts['created'])
        self.stdout.write('  Updated: %d' % counts['updated'])
        self.stdout.write('  Skipped: %d' % counts['skipped'])


class _DryRunRollback(Exception):
    """Internal exception used to roll back the dry-run transaction cleanly."""
    pass
