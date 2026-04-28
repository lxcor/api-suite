import re

from django.db import migrations, models

_REGEX_GROUP_RE = re.compile(r'\(\?P<(\w+)>[^)]+\)')


def _make_slug(path, method):
    def _sub_regex(m):
        name = m.group(1)
        return 'id' if name == 'pk' else name

    clean = _REGEX_GROUP_RE.sub(_sub_regex, path)
    clean = re.sub(r'<(?:\w+:)?(\w+)>', r'\1', clean)
    clean = re.sub(r'[^a-z0-9/\-]', '', clean.lower())
    parts = [s for s in clean.split('/') if s]
    parts.append(method.lower())
    return '-'.join(parts)


def populate_slugs(apps, schema_editor):
    DocEndpoint = apps.get_model('docca', 'DocEndpoint')
    for ep in DocEndpoint.objects.all():
        ep.slug = _make_slug(ep.path, ep.method)
        ep.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('docca', '0004_add_response_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='docendpoint',
            name='slug',
            # db_index=False avoids creating a _like index here that would
            # collide with the one created by AlterField below.
            field=models.SlugField(max_length=200, blank=True, db_index=False),
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='docendpoint',
            name='slug',
            field=models.SlugField(
                max_length=200,
                unique=True,
                help_text='URL-friendly identifier derived from path + method. Set once on creation.',
            ),
        ),
    ]
