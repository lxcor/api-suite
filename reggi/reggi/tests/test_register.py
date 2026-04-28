"""Tests for the registration form and RegisterView."""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


class RegistrationFormTests(TestCase):
    """Tests for RegistrationForm validation logic."""

    def _post(self, data):
        return self.client.post(reverse('reggi.register'), data)

    def test_valid_registration_creates_user(self):
        """A valid POST creates a new user record."""
        self._post({
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_valid_registration_logs_user_in(self):
        """A valid POST logs the new user in immediately."""
        response = self._post({
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        })
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_valid_registration_redirects(self):
        """A valid POST redirects to REGGI_REGISTER_REDIRECT_URL."""
        response = self._post({
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_duplicate_username_rejected(self):
        """Registration fails if the username already exists."""
        User.objects.create_user(username='existing', password='pass', email='a@a.com')
        response = self._post({
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already taken')

    def test_duplicate_email_rejected(self):
        """Registration fails if the email is already registered."""
        User.objects.create_user(username='other', password='pass', email='taken@example.com')
        response = self._post({
            'username': 'newuser',
            'email': 'taken@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')

    def test_password_mismatch_rejected(self):
        """Registration fails when passwords do not match."""
        response = self._post({
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'Different123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'do not match')

    def test_weak_password_rejected(self):
        """Registration fails when password does not meet Django validators."""
        response = self._post({
            'username': 'newuser',
            'email': 'new@example.com',
            'password': '123',
            'password_confirm': '123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='newuser').count(), 0)

    def test_get_renders_form(self):
        """GET renders the registration form with a 200 response."""
        response = self.client.get(reverse('reggi.register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create an account')

    @override_settings(REGGI_ALLOW_REGISTRATION=False)
    def test_registration_closed_get(self):
        """GET renders the closed notice when REGGI_ALLOW_REGISTRATION is False."""
        response = self.client.get(reverse('reggi.register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registration is closed')

    @override_settings(REGGI_ALLOW_REGISTRATION=False)
    def test_registration_closed_post_returns_403(self):
        """POST returns 403 when REGGI_ALLOW_REGISTRATION is False."""
        response = self._post({
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    @override_settings(REGGI_REGISTER_REDIRECT_URL='/custom/redirect/')
    def test_custom_redirect_url(self):
        """Valid registration redirects to REGGI_REGISTER_REDIRECT_URL when set."""
        response = self._post({
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        })
        self.assertRedirects(response, '/custom/redirect/', fetch_redirect_response=False)
