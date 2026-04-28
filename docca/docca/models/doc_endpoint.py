"""Model definition for DocEndpoint — a documented API route."""

import re

from django.db import models

_REGEX_GROUP_RE = re.compile(r'\(\?P<(\w+)>[^)]+\)')


def make_endpoint_slug(path, method):
    """Derive a stable URL slug from a DocEndpoint path + method.

    Named regex groups are replaced with their name (``pk`` becomes ``id``).
    Django angle-bracket path converters (``<int:name>``) use the param name.
    """
    def _sub_regex(m):
        name = m.group(1)
        return 'id' if name == 'pk' else name

    clean = _REGEX_GROUP_RE.sub(_sub_regex, path)
    clean = re.sub(r'<(?:\w+:)?(\w+)>', r'\1', clean)
    clean = re.sub(r'[^a-z0-9/\-]', '', clean.lower().replace('_', '-'))
    parts = [s for s in clean.split('/') if s]
    parts.append(method.lower())
    return '-'.join(parts)


class DocEndpoint(models.Model):
    """A discovered API endpoint stored in the documentation database.

    Populated by the ``syncdocs`` management command.  Managers control
    visibility via the ``published`` flag and assign tags for grouping.
    Docstrings and descriptions are extracted automatically but can be
    overridden in the admin.
    """

    METHOD_GET = 'GET'
    METHOD_POST = 'POST'
    METHOD_PUT = 'PUT'
    METHOD_PATCH = 'PATCH'
    METHOD_DELETE = 'DELETE'

    METHOD_CHOICES = [
        (METHOD_GET, 'GET'),
        (METHOD_POST, 'POST'),
        (METHOD_PUT, 'PUT'),
        (METHOD_PATCH, 'PATCH'),
        (METHOD_DELETE, 'DELETE'),
    ]

    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    view_name = models.CharField(max_length=255, blank=True)
    app_label = models.CharField(
        max_length=100,
        help_text='Django app this endpoint belongs to (e.g. astra, locci).',
    )
    summary = models.CharField(
        max_length=500,
        blank=True,
        help_text='First line of the view docstring. Auto-populated by syncdocs.',
    )
    description = models.TextField(
        blank=True,
        help_text='Full docstring text. Auto-populated by syncdocs, editable by managers.',
    )
    overview = models.TextField(
        blank=True,
        help_text='Product-facing description written by managers. '
                  'Never overwritten by syncdocs. '
                  'Shown prominently in the portal.',
    )
    tag = models.ForeignKey(
        'docca.DocTag',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='endpoints',
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text='URL-friendly identifier derived from path + method. Set once on creation.',
    )
    published = models.BooleanField(
        default=True,
        help_text='Unpublished endpoints are hidden from the portal but still function.',
    )
    is_orphan = models.BooleanField(
        default=False,
        help_text='Set by syncdocs when this path no longer exists in the URL configuration.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('path', 'method')
        ordering = ('path', 'method')

    def __str__(self):
        return '%s %s' % (self.method, self.path)
