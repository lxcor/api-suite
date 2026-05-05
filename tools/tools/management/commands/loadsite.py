"""Management command to load site fixture files into the database."""

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from tools.fixtures import fixtures

FIXTURES_DIR = 'fixtures'


class Command(BaseCommand):
    """Load each fixture listed in tools.fixtures from fixtures/<app_label>.<model_name>.json.

    Example::

        python manage.py loadsite
    """

    help = 'Load site data from fixture files defined in tools.fixtures.'

    def handle(self, **options):
        for fixture in fixtures:
            fixture_path = os.path.join(FIXTURES_DIR, '%s.json' % fixture)
            if not os.path.exists(fixture_path):
                raise CommandError('Fixture file not found: %s' % fixture_path)
            self.stdout.write('Loading %s' % fixture_path)
            call_command('loaddata', fixture_path)
            self.stdout.write(self.style.SUCCESS('Loaded:  %s' % fixture))
