# romma

Hero landing page and endpoint catalog for Django APIs.

`romma` provides a ready-made hero landing page and a full endpoint catalog, wired directly to `lxcor-docca`'s manifest. Navbar and footer fragments from `lxcor-billa` and `lxcor-reggi` are included via `{% try_include %}` — they render when those apps are installed and are silently skipped when they are not.

Part of the [lxcor/api-suite](https://github.com/lxcor/api-suite).

## Install

```bash
pip install lxcor-romma
```

## Setup

```python
# settings.py
INSTALLED_APPS = [
    ...
    'docca',  # required
    'romma',
]

TEMPLATES = [{
    ...
    'OPTIONS': {
        'context_processors': [
            ...
            'romma.context_processors.home_settings',
        ],
    },
}]
```

```python
# urls.py
urlpatterns = [
    path('', include('romma.urls')),
]
```

## Settings

| Setting | Default | Description |
|---|---|---|
| `SITE_NAME` | `'API'` | Displayed in the navbar brand and hero title |
| `SITE_TAGLINE` | `'API'` | Browser `<title>` tagline |
| `SITE_DESCRIPTION` | `''` | Hero subtitle paragraph |
| `SITE_FREE_TIER_REQUESTS` | `''` | Free tier request count shown in the hero stats (e.g. `'1,000'`) |
| `DOCS_URL` | `None` | URL for the "Documentation" button in the hero; hidden if `None` |

## What it renders

- `/` — hero page with stats, per-app cards, and CTAs
- `/endpoints/` — full endpoint catalog with sidebar filter by app and tag
- `/robots.txt` — auto-generated with sitemap reference

## License

MIT
