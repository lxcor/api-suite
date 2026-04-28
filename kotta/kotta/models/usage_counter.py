"""Model definition for UsageCounter — rolling request counter per user/IP per endpoint per window."""

from django.conf import settings
from django.db import models


class UsageCounter(models.Model):
    """Tracks request counts per user (or IP for anonymous) per endpoint per billing window.

    Window reset is lazy — it occurs on the next incoming request when the
    stored ``window_start`` is earlier than the current window start date.
    No scheduled task is required.

    Authenticated requests are keyed on ``user`` + ``endpoint`` + ``window_start``.
    Anonymous requests are keyed on ``ip_address`` + ``endpoint`` + ``window_start``.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, related_name='kotta_usage'
    )
    api_key = models.ForeignKey(
        'reggi.ApiKey', null=True, blank=True,
        on_delete=models.CASCADE, related_name='usage_counters'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    endpoint = models.ForeignKey('Endpoint', on_delete=models.CASCADE, related_name='usage_counters')
    count = models.PositiveIntegerField(default=0)
    window_start = models.DateField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)

    def __str__(self):
        """Return a readable summary of this counter."""
        identity = str(self.user) if self.user else self.ip_address
        return '%s — %s — %s: %s' % (identity, self.endpoint, self.window_start, self.count)
