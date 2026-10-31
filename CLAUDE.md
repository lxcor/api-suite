# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

A monorepo of five independently-publishable Django apps (`lxcor-*` on PyPI) for building commercial-grade APIs, plus a shared `tools` package. Each subdirectory is its own Python package with its own `pyproject.toml`, migrations, tests, and `settings_test.py`.

## Commands

All commands are run from within the target app's subdirectory (e.g. `cd billa/`).

**Run all tests for an app:**
```bash
cd billa && pytest
```

**Run a single test file:**
```bash
cd kotta && pytest tests/test_tier_throttle.py
```

**Run a single test case or method:**
```bash
cd billa && pytest tests/test_fulfill_purchase.py::FulfillPurchaseTests::test_idempotent_returns_none
```

**Build a package for distribution:**
```bash
cd docca && python -m build
```

There is no project-wide test runner or lint configuration. Each app is tested independently.

## Architecture

### Dependency order

```
docca       (no suite deps)
reggi       (no suite deps)
kotta       → reggi
billa       → reggi, kotta
romma       → docca  (optional: billa, reggi)
tools       (utility commands, no runtime deps on suite apps)
```

Each `pyproject.toml` lists sibling app directories in `[tool.pytest.ini_options] pythonpath` so tests can import across packages without installing them.

### Authentication — `reggi`

`reggi.authentication.ApiKeyAuthentication` (DRF `BaseAuthentication`) resolves an incoming key to `(user, ApiKey)`, which becomes `(request.user, request.auth)` throughout the stack. Two header styles:
- Default: `Authorization: Bearer <key>`
- Alternative (`REGGI_AUTH_HEADER_STYLE = 'apikey'`): `X-Api-Key: <key>`

Key lookup uses a stored 8-character prefix for fast indexing, then hash + salt verification against all matching candidates.

Optional `REGGI_KEY_PREFIX` strips a project-specific prefix string before the lookup (e.g. `myproject_<actual_key>`).

### Throttle chain — `kotta` + `billa`

Throttles run in this order in DRF's `DEFAULT_THROTTLE_CLASSES`:

1. **`AnonEndpointThrottle`** — enforces `Endpoint.anonymous_limit` per IP. Sets `request.kotta_throttle_info` on block.
2. **`TierThrottle`** — enforces `TierEndpointLimit` per authenticated API key. Tier resolution: `api_key.tier` → `UserTier` → `Tier(is_default=True)`. Tracks both daily and monthly `UsageCounter` rows regardless of which window is enforced.
3. **`BillerThrottle`** — atomically decrements `CreditBalance.credits_remaining`. Skips deduction if `kotta_throttle_info` is already set on the request (i.e. kotta already blocked it). Raises HTTP 402 when credits are exhausted.

`KottaMiddleware` must appear after `AuthenticationMiddleware`; it attaches `request.kotta_ip` (respects `KOTTA_TRUST_PROXY_HEADERS` for X-Forwarded-For).

`kotta.exceptions.kotta_exception_handler` replaces the raw DRF throttle response with structured JSON including a human-readable `retry_after` message and optional `upgrade` link.

### Documentation — `docca`

`DocEndpoint` records are populated by `python manage.py syncdocs <app_label> [--all]`. Each run overwrites `title` and `subtitle` from view/method docstrings but **never overwrites `description`** (set once on first creation). Annotate views with:

```python
class MyViewSet(viewsets.ViewSet):
    docca_tag = 'Solar'
    docca_overview = 'Fallback description if no @description: tag in docstring.'
```

Docstrings support structured tags: `@title:`, `@subtitle:`, `@description:`.

`docca.views.get_manifest_data()` returns a plain dict of all published endpoints — used by `romma` to build the homepage and endpoint catalog without importing `docca` models directly.

### Billing — `billa`

Payment backends live in `billa/billa/backends/`: `StubPaymentBackend` (dev), `StripePaymentBackend`, `PayPalPaymentBackend`. Configured via `BILLA_PAYMENT_BACKEND`.

`billa.services.fulfill_purchase(user, provider, provider_session_id, credit_pack)` is the single entry point for completing a purchase. It is **idempotent** on `(provider, provider_session_id)` — safe to call from webhooks that may replay.

`billa.signals.attach_free_credits` fires on `ApiKey` post_save to attach a free `CreditBalance` from the `CreditPack(is_free_tier=True)` record. To suppress this for keys created during a purchase, set `api_key._from_purchase = True` before calling `save()` (as `fulfill_purchase` does).

### Landing page — `romma`

Calls `docca.views.get_manifest_data()` at request time to build the hero page (`/`) and endpoint catalog (`/endpoints/`). Navbar/footer fragments from `billa` and `reggi` are included with `{% try_include %}` — they render silently absent when those apps are not installed.

### Fixture management — `tools`

`python manage.py dumpsite` and `python manage.py loadsite` wrap Django's `dumpdata`/`loaddata` over the full ordered fixture list defined in `tools/tools/fixtures.py`. Output files go to `fixtures/<app_label>.<model_name>.json` in the calling project root.

`python manage.py syncendpoints` (kotta) discovers URL patterns and syncs the `Endpoint` table. Removed endpoints are marked `is_orphan=True` unless `--prune` is passed. Safe to run repeatedly.

### Sandbox — `sandbox/`

A small Django project at the repo root that wires all five apps together. Run all commands from inside `sandbox/`:

```bash
cd sandbox && pip install -r requirements.txt   # installs all suite apps as editable
cp ../.env.example ../.env && echo "DJANGO_DEBUG=1" > ../.env  # first-time setup
python manage.py migrate
python manage.py runserver
```

URL layout:
- `/` and `/endpoints/` — romma (landing page + endpoint catalog)
- `/account/` — reggi (register, login, API key management)
- `/usage/` — kotta (usage dashboard)
- `/docs/` — docca (documentation portal)
- `/pricing/`, `/billing/`, `/terms/` — billa (billing flows)
- `/admin/` — Django admin

Settings live in `sandbox/core/settings.py`. They load from `.env` at the repo root (see `.env.example`). SQLite is the default; set `DJANGO_DB_NAME` to switch to Postgres. `DJANGO_DEBUG=1` is all a fresh clone needs.

The `dumpsite`/`loadsite` and `syncdocs`/`syncendpoints` management commands all work from inside `sandbox/` because `tools` is in `INSTALLED_APPS`.

### CRC scripts

`crc_start.sh`, `crc_stop.sh`, and `crc_restart.sh` manage a tmux session that runs `claude --remote-control` for this project. Session name is `crc-api-suite`.
