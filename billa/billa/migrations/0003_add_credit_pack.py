"""Add CreditPack model."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kotta', '0001_initial'),
        ('billa', '0002_purchase_provider_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditPack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('credits', models.PositiveIntegerField(help_text='Number of API request credits granted.')),
                ('stripe_price_id', models.CharField(
                    blank=True,
                    max_length=100,
                    help_text='Stripe Price ID for this pack (leave blank if not using Stripe).',
                )),
                ('paypal_price', models.DecimalField(
                    decimal_places=2,
                    max_digits=8,
                    help_text='Price charged via PayPal (e.g. 4.99).',
                )),
                ('tier', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='credit_packs',
                    to='kotta.Tier',
                    help_text='Tier assigned to the buyer on purchase. Leave blank for no tier upgrade.',
                )),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('credits',),
            },
        ),
    ]
