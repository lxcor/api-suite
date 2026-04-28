"""Model definition for the Endpoint — a discoverable API route subject to throttling."""

from django.db import models


class Endpoint(models.Model):
    """A registered API endpoint discovered from the project URL configuration.

    Populated by the ``syncendpoints`` management command.  Managers configure
    anonymous request limits and active status via Django admin.  The throttle
    classes read ``anonymous_limit`` and ``anonymous_period`` at request time.
    """

    PERIOD_SECOND = 'second'
    PERIOD_MINUTE = 'minute'
    PERIOD_HOUR = 'hour'
    PERIOD_DAY = 'day'

    PERIOD_CHOICES = [
        (PERIOD_SECOND, 'Second'),
        (PERIOD_MINUTE, 'Minute'),
        (PERIOD_HOUR, 'Hour'),
        (PERIOD_DAY, 'Day'),
    ]

    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    anonymous_limit = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Max requests per period for anonymous users. Leave blank to block anonymous access entirely.'
    )
    anonymous_period = models.CharField(
        max_length=10, choices=PERIOD_CHOICES, default=PERIOD_DAY
    )
    is_active = models.BooleanField(default=True)
    is_orphan = models.BooleanField(
        default=False,
        help_text='Set by syncendpoints when this path no longer exists in the URL configuration.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('path', 'method')
        ordering = ('path', 'method')

    def __str__(self):
        """Return the HTTP method and path as a combined identifier."""
        return '%s %s' % (self.method, self.path)
