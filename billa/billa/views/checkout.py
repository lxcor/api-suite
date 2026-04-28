from django.utils.decorators import method_decorator
from django.views import View

from billa.backends import get_backend
from billa.models import CreditPack
from reggi.decorators import reggi_login_required


@method_decorator(reggi_login_required, name='dispatch')
class CheckoutView(View):
    """POST /billing/checkout/

    Accepts provider (stripe|paypal|stub) and pack_pk from the pricing page
    form. Routes to the correct backend with the resolved CreditPack.
    """

    def post(self, request):
        provider = request.POST.get('provider') or None
        pack_pk = request.POST.get('pack_pk')

        credit_pack = None
        if pack_pk:
            credit_pack = CreditPack.objects.filter(pk=pack_pk, is_active=True).first()

        backend = get_backend(provider)
        return backend.create_checkout(request, credit_pack=credit_pack)
