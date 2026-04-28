"""Views for the home app — hero landing page and endpoint catalog."""

import hashlib

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from docca.views import get_manifest_data


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _path_segments(display_path):
    """Return non-param path segments as badge descriptors."""
    return [
        {'label': part}
        for part in display_path.split('/')
        if part and not part.startswith('{')
    ]


def _card_title(display_path):
    """Derive a human-readable card title from the last non-param URL segment.

    ``locci/geo/city/{city_id}/`` → ``City``
    ``astra/sun/rise-set/``      → ``Rise Set``
    """
    segments = [p for p in display_path.split('/') if p and not p.startswith('{')]
    if not segments:
        return ''
    return segments[-1].replace('-', ' ').replace('_', ' ').title()


def _app_badge_class(app_label):
    """Return Bootstrap badge classes for an app label."""
    palette = ['warning', 'danger', 'success', 'info']
    dark_bg = {'danger', 'success', 'info'}
    color_map = getattr(settings, 'DOCCA_APP_COLORS', {})
    if app_label in color_map:
        color = color_map[app_label]
    else:
        digest = int(hashlib.md5(app_label.encode()).hexdigest(), 16)
        color = palette[digest % len(palette)]
    text = 'text-white' if color in dark_bg else 'text-dark'
    return 'bg-%s %s' % (color, text)


def _enrich(ep):
    ep['path_segments'] = _path_segments(ep['display_path'])
    ep['app_badge_class'] = _app_badge_class(ep['app_label'])
    ep['card_title'] = _card_title(ep['display_path'])


# ---------------------------------------------------------------------------
# Hero home page
# ---------------------------------------------------------------------------

def robots_txt(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    body = (
        'User-agent: *\n'
        'Disallow: /admin/\n'
        'Disallow: /reggi/\n'
        'Disallow: /usage/\n'
        'Disallow: /billing/\n'
        'Allow: /\n'
        '\n'
        'Sitemap: %s\n' % sitemap_url
    )
    return HttpResponse(body, content_type='text/plain')


def home(request):
    manifest = get_manifest_data()
    app_descriptions = getattr(settings, 'DOCCA_APP_DESCRIPTIONS', {})

    # Build per-app summary from manifest data
    app_data = {}
    for group in manifest['groups']:
        for ep in group['endpoints']:
            label = ep['app_label']
            if label not in app_data:
                app_data[label] = {
                    'app_label': label,
                    'badge_class': _app_badge_class(label),
                    'description': app_descriptions.get(label, ''),
                    'endpoint_count': 0,
                    'tags': [],
                }
            app_data[label]['endpoint_count'] += 1
            if group['tag'] not in app_data[label]['tags']:
                app_data[label]['tags'].append(group['tag'])

    apps = sorted(app_data.values(), key=lambda a: (a['app_label'] == 'romma', a['app_label']))

    return render(request, 'romma/index.html', {
        'apps': apps,
        'total_endpoints': manifest['total_endpoints'],
    })


# ---------------------------------------------------------------------------
# Endpoint catalog
# ---------------------------------------------------------------------------

def endpoints(request):
    manifest = get_manifest_data()

    app_labels = sorted(
        {ep['app_label'] for group in manifest['groups'] for ep in group['endpoints']},
        key=lambda x: (x == 'romma', x),
    )

    for group in manifest['groups']:
        for ep in group['endpoints']:
            _enrich(ep)

    for ep in manifest['untagged']:
        _enrich(ep)

    return render(request, 'romma/endpoints.html', {
        'manifest': manifest,
        'app_labels': app_labels,
    })
