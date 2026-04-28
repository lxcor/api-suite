# kotta

Throttling and quota enforcement for Django REST Framework.

`kotta` provides per-endpoint rate limits, tier-based quotas, and usage tracking. Tiers are database-driven so limits can be changed without a deployment. Integrates with `lxcor-reggi` API keys for per-key tracking.

Part of the [lxcor/api-suite](https://github.com/lxcor/api-suite).

## Install

```bash
pip install lxcor-kotta
```

## Setup

```python
# settings.py
INSTALLED_APPS = [
    ...
    'reggi',  # required
    'kotta',
]

MIDDLEWARE = [
    ...
    'kotta.middleware.KottaMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'kotta.throttle.AnonEndpointThrottle',
        'kotta.throttle.TierThrottle',
    ],
    'EXCEPTION_HANDLER': 'kotta.exceptions.kotta_exception_handler',
}
```

```python
# urls.py
urlpatterns = [
    path('usage/', include('kotta.urls')),
]
```

Sync your URL patterns into the kotta endpoint registry:

```bash
python manage.py syncendpoints
```

## Settings

| Setting | Default | Description |
|---|---|---|
| `KOTTA_UPGRADE_MESSAGE` | `''` | Message appended to 429 responses pointing users to upgrade |

## Management commands

| Command | Description |
|---|---|
| `syncendpoints` | Register all URL patterns in the kotta endpoint table |
| `dumpconfig` | Export tier and endpoint config to JSON |
| `loadconfig` | Import tier and endpoint config from JSON |

## License

MIT
