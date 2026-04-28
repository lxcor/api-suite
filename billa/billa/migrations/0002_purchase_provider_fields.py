"""Replace stripe_session_id with provider + provider_session_id on Purchase."""

from django.db import migrations, models


def populate_provider_fields(apps, schema_editor):
    Purchase = apps.get_model('billa', 'Purchase')
    for purchase in Purchase.objects.all():
        purchase.provider_session_id = purchase.stripe_session_id
        purchase.provider = 'stub' if purchase.stripe_session_id.startswith('stub_') else 'stripe'
        purchase.save(update_fields=['provider', 'provider_session_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('billa', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='provider',
            field=models.CharField(
                choices=[('stripe', 'Stripe'), ('paypal', 'PayPal'), ('stub', 'Stub (development)')],
                max_length=16,
                default='stripe',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchase',
            name='provider_session_id',
            field=models.CharField(max_length=255, default=''),
            preserve_default=False,
        ),
        migrations.RunPython(populate_provider_fields, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='purchase',
            name='stripe_session_id',
        ),
        migrations.AlterUniqueTogether(
            name='purchase',
            unique_together={('provider', 'provider_session_id')},
        ),
    ]
