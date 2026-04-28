"""Admin configuration for DocParameterDef."""

from django.contrib import admin

from docca.models import DocParameterDef


@admin.register(DocParameterDef)
class DocParameterDefAdmin(admin.ModelAdmin):
    list_display = ['name', 'param_type', 'description']
    list_filter = ['param_type']
    search_fields = ['name', 'description']
    ordering = ('name',)
