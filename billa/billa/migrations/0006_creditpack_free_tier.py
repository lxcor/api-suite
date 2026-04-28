"""Add is_free_tier to CreditPack and seed the Free tier record."""

from decimal import Decimal

from django.db import migrations, models


def seed_free_tier(apps, schema_editor):
    CreditPack = apps.get_model('billa', 'CreditPack')
    CreditPack.objects.get_or_create(
        is_free_tier=True,
        defaults={
            'name': 'Free',
            'credits': 1000,
            'price': Decimal('0.00'),
            'is_active': False,
        },
    )


def unseed_free_tier(apps, schema_editor):
    apps.get_model('billa', 'CreditPack').objects.filter(is_free_tier=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('billa', '0005_seed_credit_packs'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditpack',
            name='is_free_tier',
            field=models.BooleanField(
                default=False,
                help_text='Mark this pack as the free-tier grant issued on account creation. '
                          'Set is_active=False to hide it from the pricing page.',
            ),
        ),
        migrations.RunPython(seed_free_tier, unseed_free_tier),
    ]
