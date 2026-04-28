"""Email sending helpers for reggi."""

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


# Separate token generator instances so password-reset and email-verification
# tokens cannot be interchanged.
password_reset_token_generator = PasswordResetTokenGenerator()


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Token generator for email address verification.

    Uses a different secret suffix so verification tokens cannot be used
    as password-reset tokens and vice-versa.
    """

    def _make_hash_value(self, user, timestamp):
        return f'{user.pk}{timestamp}{user.email}verified'


email_verification_token_generator = EmailVerificationTokenGenerator()


def _send(subject, body_txt_template, body_html_template, to_email, context):
    """Render and dispatch a plain-text (or multipart) email.

    If a HTML body template exists and renders without error, the email is
    sent as multipart/alternative.  Otherwise plain text only.
    """
    body_txt = render_to_string(body_txt_template, context)

    try:
        body_html = render_to_string(body_html_template, context)
    except Exception:
        body_html = None

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
        to=[to_email],
    )
    if body_html:
        msg.attach_alternative(body_html, 'text/html')

    msg.send()


def send_password_reset_email(request, user):
    """Send a password-reset email to *user*."""
    timeout_seconds = getattr(settings, 'REGGI_PASSWORD_RESET_TIMEOUT', 3600)
    expiry_hours = round(timeout_seconds / 3600, 1)

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token_generator.make_token(user)

    reset_url = request.build_absolute_uri(
        f'/reggi/password/reset/{uidb64}/{token}/'
    )

    site_name = getattr(settings, 'REGGI_SITE_NAME', 'API')
    subject = getattr(settings, 'REGGI_PASSWORD_RESET_SUBJECT', None)
    if subject is None:
        subject = render_to_string(
            'reggi/email/password_reset_subject.txt',
            {'site_name': site_name},
        ).strip()

    context = {
        'user': user,
        'site_name': site_name,
        'reset_url': reset_url,
        'expiry_hours': expiry_hours,
    }

    _send(
        subject=subject,
        body_txt_template='reggi/email/password_reset_body.txt',
        body_html_template='reggi/email/password_reset_body.html',
        to_email=user.email,
        context=context,
    )


def send_verification_email(request, user):
    """Send an email-verification email to *user*."""
    timeout_seconds = getattr(settings, 'REGGI_PASSWORD_RESET_TIMEOUT', 3600)
    expiry_hours = round(timeout_seconds / 3600, 1)

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token_generator.make_token(user)

    verify_url = request.build_absolute_uri(
        f'/reggi/verify/{uidb64}/{token}/'
    )

    site_name = getattr(settings, 'REGGI_SITE_NAME', 'API')
    subject = getattr(settings, 'REGGI_VERIFICATION_SUBJECT', None)
    if subject is None:
        subject = render_to_string(
            'reggi/email/verification_subject.txt',
            {'site_name': site_name},
        ).strip()

    context = {
        'user': user,
        'site_name': site_name,
        'verify_url': verify_url,
        'expiry_hours': expiry_hours,
    }

    _send(
        subject=subject,
        body_txt_template='reggi/email/verification_body.txt',
        body_html_template='reggi/email/verification_body.html',
        to_email=user.email,
        context=context,
    )
