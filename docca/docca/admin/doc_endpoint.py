"""Admin configuration for DocEndpoint and DocParameter."""

from django.contrib import admin

from docca.models import DocEndpoint, DocParameter, DocResponseField


class DocParameterInline(admin.TabularInline):
    model = DocParameter
    extra = 1
    fields = ['param_def', 'location', 'required', 'description_override', 'example']
    readonly_fields = []
    autocomplete_fields = ['param_def']


class DocResponseFieldInline(admin.TabularInline):
    model = DocResponseField
    extra = 1
    fields = ['name', 'data_type', 'nullable', 'description', 'example']
    readonly_fields = ['name', 'data_type', 'nullable']


@admin.register(DocEndpoint)
class DocEndpointAdmin(admin.ModelAdmin):
    list_display = ['method', 'path', 'app_label', 'tag', 'published', 'is_orphan']
    list_filter = ['method', 'app_label', 'published', 'is_orphan', 'tag']
    search_fields = ['path', 'view_name', 'summary']
    readonly_fields = ['path', 'method', 'view_name', 'app_label', 'is_orphan', 'created_at', 'updated_at']
    fields = [
        'path', 'method', 'view_name', 'app_label',
        'overview',
        'summary', 'description',
        'tag', 'published', 'is_orphan',
        'created_at', 'updated_at',
    ]
    inlines = [DocParameterInline, DocResponseFieldInline]
    actions = ['publish_selected', 'unpublish_selected']

    def publish_selected(self, request, queryset):
        updated = queryset.update(published=True)
        self.message_user(request, '%d endpoint(s) published.' % updated)
    publish_selected.short_description = 'Publish selected endpoints'

    def unpublish_selected(self, request, queryset):
        updated = queryset.update(published=False)
        self.message_user(request, '%d endpoint(s) unpublished.' % updated)
    unpublish_selected.short_description = 'Unpublish selected endpoints'
