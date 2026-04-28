"""View for the authenticated user's profile page."""

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from reggi.decorators import reggi_login_required
from reggi.models import ApiKey


@method_decorator(reggi_login_required, name='dispatch')
class ProfileView(View):
    """Display the authenticated user's account details."""

    def get(self, request):
        active_key_count = ApiKey.objects.filter(
            user=request.user,
            is_active=True,
            revoked_at__isnull=True,
        ).count()
        return render(request, 'reggi/profile.html', {
            'active_key_count': active_key_count,
        })
