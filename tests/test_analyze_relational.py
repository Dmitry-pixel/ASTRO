"""End-to-end tests for /analyze/*.

Coordinates are supplied explicitly so the suite never reaches Nominatim;
`timezonefinder` resolves the zone offline.
"""
import os

import pytest
from fastapi.testclient import TestClient

from humandesign.api import app
from humandesign import auth as auth_module

client = TestClient(app)

CAST = {
    "Anna":  dict(place="Moscow, Russia",    year=1985, month=3,  day=14, hour=9,  minute=25,
                  latitude=55.7558,  longitude=37.6173),
    "Boris": dict(place="Berlin, Germany",   year=1979, month=11, day=2,  hour=17, minute=40,
                  latitude=52.5200,  longitude=13.4050),
    "Chen":  dict(place="Singapore",         year=1991, month=7,  day=21, hour=6,  minute=5,
                  latitude=1.3521,   longitude=103.8198),
    "Dana":  dict(place="Sao Paulo, Brazil", year=1988, month=1,  day=9,  hour=22, minute=15,
                  latitude=-23.5505, longitude=-46.6333),
    "Erik":  dict(place="Sydney, Australia", year=1996, month=5,  day=30, hour=13, minute=50,
                  latitude=-33.8688, longitude=151.2093),
    "Farah": dict(place="Cairo, Egypt",      year=1983, month=9,  day=3,  hour=4,  minute=10,
                  latitude=30.0444,  longitude=31.2357),
    "Gita":  dict(place="Mumbai, India",     year=1990, month=6,  day=15, hour=8,  minute=0,
                  latitude=19.0760,  longitude=72.8777),
    "Hugo":  dict(place="Lisbon, Portugal",  year=1975, month=12, day=28, hour=20, minute=45,
                  latitude=38.7223,  longitude=-9.1393),
    "Iris":  dict(place="Toronto, Canada",   year=2000, month=4,  day=7,  hour=11, minute=5,
                  latitude=43.6532,  longitude=-79.3832),
    "Jonas": dict(place="Oslo, Norway",      year=1982, month=2,  day=19, hour=23, minute=55,
                  latitude=59.9139,  longitude=10.7522),
}
PAIR = {k: CAST[k] for k in ("Anna", "Boris")}
FIVE = {k: CAST[k] for k in ("Anna", "Boris", "Chen", "Dana", "Erik")}
TEN = dict(CAST)

#: sample payloads for manual inspection; gitignored
OUT_DIR = os.path.join(os.path.dirname(__file__), "_output")


TEST_DOMAIN = "relational-tests.local"


@pytest.fixture(scope="module", autouse=True)
def _real_auth():
    """Other test modules install a global `verify_token` override at import time
    and never remove it. Drop it for this module so the endpoints are exercised
    through real bearer-token verification, then put it back."""
    saved = dict(app.dependency_overrides)
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.update(saved)


@pytest.fixture(scope="module", autouse=True)
def _token():
    """A site token so verify_token accepts the requests.

    api_auth.db survives between runs, so reuse the site if it is already there.
    """
    conn = auth_module._get_db()
    try:
        row = conn.execute("SELECT token FROM sites WHERE domain = ?", (TEST_DOMAIN,)).fetchone()
    finally:
        conn.close()
    yield row["token"] if row else auth_module.add_site(TEST_DOMAIN)["token"]


@pytest.fixture()
def auth(_token):
    return {"Authorization": f"Bearer {_token}"}


def _dump(name, payload):
    os.makedirs(OUT_DIR, exist_ok=True)
    import json
    with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def post(path, body, headers):
    r = client.post(path, json=body, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", ["/analyze/composite", "/analyze/penta",
                                  "/analyze/wa", "/analyze/maia-penta"])
def test_endpoints_require_a_token(path):
    r = client.post(path, json={"participants": PAIR})
    assert r.status_code in (401, 403)


# --------------------------------------------------------------------------- #
# Composite — 2 people
# --------------------------------------------------------------------------- #
def test_composite_pair(auth):
    data = post("/analyze/composite", {"participants": PAIR, "verbosity": "standard"}, auth)
    _dump("composite_pair.json", data)

    assert data["meta"]["entity"]["code"] == "dyad"
    assert data["meta"]["verbosity"] == "standard"
    d = data["dyad"]

    formula = d["composite"]["formula"]
    assert formula["defined"] + formula["open"] == 9
    assert formula["code"] == f"{formula['defined']}+{formula['open']}"

    totals = d["connections"]["totals"]
    assert totals["total"] == sum(totals[k] for k in
                                  ("electromagnetic", "compromise", "dominance", "companionship"))
    assert totals["total"] == len(d["connections"]["channels"])
    assert len(d["composite"]["centre_dynamics"]) == 9

    for ch in d["connections"]["channels"]:
        assert ch["type"]["code"] in {"electromagnetic", "compromise", "dominance", "companionship"}
        conditioning = ch["type"]["code"] in ("compromise", "dominance")
        assert (ch["direction"] is not None) == conditioning
        holders = ch["holders"]
        full = [n for n, h in holders.items() if h["holds_full_channel"]]
        if ch["type"]["code"] == "companionship":
            assert len(full) == 2
        elif conditioning:
            assert len(full) == 1
        else:
            assert len(full) == 0


def test_all_four_maia_classes_are_reachable(auth):
    """The defect this engine replaces could only ever emit 'electromagnetic'."""
    seen = set()
    for body in ({"participants": PAIR}, {"participants": FIVE}, {"participants": TEN}):
        data = post("/analyze/maia-penta", body, auth)
        for dyad in data["dyad_matrix"]:
            for ch in dyad["connections"]["channels"]:
                seen.add(ch["type"]["code"])
    assert seen == {"electromagnetic", "compromise", "dominance", "companionship"}


def test_composite_is_order_independent(auth):
    fwd = post("/analyze/composite", {"participants": PAIR}, auth)["dyad"]
    rev = post("/analyze/composite",
               {"participants": {k: CAST[k] for k in ("Boris", "Anna")}}, auth)["dyad"]
    assert fwd["composite"]["formula"] == rev["composite"]["formula"]
    assert sorted(fwd["composite"]["defined_centres"]) == sorted(rev["composite"]["defined_centres"])
    assert fwd["connections"]["totals"] == rev["connections"]["totals"]
    assert fwd["role_conflicts"]["load"] == rev["role_conflicts"]["load"]


def test_role_conflicts_name_a_direction(auth):
    d = post("/analyze/composite", {"participants": PAIR}, auth)["dyad"]
    rc = d["role_conflicts"]
    assert rc["count"] == len(rc["channels"])
    for item in rc["channels"]:
        assert item["conditions"] != item["conditioned"]
        assert item["type"] in ("compromise", "dominance")
    per_person = rc["load"]
    assert sum(v["conditions"] for v in per_person.values()) == rc["count"]
    assert sum(v["conditioned"] for v in per_person.values()) == rc["count"]


def test_composite_rejects_three(auth):
    r = client.post("/analyze/composite", json={"participants": {k: CAST[k]
                    for k in ("Anna", "Boris", "Chen")}}, headers=auth)
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# Penta — 3-5
# --------------------------------------------------------------------------- #
def test_penta_five(auth):
    data = post("/analyze/penta", {"participants": FIVE, "group_type": "business"}, auth)
    _dump("penta_five.json", data)

    assert data["meta"]["entity"]["code"] == "penta"
    penta = data["penta"]
    anatomy = penta["penta_anatomy"]
    assert set(anatomy["upper_penta"]["channels"]) == {"8-1", "31-7", "33-13"}
    assert set(anatomy["lower_penta"]["channels"]) == {"15-5", "2-14", "46-29"}
    for key in ("vision_score", "action_score", "stability_score"):
        assert 0 <= penta["analytical_metrics"][key] <= 100


def test_penta_timestamp_is_not_frozen(auth):
    data = post("/analyze/penta", {"participants": FIVE}, auth)
    ts = data["penta"]["meta"]["generated_at"]
    assert ts != "2026-01-19T00:00:00Z"
    assert ts.endswith("Z") and len(ts) == 20


@pytest.mark.parametrize("names", [("Anna", "Boris"), tuple(CAST)])
def test_penta_rejects_wrong_sizes(auth, names):
    r = client.post("/analyze/penta", json={"participants": {k: CAST[k] for k in names}},
                    headers=auth)
    assert r.status_code == 422


def test_penta_group_type_changes_the_vocabulary(auth):
    biz = post("/analyze/penta", {"participants": FIVE, "group_type": "business"}, auth)
    fam = post("/analyze/penta", {"participants": FIVE, "group_type": "family"}, auth)
    assert biz["penta"]["meta"]["group_type"] == "business"
    assert fam["penta"]["meta"]["group_type"] == "family"
    assert (biz["penta"]["penta_anatomy"]["lower_penta"]["channels"]["2-14"]["business_label"]
            != fam["penta"]["penta_anatomy"]["lower_penta"]["channels"]["2-14"]["business_label"])


# --------------------------------------------------------------------------- #
# WA — 6+
# --------------------------------------------------------------------------- #
def test_wa_ten(auth):
    data = post("/analyze/wa", {"participants": TEN, "group_type": "business"}, auth)
    _dump("wa_ten.json", data)

    entity = data["meta"]["entity"]
    assert entity["code"] == "wa" and entity["size"] == 10
    assert entity["doctrine_implemented"] is True

    field = data["group_field"]
    assert field["structure"] == {
        "gates": 64, "channels": 36, "centres": 9,
        "note": field["structure"]["note"], "note_ru": field["structure"]["note_ru"],
    }
    cov = field["coverage"]
    assert cov["channels_total"] == field["structure"]["channels"]
    assert cov["gates_total"] == field["structure"]["gates"]
    assert 0 <= cov["channels_defined"] <= 36
    assert cov["channels_defined"] + field["gaps"]["missing_channel_count"] == 36
    assert len(field["centres"]["defined"]) + len(field["centres"]["open"]) == 9
    assert sum(field["type_mix"].values()) == 10
    assert len(field["contributions"]) == 10
    assert field["fragility"]["keystone_channel_count"] <= cov["channels_defined"]


def test_wa_rejects_five(auth):
    r = client.post("/analyze/wa", json={"participants": FIVE}, headers=auth)
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# Hybrid
# --------------------------------------------------------------------------- #
def test_hybrid_five_carries_penta(auth):
    data = post("/analyze/maia-penta", {"participants": FIVE, "group_type": "business"}, auth)
    _dump("hybrid_five.json", data)
    assert data["dyad_count"] == 10
    assert "penta" in data and "group_field" not in data
    summary = data["matrix_summary"]
    assert summary["connection_totals"]["total"] == sum(
        d["connections"]["totals"]["total"] for d in data["dyad_matrix"])
    assert summary["most_conditioning"] in FIVE
    assert summary["most_conditioned"] in FIVE


def test_hybrid_ten_carries_group_field(auth):
    data = post("/analyze/maia-penta", {"participants": TEN, "verbosity": "compact"}, auth)
    _dump("hybrid_ten_compact.json", data)
    assert data["dyad_count"] == 45
    assert "group_field" in data and "penta" not in data


# --------------------------------------------------------------------------- #
# verbosity
# --------------------------------------------------------------------------- #
def test_verbosity_levels_differ(auth):
    sizes = {}
    for level in ("compact", "standard", "full"):
        r = client.post("/analyze/composite",
                        json={"participants": PAIR, "verbosity": level}, headers=auth)
        assert r.status_code == 200
        sizes[level] = len(r.content)
        data = r.json()
        d = data["dyad"]
        if level == "compact":
            assert "channels" not in d["connections"]
            assert "centre_dynamics" not in d["composite"]
            assert "variables" not in data["participants"]["Anna"]
        else:
            assert d["connections"]["channels"]
            assert d["composite"]["centre_dynamics"]
    assert sizes["compact"] < sizes["standard"] < sizes["full"]


def test_full_verbosity_enriches_channels_and_keeps_all_activations(auth):
    data = post("/analyze/composite", {"participants": PAIR, "verbosity": "full"}, auth)
    _dump("composite_pair_full.json", data)

    anna = data["participants"]["Anna"]
    assert anna["activation_count"] == 26
    assert len(anna["activations"]) == 26, "design must not overwrite personality"
    nodes = [a for a in anna["activations"] if a["planet"] == "North_Node"]
    assert {a["polarity"] for a in nodes} == {"personality", "design"}

    enriched = [c for c in data["dyad"]["connections"]["channels"] if "reference" in c]
    assert enriched, "hd_data.sqlite reference missing at full verbosity"
    ref = enriched[0]["reference"]
    assert ref["name"].startswith("The Channel of")
    assert ref["description"] and ref["design_purpose"]
    assert len(ref["gifts"]) == 2


def test_legacy_verbosity_aliases_are_accepted(auth):
    for legacy, modern in (("all", "full"), ("partial", "compact")):
        data = post("/analyze/composite", {"participants": PAIR, "verbosity": legacy}, auth)
        assert data["meta"]["verbosity"] == modern


# --------------------------------------------------------------------------- #
# Correctness guards on what the previous engine got wrong
# --------------------------------------------------------------------------- #
def test_half_hour_timezone_is_preserved(auth):
    """Mumbai is +05:30. The deleted engine truncated it to +05:00."""
    data = post("/analyze/composite",
                {"participants": {"Gita": CAST["Gita"], "Anna": CAST["Anna"]}}, auth)
    assert data["participants"]["Gita"]["utc_offset"] == 5.5
    assert data["participants"]["Gita"]["tz"] == "Asia/Kolkata"


def test_unresolvable_participant_fails_loudly(auth, monkeypatch):
    """A participant that cannot be resolved surfaces as 422 naming itself,
    instead of vanishing from a 200.

    The geocoder is stubbed rather than fed a nonsense place name: Nominatim
    answers "Nowhere Land 12345" with real coordinates from a CI runner, so the
    original version of this test passed only where the network was unreachable.
    """
    from humandesign.relational import persons
    monkeypatch.setattr(persons, "get_latitude_longitude", lambda place: (None, None))

    broken = dict(PAIR)
    broken["Ghost"] = dict(place="Nowhere Land 12345", year=1990, month=1, day=1,
                           hour=0, minute=0)
    r = client.post("/analyze/maia-penta", json={"participants": broken}, headers=auth)
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["participant"] == "Ghost"
    assert "geocoding" in detail["error"]


def test_unusable_timezone_fails_loudly(auth):
    """The other resolution failure path, and this one needs no network at all:
    an IANA-shaped place that is not a real zone."""
    broken = dict(PAIR)
    broken["Ghost"] = dict(place="Europe/Nowhere_At_All", year=1990, month=1, day=1,
                           hour=0, minute=0, latitude=50.0, longitude=10.0)
    r = client.post("/analyze/maia-penta", json={"participants": broken}, headers=auth)
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["participant"] == "Ghost"
    assert "timezone" in detail["error"]


def test_booleans_stay_booleans(auth):
    data = post("/analyze/wa", {"participants": TEN}, auth)
    assert isinstance(data["meta"]["entity"]["doctrine_implemented"], bool)
    d = post("/analyze/composite", {"participants": PAIR}, auth)["dyad"]
    assert isinstance(d["composite"]["bridges_split"]["bridged"], bool)
    for ch in d["connections"]["channels"]:
        assert isinstance(ch["new_in_composite"], bool)


def test_variable_synergy_reads_all_four_arrows(auth):
    d = post("/analyze/composite", {"participants": PAIR}, auth)["dyad"]
    vs = d["variable_synergy"]
    assert vs["compared_arrows"] == 4
    assert {a["arrow"] for a in vs["arrows"]} == {"top_left", "top_right",
                                                 "bottom_left", "bottom_right"}
    assert vs["shorthand"] == f"{vs['matched_arrows']}/4"


def test_impossible_date_is_rejected(auth):
    bad = {"A": dict(CAST["Anna"], month=2, day=30), "B": CAST["Boris"]}
    r = client.post("/analyze/composite", json={"participants": bad}, headers=auth)
    assert r.status_code == 422

# --------------------------------------------------------------------------- #
# Thresholds and OC16 (WA doctrine)
# --------------------------------------------------------------------------- #
def test_penta_accepts_seven_as_extended(auth):
    seven = {k: CAST[k] for k in list(CAST)[:7]}
    data = post("/analyze/penta", {"participants": seven}, auth)
    assert data["meta"]["entity"]["code"] == "extended_penta"
    assert data["meta"]["entity"]["doctrine_implemented"] is True
    scale = data["penta"]["meta"]["scale"]
    assert scale["canonical_range"] == [3, 5] and scale["extended"] is True


def test_penta_rejects_nine(auth):
    nine = {k: CAST[k] for k in list(CAST)[:9]}
    r = client.post("/analyze/penta", json={"participants": nine}, headers=auth)
    assert r.status_code == 422


def test_seven_is_an_extended_penta_not_a_wa(auth):
    seven = {k: CAST[k] for k in list(CAST)[:7]}
    data = post("/analyze/wa", {"participants": seven}, auth)
    assert data["meta"]["entity"]["code"] == "extended_penta"
    assert "oc16" not in data["group_field"]


def test_nine_is_a_wa_and_carries_oc16(auth):
    nine = {k: CAST[k] for k in list(CAST)[:9]}
    data = post("/analyze/wa", {"participants": nine}, auth)
    assert data["meta"]["entity"]["code"] == "wa"
    oc = data["group_field"]["oc16"]
    assert oc["structure"]["gates"] == 16
    assert oc["structure"]["channels"] == 6
    assert len(oc["departments"]) == 6
    assert len(oc["bridge_gates"]) == 4
    cov = oc["coverage"]
    assert cov["departments_defined"] + len(
        [d for d in oc["departments"] if d["status"] == "missing"]) == 6
    assert cov["gates_defined"] + len(cov["gates_missing"]) == 16


def test_oc16_tables_match_the_engine_constants():
    from humandesign import hd_constants
    from humandesign.relational import oc16

    assert len(oc16.OC16_GATES) == 16
    assert len(oc16.DEPARTMENTS) == 6
    for d in oc16.DEPARTMENTS:
        assert d["channel"] in hd_constants.CHANNEL_MEANING_DICT
        assert set(d["channel"]) == set(d["gates"])
    assert oc16.ALPHA_CHANNEL in hd_constants.CHANNEL_MEANING_DICT
    # the engine names 31-7 itself; the doctrine did not invent the term
    assert "alpha" in hd_constants.CHANNEL_MEANING_DICT[oc16.ALPHA_CHANNEL][0].lower()


def test_bridge_gates_are_exactly_the_upper_penta():
    """Doctrine says the WA binds Pentas. Mechanically the binding is the upper
    Penta: gates 1, 8, 7, 31 are channels 8-1 Implementation and 31-7 Planning."""
    from humandesign import hd_constants
    from humandesign.relational import oc16

    upper = hd_constants.PENTA_DEFINITIONS["upper_penta"]["channels"]
    upper_gates = {g for ch in upper.values() for g in ch["gates"]}
    assert set(oc16.BRIDGE_GATES) == upper_gates - {13, 33}
    assert set(oc16.BRIDGE_GATES) == {1, 7, 8, 31}


def test_alpha_reports_evidence_not_a_verdict(auth):
    data = post("/analyze/wa", {"participants": TEN}, auth)
    a = data["group_field"]["oc16"]["alpha"]
    assert a["channel_key"] == "31-7"
    assert "признал" in a["note_ru"]          # recognition is required, not derived
    tiers = [c["tier"] for c in a["candidates"]]
    order = {"canonical": 0, "partial": 1, "supporting": 2, "none": 3}
    assert tiers == sorted(tiers, key=lambda t: order[t])
    for c in a["candidates"]:
        if c["tier"] == "canonical":
            assert any(e["code"] == "channel_31_7" for e in c["evidence"])
    assert a["canonical_holders"] == [c["name"] for c in a["candidates"]
                                      if c["tier"] == "canonical"]


def test_profile_is_style_not_eligibility(auth):
    """Any profile can hold the Alpha position. The profile describes how someone
    would lead and how the field reads them — it must never move a candidate up
    the ranking, which is the misconception the doctrine explicitly corrects."""
    data = post("/analyze/wa", {"participants": TEN}, auth)
    a = data["group_field"]["oc16"]["alpha"]

    assert "profile" in a["not_ranked_by"] and "energy_type" in a["not_ranked_by"]
    assert a["ranked_by"] == ["channel_31_7", "channel_21_45", "gate_45", "channel_1_8"]

    for c in a["candidates"]:
        codes = {e["code"] for e in c["evidence"]}
        assert not any(code.startswith("profile") for code in codes)
        assert "type" not in codes
        assert c["evidence_count"] == len(c["evidence"])
        assert len(c["style"]) == len([l for l in c["profile_lines"] if 1 <= l <= 6])

    order = {"canonical": 0, "partial": 1, "supporting": 2, "none": 3}
    keys = [(order[c["tier"]], -c["evidence_count"], c["name"]) for c in a["candidates"]]
    assert keys == sorted(keys)


# --------------------------------------------------------------------------- #
# Penta blocks inside a WA
# --------------------------------------------------------------------------- #
def test_functional_zones_are_the_penta_gates():
    """The three zones are a different cut of the Penta's twelve gates, not a
    different set. Gate 13 belongs to zone 2 with its channel partner 33."""
    from humandesign import hd_constants
    from humandesign.relational import blocks

    assert set(blocks.FUNCTIONAL_GATES) == set(hd_constants.PENTA_GATES)
    assert len(blocks.FUNCTIONAL_GATES) == 12
    assert len(blocks.ZONES) == 3
    assert blocks.ZONE_OF_GATE[13] == "demonstration"
    assert blocks.ZONE_OF_GATE[33] == "demonstration"
    # every gate lands in exactly one zone
    seen = [g for z in blocks.ZONES for g in z["gates"]]
    assert len(seen) == len(set(seen)) == 12


def test_wa_falls_into_blocks_of_three_to_five(auth):
    data = post("/analyze/wa", {"participants": TEN}, auth)
    b = data["group_field"]["penta_blocks"]
    assert b["block_count"] >= 2
    seen = []
    for blk in b["blocks"]:
        assert blocks_min() <= blk["size"] <= blocks_max()
        seen.extend(blk["members"])
    # every participant is placed exactly once, minus the Alpha if one was set aside
    expected = set(TEN) - ({b["alpha"]} if b["alpha"] else set())
    assert sorted(seen) == sorted(expected)
    assert len(seen) == len(set(seen))


def blocks_min():
    from humandesign.relational import blocks
    return blocks.BLOCK_MIN


def blocks_max():
    from humandesign.relational import blocks
    return blocks.BLOCK_MAX


def test_blocks_are_deterministic(auth):
    """A consultant must be able to re-run a group and get the same blocks."""
    a = post("/analyze/wa", {"participants": TEN}, auth)["group_field"]["penta_blocks"]
    b = post("/analyze/wa", {"participants": TEN}, auth)["group_field"]["penta_blocks"]
    assert [x["members"] for x in a["blocks"]] == [x["members"] for x in b["blocks"]]


def test_blocks_report_zone_gaps_not_just_counts(auth):
    data = post("/analyze/wa", {"participants": TEN}, auth)
    b = data["group_field"]["penta_blocks"]
    for blk in b["blocks"]:
        assert len(blk["zones"]) == 3
        for z in blk["zones"]:
            if z["status"] == "gap":
                assert z["gap_ru"] and not z["covered_gates"]
            else:
                assert z["covered_gates"]
        assert blk["viable"] == (blk["zones_covered"] == 3)


def test_managing_penta_is_not_invented(auth):
    """Block heads and the managing Penta are roles, not activations. The payload
    must say so rather than guess."""
    data = post("/analyze/wa", {"participants": TEN}, auth)
    b = data["group_field"]["penta_blocks"]
    assert "not_computed_ru" in b
    for blk in b["blocks"]:
        assert "head" not in blk and "lead" not in blk


def test_blocks_absent_below_the_wa_threshold(auth):
    seven = {k: CAST[k] for k in list(CAST)[:7]}
    data = post("/analyze/wa", {"participants": seven}, auth)
    assert "penta_blocks" not in data["group_field"]
