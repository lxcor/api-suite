import uuid

from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from billa.models import CreditPack
from billa.services import fulfill_purchase
from reggi.decorators import reggi_login_required


@method_decorator(reggi_login_required, name='dispatch')
class StubConfirmView(View):
    def get(self, request):
        pack_pk = request.GET.get('pack_pk')
        pack = None
        if pack_pk:
            pack = CreditPack.objects.filter(pk=pack_pk, is_active=True).first()
        if pack is None:
            pack = CreditPack.objects.filter(is_active=True).first()
        return render(request, 'billa/stub_confirm.html', {'pack': pack})

    def post(self, request):
        pack_pk = request.POST.get('pack_pk')
        pack = None
        if pack_pk:
            pack = CreditPack.objects.filter(pk=pack_pk, is_active=True).first()
        if pack is None:
            pack = CreditPack.objects.filter(is_active=True).first()
        session_id = f'stub_{uuid.uuid4().hex}'
        fulfill_purchase(request.user, 'stub', session_id, credit_pack=pack)
        return redirect(reverse('reggi.dashboard'))
