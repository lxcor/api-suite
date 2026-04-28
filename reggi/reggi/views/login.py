"""View for user login."""

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.views import View

from reggi.forms import LoginForm


class LoginView(View):
    """Handle user login.

    GET renders the login form.  POST validates credentials, creates a
    Django session, and redirects to ``REGGI_LOGIN_REDIRECT_URL``.

    If ``REGGI_EMAIL_VERIFICATION`` is True and the user's email is
    unverified the form is re-rendered with a notice.
    """

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(getattr(settings, 'REGGI_LOGIN_REDIRECT_URL', '/reggi/keys/'))
        return render(request, 'reggi/login.html', {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, 'reggi/login.html', {'form': form})

        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user is None:
            form.add_error(None, 'Invalid username or password.')
            return render(request, 'reggi/login.html', {'form': form})

        if getattr(settings, 'REGGI_EMAIL_VERIFICATION', False):
            if not getattr(user, 'reggi_profile', None) or not user.reggi_profile.email_verified:
                return render(request, 'reggi/login.html', {
                    'form': form,
                    'email_unverified': True,
                })

        login(request, user)
        return redirect(getattr(settings, 'REGGI_LOGIN_REDIRECT_URL', '/reggi/keys/'))
