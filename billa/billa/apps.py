"""App configuration for biller — Stripe checkout and credit-based API access."""

from django.apps import AppConfig


class BillaConfig(AppConfig):
    name = 'billa'
    verbose_name = 'billa'

    def ready(self):
        from billa import signals  # noqa: F401 — connects post_save handler
