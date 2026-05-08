"""Rename summary→title, drop old description, rename overview→description, add subtitle."""

from django.db import migrations, models


def copy_summary_to_title(apps, schema_editor):
    DocEndpoint = apps.get_model('docca', 'DocEndpoint')
    for ep in DocEndpoint.objects.all():
        ep.title = ep.summary
        ep.save(update_fields=['title'])


class Migration(migrations.Migration):

    dependencies = [
        ('docca', '0005_add_slug'),
    ]

    operations = [
        # 1. Add new fields
        migrations.AddField(
            model_name='docendpoint',
            name='title',
            field=models.CharField(
                max_length=500, blank=True,
                help_text='Short card title. Auto-populated from the first docstring line or @title: tag.',
            ),
        ),
        migrations.AddField(
            model_name='docendpoint',
            name='subtitle',
            field=models.CharField(
                max_length=500, blank=True,
                help_text='One-liner shown on the catalog card. Populated from @subtitle: tag.',
            ),
        ),
        # 2. Copy summary → title
        migrations.RunPython(copy_summary_to_title, migrations.RunPython.noop),
        # 3. Drop old description (raw docstring mirror of summary — not user-visible)
        migrations.RemoveField(model_name='docendpoint', name='description'),
        # 4. Rename overview → description (now the single product-facing text field)
        migrations.RenameField(
            model_name='docendpoint',
            old_name='overview',
            new_name='description',
        ),
        migrations.AlterField(
            model_name='docendpoint',
            name='description',
            field=models.TextField(
                blank=True,
                help_text='Full product-facing description shown on the detail page. '
                          'Populated from @description: tag or docca_overview attribute. '
                          'Never overwritten by syncdocs.',
            ),
        ),
        # 5. Drop old summary (replaced by title)
        migrations.RemoveField(model_name='docendpoint', name='summary'),
    ]
