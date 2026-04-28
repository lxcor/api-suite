"""Forms for password reset flow."""

from django import forms
from django.contrib.auth.password_validation import validate_password


class PasswordResetRequestForm(forms.Form):
    """Form that accepts an email address to initiate a password reset."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
    )


class SetNewPasswordForm(forms.Form):
    """Form for setting a new password after clicking a reset link."""

    password = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'}),
    )
    password_confirm = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
    )

    def clean_password(self):
        """Run Django's password validators."""
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        """Validate that both password fields match."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned_data
