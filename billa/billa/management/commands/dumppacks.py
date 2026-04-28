"""Management command to export biller CreditPack configuration to a JSON fixture file."""

import os

from django.core import serializers
from django.core.management.base import BaseCommand
from django.utils import timezone

from billa.models import CreditPack

DEFAULT_OUTPUT_DIR = 'fixtures'
DEFAULT_FILENAME_TEMPLATE = 'billa_packs_{timestamp}.json'


class Command(BaseCommand):
    """Export CreditPack records to a JSON fixture file.

    Purchase and CreditBalance records are excluded — they are user-specific
    transactional data, not configuration. Only the admin-editable pricing
    catalogue (CreditPack) is serialised here.

    Load order: kotta fixtures (Tier records) must be loaded before biller
    fixtures because CreditPack.tier is a FK to kotta.Tier.
    """

    help = 'Export biller CreditPack catalogue to JSON.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help=(
                'Path to write the fixture file. '
                'Defaults to fixtures/billa_packs_<timestamp>.json in the current directory.'
            ),
        )

    def handle(self, **options):
        output_path = options['output']

        if output_path is None:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = DEFAULT_FILENAME_TEMPLATE.format(timestamp=timestamp)
            output_path = os.path.join(DEFAULT_OUTPUT_DIR, filename)

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        count = CreditPack.objects.count()

        data = serializers.serialize(
            'json',
            CreditPack.objects.select_related('tier').all(),
            indent=2,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=False,
        )

        with open(output_path, 'w') as f:
            f.write(data)

        self.stdout.write(self.style.SUCCESS('biller packs exported to %s' % output_path))
        self.stdout.write('\nRecords exported:')
        self.stdout.write('  CreditPack: %d' % count)
