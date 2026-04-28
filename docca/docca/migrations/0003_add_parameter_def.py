"""Replace DocParameter name/description/example fields with DocParameterDef FK."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('docca', '0002_add_overview'),
    ]

    operations = [
        # Create DocParameterDef
        migrations.CreateModel(
            name='DocParameterDef',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('param_type', models.CharField(
                    choices=[
                        ('string', 'String'),
                        ('integer', 'Integer'),
                        ('float', 'Float'),
                        ('boolean', 'Boolean'),
                        ('date', 'Date'),
                        ('datetime', 'Datetime'),
                        ('choice', 'Choice'),
                    ],
                    default='string',
                    max_length=20,
                )),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'parameter definition',
                'verbose_name_plural': 'parameter definitions',
                'ordering': ('name',),
            },
        ),

        # Drop old DocParameter and recreate with new schema
        migrations.DeleteModel(name='DocParameter'),
        migrations.CreateModel(
            name='DocParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='parameters',
                    to='docca.docendpoint',
                )),
                ('param_def', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='usages',
                    to='docca.docparameterdef',
                    verbose_name='parameter',
                )),
                ('location', models.CharField(
                    choices=[
                        ('body', 'Body'),
                        ('path', 'Path'),
                        ('query', 'Query'),
                    ],
                    default='body',
                    max_length=10,
                )),
                ('required', models.BooleanField(default=False)),
                ('description_override', models.TextField(blank=True)),
                ('example', models.CharField(blank=True, max_length=500)),
            ],
            options={
                'verbose_name': 'parameter',
                'ordering': ('-required', 'param_def__name'),
            },
        ),
        migrations.AddConstraint(
            model_name='docparameter',
            constraint=models.UniqueConstraint(
                fields=('endpoint', 'param_def', 'location'),
                name='unique_endpoint_param_location',
            ),
        ),
    ]
