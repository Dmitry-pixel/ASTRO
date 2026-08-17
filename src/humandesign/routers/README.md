# API Routers

This directory (`src/humandesign/routers`) contains the `FastAPI` router modules that define the
application's HTTP endpoints. All four routers are registered in `api.py`.

## Modules

- **[`general.py`](general.py)** — v1 surface, no prefix, tag `general`:
    - `GET /health`: Swiss Ephemeris mode plus both SQLite databases. Unauthenticated; used by the Docker healthcheck. Answers `degraded` if either database is unreachable.
    - `GET /calculate`: Full chart calculation. Query parameters, bearer auth. `year`, `month`, `day`, `hour` and `minute` are required, as is `place` unless both `latitude` and `longitude` are given.
- **[`v2/general.py`](v2/general.py)** — prefix `/v2`, tag `v2`:
    - `POST /v2/calculate`: High-fidelity nested response with recursive `include`/`exclude` masking. Bearer auth.
- **[`admin.py`](admin.py)** — prefix `/admin`, tag `admin`, admin token required:
    - `POST /admin/sites`, `GET /admin/sites`: Register and list API consumer sites.
    - `PUT /admin/sites/{site_id}`, `DELETE /admin/sites/{site_id}`: Update and remove a site.
    - `GET /admin/stats`: Usage statistics.
- **[`panel.py`](panel.py)** — operator web panel, tag `panel`, Jinja2 templates from `../templates/panel/`:
    - HTML views: `GET /panel`, `/panel/login`, `/panel/dashboard`, `/panel/sites`, `/panel/calculator`, `/panel/logs`, `/panel/settings`; `POST /panel/login`; `GET /panel/logout`.
    - JSON sub-API: `POST /panel/api/sites`, `PUT|DELETE /panel/api/sites/{site_id}`, `GET /panel/api/logs`, `PUT /panel/api/settings/token`.

## Notes

- Every operation carries a tag, so Swagger UI groups them instead of dropping routes into `default`.
- Authentication lives in `../auth.py`. `verify_token` guards the calculation endpoints and sets
  `request.state.site_id`, which the logging middleware in `api.py` depends on. `verify_admin`
  guards `/admin/*` and the panel mutations.
- `../dependencies.py` is a compatibility shim re-exporting `verify_token`; new code should import
  from `auth.py` directly.
- `openapi.yaml` at the repository root is generated from `app.openapi()`. Regenerate it after
  changing any route signature instead of editing it by hand.
