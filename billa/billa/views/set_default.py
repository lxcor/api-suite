"""SetDefaultView — marks a CreditBalance as the user's default merge target."""

from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View

from billa.models import CreditBalance
from reggi.decorators import reggi_login_required


@method_decorator(reggi_login_required, name='dispatch')
class SetDefaultView(View):
    """POST /billing/default/<pk>/

    Sets is_default=True on the given CreditBalance and clears the flag on
    all other balances belonging to the same user (enforced in CreditBalance.save).
    """

    def post(self, request, pk):
        balance = get_object_or_404(
            CreditBalance,
            pk=pk,
            api_key__user=request.user,
        )
        balance.is_default = True
        balance.save()
        return redirect('reggi.dashboard')
