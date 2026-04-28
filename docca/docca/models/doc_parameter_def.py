"""Model definition for DocParameterDef — canonical registry of API request parameters."""

from django.db import models


class DocParameterDef(models.Model):
    """Canonical definition of a named request parameter.

    One record per distinct parameter name across the entire API.
    Descriptions are written once here and inherited by every endpoint
    that shares the same parameter name.  ``syncdocs`` creates a blank
    shell when it encounters an unknown parameter name; managers fill in
    the description once and all endpoints benefit immediately.
    """

    TYPE_STRING = 'string'
    TYPE_INTEGER = 'integer'
    TYPE_FLOAT = 'float'
    TYPE_BOOLEAN = 'boolean'
    TYPE_DATE = 'date'
    TYPE_DATETIME = 'datetime'
    TYPE_CHOICE = 'choice'

    TYPE_CHOICES = [
        (TYPE_STRING, 'String'),
        (TYPE_INTEGER, 'Integer'),
        (TYPE_FLOAT, 'Float'),
        (TYPE_BOOLEAN, 'Boolean'),
        (TYPE_DATE, 'Date'),
        (TYPE_DATETIME, 'Datetime'),
        (TYPE_CHOICE, 'Choice'),
    ]

    name = models.CharField(max_length=100, unique=True)
    param_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_STRING)
    description = models.TextField(
        blank=True,
        help_text='Canonical description shown on all endpoints that use this parameter. '
                  'Write once, inherited everywhere.',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'parameter definition'
        verbose_name_plural = 'parameter definitions'

    def __str__(self):
        return '%s (%s)' % (self.name, self.param_type)
