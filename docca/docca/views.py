"""Views for the dokks documentation portal."""

import re

from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from docca.models import DocEndpoint, DocTag

_NAMED_GROUP_RE = re.compile(r'\(\?P<(\w+)>[^)]+\)')


def _display_path(path):
    """Convert Django URL regex groups to human-readable {resource_id} tokens."""
    def _replace(m):
        group_name = m.group(1)
        if group_name == 'pk':
            preceding = path[:m.start()].rstrip('/')
            segment = preceding.rsplit('/', 1)[-1] if '/' in preceding else preceding
            return '{%s_id}' % segment
        return '{%s}' % group_name
    return _NAMED_GROUP_RE.sub(_replace, path)


def _first_sentence(text):
    """Return the first sentence or line of a block of text."""
    if not text:
        return ''
    text = text.strip()
    newline_pos = text.find('\n')
    m = re.search(r'\.\s', text)
    sentence_pos = m.start() + 1 if m else len(text)
    cut = min(newline_pos if newline_pos != -1 else len(text), sentence_pos)
    return text[:cut].rstrip('.').strip()


def _portal_order():
    """Return the published endpoint queryset in portal display order.

    Ordered by tag display order (nulls last), then path, then method —
    matching the grouping shown on the portal index.
    """
    return (
        DocEndpoint.objects
        .filter(published=True, is_orphan=False)
        .order_by(F('tag__order').asc(nulls_last=True), 'path', 'method')
    )


class PortalView(View):
    """Render the public API documentation portal.

    Displays all published, non-orphan endpoints grouped by tag.
    Untagged endpoints are collected under a fallback group rendered last.
    """

    def get(self, request):
        tags = DocTag.objects.prefetch_related('endpoints').all()
        tag_groups = []

        for tag in tags:
            endpoints = (
                tag.endpoints
                .filter(published=True, is_orphan=False)
                .order_by('path', 'method')
            )
            if endpoints.exists():
                tag_groups.append({'tag': tag, 'endpoints': endpoints})

        untagged = DocEndpoint.objects.filter(
            published=True,
            is_orphan=False,
            tag__isnull=True,
        ).order_by('path', 'method')

        app_labels = sorted(
            set(
                DocEndpoint.objects
                .filter(published=True, is_orphan=False)
                .values_list('app_label', flat=True)
            ),
            key=lambda x: (x == 'home', x),
        )

        return render(request, 'docca/portal.html', {
            'tag_groups': tag_groups,
            'untagged': untagged,
            'app_labels': app_labels,
        })


class EndpointDetailView(View):
    """Render the detail page for a single published API endpoint."""

    def get(self, request, slug):
        ep = get_object_or_404(DocEndpoint, slug=slug, published=True, is_orphan=False)

        slugs = list(_portal_order().values_list('slug', flat=True))
        idx = slugs.index(ep.slug)
        prev_ep = DocEndpoint.objects.get(slug=slugs[idx - 1]) if idx > 0 else None
        next_ep = DocEndpoint.objects.get(slug=slugs[idx + 1]) if idx < len(slugs) - 1 else None

        return render(request, 'docca/endpoint_detail.html', {
            'ep': ep,
            'prev_ep': prev_ep,
            'next_ep': next_ep,
        })


def get_manifest_data():
    """Build and return the manifest payload as a plain dict.

    Shared between ManifestView (JSON response) and any other app that needs
    to consume endpoint data without direct model imports from dokks.
    """
    groups = []

    for tag in DocTag.objects.order_by('order', 'name'):
        endpoints = (
            DocEndpoint.objects
            .filter(tag=tag, published=True, is_orphan=False)
            .order_by('path', 'method')
        )
        if not endpoints.exists():
            continue
        groups.append({
            'tag': tag.name,
            'tag_slug': tag.slug,
            'tag_description': tag.description,
            'endpoints': [_endpoint_dict(ep) for ep in endpoints],
        })

    untagged = (
        DocEndpoint.objects
        .filter(published=True, is_orphan=False, tag__isnull=True)
        .order_by('path', 'method')
    )

    return {
        'generated': timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_endpoints': sum(len(g['endpoints']) for g in groups) + untagged.count(),
        'groups': groups,
        'untagged': [_endpoint_dict(ep) for ep in untagged],
    }


def _endpoint_dict(ep):
    return {
        'pk': ep.pk,
        'path': ep.path,
        'display_path': _display_path(ep.path),
        'method': ep.method,
        'app_label': ep.app_label,
        'subtitle': _first_sentence(ep.overview) or ep.summary,
        'detail_url': '/docs/endpoint/%s/' % ep.slug,  # noqa: keep literal, avoids reverse import cycle
    }


class ManifestView(View):
    """Serve a JSON manifest of all published API endpoints.

    Designed for consumption by external or loosely-coupled apps (e.g. a home
    page catalog) without requiring direct model imports from dokks.

    URL: /docs/manifest.json
    """

    def get(self, _request):
        return JsonResponse(get_manifest_data())
