"""Custom template filters for the dokks documentation portal."""

import hashlib
import re

from django import template
from django.conf import settings
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag('docca/_null.html', takes_context=True)
def try_include(context, template_name):
    """Include a template silently if it exists; render nothing if it does not.

    Equivalent to Jinja2's ``{% include ... ignore missing %}``, which
    Django's built-in ``{% include %}`` does not support.

    Usage::

        {% load docca_tags %}
        {% try_include "reggi/_navbar_user.html" %}
    """
    try:
        t = get_template(template_name)
        return {'content': mark_safe(t.render(context.flatten()))}
    except TemplateDoesNotExist:
        return {'content': ''}

_PARAM_RE = re.compile(r'\{([\w./\-]+)\}')

# Bootstrap color classes available for app badges.
# Excludes primary/secondary (reserved for GET/POST method badges).
_APP_BADGE_PALETTE = ['warning', 'danger', 'success', 'info']

# Colors that need white text for legibility (dark backgrounds).
_DARK_BG_COLORS = {'danger', 'success', 'info'}


@register.filter
def app_badge_class(app_label):
    """Return Bootstrap badge classes (bg + text color) for an app label.

    Reads ``DOCCA_APP_COLORS`` from settings for explicit assignments::

        DOCCA_APP_COLORS = {'astra': 'warning', 'locci': 'danger'}

    Any app not listed falls back to a stable deterministic color derived
    from the app name so new apps always get the same color without config.

    Usage::

        <span class="badge {{ ep.app_label|app_badge_class }}">
    """
    color_map = getattr(settings, 'DOCCA_APP_COLORS', {})
    if app_label in color_map:
        color = color_map[app_label]
    else:
        digest = int(hashlib.md5(app_label.encode()).hexdigest(), 16)
        color = _APP_BADGE_PALETTE[digest % len(_APP_BADGE_PALETTE)]
    text = 'text-white' if color in _DARK_BG_COLORS else 'text-dark'
    return 'bg-%s %s' % (color, text)

# Matches Django named URL groups: (?P<name>[^/.]+)
_NAMED_GROUP_RE = re.compile(r'\(\?P<(\w+)>[^)]+\)')


@register.filter
def clean_path(path):
    """Replace Django URL regex groups with human-readable {resource_id} tokens.

    ``(?P<pk>[^/.]+)`` is replaced using the preceding path segment so that
    e.g. ``timezone/(?P<pk>[^/.]+)/`` becomes ``timezone/{timezone_id}/``.
    Any other named group ``(?P<name>...)`` is replaced with ``{name}``.

    Usage::

        {{ ep.path|clean_path }}
    """
    def _replace(m):
        group_name = m.group(1)
        if group_name == 'pk':
            # Derive a descriptive name from the segment immediately before this group.
            preceding = path[:m.start()].rstrip('/')
            segment = preceding.rsplit('/', 1)[-1] if '/' in preceding else preceding
            return '{%s_id}' % segment
        return '{%s}' % group_name

    return _NAMED_GROUP_RE.sub(_replace, path)


@register.filter
def first_sentence(value):
    """Return the first sentence or line of a block of text.

    Splits on the first ``.`` followed by whitespace/end, or on the first
    newline — whichever comes first.  Strips trailing punctuation that would
    look odd as a standalone subtitle.

    Usage::

        {{ ep.overview|first_sentence }}
    """
    if not value:
        return ''
    text = value.strip()
    # Split on first newline
    newline_pos = text.find('\n')
    # Split on first ". " or ".\n" or end-of-string after a period
    sentence_match = re.search(r'\.\s', text)
    sentence_pos = sentence_match.start() + 1 if sentence_match else len(text)

    cut = min(
        newline_pos if newline_pos != -1 else len(text),
        sentence_pos,
    )
    return text[:cut].rstrip('.').strip()


@register.filter(needs_autoescape=True)
def codify_params(value, autoescape=True):
    """Wrap {param_name} tokens in <code> tags for inline display.

    Safe to use in templates: the surrounding text is escaped normally;
    only the generated <code> tags are marked safe.

    Usage::

        {{ field.description|codify_params }}
    """
    if autoescape:
        escaped = conditional_escape(value)
    else:
        escaped = value

    result = _PARAM_RE.sub(r'<code>\1</code>', escaped)
    return mark_safe(result)
