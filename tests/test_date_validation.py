"""Birth dates must exist before they reach the ephemeris.

Out-of-range components used to travel all the way into the Swiss Ephemeris
call and surface as a 500, and an impossible day (31 April, 29 February in a
common year) silently shifted the chart. Both interfaces now reject them with
a 422 before any calculation happens.
"""

import pytest
from fastapi.testclient import TestClient

from humandesign.api import app
from humandesign.dependencies import verify_token
from humandesign.utils.date_utils import validate_calendar_date

app.dependency_overrides[verify_token] = lambda: True
client = TestClient(app)

VALID = {
    "year": 1968,
    "month": 2,
    "day": 21,
    "hour": 11,
    "minute": 0,
    "latitude": 39.84,
    "longitude": 33.51,
}


def _v1_query(**overrides):
    params = {**VALID, **overrides}
    return "&".join(f"{k}={v}" for k, v in params.items())


@pytest.mark.parametrize(
    "field,value",
    [
        ("month", 0),
        ("month", 13),
        ("day", 0),
        ("day", 32),
        ("hour", 24),
        ("hour", -1),
        ("minute", 60),
        ("second", 60),
    ],
)
def test_v1_rejects_out_of_range_components(field, value):
    response = client.get(f"/calculate?{_v1_query(**{field: value})}")
    assert response.status_code == 422, response.text


@pytest.mark.parametrize(
    "field,value",
    [
        ("month", 0),
        ("month", 13),
        ("day", 32),
        ("hour", 24),
        ("minute", 60),
        ("second", 60),
    ],
)
def test_v2_rejects_out_of_range_components(field, value):
    response = client.post("/v2/calculate", json={**VALID, field: value})
    assert response.status_code == 422, response.text


@pytest.mark.parametrize(
    "year,month,day",
    [
        (2025, 2, 29),  # common year
        (2025, 4, 31),
        (2025, 6, 31),
        (2025, 9, 31),
        (2025, 11, 31),
    ],
)
def test_impossible_days_are_rejected(year, month, day):
    """A day the month does not have must not be normalised away."""
    query = _v1_query(year=year, month=month, day=day)
    assert client.get(f"/calculate?{query}").status_code == 422

    body = {**VALID, "year": year, "month": month, "day": day}
    assert client.post("/v2/calculate", json=body).status_code == 422


def test_leap_day_is_accepted_by_the_validator():
    """29 February in a leap year is a date and must pass the check."""
    validate_calendar_date(2024, 2, 29)


def test_validator_message_names_the_month():
    with pytest.raises(ValueError, match="out of range for month 4"):
        validate_calendar_date(2025, 4, 31)
