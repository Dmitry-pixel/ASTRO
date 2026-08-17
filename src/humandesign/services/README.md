# Application Services

This directory (`src/humandesign/services`) contains the service layer. It bridges raw calculations
(`features/`) and the transport layer (`routers/`).

## Modules

- **[`masking.py`](masking.py)** — `OutputMaskingService`.
    - Parses dot-notation paths into a tree and applies recursive `include` (whitelist) or
      `exclude` (blacklist) filtering to the finished response dictionary.
    - Used by `POST /v2/calculate`.
- **[`enrichment.py`](enrichment.py)** — `EnrichmentService`.
    - Resolves gate and line codes to human-readable names and descriptions via `sqlite_repository`.
- **[`sqlite_repository.py`](sqlite_repository.py)** — `SQLiteRepository`.
    - Singleton read-only accessor over `hd_data.sqlite`, tables `public_gates` and
      `public_gate_lines`.
    - The database path is resolved from the project root, not the process working directory, so
      the repository works wherever uvicorn or pytest was started. `HD_DATA_PATH` overrides it.
- **[`geolocation.py`](geolocation.py)** — location resolution.
    - `get_latitude_longitude`, `get_address`, `batch_geocode`, `calculate_distance`.
    - Uses `geopy`; the module-level `tf` is a shared `TimezoneFinder` singleton.
- **[`dream_rave.py`](dream_rave.py)** — `DreamRaveEngine`. Design-side mechanics, loaded lazily
  inside the `/v2/calculate` handler.
- **[`global_cycles.py`](global_cycles.py)** — `GlobalCycleEngine`. Cycle mechanics, loaded lazily
  inside the `/v2/calculate` handler.
## Removed

The relational service that backed the `/analyze/*` endpoints was deleted along with them. Penta and
composite-combination logic remains in `features/core.py` — `get_penta`, `hd_composite`,
`get_composite_combinations` — and is covered by `tests/test_penta.py`.

## Note on visualization

There is no chart-rendering service. `matplotlib`, `svgpath2mpl` and `Pillow` are declared only
under `[project.optional-dependencies].dev` in `pyproject.toml` and are not imported anywhere
under `src/`.
