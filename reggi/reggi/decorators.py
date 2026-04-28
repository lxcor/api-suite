"""Custom decorators for reggi views."""

from django.conf import settings
from django.contrib.auth.decorators import login_required


def reggi_login_required(view_func):
    """Wrap ``login_required`` using the configured ``REGGI_LOGIN_URL``.

    Falls back to ``'/reggi/login/'`` if the setting is not present, so
    reggi never redirects unauthenticated users to Django's default
    ``/accounts/login/``.
    """
    login_url = getattr(settings, 'REGGI_LOGIN_URL', '/reggi/login/')
    return login_required(view_func, login_url=login_url)
