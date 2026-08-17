# Project Architecture Blueprint

**Version:** 3.4.1
**Project:** Human Design API (`humandesign-api`)
**Scope:** Reflects the code as it exists in this repository. Every module, endpoint and
dependency listed below was verified against source before writing.

---

## 1. Technology Stack

| Concern | Choice |
|---|---|
| Language | Python, `requires-python = ">=3.12"` |
| Web framework | FastAPI (`>=0.115.0`) |
| ASGI server | Uvicorn 0.27.1, single worker |
| Validation | Pydantic v2 (`>=2.7.0`) |
| Templating | Jinja2 — admin panel HTML |
| Astronomy engine | `pysweph` (Swiss Ephemeris), compressed JPL DE431 `.se1` files |
| Numerics | NumPy 2.1.2, pandas 2.2.3 |
| Geocoding | `geopy` |
| Timezones | `timezonefinder` (singleton), `tzdata` |
| Reference data | SQLite — `hd_data.sqlite` |
| Auth store | SQLite — `api_auth.db`, created at runtime |
| Packaging | setuptools, PEP 621 metadata in `pyproject.toml` |
| Containerization | Docker multi-stage build, Docker Compose |

There is **no** visualization or chart-rendering dependency in the runtime stack.
`matplotlib`, `svgpath2mpl` and `Pillow` appear only under `[project.optional-dependencies].dev`
and are not imported by any module under `src/`.

---

## 2. Architectural Pattern

**Layered modular monolith.** A single FastAPI application composed of four routers, backed by a
service layer, a pure calculation core, and a set of stateless utilities.

```
HTTP ──► routers/ ──► services/ ──► features/ ──► pysweph + ephe/*.se1
                 │           │
                 │           └──► sqlite_repository ──► hd_data.sqlite
                 └──► auth.py ──────────────────────► api_auth.db
```

**Guiding properties observed in the code**

1. **Stateless request handling.** No session state between calls; the only mutable state is the
   auth/logging database.
2. **Calculation core isolated from transport.** `features/` imports nothing from `routers/`.
3. **Lazy service loading.** `enrichment`, `dream_rave` and `global_cycles` are imported inside the
   `/v2/calculate` handler body, not at module import time.
4. **Payload shaping at the edge.** Recursive dot-notation masking is applied to the finished
   response dictionary, not threaded through the calculation.

---

## 3. Component Map

### 3.1 Application root — `src/humandesign/`

| Module | Responsibility |
|---|---|
| `api.py` | Builds the `FastAPI` app, mounts `/static`, registers four routers, installs two middlewares |
| `auth.py` | Bearer-token auth, site registry, request logging, statistics. Owns `api_auth.db` |
| `dependencies.py` | Backward-compatible shim; re-exports `verify_token` and `security` from `auth.py` |
| `hd_constants.py` | Static domain maps — energy types, centers, channels, gate metadata |

**Middleware chain** (`api.py`)

- `security_headers_middleware` — sets `X-Frame-Options: SAMEORIGIN` and `X-Content-Type-Options: nosniff`. Defence in depth; Nginx sets the same headers upstream.
- `log_requests_middleware` — measures elapsed time and writes a row via `auth.log_request`, but **only** when `request.state.site_id` was set by `verify_token`. Unauthenticated traffic is not logged.

**CORS** is opt-in. Absent `CORS_ORIGINS`, no CORS middleware is added at all — same-origin only.

### 3.2 Transport layer — `routers/`

| Module | Prefix | Endpoints |
|---|---|---|
| `general.py` | — | `GET /health`, `GET /calculate` |
| `v2/general.py` | `/v2` | `POST /v2/calculate` |
| `admin.py` | `/admin` | `POST|GET /sites`, `PUT|DELETE /sites/{site_id}`, `GET /stats` |
| `panel.py` | — | 14 routes under `/panel` — HTML views plus a JSON sub-API |

`panel.py` serves the operator UI: `login`, `logout`, `dashboard`, `sites`, `calculator`, `logs`,
`settings`, and a JSON surface at `/panel/api/*` for site CRUD, log retrieval and admin-token
rotation.

### 3.3 Service layer — `services/`

| Module | Status | Responsibility |
|---|---|---|
| `masking.py` | Live | `OutputMaskingService` — recursive dot-notation `include`/`exclude` filtering |
| `enrichment.py` | Live | `EnrichmentService` — resolves gate and line codes to human-readable text |
| `sqlite_repository.py` | Live | Singleton reader over `hd_data.sqlite` (`public_gates`, `public_gate_lines`) |
| `geolocation.py` | Live | Geocoding, reverse geocoding, batch geocoding, distance |
| `dream_rave.py` | Live | `DreamRaveEngine` — design-side mechanics |
| `global_cycles.py` | Live | `GlobalCycleEngine` — cycle mechanics |

The relational service that once backed `/analyze/*` was removed together with those endpoints.
Penta and composite-combination logic still lives in `features/core.py` (`get_penta`,
`hd_composite`, `get_composite_combinations`) and is covered by `tests/test_penta.py`.

### 3.4 Calculation core — `features/`

| Module | Contents |
|---|---|
| `core.py` | `hd_features` class, `hd_composite` class, single- and multi-chart calculation, Penta, composite combinations. Configures the Swiss Ephemeris path at import time |
| `mechanics.py` | System rules — authority, energy type, definition, channels and active centers |
| `attributes.py` | Derived attributes — incarnation cross, quarter, profile, variables, line counts, yin/yang balance, sun roles, lunar phase |

**Ephemeris resolution** (`core.py`, at import): `SE_EPHE_PATH` env var → bundled `ephe/` directory.
A directory named by `SE_EPHE_PATH` that does not exist is logged and ignored. If neither source
yields a directory, the module raises `RuntimeError` under `ENVIRONMENT=production` and otherwise
logs a warning before continuing in Moshier mode.

**Thread affinity.** `swe_set_ephe_path` is thread-local in this build of pysweph, and FastAPI runs
non-async path operations in an anyio worker thread. A path applied only at import time is therefore
invisible to request handlers. `ensure_ephe_path()` re-applies it and is called from
`hd_features.__init__` and from the health probe. Removing those calls reintroduces a measured
divergence in the Variables arrows on roughly 5% of charts, guarded by
`tests/test_ephemeris_threading.py`.

### 3.5 Utilities — `utils/`

`astrology.py` (zodiac sign from solar longitude) · `calculations.py` (transit processing, native-type
sanitization, transit metadata) · `date_utils.py` (ISO conversion, age) · `health_utils.py`
(Swiss Ephemeris health probe) · `serialization.py` (incarnation-cross map, profile name, gates and
channels JSON shaping) · `version.py` (reads version from `pyproject.toml`).

### 3.6 Contracts — `schemas/`

`general.py` — `HealthResponse`, the v1 health shape.
`v2/calculate.py` — 19 models forming the v2 response tree: `GeneralSectionV2`, `GatesV2`,
`CentersV2`, `AnalyticsSectionV2`, `AdvancedSectionV2` and leaves. Fields are `Optional` so that
`response_model_exclude_none=True` yields sparse output.

---

## 4. Request Flow — `POST /v2/calculate`

1. **Auth.** `verify_token` resolves the bearer token to a site, sets `request.state.site_id`.
2. **Validation.** Pydantic parses `CalculateRequestV2`. Every field has a default, so an empty body is accepted.
3. **Location.** Supplied `latitude`/`longitude` are used as-is; otherwise `place` is geocoded. Timezone comes from the `timezonefinder` singleton.
4. **Offset.** UTC offset derived from the zone with DST respected.
5. **Astronomy.** Swiss Ephemeris computes planetary longitudes for personality and design times.
6. **Rave transformation.** Longitudes mapped to gates, lines, colors and tones.
7. **Mechanics.** Channels, active centers, energy type, authority and definition derived.
8. **Attributes.** Profile, incarnation cross, variables, quarter, line counts, sun roles, lunar phase.
9. **Enrichment.** `EnrichmentService` resolves codes to names via `hd_data.sqlite`.
10. **Advanced.** `DreamRaveEngine` and `GlobalCycleEngine` run when requested.
11. **Masking.** `OutputMaskingService` applies the `include`/`exclude` tree.
12. **Egress.** `CalculateResponseV2` serialized with `exclude_none`.
13. **Logging.** Middleware records endpoint, method, status and elapsed milliseconds.

`GET /calculate` follows the same path through step 8, then returns the v1 shape without masking.

---

## 5. Cross-Cutting Concerns

**Authentication.** Two distinct bearer identities. `verify_token` validates per-site tokens from
`api_auth.db` and guards the calculation endpoints. `verify_admin` validates `HD_ADMIN_TOKEN` and
guards `/admin/*` and panel mutations. `GET /health` is unauthenticated by design — the Docker
healthcheck calls it.

**Configuration.** Environment-driven: `HD_ADMIN_TOKEN`, `ENVIRONMENT`, `SE_EPHE_PATH`,
`AG_DATA_DIR`, `AG_ENV_PATH`, `CORS_ORIGINS`. `.env` is git-ignored; `.env_example` is the template.

**Observability.** `GET /health` reports three dependencies: the Swiss Ephemeris mode via
`health_utils`, the writable auth database, and the read-only reference database. It answers
`degraded` if either database is unreachable — `hd_data.sqlite` is checked explicitly because
`/v2/calculate` fails without it while `api_auth.db` stays healthy. Per-request logging lands in
`api_auth.db` and is surfaced at `/panel/logs` and `/panel/api/logs`.

**Data separation.** `hd_data.sqlite` is reference data, mounted read-only. `api_auth.db` is mutable
runtime state, created under `AG_DATA_DIR` on a writable volume.

---

## 6. Deployment

Multi-stage Docker build. Stage 1 compiles C extensions with `gcc`/`g++`; stage 2 is a clean
`python:3.12-slim` runtime that copies only the built packages. Runs as non-root `appuser` (uid
1000). `PYTHONPATH=/app/src`, so the package resolves without installation.

Entrypoint: `uvicorn humandesign.api:app --host 0.0.0.0 --port 9021 --workers 1`

Compose binds to `127.0.0.1:9021` — not publicly exposed; a reverse proxy is expected in front.
Limits: 1 GB memory, 1 CPU. Logs rotate at 10 MB × 3 files. Healthcheck polls `/health` every 30 s
after a 15 s grace period. Volumes: `./data` writable, `hd_data.sqlite` read-only.

`setup_ubuntu.sh` performs a bare-metal install and verifies the ephemeris mode at the end. It does
**not** download ephemeris files — `ephe/` ships in the repository and is the only source.

---

## 7. Extending the System

1. **Schema first.** Add or extend models in `schemas/` — `v2/calculate.py` for v2 responses.
2. **Pure logic.** Implement calculation as free functions in `features/`, with no FastAPI imports.
3. **Orchestration.** If the work spans several concerns or touches I/O, place it in `services/`.
4. **Transport.** Register the route on an existing router, or add a router and include it in `api.py`.
5. **Regenerate the contract.** `openapi.yaml` is a dump of `app.openapi()`. Regenerate it rather
   than editing by hand, otherwise the spec and the code drift apart.
6. **Test.** `tests/` holds 17 modules covering calculation parity, schema shape, v2 behaviour,
   variables, Penta, health and ephemeris thread affinity.

---

## 8. Known Constraints

| Item | Detail |
|---|---|
| Demo defaults on inputs | All birth parameters default to a fixed date and place, so a parameter-less request returns a plausible chart rather than a validation error |
| Single worker | `--workers 1`; horizontal scaling requires multiple containers behind the proxy |
| Moshier permitted outside production | Development and test runs continue without `ephe/`, so a local result can differ from a production one |
| Reference database path | Resolved from the project root, overridable with `HD_DATA_PATH`. Moving `hd_data.sqlite` without setting that variable breaks `/v2/calculate` |
