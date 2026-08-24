"""Relational analysis: dyads, Penta groups and WA-scale group fields.

Public surface:

    analyse_composite(participants, verbosity)          -> exactly 2 people
    analyse_penta_group(participants, group_type, ...)  -> 3-8 people
    analyse_wa_group(participants, group_type, ...)     -> 6+ people; OC16 from 9
    analyse_hybrid(participants, group_type, ...)       -> 2+ people, dyads + group
"""
import itertools
from typing import Any, Dict, List, Optional

from ..utils.version import get_version
from . import blocks
from . import channels
from . import oc16
from . import semantics
from .engine import VERBOSITY_LEVELS, analyse_dyad, normalise_verbosity
from .groups import (GROUP_MAX, PENTA_EXTENDED_MAX, PENTA_MAX, PENTA_MIN, WA_MIN,
                     analyse_group_field, analyse_penta, classify_entity, now_iso)
from .persons import Person, PersonResolutionError, resolve_all

ENGINE_VERSION = "relational-1.0"

__all__ = [
    "analyse_composite", "analyse_penta_group", "analyse_wa_group", "analyse_hybrid",
    "resolve_all", "Person", "PersonResolutionError", "normalise_verbosity",
    "VERBOSITY_LEVELS", "PENTA_MIN", "PENTA_MAX", "PENTA_EXTENDED_MAX", "WA_MIN",
    "GROUP_MAX", "semantics", "oc16", "blocks", "channels",
]


def _enricher(enrich: bool):
    if not enrich:
        return None
    try:
        from ..services.enrichment import EnrichmentService
        return EnrichmentService()
    except Exception:
        return None


def _meta(kind: str, size: int, group_type: Optional[str], verbosity: str) -> Dict[str, Any]:
    return {
        "engine": ENGINE_VERSION,
        "api_version": get_version(),
        "analysis": kind,
        "entity": classify_entity(size),
        "group_type": group_type,
        "verbosity": verbosity,
        "ephemeris": "Swiss Ephemeris JPL DE431 (pysweph)",
        "generated_at": now_iso(),
    }


def _participants_block(people: Dict[str, Person], verbosity: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for name, p in people.items():
        summary = dict(p.summary)
        if verbosity == "compact":
            for key in ("defined_channels", "variables", "strategy", "signature",
                        "not_self", "aura", "latitude", "longitude"):
                summary.pop(key, None)
        elif verbosity == "full":
            summary["activations"] = p.activations
        out[name] = summary
    return out


# --------------------------------------------------------------------------- #
def analyse_composite(participants: Dict[str, Any], verbosity: str = "standard",
                      enrich: bool = True) -> Dict[str, Any]:
    verbosity = normalise_verbosity(verbosity)
    people = resolve_all(participants)
    names = list(people)
    if len(names) != 2:
        raise ValueError(f"Composite analysis takes exactly 2 participants, got {len(names)}")

    a, b = people[names[0]], people[names[1]]
    return {
        "meta": _meta("composite", 2, None, verbosity),
        "participants": _participants_block(people, verbosity),
        "dyad": analyse_dyad(a, b, verbosity, _enricher(enrich and verbosity == "full")),
    }


def analyse_penta_group(participants: Dict[str, Any], group_type: str = "business",
                        verbosity: str = "standard") -> Dict[str, Any]:
    verbosity = normalise_verbosity(verbosity)
    people = resolve_all(participants)
    size = len(people)
    if not (PENTA_MIN <= size <= PENTA_EXTENDED_MAX):
        raise ValueError(f"Penta analysis takes {PENTA_MIN}-{PENTA_EXTENDED_MAX} participants "
                         f"({PENTA_MIN}-{PENTA_MAX} canonical, extended to "
                         f"{PENTA_EXTENDED_MAX}), got {size}")

    return {
        "meta": _meta("penta", size, group_type, verbosity),
        "participants": _participants_block(people, verbosity),
        "penta": analyse_penta(people, group_type, verbosity),
    }


def analyse_wa_group(participants: Dict[str, Any], group_type: str = "business",
                     verbosity: str = "standard", enrich: bool = True) -> Dict[str, Any]:
    verbosity = normalise_verbosity(verbosity)
    people = resolve_all(participants)
    size = len(people)
    if size < PENTA_MAX + 1:
        raise ValueError(f"Group-field analysis takes more than {PENTA_MAX} participants, "
                         f"got {size}. Use /analyze/penta for {PENTA_MIN}-{PENTA_MAX}. "
                         f"A WA proper — and the OC16 layer — begins at {WA_MIN}.")
    if size > GROUP_MAX:
        raise ValueError(f"At most {GROUP_MAX} participants, got {size}")

    field = analyse_group_field(people, group_type, verbosity,
                                _enricher(enrich and verbosity == "full"))
    return {
        "meta": _meta("wa", size, group_type, verbosity),
        "participants": _participants_block(people, verbosity),
        "group_field": field,
    }


def analyse_hybrid(participants: Dict[str, Any], group_type: str = "business",
                   verbosity: str = "standard", enrich: bool = True) -> Dict[str, Any]:
    """Every dyad plus the group layer that fits the size."""
    verbosity = normalise_verbosity(verbosity)
    people = resolve_all(participants)
    size = len(people)
    if size < 2:
        raise ValueError("At least 2 participants are required")
    if size > GROUP_MAX:
        raise ValueError(f"At most {GROUP_MAX} participants, got {size}")

    enricher = _enricher(enrich and verbosity == "full")
    dyads = [analyse_dyad(people[a], people[b], verbosity, enricher)
             for a, b in itertools.combinations(people, 2)]

    result: Dict[str, Any] = {
        "meta": _meta("hybrid", size, group_type, verbosity),
        "participants": _participants_block(people, verbosity),
        "dyad_matrix": dyads,
        "dyad_count": len(dyads),
        "matrix_summary": _matrix_summary(dyads),
    }

    if PENTA_MIN <= size <= PENTA_EXTENDED_MAX:
        result["penta"] = analyse_penta(people, group_type, verbosity)
    elif size > PENTA_EXTENDED_MAX:
        result["group_field"] = analyse_group_field(people, group_type, verbosity, enricher)
    return result


def _matrix_summary(dyads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Cross-dyad roll-up: the view a consultant reads before any single pair."""
    totals = {c: 0 for c in semantics.MAIA_TYPES}
    formulas: Dict[str, int] = {}
    asymmetric: List[Dict[str, Any]] = []
    load: Dict[str, Dict[str, int]] = {}

    for d in dyads:
        for code in totals:
            totals[code] += d["connections"]["totals"][code]
        code = d["composite"]["formula"]["code"]
        formulas[code] = formulas.get(code, 0) + 1
        for name, l in d["role_conflicts"]["load"].items():
            agg = load.setdefault(name, {"conditions": 0, "conditioned": 0})
            agg["conditions"] += l["conditions"]
            agg["conditioned"] += l["conditioned"]
        balance = d["role_conflicts"]["balance"]
        if balance["code"] == "asymmetric":
            asymmetric.append({"pair": d["pair"], "lead": balance["lead"],
                               "following": balance["following"]})

    ranked = sorted(load.items(), key=lambda kv: -(kv[1]["conditions"] - kv[1]["conditioned"]))
    return {
        "connection_totals": {**totals, "total": sum(totals.values())},
        "formula_distribution": formulas,
        "conditioning_load": load,
        "most_conditioning": ranked[0][0] if ranked else None,
        "most_conditioned": ranked[-1][0] if ranked else None,
        "asymmetric_pairs": asymmetric,
    }
