"""MergeView — transfers credits from one token to another and revokes the source."""

from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View

from billa.models import CreditBalance
from reggi.decorators import reggi_login_required


@method_decorator(reggi_login_required, name='dispatch')
class MergeView(View):
    """POST /billing/merge/<source_pk>/

    Transfers all credits from the source CreditBalance into a target.
    Target defaults to the user's is_default token; an explicit target_pk
    POST parameter overrides this.

    The source ApiKey is revoked after the transfer completes.
    """

    def post(self, request, source_pk):
        source = get_object_or_404(
            CreditBalance,
            pk=source_pk,
            api_key__user=request.user,
            api_key__revoked_at__isnull=True,
        )

        target_pk = request.POST.get('target_pk')
        if target_pk:
            target = get_object_or_404(
                CreditBalance,
                pk=target_pk,
                api_key__user=request.user,
                api_key__revoked_at__isnull=True,
            )
        else:
            try:
                target = CreditBalance.objects.get(
                    api_key__user=request.user,
                    is_default=True,
                    api_key__revoked_at__isnull=True,
                )
            except CreditBalance.DoesNotExist:
                return HttpResponseBadRequest(
                    'No default token found. Set a default token before merging.'
                )

        if source.pk == target.pk:
            return HttpResponseBadRequest('Cannot merge a token into itself.')

        source.merge_into(target)
        return redirect('reggi.dashboard')
