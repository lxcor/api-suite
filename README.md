# api-suite

A suite of reusable Django apps for building commercial-grade APIs.

Each app is independently installable from PyPI and designed to work together.
See [lxcor/calendula](https://github.com/lxcor/calendula) for a full reference implementation.

## Apps

| App | PyPI | Description |
|-----|------|-------------|
| [docca](docca/) | `pip install lxcor-docca` | API documentation portal — auto-syncs DRF endpoints into a searchable portal |
| [reggi](reggi/) | `pip install lxcor-reggi` | API key management and user identity — registration, verification, key rotation |
| [kotta](kotta/) | `pip install lxcor-kotta` | Throttling and quota enforcement — per-endpoint limits, tier-based quotas |
| [billa](billa/) | `pip install lxcor-billa` | Credit-based billing — Stripe, PayPal, and stub backends, credit pack catalogue |
| [romma](romma/) | `pip install lxcor-romma` | Hero landing page and endpoint catalog — wires docca's manifest into a ready-made portal |

## Dependency order

```
docca       (no suite deps)
reggi       (no suite deps)
kotta       → reggi
billa       → reggi, kotta
romma       → docca  (optional: billa, reggi)
```

## License

MIT — see each app's `LICENSE` file.