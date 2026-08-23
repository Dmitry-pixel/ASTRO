# Human Design API Documentation

**Version:** 3.5.0
**Base URL:** `http://localhost:8000` (or `https://api.humandesign.ai`)

## Overview

The Human Design API provides a robust engine for calculating astrological and Human Design metrics. It offers stateless, RESTful endpoints for individual charts, composite relationships, and temporal transit analysis.

## Authentication

All API endpoints are protected via **Bearer Token** authentication. You must provide your API token in the `Authorization` header.

**Header Format:**
```http
Authorization: Bearer <your_token>
```

> [!IMPORTANT]
> Keep your `HD_API_TOKEN` secure. Do not expose it in client-side code.

---

## 1. Core Endpoints

### Calculate Chart (V2 Flagship)
The high-fidelity calculation engine (v2). Returns a semantic, hierarchical JSON response with optional "sparse fieldset" masking.

**Endpoint:** `POST /v2/calculate`

#### Request Body
```json
{
  "year": 1990,
  "month": 1,
  "day": 12,
  "hour": 8,
  "minute": 0,
  "place": "New York, USA",
  "include": ["general", "gates.personality"],
  "exclude": ["channels"]
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `year` | int | Yes | Birth Year |
| `month` | int | Yes | Birth Month (1-12) |
| `day` | int | Yes | Birth Day (1-31) |
| `hour` | int | Yes | Birth Hour (0-23) |
| `minute` | int | Yes | Birth Minute (0-59) |
| `place` | string | Yes | "City, Country" (e.g., "London, UK") |
| `latitude` | float | No | Explicit Latitude (bypasses geocoding) |
| `longitude` | float | No | Explicit Longitude (bypasses geocoding) |
| `include` | list[str] | No | Whitelist fields (supports dot syntax: `gates.personality`) |
| `exclude` | list[str] | No | Blacklist fields |

#### Example Response
```json
{
  "general": {
    "energy_type": "Generator",
    "inner_authority": "Sacral Authority",
    "profile": "4/6: Opportunist Role Model",
    "inc_cross": "The Right Angle Cross of Planning (37/40 | 9/16)",
    "definition": "Split Definition"
  },
  "centers": {
    "defined": ["Sacral", "Root"],
    "undefined": ["Head", "Ajna", "Throat", "G_Center", "Heart", "Solar Plexus", "Spleen"]
  },
  "gates": {
    "personality": {
      "Sun": {
        "gate": 61,
        "line": 1, 
        "gate_name": "The Gate of Inner Truth",
        "fixation": { "type": "Exalted", "value": "Up" }
      }
    }
  },
  "advanced": {
    "dream_rave": { ... },
    "global_cycle": { ... }
  }
}
```

### System Health
Check API operational status.

**Endpoint:** `GET /health`

---

## 2. Transit Analysis

### Daily Transit ("Weather")
Analyze the "Weather of the Day" by combining a birth chart with the current transit field. Supports "Travel Mode" (calculating transits relative to current location).

**Endpoint:** `GET /transits/daily`

#### Parameters
| Name | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `place` | string | Yes | Birth Place |
| `year`, `month`, `day`, `hour`, `minute` | int | Yes | Birth Date/Time |
| `transit_year` | int | Yes | Target Year |
| `transit_month` | int | Yes | Target Month |
| `transit_day` | int | Yes | Target Day |
| `current_place` | string | No | **New:** Current User Location (for timezone-aware transits) |
| `transit_hour` | int | No | **New:** Target Hour (Local time at current_place) |

#### Example Request
```bash
curl -X GET "http://localhost:8000/transits/daily?place=London,UK&year=1990&month=1&day=1&hour=12&minute=0&transit_year=2025&transit_month=1&transit_day=1&current_place=New%20York,USA&transit_hour=9" \
  -H "Authorization: Bearer <your_token>"
```

### Solar Return
Calculate the Yearly Theme (Solar Return).

**Endpoint:** `GET /transits/solar_return`
*Parameters similar to Daily Transit, with `sr_year_offset` (0=Birth Year, 1=First Return).*

---

## 3. Relationship & Group Analysis

Four endpoints, all Bearer-protected, all accepting `verbosity`.

| Endpoint | Participants | Purpose |
| :--- | :--- | :--- |
| `POST /analyze/composite` | exactly 2 | Dyad and composite bodygraph |
| `POST /analyze/penta` | 3-5 | Penta entity, Sovereign Standard |
| `POST /analyze/wa` | 6+ | WA — the whole-bodygraph group entity (from 10 people) |
| `POST /analyze/maia-penta` | 2+ | Every dyad plus the fitting group layer |

### Shared request shape

```json
{
  "participants": {
    "Anna":  { "place": "Moscow, Russia",  "year": 1985, "month": 3,  "day": 14, "hour": 9,  "minute": 25 },
    "Boris": { "place": "Berlin, Germany", "year": 1979, "month": 11, "day": 2,  "hour": 17, "minute": 40 }
  },
  "group_type": "business",
  "verbosity": "standard"
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `participants` | object | Yes | Name → birth data. Names are echoed throughout the response. |
| `participants[].place` | string | Yes | "City, Country", or an IANA zone such as `Europe/Moscow` |
| `participants[].year/month/day/hour/minute` | int | Yes | Ranges validated before any calculation |
| `participants[].latitude/longitude` | float | No | Supply both to skip geocoding |
| `group_type` | enum | No | `business` (default) or `family`. Ignored by `/analyze/composite`. |
| `verbosity` | enum | No | `compact`, `standard` (default), `full`. `partial` and `all` are accepted as aliases for `compact` and `full`. |

### Verbosity

| Level | Contains |
| :--- | :--- |
| `compact` | Roll-ups only: formula, connection totals, role-conflict balance, group metrics. No per-channel lists, trimmed participant summaries. |
| `standard` | Plus every channel with its Maia class, circuit, holders and conditioning direction; centre dynamics; the full gap and fragility lists. |
| `full` | Plus `hd_data.sqlite` reference text per channel (name, design purpose, description, both gate gifts) and all 26 activations per participant. |

### The four Maia connection classes

Every channel the pair forms is classified. This is the core of the composite.

| Class | Mechanics | Reads as |
| :--- | :--- | :--- |
| `companionship` | Both hold the whole channel | Complete agreement; nothing needs explaining |
| `compromise` | One holds it whole, the other holds one gate | Pressure zone — the single-gate side always yields |
| `dominance` | One holds it whole, the other holds neither gate | Fixed pattern; the other reflects and absorbs it |
| `electromagnetic` | One gate each | Attraction and the pair's main point of conflict |

`compromise` and `dominance` carry a `direction` object naming who conditions
whom; they are aggregated into `role_conflicts`.

### Centre formula

`composite.formula.code` is `defined+open` over the nine centres, with a reading:
`9+0` nowhere to hide, `8+1` room to grow, `7+2` work to do, `6+3` and below not
enough glue.

### `/analyze/composite` — response outline

```json
{
  "meta": { "engine": "relational-1.0", "entity": { "code": "dyad", "size": 2 }, "verbosity": "standard" },
  "participants": { "Anna": { "energy_type": "Projector", "utc_offset": 3.0, "...": "..." } },
  "dyad": {
    "pair": ["Anna", "Boris"],
    "composite": { "formula": { "code": "8+1", "label": "Room to grow" },
                   "defined_centres": [], "centre_dynamics": {}, "bridges_split": {} },
    "genetic_type": { "label": "Union of direction", "task": "..." },
    "connections": { "totals": { "electromagnetic": 2, "compromise": 5, "dominance": 2,
                                 "companionship": 0, "total": 9 },
                     "circuitry": {}, "dominant_circuit": {}, "channels": [] },
    "role_conflicts": { "balance": {}, "load": {}, "channels": [] },
    "profile_resonance": {}, "variable_synergy": {}, "environmental_resonance": {},
    "love_gates": []
  }
}
```

### `/analyze/penta` — response outline

`penta.penta_anatomy` holds the six channels split into `upper_penta`
(direction and vision) and `lower_penta` (action and generation), each with
status, contributor breakdown by gate and line, or a gap analysis with severity
and impact. Alongside it: `analytical_metrics` (vision, action and stability
scores plus backbone integrity), `functional_roles` and `hiring_logic`.

### `/analyze/wa` — response outline

The WA is the entity formed from ten people upward. Where the Penta is scored
over twelve gates in six fixed channels, the WA is built on the **whole
bodygraph**, and the payload states that structure explicitly:

```json
"structure": { "gates": 64, "channels": 36, "centres": 9 }
```

`group_field` carries that `structure`, then `coverage` against it (gates,
channels, centres, and share by circuit group), `centres`, `type_mix`,
`contributions` (per person, including the gates nobody else in the group holds),
`fragility` (the channels that break if one person leaves) and `gaps`.

> [!NOTE]
> Six to nine people form neither entity. The same mechanics are applied, but
> `meta.entity` reports `aggregate` with `doctrine_implemented: false`. Ten and
> above is a `wa` with `doctrine_implemented: true`.

### `/analyze/maia-penta` — response outline

`dyad_matrix` (one entry per pair, same shape as `dyad` above), `dyad_count`,
`matrix_summary` (connection totals across all pairs, formula distribution,
conditioning load per person, who conditions most and who is conditioned most,
and the asymmetric pairs), plus `penta` for 3-5 participants or `group_field`
for 6 and above.

### Errors

A participant that cannot be resolved returns `422` naming it, rather than
disappearing from a `200`:

```json
{ "detail": { "participant": "Ghost", "error": "geocoding failed for 'Nowhere Land'" } }
```

## Error Handling

| Status Code | Description |
| :--- | :--- |
| `200` | Success |
| `400` | Bad Request (Validation or Geocoding failed) |
| `401` | Unauthorized (Missing or Invalid Token) |
| `422` | Unprocessable Entity (Input formatting issues) |
| `500` | Internal Server Error |

---
*Documentation updated for v3.5.0*
