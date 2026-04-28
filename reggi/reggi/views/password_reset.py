"""Views for the password-reset flow."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View

from reggi.forms import PasswordResetRequestForm, SetNewPasswordForm
from reggi.mail import password_reset_token_generator, send_password_reset_email

User = get_user_model()


class PasswordResetView(View):
    """Initiate a password reset.

    POST always renders the "email sent" confirmation regardless of whether
    the submitted address matches a registered user — prevents enumeration.
    """

    def get(self, request):
        return render(request, 'reggi/password_reset.html', {'form': PasswordResetRequestForm()})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email=form.cleaned_data['email'])
                send_password_reset_email(request, user)
            except User.DoesNotExist:
                pass  # Silently ignore — no enumeration
        return render(request, 'reggi/password_reset_done.html')


class PasswordResetConfirmView(View):
    """Validate the reset token and set the new password.

    GET: validates token — renders the new-password form or an invalid-link
    page.  POST: sets the password and redirects to login.
    """

    def _get_user(self, uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return None

    def get(self, request, uidb64, token):
        user = self._get_user(uidb64)
        if user is None or not password_reset_token_generator.check_token(user, token):
            return render(request, 'reggi/password_reset_invalid.html')
        form = SetNewPasswordForm()
        return render(request, 'reggi/password_reset_confirm.html', {
            'form': form,
            'uidb64': uidb64,
            'token': token,
        })

    def post(self, request, uidb64, token):
        user = self._get_user(uidb64)
        if user is None or not password_reset_token_generator.check_token(user, token):
            return render(request, 'reggi/password_reset_invalid.html')

        form = SetNewPasswordForm(request.POST)
        if not form.is_valid():
            return render(request, 'reggi/password_reset_confirm.html', {
                'form': form,
                'uidb64': uidb64,
                'token': token,
            })

        user.set_password(form.cleaned_data['password'])
        user.save()
        return render(request, 'reggi/password_reset_complete.html')
