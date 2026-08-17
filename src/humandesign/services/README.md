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
    - `_db_path` is relative and resolves against the process working directory. Correct under
      Docker (`WORKDIR /app`); set it explicitly if launching from elsewhere.
- **[`geolocation.py`](geolocation.py)** — location resolution.
    - `get_latitude_longitude`, `get_address`, `batch_geocode`, `calculate_distance`.
    - Uses `geopy`; the module-level `tf` is a shared `TimezoneFinder` singleton.
- **[`dream_rave.py`](dream_rave.py)** — `DreamRaveEngine`. Design-side mechanics, loaded lazily
  inside the `/v2/calculate` handler.
- **[`global_cycles.py`](global_cycles.py)** — `GlobalCycleEngine`. Cycle mechanics, loaded lazily
  inside the `/v2/calculate` handler.
- **[`composite.py`](composite.py)** — relational analysis. **Currently has no HTTP surface.**
    - Maia connection classification, center dynamics, bridging, aura dynamics, profile resonance,
      variable synergy, nodal resonance, Penta dynamics.
    - The endpoints that exposed this module were removed; the logic and its tests
      (`tests/test_penta.py`, `tests/test_nodal_synergy.py`, `tests/test_variable_synergy.py`)
      were retained. Reachable in code via `features.get_penta` and `features.hd_composite`.

## Note on visualization

There is no chart-rendering service. `matplotlib`, `svgpath2mpl` and `Pillow` are declared only
under `[project.optional-dependencies].dev` in `pyproject.toml` and are not imported anywhere
under `src/`.
