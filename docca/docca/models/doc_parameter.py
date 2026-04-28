"""Model definition for DocParameter — per-endpoint parameter link."""

from django.db import models


class DocParameter(models.Model):
    """Links a DocParameterDef to a DocEndpoint with endpoint-specific metadata.

    ``syncdocs`` creates these records automatically by introspecting
    ``serializer_class`` fields (body parameters) and named groups in the
    URL pattern (path parameters).  The following fields are refreshed on
    every sync: ``required``, ``location``.  The following fields are
    manager-owned and never overwritten: ``description_override``,
    ``example``.
    """

    LOCATION_BODY = 'body'
    LOCATION_PATH = 'path'
    LOCATION_QUERY = 'query'

    LOCATION_CHOICES = [
        (LOCATION_BODY, 'Body'),
        (LOCATION_PATH, 'Path'),
        (LOCATION_QUERY, 'Query'),
    ]

    endpoint = models.ForeignKey(
        'docca.DocEndpoint',
        on_delete=models.CASCADE,
        related_name='parameters',
    )
    param_def = models.ForeignKey(
        'docca.DocParameterDef',
        on_delete=models.CASCADE,
        related_name='usages',
        verbose_name='parameter',
    )
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES, default=LOCATION_BODY)
    required = models.BooleanField(default=False)
    description_override = models.TextField(
        blank=True,
        help_text='Leave blank to use the canonical description from the parameter definition.',
    )
    example = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ('-required', 'param_def__name')
        unique_together = ('endpoint', 'param_def', 'location')
        verbose_name = 'parameter'

    def __str__(self):
        return '%s → %s' % (self.endpoint, self.param_def.name)

    @property
    def name(self):
        return self.param_def.name

    @property
    def param_type(self):
        return self.param_def.param_type

    @property
    def effective_description(self):
        """Return the override if set, otherwise the canonical definition description."""
        return self.description_override or self.param_def.description
