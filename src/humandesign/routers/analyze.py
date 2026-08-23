"""Relational and group analysis endpoints.

    POST /analyze/composite    exactly 2 people — the dyad and its composite
    POST /analyze/penta        3-5 people — the Penta entity (Sovereign Standard)
    POST /analyze/wa           6+ people — group bodygraph aggregate
    POST /analyze/maia-penta   2+ people — every dyad plus the fitting group layer

All four are bearer-token protected and all four honour `verbosity`.
"""
from fastapi import APIRouter, Depends, HTTPException

from .. import relational
from ..dependencies import verify_token
from ..relational.persons import PersonResolutionError
from ..schemas.analyze import CompositeRequest, HybridRequest, PentaRequest, WaRequest

router = APIRouter(prefix="/analyze", tags=["analyze"])


def _run(fn, **kwargs):
    try:
        return fn(**kwargs)
    except PersonResolutionError as exc:
        raise HTTPException(
            status_code=422,
            detail={"participant": exc.name, "error": exc.reason},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"relational engine error: {exc}") from exc


@router.post("/composite", summary="Dyad and composite bodygraph (2 people)")
def analyze_composite(request: CompositeRequest, authorized: bool = Depends(verify_token)):
    """Composite chart of one auric pair.

    Returns the centre formula (9+0 … 5+4), all channels the pair forms classified
    into the four Maia types, the conditioning direction of every centre, the
    genetic type of the union, profile and variable synergy, nodal resonance, and
    a role-conflict block that names who conditions whom and how often.
    """
    return _run(relational.analyse_composite,
                participants=request.participants, verbosity=request.verbosity)


@router.post("/penta", summary="Penta Analysis 2.0, Sovereign Standard (3-5 people)")
def analyze_penta(request: PentaRequest, authorized: bool = Depends(verify_token)):
    """Penta entity: six channels, functional roles, gap severity, hiring logic and
    the vision / action / stability metrics."""
    return _run(relational.analyse_penta_group,
                participants=request.participants, group_type=request.group_type,
                verbosity=request.verbosity)


@router.post("/wa", summary="Group field aggregate — WA scale (6+ people)")
def analyze_wa(request: WaRequest, authorized: bool = Depends(verify_token)):
    """Group bodygraph over six or more people: coverage of the 64 gates and 36
    channels, circuit balance, per-person contribution, and the fragility block
    that names the channels a single departure would break.

    Ten or more participants are labelled a WA. The canonical WA gate structure is
    not implemented — `meta.entity.doctrine_implemented` is `false` and the output
    is stated as an aggregate rather than a classical WA.
    """
    return _run(relational.analyse_wa_group,
                participants=request.participants, group_type=request.group_type,
                verbosity=request.verbosity)


@router.post("/maia-penta", summary="Hybrid — every dyad plus the group layer (2+ people)")
def analyze_maia_penta(request: HybridRequest, authorized: bool = Depends(verify_token)):
    """Every pair in the group analysed as a composite, plus a cross-dyad roll-up
    and whichever group layer fits the size: Penta for 3-5, group field for 6+."""
    return _run(relational.analyse_hybrid,
                participants=request.participants, group_type=request.group_type,
                verbosity=request.verbosity)
