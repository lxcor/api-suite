from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from reggi.decorators import reggi_login_required

_SESSION_KEY = 'billa_new_raw_key'


@method_decorator(reggi_login_required, name='dispatch')
class PurchaseKeyRevealView(View):
    """Show the raw API key exactly once after a purchase, then discard it."""

    def get(self, request):
        raw_key = request.session.pop(_SESSION_KEY, None)
        if raw_key is None:
            cache_key = f'billa_new_key_{request.user.pk}'
            raw_key = cache.get(cache_key)
            if raw_key:
                cache.delete(cache_key)
        if not raw_key:
            return redirect('reggi.dashboard')
        return render(request, 'billa/key_reveal.html', {'raw_key': raw_key})
