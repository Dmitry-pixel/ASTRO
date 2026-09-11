"""team_dynamics in the calculation responses and the /analyze/team-dynamics layer.

Coordinates are explicit; nothing reaches Nominatim.
"""
import pytest
from fastapi.testclient import TestClient

from humandesign import auth as auth_module
from humandesign.api import app
from humandesign.relational.team_matrix import binom_sf, p_absent

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
    assert td["code"] == "F·D·H·P·I1"
    assert td["time_stability"] is None          # default precision 1 min — no scan
    assert set(td["axes"]) == {"transfer", "processing", "decision", "execution"}


def test_v2_carries_team_dynamics_with_scan(auth):
    r = client.post("/v2/calculate", json={**SAM, "time_precision_min": 30}, headers=auth)
    assert r.status_code == 200, r.text
    td = r.json()["team_dynamics"]
    assert td["code"] == "F·D·H·P·I1"
    assert td["time_stability"]["precision_min"] == 30.0
    assert td["axes"]["decision"]["evidence"][0]["key"] == "SP"
    assert td["axes"]["execution"]["basis"] == "perspective_only"
    assert td["model_version"] == "1.1"


def test_v2_dot_path_include_and_exclude(auth):
    r = client.post("/v2/calculate", json={**SAM, "include": ["team_dynamics.code"]}, headers=auth)
    assert r.status_code == 200, r.text
    assert r.json() == {"team_dynamics": {"code": "F·D·H·P·I1"}}
    r = client.post("/v2/calculate", json={**SAM, "exclude": ["team_dynamics"]}, headers=auth)
    assert "team_dynamics" not in r.json()


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def test_binomial_tail_is_exact():
    assert binom_sf(0, 5, 0.3) == 1.0
    assert binom_sf(6, 5, 0.3) == 0.0
    assert binom_sf(5, 5, 0.5) == pytest.approx(1 / 32)
    # "three of six decide by instant recognition" at 7.9% — thresholds doc: k=3 is robust at n=4
    assert binom_sf(3, 6, 0.079) < 0.05
    assert p_absent(8, 0.5) == pytest.approx(1 / 256)


# --------------------------------------------------------------------------- #
# Team layer
# --------------------------------------------------------------------------- #
def test_team_endpoint_requires_a_token():
    r = client.post("/analyze/team-dynamics", json={"participants": {k: CAST[k] for k in ("Anna", "Boris")}})
    assert r.status_code in (401, 403)


def test_team_endpoint_rejects_one(auth):
    r = client.post("/analyze/team-dynamics", json={"participants": {"Anna": CAST["Anna"]}}, headers=auth)
    assert r.status_code == 422


def test_small_team_does_not_evaluate_absence(auth):
    body = {"participants": {k: CAST[k] for k in ("Anna", "Boris", "Chen", "Dana", "Erik")}}
    r = client.post("/analyze/team-dynamics", json=body, headers=auth)
    assert r.status_code == 200, r.text
    tm = r.json()["team_matrix"]
    assert tm["size"] == 5
    assert tm["absence"]["evaluated"] is False and tm["absence"]["items"] == []
    assert [row["name"] for row in tm["matrix"]["rows"]] == list(body["participants"])
    for o in tm["overrepresentation"]:
        assert o["k"] >= 2 and o["p_value"] < 0.05
        assert (o["statement_ru"] is not None) == (o["level"] == "robust")


def test_nine_people_matrix_and_bridging(auth):
    body = {"participants": {**CAST, "Anna": {**CAST["Anna"], "time_precision_min": 60}}}
    r = client.post("/analyze/team-dynamics", json=body, headers=auth)
    assert r.status_code == 200, r.text
    d = r.json()
    tm = d["team_matrix"]
    assert d["meta"]["analysis"] == "team_dynamics"
    assert tm["absence"]["evaluated"] is True
    assert tm["profiles"]["Anna"]["time_stability"]["precision_min"] == 60.0
    assert tm["profiles"]["Boris"]["time_stability"] is None
    for row in tm["matrix"]["rows"]:
        assert row["code"] == tm["profiles"][row["name"]]["code"]
    for b in tm["bridging"]:
        assert b["components_after"] < b["components_before"]
        assert b["bridge"] != b["closes_for"]
    # the team code is the majority pole per axis
    from humandesign.features.team_axes import POLES
    for i, a in enumerate(("transfer", "processing", "decision", "execution")):
        s = tm["axes_summary"][a]
        ka, kb = len(s["poles"][POLES[a]["a"]["code"]]), len(s["poles"][POLES[a]["b"]["code"]])
        want = POLES[a]["a"]["letter"] if ka > kb else (POLES[a]["b"]["letter"] if kb > ka else "–")
        assert tm["team_code"].split("·")[i] == want
        idx = [row[a]["index"] for row in tm["matrix"]["rows"]]
        assert s["min_index"] == min(idx) and s["max_index"] == max(idx)
    for risk in tm["risk_hypotheses"]:
        assert risk["k"] >= 3 and "Гипотеза" in risk["text_ru"]
