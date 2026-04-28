"""Model definition for TierEndpointLimit — the request cap for one endpoint within one tier."""

from django.conf import settings
from django.db import models

_DEFAULT_PERIOD = getattr(settings, 'KOTTA_DEFAULT_PERIOD', 'month')


class TierEndpointLimit(models.Model):
    """The maximum number of requests a user on a given tier may make to a specific endpoint.

    If no record exists for a tier + endpoint combination the request is
    allowed by default (open-by-default policy) to prevent accidental
    lockout after ``syncendpoints`` adds newly discovered endpoints.
    """

    PERIOD_DAY = 'day'
    PERIOD_MONTH = 'month'

    PERIOD_CHOICES = [
        (PERIOD_DAY, 'Day'),
        (PERIOD_MONTH, 'Month'),
    ]

    tier = models.ForeignKey('Tier', on_delete=models.CASCADE, related_name='endpoint_limits')
    endpoint = models.ForeignKey('Endpoint', on_delete=models.CASCADE, related_name='tier_limits')
    limit = models.PositiveIntegerField(help_text='Maximum requests allowed within the period.')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default=_DEFAULT_PERIOD)

    class Meta:
        unique_together = ('tier', 'endpoint')
        ordering = ('tier', 'endpoint')

    def __str__(self):
        """Return a readable summary of the limit."""
        return '%s — %s: %s/%s' % (self.tier, self.endpoint, self.limit, self.period)
