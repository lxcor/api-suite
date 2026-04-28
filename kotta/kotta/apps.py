"""Django application configuration for the kotta app."""

from django.apps import AppConfig


class KottaConfig(AppConfig):
    """Application configuration for kotta — per-endpoint throttling and tier management."""

    name = 'kotta'
