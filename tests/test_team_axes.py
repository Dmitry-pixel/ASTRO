"""Team dynamics model v1.2 — rule-level tests.

Synthetic charts pin each agreed rule; a sample of real charts pins the
invariants that tie index, band, pole and code together.

The decisions these tests exist to protect, in the order they were agreed:
complete 13-channel Throat set, centre status weight 2 on both scored
information axes, dangling gates from the axis' own centre only, individual
circuit at 2 in Processing, 46-29 on the planned side, Perspective in Execution
only, Decision categorical, Root/Sacral a separate field, Integration read as
closed/bridged, and no ``insufficient`` anywhere.
"""
import datetime as dt
import random
import re

import pytest

from humandesign.features import team_axes as ta
from humandesign.features import team_axes_baseline as base
from humandesign.features.core import hd_features

CODE_RE = re.compile(r"^[SN~]·[FR~]·[CH–]·[PA~]$")


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
    assert ta._band(idx) == band


def test_no_insufficient_band_exists():
    """Agreed: three values per axis — pole A, pole B, mixed. Never 'no data'."""
    assert "insufficient" not in ta.BAND_RU
    for gates, centres in (((), ()), ((17, 62), {"AA", "TT"}), ((11,), ())):
        for a in ta.SCORED_AXES:
            assert axes(gates, centres)["axes"][a]["band"] != "insufficient"


def test_mixed_is_a_value_not_a_gap():
    t = axes({21, 45, 13, 33, 10, 20}, {"TT", "GC", "HT"})["axes"]["transfer"]
    assert t["evidence_a"] == t["evidence_b"] and t["band"] == "mixed"
    assert (t["pole"], t["letter"], t["side"]) == ("mixed", "~", None)


# --------------------------------------------------------------------------- #
# Transfer
# --------------------------------------------------------------------------- #
def test_throat_status_weighs_two_both_ways():
    assert ("TT определён", "a", 2.0) in keys(axes(centres={"TT"})["axes"]["transfer"])
    assert ("TT открыт", "b", 2.0) in keys(axes()["axes"]["transfer"])


def test_all_thirteen_throat_channels_are_present():
    channels = {r[1] for r in ta.RULES["transfer"] if r[0] == "channel"}
    assert channels == {(17, 62), (16, 48), (7, 31), (23, 43), (21, 45),
                        (35, 36), (12, 22), (20, 57), (13, 33), (11, 56),
                        (1, 8), (10, 20), (20, 34)}


def test_channels_added_in_v12():
    assert ("16-48", "a", 3.0) in keys(axes({16, 48}, {"TT"})["axes"]["transfer"])
    assert ("21-45", "a", 2.0) in keys(axes({21, 45}, {"TT"})["axes"]["transfer"])


def test_1_8_is_emergent_not_structured():
    """Reversed from v1.1, where 8-1 sat on the structured side."""
    assert ("1-8", "b", 2.0) in keys(axes({1, 8}, {"TT", "GC"})["axes"]["transfer"])


def test_no_secondary_axis_discount():
    """Each axis is scored on its own table at full weight."""
    t = axes({17, 62, 23, 43, 20, 34}, {"AA", "TT", "SL"})["axes"]["transfer"]
    assert ("17-62", "a", 3.0) in keys(t)
    assert ("23-43", "a", 2.0) in keys(t)
    assert ("20-34", "b", 2.0) in keys(t)
    p = axes({11, 56}, {"AA", "TT"})["axes"]["processing"]
    assert ("11-56", "b", 2.0) in keys(p)


def test_transfer_dangling_gates_come_from_the_throat_only():
    """Gate 62 is Ajna, 48 Spleen, 34 Sacral — none of them are Throat gates."""
    dangling = {r[1] for r in ta.RULES["transfer"] if r[0] == "dangling_gate"}
    assert dangling == ta.CENTRE_GATES["TT"]
    assert dangling == {62, 23, 56, 16, 20, 31, 8, 33, 35, 12, 45}
    t = axes({17, 48, 34})["axes"]["transfer"]
    assert not any(k.startswith("ворота") for k, _, _ in keys(t))


def test_gate_inside_a_complete_channel_is_not_counted_twice():
    t = axes({35, 36}, {"TT", "SP"})["axes"]["transfer"]
    assert ("35-36", "b", 3.0) in keys(t) and ("ворота 35", "b", 1.0) not in keys(t)
    t = axes({35}, set())["axes"]["transfer"]
    assert ("ворота 35", "b", 1.0) in keys(t)


# --------------------------------------------------------------------------- #
# Processing
# --------------------------------------------------------------------------- #
def test_ajna_status_weighs_two_both_ways():
    p = axes(centres={"AA"})["axes"]["processing"]
    assert (p["index"], p["band"], p["pole"]) == (25.0, "moderate_a", "fixed")
    p = axes()["axes"]["processing"]
    assert (p["index"], p["band"], p["pole"]) == (75.0, "moderate_b", "relative")


def test_circuit_weights():
    """logic 3 · abstract 2 · individual 2 — individual never above logic."""
    w = {r[1]: r[3] for r in ta.RULES["processing"] if r[0] == "channel"}
    assert w[(4, 63)] == w[(17, 62)] == 3.0
    assert w[(47, 64)] == w[(11, 56)] == 2.0
    assert w[(43, 23)] == w[(24, 61)] == 2.0


def test_individual_channel_outweighs_its_own_dangling_gate():
    ch = axes({43, 23}, {"AA", "TT"})["axes"]["processing"]
    gate = axes({43}, set())["axes"]["processing"]
    assert ("43-23", "a", 2.0) in keys(ch)
    assert ("ворота 43", "a", 1.0) in keys(gate)


def test_processing_dangling_gates_come_from_the_ajna_only():
    """Gate 64 (Head) left the set in v1.2, gate 24 (Ajna) joined it."""
    dangling = {r[1] for r in ta.RULES["processing"] if r[0] == "dangling_gate"}
    assert dangling == ta.CENTRE_GATES["AA"] == {4, 17, 43, 24, 11, 47}
    assert ("ворота 64", "b", 1.0) not in keys(axes({64})["axes"]["processing"])
    assert ("ворота 24", "a", 1.0) in keys(axes({24})["axes"]["processing"])


def test_defined_ajna_can_be_relative():
    """Defined is not the same as Fixed — the point of the whole three-level split."""
    p = axes({47, 64, 11, 56}, {"AA", "HD", "TT"})["axes"]["processing"]
    assert p["field"]["status"] == "defined" and p["pole"] == "relative"


@pytest.mark.parametrize("gates,centres,status", [
    ((17, 62), {"AA", "TT"}, "defined"),
    ((17,), set(), "undefined"),
    ((), set(), "open"),
])
def test_centre_status_has_three_values(gates, centres, status):
    assert axes(gates, centres)["axes"]["processing"]["field"]["status"] == status


# --------------------------------------------------------------------------- #
# Decision — categorical
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("auth,pole,mode", [
    ("SL", "internal", "response"), ("SN", "internal", "instant"),
    ("HT", "internal", "will"), ("HT_GC", "internal", "will"),
    ("GC", "internal", "articulated"), ("SP", "relational", "delayed"),
    ("outer", "relational", "external"), ("lunar", "relational", "lunar"),
])
def test_decision_is_the_authority(auth, pole, mode):
    d = axes(auth=auth)["axes"]["decision"]
    assert (d["kind"], d["index"], d["band"]) == ("categorical", None, None)
    assert (d["pole"], d["mode"]) == (pole, mode)
    assert d["mode_label_ru"] and d["mode_ru"]


def test_g_channels_never_move_the_pole():
    """Three C channels must not outweigh an H authority."""
    plain = axes(auth="SP")["axes"]["decision"]
    loaded = axes({1, 8, 7, 31, 2, 14}, {"GC", "TT", "SL"}, auth="SP")["axes"]["decision"]
    assert plain["pole"] == loaded["pole"] == "relational"
    assert loaded["g_support"]["c_signal"] == 9.0 and loaded["g_support"]["h_signal"] == 0.0


def test_g_gate_not_counted_inside_its_channel():
    g = axes({1, 8}, {"GC", "TT"})["axes"]["decision"]["g_support"]
    assert [e["key"] for e in g["evidence"]] == ["1-8"]
    g = axes({1}, set())["axes"]["decision"]["g_support"]
    assert [e["key"] for e in g["evidence"]] == ["ворота 1"]


def test_open_centres_and_definition_never_enter_decision():
    for definition in (1, 2, 3, 4):
        assert axes(auth="SP", definition=definition)["axes"]["decision"]["pole"] == "relational"
    assert axes(auth="SL", centres={"SL"})["axes"]["decision"]["pole"] == \
           axes(auth="SL", centres={"SL", "SP", "AA"})["axes"]["decision"]["pole"]


@pytest.mark.parametrize("auth,definition,code", [
    ("SL", 1, "internal_closed"), ("SL", 2, "internal_bridged"),
    ("SP", 1, "relational_closed"), ("SP", 3, "relational_bridged"),
])
def test_integration_reading(auth, definition, code):
    assert axes(auth=auth, definition=definition)["axes"]["decision"]["integration_reading"]["code"] == code


# --------------------------------------------------------------------------- #
# Execution
# --------------------------------------------------------------------------- #
def test_execution_channel_set():
    rules = {r[1]: (r[2], r[3]) for r in ta.RULES["execution"] if r[0] == "channel"}
    assert rules[(46, 29)] == ("a", 2.0)          # planned, agreed 2026-09-13
    assert rules[(2, 14)] == ("a", 2.0)           # added in v1.2
    assert rules[(54, 32)] == ("a", 1.0)
    assert {c for c, (s, _) in rules.items() if s == "b"} == \
           {(3, 60), (20, 34), (57, 34), (20, 57), (34, 10), (38, 28)}


def test_perspective_alone_decides_and_is_flagged():
    r = axes(persp="right")
    e = r["axes"]["execution"]
    assert (e["basis"], e["pole"], e["band"], e["index"]) == ("perspective_only", "adaptive", "moderate_b", 66.7)
    assert e["hypothesis_share"] == 1.0
    assert any(f["code"] == "perspective_only" for f in r["flags"])


def test_perspective_does_not_override_a_channel():
    e = axes({5, 15}, {"GC", "RT"}, persp="right")["axes"]["execution"]
    assert e["pole"] == "planned" and e["basis"] == "channels"


def test_perspective_is_used_only_in_execution():
    left = axes({31, 7}, {"TT", "GC"}, persp="left")
    right = axes({31, 7}, {"TT", "GC"}, persp="right")
    for a in ("transfer", "processing"):
        assert left["axes"][a]["index"] == right["axes"][a]["index"]
    assert left["axes"]["decision"]["pole"] == right["axes"]["decision"]["pole"]


def test_perspective_near_boundary_is_flagged():
    assert any(f["code"] == "perspective_near_boundary" for f in axes(persp="left", pconf="low")["flags"])


def test_root_and_sacral_do_not_vote_for_a_pole():
    a = axes(centres={"RT", "SL"}, persp="left")["axes"]["execution"]
    b = axes(centres=set(), persp="left")["axes"]["execution"]
    assert a["index"] == b["index"]


@pytest.mark.parametrize("centres,code", [
    ({"RT", "SL"}, "autonomous"), ({"RT"}, "stimulus_led"),
    ({"SL"}, "energy_led"), (set(), "context_dependent"),
])
def test_energy_profile_is_a_separate_field(centres, code):
    ep = axes(centres=centres)["axes"]["execution"]["energy_profile"]
    assert ep["code"] == code and ep["label_ru"] and ep["text_ru"]


# --------------------------------------------------------------------------- #
# Integration
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("definition,reading,raw", [
    (0, "reflector", "R"), (1, "closed", "I1"), (2, "bridged", "I2"),
    (3, "bridged", "I3"), (4, "bridged", "I4"),
])
def test_integration_reading_and_raw(definition, reading, raw):
    i = axes(definition=definition)["integration"]
    assert (i["reading"], i["raw"]) == (reading, raw)
    assert i["label_ru"] and i["text_ru"]


# --------------------------------------------------------------------------- #
# Reference chart and invariants
# --------------------------------------------------------------------------- #
def test_reference_chart_sam():
    d = hd_features(1966, 12, 9, 17, 0, 0, 6).birth_creat_date_to_gate()
    r = ta.compute_from_date_to_gate(d)
    assert r["code"] == "N·~·H·P"
    ax = r["axes"]
    assert (ax["transfer"]["index"], ax["processing"]["index"], ax["execution"]["index"]) == (63.6, 50.0, 20.0)
    assert ax["decision"]["index"] is None and ax["decision"]["pole"] == "relational"
    assert ax["processing"]["pole"] == "mixed"
    assert ax["execution"]["basis"] == "channels"
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
        for a in ta.SCORED_AXES:
            ax = r["axes"][a]
            assert ax["index"] == ta._index(ax["evidence_a"], ax["evidence_b"])
            assert 0 <= ax["index"] <= 100
            assert ax["band"] != "insufficient"
            if ax["side"]:
                assert ax["letter"] == ta.POLES[a][ax["side"]]["letter"]
                assert ax["band"] in (("strong_a", "moderate_a") if ax["side"] == "a"
                                      else ("strong_b", "moderate_b"))
            else:
                assert (ax["pole"], ax["letter"]) == ("mixed", "~")
            assert a == "execution" or not any(e["key"].startswith("perspective") for e in ax["evidence"])
        assert r["axes"]["decision"]["index"] is None


def test_every_chart_gets_a_value_on_every_axis():
    for r in _random(200, seed=11):
        for a in ta.SCORED_AXES:
            assert r["axes"][a]["pole"] in {ta.POLES[a]["a"]["code"], ta.POLES[a]["b"]["code"], "mixed"}
        assert r["axes"]["decision"]["pole"] in {"internal", "relational"}


# --------------------------------------------------------------------------- #
# Baseline and time scan
# --------------------------------------------------------------------------- #
def test_baseline_is_current_and_complete():
    assert base.MODEL_VERSION == ta.MODEL_VERSION, "regenerate: scripts/gen_team_axes_baseline.py"
    for a in ta.AXES:
        assert abs(sum(base.POLE_SHARES_PCT[a].values()) - 100) < 0.1
        assert abs(sum(base.BAND_SHARES_PCT[a].values()) - 100) < 0.1
    for a in ta.SCORED_AXES:
        cdf = base.INDEX_CDF_PCT[a]
        assert len(cdf) == 101 and cdf[-1] == 100.0 and cdf == sorted(cdf)


def test_baseline_has_no_insufficient_share():
    for a in ta.SCORED_AXES:
        assert "insufficient" not in base.BAND_SHARES_PCT[a]
        assert base.POLE_SHARES_PCT[a].get("none", 0) == 0


def test_population_block():
    t = axes({31, 7, 16, 48}, {"TT", "GC", "SN"})["axes"]["transfer"]
    assert t["population"]["pole_pct"] == base.POLE_SHARES_PCT["transfer"]["structured"]
    assert t["population"]["index_percentile"] == base.INDEX_CDF_PCT["transfer"][int(t["index"])]


def test_time_scan_skipped_below_five_minutes():
    assert ta.time_stability((1966, 12, 9, 17, 0, 0, 6), 1.0) is None


def test_time_scan_full_day():
    ts = ta.time_stability((1966, 12, 9, 17, 0, 0, 6), 720)
    assert ts["samples"] == 49 and ts["offsets_min"][0] == -720.0
    for a in ta.AXES:
        assert abs(sum(ts["axes"][a]["poles"].values()) - 1) < 0.01
    assert ts["axes"]["decision"]["index_min"] is None
    assert ts["axes"]["transfer"]["index_min"] <= ts["axes"]["transfer"]["index_max"]
