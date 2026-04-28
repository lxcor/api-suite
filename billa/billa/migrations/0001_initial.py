"""Initial biller migration — creates CreditBalance and Purchase."""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('reggi', '0002_add_user_profile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditBalance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credits_remaining', models.PositiveIntegerField(default=0)),
                ('is_default', models.BooleanField(default=False, help_text='Designated merge target. Only one per user.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('api_key', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='credit_balance',
                    to='reggi.ApiKey',
                )),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_session_id', models.CharField(max_length=255, unique=True)),
                ('credits_granted', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='biller_purchases',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('credit_balance', models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='purchase',
                    to='billa.CreditBalance',
                )),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
    ]
