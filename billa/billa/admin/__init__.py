"""Django admin registrations for biller models."""

from django.contrib import admin

from billa.models import CreditBalance, CreditPack, Purchase


@admin.register(CreditBalance)
class CreditBalanceAdmin(admin.ModelAdmin):
    list_display = ('api_key', 'credits_remaining', 'is_default', 'created_at', 'updated_at')
    list_filter = ('is_default',)
    search_fields = ('api_key__user__username', 'api_key__name')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('api_key',)


@admin.register(CreditPack)
class CreditPackAdmin(admin.ModelAdmin):
    list_display = ('name', 'credits', 'price', 'tier', 'is_active', 'is_free_tier')
    list_filter = ('is_active', 'is_free_tier')
    search_fields = ('name',)
    raw_id_fields = ('tier',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'credits_granted', 'provider_session_id', 'created_at')
    list_filter = ('provider',)
    search_fields = ('user__username', 'provider_session_id')
    readonly_fields = ('provider', 'provider_session_id', 'credits_granted', 'created_at')
    raw_id_fields = ('user', 'credit_balance')
