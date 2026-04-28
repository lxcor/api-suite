from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse


class StubPaymentBackend:
    def create_checkout(self, request, credit_pack=None):
        url = reverse('billa.stub_confirm')
        if credit_pack:
            url += f'?pack_pk={credit_pack.pk}'
        return redirect(url)

    def handle_webhook(self, request):
        return HttpResponse(status=400)
