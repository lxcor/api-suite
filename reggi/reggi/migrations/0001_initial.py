"""Initial migration — creates the ApiKey table."""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='A label to identify this key (e.g. Production, Testing).', max_length=255)),
                ('prefix', models.CharField(help_text='First 8 characters of the token — stored for lookup only.', max_length=8)),
                ('key_hash', models.CharField(max_length=128)),
                ('salt', models.CharField(max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(blank=True, help_text='Updated on every authenticated request.', null=True)),
                ('expires_at', models.DateTimeField(blank=True, help_text='Leave blank for no expiry.', null=True)),
                ('revoked_at', models.DateTimeField(blank=True, help_text='Set when the key is revoked. Null means the key is active.', null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Disable without deleting.')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
                'unique_together': {('user', 'name')},
            },
        ),
    ]
