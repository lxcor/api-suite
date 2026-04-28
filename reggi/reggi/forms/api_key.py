"""Form for creating a new API key."""

from django import forms


class ApiKeyCreateForm(forms.Form):
    """Form for issuing a new API key.

    ``name`` is a label the user assigns (e.g. "Production", "Testing").
    ``expires_at`` is optional — leave blank for no expiry.
    """

    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Production'}),
        help_text='A label to identify this key.',
    )
    expires_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M',
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
        help_text='Optional — leave blank for no expiry.',
    )
