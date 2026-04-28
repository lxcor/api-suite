"""Model definition for DocTag — a grouping label for documented endpoints."""

from django.db import models
from django.utils.text import slugify


class DocTag(models.Model):
    """A grouping label for API endpoints in the documentation portal.

    Managers assign tags to endpoints via Django admin.  The portal
    renders endpoints grouped by tag, ordered by ``order`` then ``name``.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers appear first in the portal.',
    )

    class Meta:
        ordering = ('order', 'name')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
