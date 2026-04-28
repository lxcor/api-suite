"""Admin configuration for DocTag."""

from django.contrib import admin

from docca.models import DocTag


@admin.register(DocTag)
class DocTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
