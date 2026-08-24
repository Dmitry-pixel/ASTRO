# Human Design API

[![tests](https://github.com/Dmitry-pixel/ASTRO/actions/workflows/tests.yml/badge.svg)](https://github.com/Dmitry-pixel/ASTRO/actions/workflows/tests.yml)

Python-based Human Design calculation API. Calculates Energy Types, Profiles, Incarnation Crosses, Gates, Variables, and extended analytics using Swiss Ephemeris (JPL DE431).

## Quick Start

### Docker (recommended for VPS)

```bash
git clone <your-repo-url>
cd ASTRO
cp .env_example .env
# Edit .env — set HD_ADMIN_TOKEN
docker-compose up --build -d
```

API available at `http://localhost:9021`. Swagger UI at `http://localhost:9021/docs`.

### Ubuntu / WSL2

```bash
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh
source venv/bin/activate
uvicorn humandesign.api:app --host 0.0.0.0 --port 9021 --reload
```

## Authentication

Two-level token system:

- **Admin token** (`HD_ADMIN_TOKEN` in `.env`) — for managing sites via `/admin/*`
- **Site tokens** (stored in SQLite `api_auth.db`) — each site gets its own token

### Register a site

```bash
curl -X POST http://localhost:9021/admin/sites \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain": "mysite.com"}'
```

Returns auto-generated token. Use it for all `/calculate` requests from that site.

## API Endpoints

### `GET /health`

No auth required. Returns status, version, ephemeris mode.

### `GET /calculate`

Main endpoint. Query parameters: `year`, `month`, `day`, `hour`, `minute`, `second`, `place`, `latitude`, `longitude`, `gender`, `islive`.

Response includes:

| Section | Contents |
|---------|----------|
| `general.energy_type` | Generator, Projector, Manifestor, MG, Reflector |
| `general.strategy` | Wait to Respond, Wait for the Invitation, etc. |
| `general.inner_authority` | Emotional, Sacral, Splenic, Ego, Self-Projected, etc. |
| `general.profile` | 1/3, 2/4, 3/5, 4/6, 5/1, 6/2, etc. |
| `general.cross_name` | Full Incarnation Cross name |
| `general.quarter` | Quarter number and name |
| `general.definition` | Single, Split, Triple Split, Quadruple Split |
| `general.variables` | 4 arrows (Motivation, Perspective, Digestion, Environment) |
| `general.line_counts` | Line frequency (prs / des / total) |
| `general.sun_roles` | Gate role classification (8 roles) |
| `general.yin_yang_balance` | Yang / Yin / Balance percentages |
| `general.contour` | Realization, Mind, Decision, Big O percentages |
| `gates` | All 26 planetary activations (gate, line, color, tone, base) |
| `channels` | Active channels list |

### `POST /v2/calculate`

Same calculation via JSON body. Supports `include`/`exclude` field masking.

### `POST /admin/sites`

Register a new site. Returns unique API token.

### `GET /admin/sites`

List all registered sites.

### `PUT /admin/sites/{id}`

Update domain, token, or deactivate a site.

### `DELETE /admin/sites/{id}`

Delete site and its request logs.

### `GET /admin/stats`

Request statistics per site, daily breakdown, endpoint usage.

## Project Structure

```
humandesign_api/
├── src/humandesign/
│   ├── api.py                 # FastAPI entry point
│   ├── auth.py                # Multi-site auth + request logging
│   ├── dependencies.py        # Auth dependency (re-export)
│   ├── hd_constants.py        # HD constants, gate maps, cross DB
│   ├── features/
│   │   ├── core.py            # Calculation engine (Swiss Ephemeris)
│   │   ├── mechanics.py       # Type, authority, channels, definition
│   │   └── attributes.py      # Profile, cross, quarter, variables, contour
│   ├── routers/
│   │   ├── general.py         # /health, /calculate
│   │   ├── analyze.py         # /analyze/composite, /penta, /wa, /maia-penta
│   │   ├── admin.py           # /admin/sites, /admin/stats
│   │   ├── panel.py           # /panel/* operator web panel
│   │   └── v2/general.py      # /v2/calculate
│   ├── relational/            # Dyad, Penta and WA analysis
│   │   ├── semantics.py       # Semantic tables, EN + RU, machine codes
│   │   ├── persons.py         # One birth-data resolution path for /analyze/*
│   │   ├── engine.py          # Composite over all 36 channels
│   │   └── groups.py          # Penta wrapper and the group field
│   ├── services/
│   │   ├── geolocation.py     # Nominatim + TimezoneFinder
│   │   ├── enrichment.py      # Gate/line/channel reference from hd_data.sqlite
│   │   ├── sqlite_repository.py  # Read-only accessor over hd_data.sqlite
│   │   └── masking.py         # include/exclude filtering for /v2/calculate
│   ├── schemas/               # Pydantic models
│   ├── templates/panel/       # Jinja2 templates for the operator panel
│   ├── static/vendor/         # Self-hosted Tailwind, Chart.js and web fonts
│   └── utils/                 # Serialization, dates, astrology
├── ephe/                      # Swiss Ephemeris DE431 data files
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── setup_ubuntu.sh
└── .env_example
```

## Tech Stack

- **Python 3.12+**, **FastAPI**, **uvicorn**
- **pysweph** (Swiss Ephemeris, compressed JPL DE431)
- **zoneinfo + tzdata** (timezone handling)
- **geopy + timezonefinder** (geocoding)
- **SQLite** (auth + request logging)
