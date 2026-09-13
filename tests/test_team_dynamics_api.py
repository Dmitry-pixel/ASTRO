"""team_dynamics in the calculation responses and the /analyze/team-dynamics layer.

Coordinates are explicit; nothing reaches Nominatim.
"""
import pytest
from fastapi.testclient import TestClient

from humandesign import auth as auth_module
from humandesign.api import app

client = TestClient(app)
TEST_DOMAIN = "team-dynamics-tests.local"

SAM = {"year": 1966, "month": 12, "day": 9, "hour": 17, "minute": 0,
       "place": "Asia/Almaty", "latitude": 43.25, "longitude": 76.95}

CAST = {
    "Anna":  dict(place="Moscow, Russia",    year=1985, month=3,  day=14, hour=9,  minute=25, latitude=55.7558,  longitude=37.6173),
    "Boris": dict(place="Berlin, Germany",   year=1979, month=11, day=2,  hour=17, minute=40, latitude=52.5200,  longitude=13.4050),
    "Chen":  dict(place="Singapore",         year=1991, month=7,  day=21, hour=6,  minute=5,  latitude=1.3521,   longitude=103.8198),
    "Dana":  dict(place="Sao Paulo, Brazil", year=1988, month=1,  day=9,  hour=22, minute=15, latitude=-23.5505, longitude=-46.6333),
    "Erik":  dict(place="Sydney, Australia", year=1996, month=5,  day=30, hour=13, minute=50, latitude=-33.8688, longitude=151.2093),
    "Farah": dict(place="Cairo, Egypt",      year=1983, month=9,  day=3,  hour=4,  minute=10, latitude=30.0444,  longitude=31.2357),
    "Gita":  dict(place="Mumbai, India",     year=1990, month=6,  day=15, hour=8,  minute=0,  latitude=19.0760,  longitude=72.8777),
    "Hugo":  dict(place="Lisbon, Portugal",  year=1975, month=12, day=28, hour=20, minute=45, latitude=38.7223,  longitude=-9.1393),
    "Iris":  dict(place="Toronto, Canada",   year=2000, month=4,  day=7,  hour=11, minute=5,  latitude=43.6532,  longitude=-79.3832),
}


@pytest.fixture(scope="module", autouse=True)
def _real_auth():
    saved = dict(app.dependency_overrides)
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.update(saved)


@pytest.fixture(scope="module")
def auth():
    conn = auth_module._get_db()
    try:
        row = conn.execute("SELECT token FROM sites WHERE domain = ?", (TEST_DOMAIN,)).fetchone()
    finally:
        conn.close()
    token = row["token"] if row else auth_module.add_site(TEST_DOMAIN)["token"]
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Single chart
# --------------------------------------------------------------------------- #
def test_v1_carries_team_dynamics(auth):
    r = client.get("/calculate", params=SAM, headers=auth)
    assert r.status_code == 200, r.text
    td = r.json()["team_dynamics"]
    assert td["code"] == "N·~·H·P"
    assert td["time_stability"] is None          # default precision 1 min — no scan
    assert set(td["axes"]) == {"transfer", "processing", "decision", "execution"}


def test_v2_carries_team_dynamics_with_scan(auth):
    r = client.post("/v2/calculate", json={**SAM, "time_precision_min": 30}, headers=auth)
    assert r.status_code == 200, r.text
    td = r.json()["team_dynamics"]
    assert td["code"] == "N·~·H·P"
    assert td["time_stability"]["precision_min"] == 30.0
    assert td["axes"]["decision"]["authority"] == "SP"
    assert td["axes"]["decision"]["kind"] == "categorical"
    assert td["axes"]["execution"]["basis"] == "channels"
    assert td["integration"]["reading"] == "closed"
    assert td["model_version"] == "1.2"


def test_v2_dot_path_include_and_exclude(auth):
    r = client.post("/v2/calculate", json={**SAM, "include": ["team_dynamics.code"]}, headers=auth)
    assert r.status_code == 200, r.text
    assert r.json() == {"team_dynamics": {"code": "N·~·H·P"}}
    r = client.post("/v2/calculate", json={**SAM, "exclude": ["team_dynamics"]}, headers=auth)
    assert "team_dynamics" not in r.json()


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Team layer
# --------------------------------------------------------------------------- #
def test_team_endpoint_requires_a_token():
    r = client.post("/analyze/team-dynamics", json={"participants": {k: CAST[k] for k in ("Anna", "Boris")}})
    assert r.status_code in (401, 403)


def test_team_endpoint_rejects_one(auth):
    r = client.post("/analyze/team-dynamics", json={"participants": {"Anna": CAST["Anna"]}}, headers=auth)
    assert r.status_code == 422


def test_composition_counts_and_order(auth):
    body = {"participants": {k: CAST[k] for k in ("Anna", "Boris", "Chen", "Dana", "Erik")}}
    r = client.post("/analyze/team-dynamics", json=body, headers=auth)
    assert r.status_code == 200, r.text
    tm = r.json()["team_matrix"]
    assert tm["kind"] == "composition" and tm["size"] == 5
    assert [row["id"] for row in tm["matrix"]["rows"]] == list(body["participants"])
    for a in ("transfer", "processing", "decision", "execution"):
        comp = tm["composition"][a]
        assert sum(comp["counts"].values()) == 5
        for item in comp["items"]:
            assert item["count"] == len(item["members"]) and item["label_ru"] and item["meaning_ru"]
        everyone = sorted(m for item in comp["items"] for m in item["members"])
        assert everyone == sorted(body["participants"])


@pytest.mark.parametrize("block", ["decision_modes", "integration", "energy_profiles"])
def test_counted_values_carry_code_label_and_meaning(auth, block):
    body = {"participants": {k: CAST[k] for k in ("Anna", "Boris", "Chen", "Dana", "Erik")}}
    tm = client.post("/analyze/team-dynamics", json=body, headers=auth).json()["team_matrix"]
    items = tm[block]["items"]
    assert items and tm[block]["summary_ru"]
    for i in items:
        assert i["code"] and i["label_ru"] and i["meaning_ru"]
        assert i["count"] == len(i["members"])
    assert sum(i["count"] for i in items) == 5


def test_no_statistics_anywhere_in_the_team_layer(auth):
    body = {"participants": {k: CAST[k] for k in ("Anna", "Boris", "Chen", "Dana", "Erik")}}
    tm = client.post("/analyze/team-dynamics", json=body, headers=auth).json()["team_matrix"]
    for gone in ("absence", "overrepresentation", "risk_hypotheses", "polarization",
                 "tests_run", "expected_false_signals_at_0_05", "axes_summary",
                 "report_rules_ru"):
        assert gone not in tm
    for a in ("transfer", "processing", "decision", "execution"):
        for gone in ("mean_index", "std_index", "min_index", "max_index"):
            assert gone not in tm["composition"][a]


def test_list_and_object_participants_agree(auth):
    order = ("Anna", "Boris", "Chen")
    as_list = client.post("/analyze/team-dynamics",
                          json={"participants": [CAST[k] for k in order]}, headers=auth)
    as_object = client.post("/analyze/team-dynamics",
                            json={"participants": {str(i): CAST[k] for i, k in enumerate(order, 1)}},
                            headers=auth)
    assert as_list.status_code == as_object.status_code == 200, as_list.text
    a, b = as_list.json()["team_matrix"], as_object.json()["team_matrix"]
    assert [row["id"] for row in a["matrix"]["rows"]] == ["1", "2", "3"]
    assert a == b


def test_nine_people_matrix_and_bridging(auth):
    body = {"participants": {**CAST, "Anna": {**CAST["Anna"], "time_precision_min": 60}}}
    r = client.post("/analyze/team-dynamics", json=body, headers=auth)
    assert r.status_code == 200, r.text
    d = r.json()
    tm = d["team_matrix"]
    assert d["meta"]["analysis"] == "team_dynamics"
    assert tm["profiles"]["Anna"]["time_stability"]["precision_min"] == 60.0
    assert tm["profiles"]["Boris"]["time_stability"] is None
    for row in tm["matrix"]["rows"]:
        assert row["code"] == tm["profiles"][row["id"]]["code"]
    for b in tm["bridging"]:
        assert b["components_after"] < b["components_before"]
        assert b["bridge"] != b["closes_for"]
        assert b["bridge"] in b["text_ru"] and b["closes_for"] in b["text_ru"]
        assert "{bridge}" in b["text_template_ru"] and "{closes_for}" in b["text_template_ru"]
    assert "проксимальн" not in tm.get("bridging_legend_ru", "")
    # the team code is the value most participants carry, per axis
    for i, a in enumerate(("transfer", "processing", "decision", "execution")):
        counts = tm["composition"][a]["counts"]
        top = max(counts.values())
        winners = [c for c, k in counts.items() if k == top]
        letter = tm["team_code"].split("·")[i]
        if len(winners) > 1:
            assert letter == "–"
        else:
            assert letter != "–"


# --------------------------------------------------------------------------- #
# Panel templates
# --------------------------------------------------------------------------- #
def test_panel_reads_no_removed_fields():
    """The single-chart «Команда» tab shipped 3.12.0 still reading v1.1 fields.

    Nothing rendered and nothing failed — the tab just showed dashes. These are
    the field names the panel JS must not mention any more.
    """
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    panel = root / "src" / "humandesign" / "templates" / "panel"
    js = "\n".join(p.read_text(encoding="utf-8") for p in panel.glob("*.html"))
    for gone in ("integration.code", "ig.code", "f.stability", "field.stability",
                 "axes_summary", "overrepresentation", "risk_hypotheses",
                 "mean_index", "std_index", "insufficient", "bridging_note_ru"):
        assert gone not in js, f"panel still reads removed field: {gone}"


def test_panel_renders_every_block_the_api_ships():
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    panel = root / "src" / "humandesign" / "templates" / "panel"
    js = "\n".join(p.read_text(encoding="utf-8") for p in panel.glob("*.html"))
    for shipped in ("energy_profile", "g_support", "status_ru", "integration_reading",
                    "composition", "decision_modes", "energy_profiles",
                    "bridging_legend_ru"):
        # text_template_ru is deliberately absent: it exists for consuming sites
        # that substitute their own display names. The panel has real ids and
        # renders text_ru directly.
        assert shipped in js, f"API ships {shipped} and nothing in the panel renders it"
