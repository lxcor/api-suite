"""Replace stripe_price_id + paypal_price with a single price field on CreditPack."""

from django.db import migrations, models


def backfill_price(apps, schema_editor):
    CreditPack = apps.get_model('billa', 'CreditPack')
    for pack in CreditPack.objects.all():
        pack.price = pack.paypal_price
        pack.save(update_fields=['price'])


class Migration(migrations.Migration):

    dependencies = [
        ('billa', '0003_add_credit_pack'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditpack',
            name='price',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Price charged to the buyer (e.g. 4.99). Used by all payment providers.',
                max_digits=8,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_price, migrations.RunPython.noop),
        migrations.RemoveField(model_name='creditpack', name='stripe_price_id'),
        migrations.RemoveField(model_name='creditpack', name='paypal_price'),
    ]
