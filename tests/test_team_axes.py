"""Team dynamics model v1.1 — rule-level tests.

Synthetic charts pin each agreed rule; a sample of real charts pins the
invariants that tie index, band, pole and code together.
"""
import datetime as dt
import random
import re

import pytest

from humandesign.features import team_axes as ta
from humandesign.features import team_axes_baseline as base
from humandesign.features.core import hd_features

CODE_RE = re.compile(r"^[SF–]·[DR–]·[CH–]·[PA–]·(I[1-4]|R|–)$")


def axes(gates=(), centres=(), auth="outer", typ="Projector", definition=1, persp=None, pconf=None):
    return ta.compute_axes(gates, centres, auth, typ, definition, persp, pconf)


def keys(ax):
    return sorted((e["key"], e["side"], e["weight"]) for e in ax["evidence"])


# --------------------------------------------------------------------------- #
# Formula and bands
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("a,b,idx", [(0, 0, 50.0), (3, 0, 20.0), (0, 2, 75.0), (2, 2, 50.0), (1, 4, 71.4)])
def test_index_formula(a, b, idx):
    assert ta._index(a, b) == idx


@pytest.mark.parametrize("idx,band", [(20, "strong_a"), (25, "moderate_a"), (44.9, "moderate_a"),
                                      (45, "mixed"), (55, "mixed"), (55.1, "moderate_b"),
                                      (75, "moderate_b"), (75.1, "strong_b")])
def test_band_edges(idx, band):
    assert ta._band(idx, 5) == band


def test_thin_evidence_gets_no_band():
    assert ta._band(33.3, 1) == "insufficient"


# --------------------------------------------------------------------------- #
# Transfer
# --------------------------------------------------------------------------- #
def test_throat_alone_is_insufficient():
    t = axes(centres={"TT"})["axes"]["transfer"]
    assert (t["index"], t["band"], t["pole"]) == (33.3, "insufficient", None)


def test_section_7_weights_in_transfer():
    t = axes({43, 23, 17, 62, 20, 34}, {"AA", "TT", "SL"})["axes"]["transfer"]
    assert keys(t) == sorted([("TT определён", "a", 1.0), ("43-23", "a", 1.0),
                              ("17-62", "a", 0.5), ("20-34", "b", 0.5)])


def test_narrative_channels_make_emergent():
    t = axes({11, 56, 35, 36}, {"AA", "TT", "SP"})["axes"]["transfer"]
    assert t["pole"] == "emergent" and t["letter"] == "F"
    assert t["evidence_b"] == 4.0 and t["evidence_a"] == 1.0


def test_throat_channels_added_by_agreement():
    t = axes({33, 13, 20, 10}, {"TT", "GC"})["axes"]["transfer"]
    assert ("33-13", "b", 1.0) in keys(t) and ("20-10", "b", 1.0) in keys(t)
    assert not any(k.startswith(("16-48", "45-21")) for k, _, _ in keys(axes({16, 48, 45, 21}, {"TT"})["axes"]["transfer"]))


# --------------------------------------------------------------------------- #
# Processing
# --------------------------------------------------------------------------- #
def test_ajna_alone_is_moderate_consistent():
    p = axes(centres={"AA"})["axes"]["processing"]
    assert (p["index"], p["band"], p["pole"]) == (25.0, "moderate_a", "consistent")
    p = axes()["axes"]["processing"]
    assert (p["index"], p["band"], p["pole"]) == (75.0, "moderate_b", "contextual")


def test_logic_channel_is_strong():
    p = axes({63, 4}, {"HD", "AA"})["axes"]["processing"]
    assert p["evidence_a"] == 5.0 and p["band"] == "strong_a"


def test_gate_inside_a_complete_channel_is_not_dangling():
    p = axes({17, 62}, {"AA", "TT"})["axes"]["processing"]
    assert ("ворота 17", "a", 1.0) not in keys(p) and ("17-62", "a", 2.0) in keys(p)
    p = axes({17}, set())["axes"]["processing"]
    assert ("ворота 17", "a", 1.0) in keys(p)
    assert p["evidence"][-1]["status"] == "hypothesis" or any(e["status"] == "hypothesis" for e in p["evidence"])


def test_11_56_is_secondary_in_processing():
    p = axes({11, 56}, {"AA", "TT"})["axes"]["processing"]
    assert ("11-56", "b", 0.5) in keys(p)


# --------------------------------------------------------------------------- #
# Decision
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("auth,idx,pole,mode", [
    ("SL", 20.0, "internal", "response"), ("SN", 20.0, "internal", "instant"),
    ("HT", 20.0, "internal", "will"), ("HT_GC", 20.0, "internal", "will"),
    ("GC", 25.0, "internal", "articulated"), ("SP", 75.0, "relational", "delayed"),
    ("outer", 80.0, "relational", "external"), ("lunar", 80.0, "relational", "lunar"),
])
def test_decision_from_authority_only(auth, idx, pole, mode):
    d = axes(auth=auth)["axes"]["decision"]
    assert (d["index"], d["pole"], d["mode"]) == (idx, pole, mode)
    assert len(d["evidence"]) == 1       # no open-centre modifiers


def test_open_centres_never_enter_decision():
    with_open = axes(auth="SL", centres={"SL"})["axes"]["decision"]
    all_def = axes(auth="SL", centres={"SL", "SP", "AA"})["axes"]["decision"]
    assert with_open["index"] == all_def["index"] == 20.0


@pytest.mark.parametrize("auth,definition,code", [
    ("SL", 1, "internal_closed"), ("SL", 2, "internal_bridged"),
    ("SP", 1, "relational_closed"), ("SP", 3, "relational_bridged"),
    ("lunar", 0, "relational_bridged"),
])
def test_integration_reading(auth, definition, code):
    d = axes(auth=auth, definition=definition)["axes"]["decision"]
    assert d["integration_reading"]["code"] == code


def test_definition_does_not_move_decision_index():
    assert axes(auth="SP", definition=1)["axes"]["decision"]["index"] == \
           axes(auth="SP", definition=3)["axes"]["decision"]["index"]


# --------------------------------------------------------------------------- #
# Execution
# --------------------------------------------------------------------------- #
def test_perspective_alone_decides_and_is_flagged():
    r = axes(persp="right")
    e = r["axes"]["execution"]
    assert (e["basis"], e["pole"], e["band"], e["index"]) == ("perspective_only", "adaptive", "moderate_b", 66.7)
    assert e["hypothesis_share"] == 1.0
    assert any(f["code"] == "perspective_only" for f in r["flags"])


def test_perspective_does_not_override_a_channel():
    e = axes({5, 15}, {"GC", "SL"}, persp="right")["axes"]["execution"]
    assert e["pole"] == "planned" and e["basis"] == "channels"


def test_perspective_breaks_a_tie():
    assert axes({5, 15, 20, 34}, persp="left")["axes"]["execution"]["pole"] == "planned"
    assert axes({5, 15, 20, 34}, persp="right")["axes"]["execution"]["pole"] == "adaptive"


def test_root_and_sacral_definition_are_ignored():
    a = axes(centres={"RT", "SL"}, persp="left")["axes"]["execution"]
    b = axes(centres=set(), persp="left")["axes"]["execution"]
    assert a["index"] == b["index"]


def test_54_32_is_planned_and_46_29_added():
    assert ("54-32", "a", 1.0) in keys(axes({54, 32})["axes"]["execution"])
    assert ("46-29", "a", 2.0) in keys(axes({46, 29})["axes"]["execution"])


def test_perspective_near_boundary_is_flagged():
    r = axes(persp="left", pconf="low")
    assert any(f["code"] == "perspective_near_boundary" for f in r["flags"])


def test_perspective_is_used_only_in_execution():
    l, rr = axes({31, 7}, {"TT", "GC"}, persp="left"), axes({31, 7}, {"TT", "GC"}, persp="right")
    for a in ("transfer", "processing", "decision"):
        assert l["axes"][a]["index"] == rr["axes"][a]["index"]


# --------------------------------------------------------------------------- #
# Integration, code, reference chart
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("definition,code", [(0, "R"), (1, "I1"), (2, "I2"), (3, "I3"), (4, "I4")])
def test_integration_codes(definition, code):
    assert axes(definition=definition)["integration"]["code"] == code


def test_reference_chart_sam():
    d = hd_features(1966, 12, 9, 17, 0, 0, 6).birth_creat_date_to_gate()
    r = ta.compute_from_date_to_gate(d)
    assert r["code"] == "F·D·H·P·I1"
    ax = r["axes"]
    assert (ax["transfer"]["index"], ax["processing"]["index"],
            ax["decision"]["index"], ax["execution"]["index"]) == (71.4, 38.5, 75.0, 33.3)
    assert ax["execution"]["basis"] == "perspective_only"
    assert ax["decision"]["integration_reading"]["code"] == "relational_closed"


def _random(n, seed=7):
    rnd = random.Random(seed)
    start = dt.datetime(1960, 1, 1)
    span = (dt.datetime(2006, 1, 1) - start).total_seconds()
    for _ in range(n):
        t = start + dt.timedelta(seconds=rnd.random() * span)
        yield ta.compute_from_date_to_gate(hd_features(t.year, t.month, t.day, t.hour, t.minute, 0, 0)
                                           .birth_creat_date_to_gate())


def test_invariants_on_real_charts():
    for r in _random(300):
        assert CODE_RE.match(r["code"]), r["code"]
        for a in ta.AXES:
            ax = r["axes"][a]
            total = ax["evidence_a"] + ax["evidence_b"]
            assert ax["index"] == ta._index(ax["evidence_a"], ax["evidence_b"])
            assert 0 <= ax["index"] <= 100
            if ax["band"] == "insufficient":
                assert total < ta.MIN_EVIDENCE and ax["pole"] is None
            if ax["pole"]:
                assert ax["letter"] == ta.POLES[a][ax["side"]]["letter"]
                assert ax["band"] in (("strong_a", "moderate_a") if ax["side"] == "a" else ("strong_b", "moderate_b"))
            assert not any(e["key"].startswith("perspective") for e in ax["evidence"]) or a == "execution"


# --------------------------------------------------------------------------- #
# Baseline and time scan
# --------------------------------------------------------------------------- #
def test_baseline_is_current_and_complete():
    assert base.MODEL_VERSION == ta.MODEL_VERSION, "regenerate: scripts/gen_team_axes_baseline.py"
    for a in ta.AXES:
        assert abs(sum(base.POLE_SHARES_PCT[a].values()) - 100) < 0.1
        assert abs(sum(base.BAND_SHARES_PCT[a].values()) - 100) < 0.1
        cdf = base.INDEX_CDF_PCT[a]
        assert len(cdf) == 101 and cdf[-1] == 100.0 and cdf == sorted(cdf)


def test_population_block():
    t = axes({31, 7, 8, 1}, {"TT", "GC"})["axes"]["transfer"]
    assert t["population"]["pole_pct"] == base.POLE_SHARES_PCT["transfer"]["structured"]
    assert t["population"]["index_percentile"] == base.INDEX_CDF_PCT["transfer"][int(t["index"])]


def test_time_scan_skipped_below_five_minutes():
    assert ta.time_stability((1966, 12, 9, 17, 0, 0, 6), 1.0) is None


def test_time_scan_full_day():
    ts = ta.time_stability((1966, 12, 9, 17, 0, 0, 6), 720)
    assert ts["samples"] == 49 and ts["offsets_min"][0] == -720.0
    for a in ta.AXES:
        assert abs(sum(ts["axes"][a]["poles"].values()) - 1) < 0.01
        assert ts["axes"][a]["index_min"] <= ts["axes"][a]["index_max"]
