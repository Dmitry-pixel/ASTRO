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
- **[`analyze.py`](analyze.py)** — request models for the four relational endpoints (3.5.0).
    - `ParticipantInput`: one person's birth data. Range constraints live on the fields, so they
      appear in `openapi.yaml` and produce the standard FastAPI 422. A model validator rejects a
      date the calendar does not have; `latitude` + `longitude` skip geocoding.
    - `CompositeRequest` (exactly 2), `PentaRequest` (3-5), `WaRequest` (6+), `HybridRequest` (2+) —
      each enforces its own participant count, plus `group_type` and `verbosity`. Legacy `verbosity`
      values `all` and `partial` are mapped onto `full` and `compact` by a `mode="before"` validator.
    - There is no response model: the relational engines return plain dictionaries.
- **[`v2/__init__.py`](v2/__init__.py)**, **[`__init__.py`](__init__.py)** — package markers, empty.

## Removed

`input_models.py` and `response_models.py` described the request and response contracts of the
`/analyze/*`, `/transits/*` and `/bodygraph` endpoints as they existed before 3.5.0. Those
endpoints were removed and the modules deleted with them; they remain recoverable from git history.

`/analyze/*` came back in 3.5.0, but on `analyze.py` above and on a different engine
(`humandesign.relational`). Nothing was restored from the old modules — `response_models.py` could
not validate the engine's own output, which is part of why it was not brought back. `/transits/*`
and `/bodygraph` do not exist.

`GET /calculate` (v1) returns a plain dictionary and declares no `response_model`.
