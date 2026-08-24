# Application Services

This directory (`src/humandesign/services`) contains the service layer. It bridges raw calculations
(`features/`) and the transport layer (`routers/`).

## Modules

- **[`masking.py`](masking.py)** — `OutputMaskingService`.
    - Parses dot-notation paths into a tree and applies recursive `include` (whitelist) or
      `exclude` (blacklist) filtering to the finished response dictionary.
    - Used by `POST /v2/calculate`.
- **[`enrichment.py`](enrichment.py)** — `EnrichmentService`.
    - `enrich_gate` resolves a gate, line and planet to names, descriptions and any fixation.
    - `enrich_channel` and `enrich_gate_reference` (3.5.0) resolve a channel and a standalone gate.
      Currently reached only by `/analyze/wa` at `verbosity: full`; the dyad and Penta responses do
      not carry reference text yet.
- **[`sqlite_repository.py`](sqlite_repository.py)** — `SQLiteRepository`.
    - Singleton read-only accessor over `hd_data.sqlite`: `public_gates`, `public_gate_lines`,
      `public_channels`, `public_channel_gates` and `public_planets`.
    - The database path is resolved from the project root, not the process working directory, so
      the repository works wherever uvicorn or pytest was started. `HD_DATA_PATH` overrides it.
- **[`geolocation.py`](geolocation.py)** — location resolution.
    - `get_latitude_longitude`, `get_address`, `batch_geocode`, `calculate_distance`.
    - Uses `geopy`; the module-level `tf` is a shared `TimezoneFinder` singleton.
- **[`dream_rave.py`](dream_rave.py)** — `DreamRaveEngine`. Design-side mechanics, loaded lazily
  inside the `/v2/calculate` handler.
- **[`global_cycles.py`](global_cycles.py)** — `GlobalCycleEngine`. Cycle mechanics, loaded lazily
  inside the `/v2/calculate` handler.

## Where the relational logic lives

`services/composite.py` backed the pre-3.5.0 `/analyze/*` endpoints and was deleted with them. The
endpoints returned in 3.5.0 on `humandesign.relational`, a separate package rather than a service —
see `../relational/README.md` for why the old file was not restored.

`features/core.py` still holds `get_penta`, `hd_composite` and `get_composite_combinations`;
`get_penta` is the Penta engine the `/analyze/penta` endpoint delegates to, and is covered by
`tests/test_penta.py`.

## Note on visualization

There is no chart-rendering service. `matplotlib`, `svgpath2mpl` and `Pillow` are declared only
under `[project.optional-dependencies].dev` in `pyproject.toml` and are not imported anywhere
under `src/`.
