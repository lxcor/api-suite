"""Views for API key creation and revocation."""

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from reggi.decorators import reggi_login_required
from reggi.forms import ApiKeyCreateForm
from reggi.models import ApiKey
from reggi.models.api_key import generate_api_key


@method_decorator(reggi_login_required, name='dispatch')
class ApiKeyCreateView(View):
    """Issue a new API key for the authenticated user.

    GET renders the key creation form.  POST generates the key, saves the
    record, and renders the one-time raw-key display template.
    """

    def get(self, request):
        return render(request, 'reggi/key_create.html', {'form': ApiKeyCreateForm()})

    def post(self, request):
        form = ApiKeyCreateForm(request.POST)
        if not form.is_valid():
            return render(request, 'reggi/key_create.html', {'form': form})

        raw_key, lookup_prefix, key_hash, salt_hex = generate_api_key()

        expires_at = form.cleaned_data.get('expires_at')
        if expires_at is None:
            expiry_days = getattr(settings, 'REGGI_KEY_EXPIRY_DAYS', None)
            if expiry_days is not None:
                expires_at = timezone.now() + timezone.timedelta(days=expiry_days)

        try:
            with transaction.atomic():
                ApiKey.objects.create(
                    user=request.user,
                    name=form.cleaned_data['name'],
                    prefix=lookup_prefix,
                    key_hash=key_hash,
                    salt=salt_hex,
                    expires_at=expires_at,
                )
        except IntegrityError:
            form.add_error('name', 'You already have a key with this name.')
            return render(request, 'reggi/key_create.html', {'form': form})

        return render(request, 'reggi/key_created.html', {'raw_key': raw_key})


@method_decorator(reggi_login_required, name='dispatch')
class ApiKeyRevokeView(View):
    """Revoke one of the authenticated user's API keys.

    POST sets ``revoked_at`` and ``is_active=False`` then redirects to the
    dashboard.  Returns 403 if the key belongs to a different user.
    """

    def post(self, request, pk):
        key = get_object_or_404(ApiKey, pk=pk)
        if key.user != request.user:
            return HttpResponseForbidden()
        key.revoked_at = timezone.now()
        key.is_active = False
        key.save(update_fields=['revoked_at', 'is_active'])
        return redirect('reggi.dashboard')
