# Data Schemas

This directory (`src/humandesign/schemas`) contains the `Pydantic` models used for request
validation and response serialization.

## Modules

- **[`general.py`](general.py)** — `HealthResponse`: the shape returned by `GET /health`.
  `dependencies` is a free-form string map, currently `pysweph`, `sqlite` and `hd_data`.
- **[`v2/calculate.py`](v2/calculate.py)** — the v2 contract, 19 models.
    - `CalculateRequestV2`: birth parameters plus the `include` / `exclude` masking lists.
      `year`, `month`, `day`, `hour` and `minute` are required. A model validator requires either
      `place` or both `latitude` and `longitude` — the API does not substitute a stand-in chart for
      an incomplete request.
    - `CalculateResponseV2`: the response tree — `GeneralSectionV2`, `GatesV2`, `CentersV2`,
      `AnalyticsSectionV2`, `AdvancedSectionV2` and their leaf models.
    - Fields are `Optional` so that `response_model_exclude_none=True` produces sparse output after
      masking.
- **[`v2/__init__.py`](v2/__init__.py)**, **[`__init__.py`](__init__.py)** — package markers, empty.

## Removed

`input_models.py` and `response_models.py` described the request and response contracts of the
`/analyze/*`, `/transits/*` and `/bodygraph` endpoints. Those endpoints were removed; the schema
modules had no remaining consumer in either the application or the tests, and were deleted with
them. They remain recoverable from git history.

`GET /calculate` (v1) returns a plain dictionary and declares no `response_model`.
