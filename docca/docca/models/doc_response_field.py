"""Model definition for DocResponseField — a field in an endpoint's JSON response."""

from django.db import models


class DocResponseField(models.Model):
    """Documents one field in the JSON response of a specific endpoint.

    Records are flat and fully endpoint-scoped — field names are not shared
    across endpoints, so identical names (e.g. ``name``) carry independent
    descriptions appropriate to their response context.

    ``syncdocs`` creates records automatically for endpoints that declare a
    ``ModelSerializer`` as their ``serializer_class``.  For all other
    endpoints the records must be created via ``dumpsite``/``loadsite``.

    syncdocs-managed fields (refreshed on every sync):
        ``name``, ``data_type``, ``nullable``

    Manager-owned fields (never overwritten by syncdocs):
        ``description``, ``example``
    """

    TYPE_STRING = 'string'
    TYPE_INTEGER = 'integer'
    TYPE_FLOAT = 'float'
    TYPE_BOOLEAN = 'boolean'
    TYPE_OBJECT = 'object'
    TYPE_ARRAY = 'array'
    TYPE_DATETIME = 'datetime'

    TYPE_CHOICES = [
        (TYPE_STRING, 'String'),
        (TYPE_INTEGER, 'Integer'),
        (TYPE_FLOAT, 'Float'),
        (TYPE_BOOLEAN, 'Boolean'),
        (TYPE_OBJECT, 'Object'),
        (TYPE_ARRAY, 'Array'),
        (TYPE_DATETIME, 'Datetime'),
    ]

    endpoint = models.ForeignKey(
        'docca.DocEndpoint',
        on_delete=models.CASCADE,
        related_name='response_fields',
    )
    name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_STRING)
    nullable = models.BooleanField(default=False)
    description = models.TextField(
        blank=True,
        help_text='Description of this field in the context of this endpoint. '
                  'Never overwritten by syncdocs.',
    )
    example = models.CharField(
        max_length=500,
        blank=True,
        help_text='Example value as it appears in a real response.',
    )

    class Meta:
        ordering = ('name',)
        unique_together = ('endpoint', 'name')
        verbose_name = 'response field'

    def __str__(self):
        return '%s → %s (%s)' % (self.endpoint, self.name, self.data_type)
