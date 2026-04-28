"""URL configuration for the reggi identity management app."""

from django.urls import path

from reggi.views import (
    ApiKeyCreateView,
    ApiKeyRevokeView,
    ChangePasswordView,
    DashboardView,
    EmailVerificationView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
    ProfileView,
    RegisterView,
    ResendVerificationView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='reggi.register'),
    path('login/', LoginView.as_view(), name='reggi.login'),
    path('logout/', LogoutView.as_view(), name='reggi.logout'),
    path('keys/', DashboardView.as_view(), name='reggi.dashboard'),
    path('keys/create/', ApiKeyCreateView.as_view(), name='reggi.key_create'),
    path('keys/<int:pk>/revoke/', ApiKeyRevokeView.as_view(), name='reggi.key_revoke'),
    path('password/reset/', PasswordResetView.as_view(), name='reggi.password_reset'),
    path('password/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='reggi.password_reset_confirm'),
    path('verify/<uidb64>/<token>/', EmailVerificationView.as_view(), name='reggi.email_verify'),
    path('verify/resend/', ResendVerificationView.as_view(), name='reggi.email_verify_resend'),
    path('profile/', ProfileView.as_view(), name='reggi.profile'),
    path('profile/password/', ChangePasswordView.as_view(), name='reggi.change_password'),
]
