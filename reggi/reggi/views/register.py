"""View for new user registration."""

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render
from django.views import View

from reggi.forms import RegistrationForm
from reggi.mail import send_verification_email
from reggi.models import ApiKey, UserProfile
from reggi.models.api_key import generate_api_key

User = get_user_model()


class RegisterView(View):
    """Handle new user registration.

    GET renders the registration form.  POST validates the form, creates
    the user, and either logs them in immediately or sends a verification
    email (when ``REGGI_EMAIL_VERIFICATION`` is True).

    If ``REGGI_ALLOW_REGISTRATION`` is False, GET renders a registration-
    closed notice and POST returns a 403 response.
    """

    def get(self, request):
        """Render the registration form or a closed notice."""
        if not getattr(settings, 'REGGI_ALLOW_REGISTRATION', True):
            return render(request, 'reggi/register_closed.html', status=200)
        form = RegistrationForm()
        return render(request, 'reggi/register.html', {'form': form})

    def post(self, request):
        """Validate the form and create the user account."""
        if not getattr(settings, 'REGGI_ALLOW_REGISTRATION', True):
            return render(request, 'reggi/register_closed.html', status=403)

        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )

            if getattr(settings, 'REGGI_AUTO_ISSUE_KEY', False):
                raw_key, lookup_prefix, key_hash, salt_hex = generate_api_key()
                ApiKey.objects.create(
                    user=user,
                    name='Free',
                    prefix=lookup_prefix,
                    key_hash=key_hash,
                    salt=salt_hex,
                )

            if getattr(settings, 'REGGI_EMAIL_VERIFICATION', False):
                UserProfile.objects.create(user=user, email_verified=False)
                send_verification_email(request, user)
                login_url = getattr(settings, 'REGGI_LOGIN_URL', '/reggi/login/')
                return redirect(login_url)

            login(request, user)
            redirect_url = getattr(settings, 'REGGI_REGISTER_REDIRECT_URL', '/reggi/keys/')
            return redirect(redirect_url)

        return render(request, 'reggi/register.html', {'form': form})
