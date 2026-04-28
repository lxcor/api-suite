"""Model definition for the Tier — a membership level with associated endpoint limits."""

from django.db import models
from django.utils.text import slugify


class Tier(models.Model):
    """A membership level that groups users and governs their per-endpoint request limits.

    Examples: Free, Basic, Pro.  Exactly one tier may be marked as the
    default — it is applied to users with no explicit ``UserTier`` assignment.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(
        default=False,
        help_text='Assigned to users with no explicit tier. Only one tier may be the default.'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('name',)

    def save(self, *args, **kwargs):
        """Auto-generate slug from name before saving."""
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        """Return the tier name."""
        return self.name
