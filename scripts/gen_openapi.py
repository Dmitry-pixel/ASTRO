#!/usr/bin/env python3
"""Regenerate openapi.yaml from the live FastAPI application.

The specification is a build artifact, not a hand-maintained document. Run this
after changing any route signature, request model or response model, and commit
the result alongside the code change.

Usage (from the repository root, with runtime dependencies installed):

    PYTHONPATH=src python scripts/gen_openapi.py

Exit codes:
    0  spec written
    1  application failed to import, or the produced spec is invalid
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "openapi.yaml"

sys.path.insert(0, str(ROOT / "src"))


class _Dumper(yaml.SafeDumper):
    """Preserve insertion order instead of sorting keys alphabetically."""


_Dumper.add_representer(dict, lambda d, data: d.represent_dict(data.items()))


def build_spec() -> dict:
    """The specification as the live application describes itself."""
    from humandesign.api import app

    return app.openapi()


def render(spec: dict) -> str:
    """Serialise a specification exactly the way openapi.yaml is stored.

    The test that guards openapi.yaml against drift calls this same function,
    so the generator and the check can never disagree on formatting.
    """
    return yaml.dump(
        spec,
        Dumper=_Dumper,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=100,
    )


def main() -> int:
    try:
        spec = build_spec()
    except Exception as exc:  # noqa: BLE001 - report any import failure verbatim
        print(f"error: could not import humandesign.api: {exc}", file=sys.stderr)
        return 1

    paths = len(spec.get("paths", {}))
    operations = sum(len(v) for v in spec.get("paths", {}).values())
    schemas = len(spec.get("components", {}).get("schemas", {}))

    if paths == 0:
        print("error: generated specification contains no paths", file=sys.stderr)
        return 1

    OUTPUT.write_text(render(spec), encoding="utf-8")

    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    print(f"  version:    {spec['info'].get('version')}")
    print(f"  paths:      {paths}")
    print(f"  operations: {operations}")
    print(f"  schemas:    {schemas}")

    # Optional structural check — skipped silently if the validator is absent.
    try:
        from openapi_spec_validator import validate
    except ImportError:
        print("  validation: skipped (pip install openapi-spec-validator to enable)")
        return 0

    try:
        validate(spec)
    except Exception as exc:  # noqa: BLE001 - surface the validator's own message
        print(f"error: specification is not valid OpenAPI: {exc}", file=sys.stderr)
        return 1

    print("  validation: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
