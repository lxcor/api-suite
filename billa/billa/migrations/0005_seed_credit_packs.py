"""Seed the two initial CreditPack records (Basic and Pro)."""

from decimal import Decimal

from django.db import migrations


def create_packs(apps, schema_editor):
    CreditPack = apps.get_model('billa', 'CreditPack')
    CreditPack.objects.get_or_create(
        name='Basic',
        defaults={'credits': 10000, 'price': Decimal('3.99'), 'is_active': True},
    )
    CreditPack.objects.get_or_create(
        name='Pro',
        defaults={'credits': 50000, 'price': Decimal('15.99'), 'is_active': True},
    )


def remove_packs(apps, schema_editor):
    CreditPack = apps.get_model('billa', 'CreditPack')
    CreditPack.objects.filter(name__in=['Basic', 'Pro']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('billa', '0004_creditpack_single_price'),
    ]

    operations = [
        migrations.RunPython(create_packs, remove_packs),
    ]
