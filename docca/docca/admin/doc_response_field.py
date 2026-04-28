"""Admin configuration for DocResponseField."""

from django.contrib import admin

from docca.models import DocResponseField


class DocResponseFieldInline(admin.TabularInline):
    model = DocResponseField
    extra = 1
    fields = ['name', 'data_type', 'nullable', 'description', 'example']
    readonly_fields = ['name', 'data_type', 'nullable']
