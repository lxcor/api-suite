"""View for changing the authenticated user's password."""

from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from reggi.decorators import reggi_login_required
from reggi.forms.change_password import ChangePasswordForm


@method_decorator(reggi_login_required, name='dispatch')
class ChangePasswordView(View):
    """Allow an authenticated user to change their password.

    Validates the current password before setting the new one.
    Calls ``update_session_auth_hash`` so the user stays logged in
    after the change.
    """

    def get(self, request):
        return render(request, 'reggi/change_password.html', {'form': ChangePasswordForm()})

    def post(self, request):
        form = ChangePasswordForm(request.POST)
        if not form.is_valid():
            return render(request, 'reggi/change_password.html', {'form': form})

        if not request.user.check_password(form.cleaned_data['current_password']):
            form.add_error('current_password', 'Incorrect password.')
            return render(request, 'reggi/change_password.html', {'form': form})

        request.user.set_password(form.cleaned_data['new_password'])
        request.user.save()
        update_session_auth_hash(request, request.user)
        return render(request, 'reggi/change_password.html', {'form': ChangePasswordForm(), 'success': True})
