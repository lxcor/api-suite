"""View for user logout."""

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View


class LogoutView(View):
    """Handle user logout.

    POST clears the Django session and redirects to
    ``REGGI_LOGOUT_REDIRECT_URL``.  GET requests are redirected to the
    login page.
    """

    def get(self, request):
        return redirect(getattr(settings, 'REGGI_LOGIN_URL', '/reggi/login/'))

    def post(self, request):
        logout(request)
        return redirect(getattr(settings, 'REGGI_LOGOUT_REDIRECT_URL', '/reggi/login/'))
