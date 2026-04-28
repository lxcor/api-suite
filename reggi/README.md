# reggi

API key management and user identity for Django.

`reggi` provides registration, email verification, login, password reset, API key issuance and rotation, and tier assignment — everything needed to get users authenticated and issuing API requests.

Part of the [lxcor/api-suite](https://github.com/lxcor/api-suite).

## Install

```bash
pip install lxcor-reggi
```

## Setup

```python
# settings.py
INSTALLED_APPS = [
    ...
    'reggi',
]
```

```python
# urls.py
urlpatterns = [
    path('reggi/', include('reggi.urls')),
]
```

## Settings

| Setting | Default | Description |
|---|---|---|
| `REGGI_SITE_NAME` | `'API'` | Site name shown in emails and the navbar |
| `REGGI_AUTO_ISSUE_KEY` | `False` | Auto-issue a free API key named "Default" on registration |
| `REGGI_DOCS_URL` | `None` | URL shown as "Docs" link in the user navbar dropdown |
| `REGGI_USAGE_URL` | `None` | URL shown as "Usage" link in the user navbar dropdown |

## Features

- Registration with email verification
- Login / logout / password reset
- API key creation, rotation, and revocation
- Tier assignment per key (integrates with `lxcor-kotta`)
- `reggi_login_required` decorator for protecting views
- `{% include "reggi/_navbar_user.html" %}` — drop-in navbar fragment

## License

MIT
