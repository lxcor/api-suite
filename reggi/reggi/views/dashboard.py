"""Dashboard view — lists a user's active API keys."""

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from reggi.decorators import reggi_login_required
from reggi.models import ApiKey


@method_decorator(reggi_login_required, name='dispatch')
class DashboardView(View):
    """Render the API key dashboard for the authenticated user.

    Displays all non-revoked keys.  Does not show the raw key or hash.
    """

    def get(self, request):
        keys = ApiKey.objects.filter(
            user=request.user,
            revoked_at__isnull=True,
        ).select_related('credit_balance__purchase')
        return render(request, 'reggi/dashboard.html', {'keys': keys})
