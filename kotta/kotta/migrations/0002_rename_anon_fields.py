"""Rename Endpoint.anon_limit → anonymous_limit and anon_period → anonymous_period."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kotta', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='endpoint',
            old_name='anon_limit',
            new_name='anonymous_limit',
        ),
        migrations.RenameField(
            model_name='endpoint',
            old_name='anon_period',
            new_name='anonymous_period',
        ),
    ]
