"""Management command to export kotta configuration to a JSON fixture file."""

import json
import os

from django.core import serializers
from django.core.management.base import BaseCommand
from django.utils import timezone

from kotta.models import Endpoint, Tier, TierEndpointLimit, UserTier

DEFAULT_OUTPUT_DIR = 'fixtures'
DEFAULT_FILENAME_TEMPLATE = 'kotta_config_{timestamp}.json'


class Command(BaseCommand):
    """Export kotta configuration models to a JSON fixture file.

    Dumps Endpoint, Tier, TierEndpointLimit, and UserTier records.
    UsageCounter is excluded — counters are ephemeral and reset each
    billing window.

    Safe to run at any time without affecting live data.
    """

    help = 'Export kotta configuration (Endpoint, Tier, TierEndpointLimit, UserTier) to JSON.'

    def add_arguments(self, parser):
        """Add optional output path argument."""
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help=(
                'Path to write the fixture file. '
                'Defaults to fixtures/kotta_config_<timestamp>.json in the current directory.'
            ),
        )

    def handle(self, **options):
        """Serialise kotta configuration models and write to a JSON file."""
        output_path = options['output']

        if output_path is None:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = DEFAULT_FILENAME_TEMPLATE.format(timestamp=timestamp)
            output_path = os.path.join(DEFAULT_OUTPUT_DIR, filename)

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        querysets = [
            Endpoint.objects.all(),
            Tier.objects.all(),
            TierEndpointLimit.objects.all(),
            UserTier.objects.all(),
        ]

        counts = {
            'Endpoint': Endpoint.objects.count(),
            'Tier': Tier.objects.count(),
            'TierEndpointLimit': TierEndpointLimit.objects.count(),
            'UserTier': UserTier.objects.count(),
        }

        all_objects = []
        for qs in querysets:
            all_objects.extend(qs)

        data = serializers.serialize(
            'json',
            all_objects,
            indent=2,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=False,
        )

        with open(output_path, 'w') as f:
            f.write(data)

        self.stdout.write(self.style.SUCCESS('kotta configuration exported to %s' % output_path))
        self.stdout.write('\nRecords exported:')
        for model, count in counts.items():
            self.stdout.write('  %s: %d' % (model, count))
