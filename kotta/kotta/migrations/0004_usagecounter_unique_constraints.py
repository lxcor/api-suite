from django.db import migrations, models


def deduplicate_usage_counters(apps, schema_editor):
    """Remove duplicate UsageCounter rows, keeping the one with the highest count."""
    UsageCounter = apps.get_model('kotta', 'UsageCounter')

    # Deduplicate anonymous counters (keyed on ip_address + endpoint + window_start)
    seen = {}
    for counter in UsageCounter.objects.filter(api_key__isnull=True).order_by('-count'):
        key = (counter.ip_address, counter.endpoint_id, counter.window_start)
        if key in seen:
            counter.delete()
        else:
            seen[key] = counter.pk

    # Deduplicate authenticated counters (keyed on api_key + endpoint + window_start)
    seen = {}
    for counter in UsageCounter.objects.filter(api_key__isnull=False).order_by('-count'):
        key = (counter.api_key_id, counter.endpoint_id, counter.window_start)
        if key in seen:
            counter.delete()
        else:
            seen[key] = counter.pk


class Migration(migrations.Migration):

    dependencies = [
        ('kotta', '0003_usagecounter_apikey'),
    ]

    operations = [
        migrations.RunPython(deduplicate_usage_counters, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='usagecounter',
            constraint=models.UniqueConstraint(
                fields=['ip_address', 'endpoint', 'window_start'],
                condition=models.Q(api_key__isnull=True),
                name='unique_anon_usage_counter',
            ),
        ),
        migrations.AddConstraint(
            model_name='usagecounter',
            constraint=models.UniqueConstraint(
                fields=['api_key', 'endpoint', 'window_start'],
                condition=models.Q(ip_address__isnull=True),
                name='unique_auth_usage_counter',
            ),
        ),
    ]
