# Human Design API — Project Context for AI Assistants

## Project Overview
**Astro Gates — Human Design API**
Server-rendered Python/FastAPI application with vanilla JS frontend.
No React/Vue/Angular — Jinja2 + vanilla JS. Tailwind is compiled at build
time and served from `/static/vendor/`; nothing is fetched from a CDN.
Single-command deploy via `deploy.sh` (Docker + Nginx + SSL).
SQLite databases: `api_auth.db` (auth/logging), `hd_data.sqlite` (HD reference data).
Swiss Ephemeris integration for astrological calculations.

## Architecture

```
Client → Nginx (:80/:443) → Docker (127.0.0.1:9021) → uvicorn (1 worker) → FastAPI

Volume: ./data:/app/data  (api_auth.db, .env — persistent, writable)
Baked:  /app/ephe/         (ephemeris .se1 files — read-only, in image)
Baked:  /app/hd_data.sqlite (HD reference DB — read-only, in image)
```

### Key Design Decisions
- **SSR over SPA**: Faster development, no build step, no npm
- **No HTMX**: it was loaded on every panel page and never used — zero `hx-*`
  attributes. All panel AJAX is `fetch()`. Removed in 3.5.1.
- **1 uvicorn worker**: In-memory sessions and ADMIN_TOKEN don't sync across workers
- **Docker multi-stage build**: gcc/g++ in builder only, slim runtime image
- **SQLite in production**: Simple, file-based, easy backups
- **Nginx reverse proxy**: SSL termination, rate limiting (10 req/s), security headers
- **PYTHONPATH over pip install**: `ENV PYTHONPATH="/app/src"` — simpler than setuptools in Docker

## Tech Stack
| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, Pydantic v2, Uvicorn |
| **Auth DB** | SQLite (`data/api_auth.db`) — sites, tokens, request logs |
| **Reference DB** | SQLite (`hd_data.sqlite`) — gate names, line descriptions, planet info |
| **Astrology** | Swiss Ephemeris (`pysweph`), `timezonefinder`, `geopy` (Nominatim) |
| **Data Processing** | `pandas`, `numpy`, `python-dateutil` |
| **Frontend** | Jinja2 templates, TailwindCSS (compiled, self-hosted), Chart.js (self-hosted), Vanilla JS |
| **Infra** | Docker, Docker Compose, Nginx, Certbot (Let's Encrypt) |

## Directory Structure

```
project-root/
├── src/humandesign/
│   ├── api.py                  # FastAPI app, CORS, security headers middleware
│   ├── auth.py                 # SQLite CRUD, sessions, set_admin_token(), verify_token/admin
│   ├── dependencies.py         # FastAPI dependency: verify_token
│   ├── hd_constants.py         # HD constants (gates, channels, types, chakras)
│   ├── routers/
│   │   ├── general.py          # /health, /calculate (v1)
│   │   ├── v2/general.py       # POST /v2/calculate (with analytics section)
│   │   ├── analyze.py          # /analyze/composite, /penta, /wa, /maia-penta
│   │   ├── admin.py            # /admin/sites CRUD, /admin/stats
│   │   └── panel.py            # /panel/* web UI + internal JSON API
│   ├── schemas/                # Pydantic models (HealthResponse, CalculateResponseV2, etc.)
│   ├── relational/             # Dyad / Penta / WA analysis (3.5.0)
│   │   ├── semantics.py        # Semantic tables, EN + RU, machine codes
│   │   ├── persons.py          # One birth-data resolution path for /analyze/*
│   │   ├── engine.py           # Composite: 4 Maia classes over all 36 channels
│   │   └── groups.py           # Penta 2.0 wrapper + group-field aggregate
│   ├── services/
│   │   ├── enrichment.py       # Gate/line/channel enrichment from hd_data.sqlite
│   │   ├── sqlite_repository.py # Read-only access to hd_data.sqlite
│   │   ├── geolocation.py      # Nominatim geocoding + TimezoneFinder
│   │   └── masking.py          # Output field filtering (include/exclude)
│   ├── features/
│   │   ├── core.py             # calc_single_hd_features, Swiss Ephemeris calls
│   │   ├── attributes.py       # Incarnation cross, profile, variables
│   │   └── mechanics.py        # Channels, centers, definition logic (numpy)
│   ├── utils/
│   │   ├── calculations.py     # Date/time conversions, Julian Day
│   │   ├── date_utils.py       # Birth date parsing
│   │   ├── health_utils.py     # check_swisseph_health()
│   │   ├── serialization.py    # JSON serialization helpers
│   │   └── version.py          # Version detection from pyproject.toml
│   ├── templates/panel/        # 9 Jinja2 templates (base, login, dashboard, calculator,
│                               _relational, _relational_js, ...)
│   └── static/                 # favicon.ico + vendor/ (tailwind.min.css, chart.umd.min.js)
├── ephe/                       # Swiss Ephemeris .se1 files (baked into Docker image)
├── hd_data.sqlite              # HD reference DB (baked into Docker image, read-only)
├── data/                       # PERSISTENT VOLUME (mounted in Docker)
│   ├── api_auth.db             # Auth DB (auto-created on first start)
│   └── .env                    # Runtime config (copied from root .env on first deploy)
├── docker-compose.yml          # Service config, volumes, healthcheck, resource limits
├── Dockerfile                  # Multi-stage: builder (gcc) → runtime (slim + curl)
├── deploy.sh                   # One-command deploy: Docker + Nginx + optional SSL
├── requirements.txt            # Production deps only (all pinned ==)
├── requirements-dev.txt        # Dev deps (pytest, ruff, ipython, matplotlib)
├── pyproject.toml              # Package metadata, optional-dependencies
├── .env                        # Default config (HD_ADMIN_TOKEN=12345)
├── .env_example                # Template for environment variables
├── .dockerignore               # Excludes .env, *.db (except !hd_data.sqlite), tests, etc.
├── .gitignore                  # Excludes data/, .env, api_auth.db, __pycache__
├── CLAUDE.md                   # This file
└── tests/                      # 19 test files (pytest + httpx TestClient)
```

## Environment Variables (.env)

```env
# Authentication (CHANGE DEFAULT 12345 BEFORE PRODUCTION!)
HD_ADMIN_TOKEN=12345

# Environment: production | development (controls uvicorn reload)
ENVIRONMENT=production

# Ephemeris path (read-only, baked into Docker image)
SE_EPHE_PATH=/app/ephe

# Data directory for persistent files (SQLite + .env)
# Docker: /app/data (mounted volume). Local: project root (default).
# AG_DATA_DIR=/app/data
# AG_ENV_PATH=/app/data/.env

# CORS (optional, empty = disabled = same-origin only)
# CORS_ORIGINS=https://mysite.com,https://app.mysite.com
```

## Critical Implementation Details

### Authentication Flow
- Admin logs in via `/panel/login` with `HD_ADMIN_TOKEN`
- Session stored in-memory dict `_sessions` (panel.py) — lost on restart
- `set_admin_token()` updates global var + rewrites `data/.env`
- `verify_admin()` reads via `globals()["ADMIN_TOKEN"]` for live updates
- Site tokens verified via `get_site_by_token()` → SQLite lookup

### Why 1 Worker
`--workers 1` in Dockerfile. With 2+ workers:
- In-memory sessions don't sync → user gets logged out randomly
- `ADMIN_TOKEN` update in one worker invisible to others
- To scale: move sessions to Redis, read token from DB/file per-request

### Ephemeris Files
- 4 files in `ephe/` (2.1 MB total): `seas_18.se1`, `semo_18.se1`, `sepl_18.se1`, `sefstars.txt`
- Baked into Docker image via `COPY . /app` (NOT in volume)
- `.dockerignore` has `!ephe/` to ensure inclusion
- `features/core.py` reads `SE_EPHE_PATH` env var with fallback to relative path

### hd_data.sqlite (Reference Database)
- Read-only SQLite with gate names, line descriptions, planet info
- Used by `services/sqlite_repository.py` and `services/enrichment.py`
- Baked into Docker image (`.dockerignore` has `!hd_data.sqlite`)
- Path: relative to working directory (`/app/hd_data.sqlite` in Docker)

### Database Connections
- All functions in `auth.py` use `try/finally: conn.close()` pattern
- No connection pooling — new connection per request (fine for SQLite)
- `_get_db()` returns `sqlite3.Connection` with `row_factory=sqlite3.Row`

### Security
- Port 9021 bound to `127.0.0.1` only (not accessible from internet)
- Non-root `appuser` (UID 1000) in Docker
- XSS: tokens escaped via `| tojson` (settings) and `data-*` attributes (sites)
- CORS disabled by default, configurable via `CORS_ORIGINS` env
- Security headers in both Nginx and FastAPI middleware
- `.env` and `data/` in `.gitignore`

### Docker Build
- Multi-stage: `python:3.12-slim` builder (gcc, g++) → runtime (slim + curl)
- `PYTHONPATH="/app/src"` — no `pip install .` needed
- `PYTHONUNBUFFERED=1` for instant log output
- Healthcheck in `docker-compose.yml` only (not duplicated in Dockerfile)
- Resource limits: `mem_limit: 1g`, `cpus: 1.0`
- Log rotation: `max-size: 10m`, `max-file: 3`

## Common Commands

### Development
```bash
# Run locally (with reload)
PYTHONPATH=src uvicorn humandesign.api:app --host 0.0.0.0 --port 9021 --reload

# Run tests
pytest

# Lint
ruff check src/

# Build Docker image
docker build -t humandesign-api .

# Run container locally
docker run -p 9021:9021 --env-file .env humandesign-api
```

### Deploy to fresh VPS
```bash
scp humandesign_api_ubuntu_final.tar.gz root@IP:~
ssh root@IP
tar xzf humandesign_api_ubuntu_final.tar.gz
cd humandesign_api
bash deploy.sh              # HTTP only
bash deploy.sh domain.com   # HTTP + HTTPS
```

### Production / Ops
```bash
# View logs
docker logs -f humandesignapi
sudo tail -f /var/log/nginx/access.log

# Restart services
docker restart humandesignapi
sudo systemctl reload nginx

# Rebuild after code changes
docker compose build --no-cache
docker compose up -d

# Backup database
cp data/api_auth.db backups/api_auth.db.$(date +%F).bak

# Check health
docker inspect --format='{{.State.Health.Status}}' humandesignapi
curl -s http://127.0.0.1:9021/health | python3 -m json.tool

# Update & redeploy
git pull
bash deploy.sh your-domain.com
```

### Debugging
```bash
# Enter running container
docker exec -it humandesignapi /bin/bash

# Check volume contents
docker exec humandesignapi ls -la /app/data/

# Test endpoint directly
curl -H "Authorization: Bearer your_token" http://127.0.0.1:9021/admin/sites

# Check Python imports
docker exec humandesignapi python -c "from humandesign import api; print('OK')"
```

## Dependencies Notes

Two files control dependencies: `requirements.txt` (Docker production, all pinned `==`) and `pyproject.toml` (package metadata, `>=` minimums).

```toml
# requirements.txt — pinned for reproducible Docker builds
# Core computation
numpy==2.1.2
pandas==2.2.3          # Large binary ~50MB — deeply integrated, can't easily remove
pysweph==2.10.3.6      # Requires gcc in Docker build stage (builder only)
tqdm==4.66.5

# Web framework
fastapi==0.115.6
uvicorn==0.27.1
pydantic==2.10.4
jinja2==3.1.5
python-multipart==0.0.18

# Geo & timezone
geopy==2.4.1
timezonefinder==8.2.1  # ~50MB, loads 20-30MB into RAM (in_memory=True)

# Config
python-dotenv==1.0.1
```

```toml
# pyproject.toml [project.optional-dependencies]
# Dev dependencies — NOT installed in production Docker image
dev = [
    "ipython==8.12.3",   # Used by features/core.py display() in report mode
    "ruff",               # Linter
    "pytest",             # Tests
    "httpx",              # Test HTTP client
    "matplotlib",         # Not imported in src/ — legacy
    "svgpath2mpl",        # Not imported in src/ — legacy
    "Pillow",             # Not imported in src/ — legacy
]
```

## Known Limitations
- Sessions in-memory → lost on container restart (user must re-login)
- 1 uvicorn worker → no parallel request processing (fine for current load)
- Nominatim geocoding has 5s timeout and rate limits (free public service)
- `pandas` and `numpy` are heavy (~90MB) but deeply integrated in calculations
- `timezonefinder` loads ~20-30MB into RAM on first query (in_memory=True)

## Relational analysis (3.5.0)

`humandesign.relational` replaces the deleted `services/composite.py`. The engine
classifies composite channels across the full set of 36 rather than only the
channels new to the pair, which is what makes Compromise, Dominance and
Companionship reachable — and role-conflict diagnostics with them. See
`docs/relational-decision-2026-08-23.md` for why the old file was not restored
and for the licensing question it surfaced.

Rules to keep:
- **One resolution path.** `relational/persons.py` is the only place birth data
  becomes a chart for `/analyze/*`. UTC offsets stay floats; activations are
  keyed by `(polarity, planet)` so a chart keeps all 26.
- **Failures raise.** A participant that cannot be resolved returns 422 naming
  itself. Never swallow one and return a partial 200.
- **`semantics.py` holds data, not logic.** Every block carries a machine `code`
  plus `label` / `label_ru`, so the consuming app can interpret in either
  language.
- **Do not claim doctrine that is not implemented.** `meta.entity.doctrine_implemented`
  is `true` only where the size forms a canonical entity — dyad, Penta (3-5),
  WA (10+). The 6-9 aggregate sets it `false`.
