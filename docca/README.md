# docca

API documentation portal for Django REST Framework.

`docca` auto-discovers your DRF viewsets and API views, syncs them into a database-backed manifest, and renders a searchable portal with tags, parameters, and response fields — no YAML, no decorators, no separate spec file.

Part of the [lxcor/api-suite](https://github.com/lxcor/api-suite).

## Install

```bash
pip install lxcor-docca
```

## Setup

```python
# settings.py
INSTALLED_APPS = [
    ...
    'docca',
]
```

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('docs/', include('docca.urls')),
]
```

Annotate your views:

```python
class MySunriseViewSet(viewsets.ViewSet):
    docca_tag = 'Solar'
    docca_overview = 'Returns sunrise and sunset times for a given location and date.'
```

Sync endpoints into the database:

```bash
python manage.py syncdocs
```

Visit `/docs/` to see the portal.

## Settings

| Setting | Default | Description |
|---|---|---|
| `DOCCA_APP_COLORS` | `{}` | Bootstrap color per app label (`'warning'`, `'danger'`, etc.) |
| `DOCCA_APP_DESCRIPTIONS` | `{}` | Product-facing description per app, shown on the portal |

## Management commands

| Command | Description |
|---|---|
| `syncdocs` | Discover and sync all DRF endpoints into the database |

## License

MIT
