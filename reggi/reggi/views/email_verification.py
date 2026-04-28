"""Views for email verification flow."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View

from reggi.decorators import reggi_login_required
from reggi.mail import email_verification_token_generator, send_verification_email
from reggi.models import UserProfile

User = get_user_model()


class EmailVerificationView(View):
    """Validate an email verification token (GET only).

    On success marks the user's email as verified and redirects to login.
    On failure renders the invalid-link template.

    Only active when ``REGGI_EMAIL_VERIFICATION`` is True.
    """

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            user = None

        if user is None or not email_verification_token_generator.check_token(user, token):
            return render(request, 'reggi/email_verification_invalid.html')

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.save(update_fields=['email_verified'])

        return redirect(getattr(settings, 'REGGI_LOGIN_URL', '/reggi/login/'))


@method_decorator(reggi_login_required, name='dispatch')
class ResendVerificationView(View):
    """Resend the email verification message to the logged-in user.

    Only active when ``REGGI_EMAIL_VERIFICATION`` is True.
    GET renders the resend form.  POST resends the email (silently ignores
    if already verified).
    """

    def get(self, request):
        return render(request, 'reggi/resend_verification.html')

    def post(self, request):
        profile = getattr(request.user, 'reggi_profile', None)
        if profile is None or not profile.email_verified:
            send_verification_email(request, request.user)
        return render(request, 'reggi/resend_verification.html', {'sent': True})
