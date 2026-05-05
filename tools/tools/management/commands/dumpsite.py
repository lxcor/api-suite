"""Management command to dump site data to fixture files for each model in tools.fixtures."""

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

from tools.fixtures import fixtures

FIXTURES_DIR = 'fixtures'


class Command(BaseCommand):
    """Dump each model listed in tools.fixtures to a JSON file under fixtures/.

    Output files are written to ``fixtures/<app_label>.<model_name>.json``
    relative to the current working directory (the project root) so they can
    be committed to the repository.

    Example::

        python manage.py dumpsite
    """

    help = 'Dump site data to fixture files defined in tools.fixtures.'

    def handle(self, **options):
        if not os.path.exists(FIXTURES_DIR):
            os.makedirs(FIXTURES_DIR)

        for fixture in fixtures:
            output_path = os.path.join(FIXTURES_DIR, '%s.json' % fixture)
            call_command(
                'dumpdata',
                fixture,
                format='json',
                indent=2,
                natural_foreign=True,
                output=output_path,
            )
            self.stdout.write(self.style.SUCCESS('Dumped: %s → %s' % (fixture, output_path)))
