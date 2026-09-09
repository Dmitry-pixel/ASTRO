"""time_precision_min: how precisely the birth time is known.

The parameter never changes an arrow, only the confidence flag beside it.
A solar arrow moves 2.46" per minute of uncertainty against a tone 93.75" wide,
so half an hour of doubt is already wider than the cell.

The reference chart is Sam, 1966-12-09 17:00, UTC+6 - the same one used to
verify the ephemeris work, so a regression here shows up against known numbers.
"""

import pytest
from fastapi.testclient import TestClient

from humandesign import api as hd_api
from humandesign import dependencies as hd_dependencies

hd_api.app.dependency_overrides[hd_dependencies.verify_token] = lambda: True
client = TestClient(hd_api.app)

BIRTH = {
    "year": 1966, "month": 12, "day": 9, "hour": 17, "minute": 0,
    "place": "Asia/Almaty",
}
ARROWS = ("top_right", "bottom_right", "top_left", "bottom_left")
SOLAR = ("top_right", "top_left")  # Motivation and Digestion ride the Sun


def _v1(**extra):
    r = client.get("/calculate", params={**BIRTH, **extra})
    assert r.status_code == 200, r.text
    return r.json()["general"]["variables"]


def _v2(**extra):
    body = {**BIRTH, "include": ["variables"], **extra}
    r = client.post("/v2/calculate", json=body)
    assert r.status_code == 200, r.text
    return r.json()["variables"]


def test_default_is_one_minute_and_is_echoed_back():
    """Omitting the parameter must not change the existing behaviour."""
    v = _v1()
    assert v["time_precision_min"] == 1.0
    assert v["short_code"] == "PLL DLR"
    assert v["low_confidence_arrows"] == ["bottom_left"]


def test_arrows_never_move_with_precision():
    """Precision drives the flag, not the answer."""
    codes = {p: _v1(time_precision_min=p)["short_code"] for p in (1, 30, 720)}
    assert set(codes.values()) == {"PLL DLR"}, codes


def test_required_margin_grows_with_uncertainty():
    need = [
        _v1(time_precision_min=p)["top_right"]["required_arcsec"]
        for p in (1, 30, 720)
    ]
    assert need[0] < need[1] < need[2], need


def test_solar_arrows_lose_confidence_at_half_an_hour():
    v = _v1(time_precision_min=30)
    for key in SOLAR:
        assert v[key]["confidence"] == "low", (key, v[key])
        assert v[key]["limiting_factor"] == "time"
    assert v["all_arrows_confident"] is False


def test_unknown_time_flags_every_solar_arrow():
    """Noon substituted: 720 minutes of doubt.

    Not every arrow goes low. The oscillating true node barely moves in twelve
    hours, so a node arrow with enough margin legitimately stays confident -
    that is the model being honest, not a missing check. The solar arrows,
    which move roughly a degree a day, cannot survive it.
    """
    v = _v1(time_precision_min=720)
    for key in SOLAR:
        assert v[key]["confidence"] == "low", (key, v[key])
    assert v["time_precision_min"] == 720.0
    assert v["all_arrows_confident"] is False


def test_out_of_range_precision_is_rejected():
    r = client.get("/calculate", params={**BIRTH, "time_precision_min": 1441})
    assert r.status_code == 422


@pytest.mark.parametrize("precision", [1, 30, 720])
def test_v2_carries_the_same_confidence_payload(precision):
    """v2 used to drop every reliability field on the floor."""
    v1 = _v1(time_precision_min=precision)
    v2 = _v2(time_precision_min=precision)

    assert v2["time_precision_min"] == float(precision)
    assert v2["low_confidence_arrows"] == v1["low_confidence_arrows"]
    assert v2["all_arrows_confident"] == v1["all_arrows_confident"]
    for key in ARROWS:
        assert v2[key]["confidence"] == v1[key]["confidence"]
        assert v2[key]["margin_arcsec"] == v1[key]["margin_arcsec"]
        assert v2[key]["required_arcsec"] == v1[key]["required_arcsec"]
        assert v2[key]["limiting_factor"] == v1[key]["limiting_factor"]


def test_v2_default_matches_v1_default():
    assert _v2()["low_confidence_arrows"] == _v1()["low_confidence_arrows"]
