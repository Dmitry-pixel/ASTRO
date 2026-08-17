"""Birth parameters are required - the API must not invent them.

Earlier versions defaulted every field to a fixed chart (1968-02-21, Kirikkale),
so a request that dropped its parameters through an integration bug still returned
a plausible 200 response. These tests pin the replacement behaviour.
"""

from fastapi.testclient import TestClient

from humandesign.api import app
from humandesign.dependencies import verify_token

app.dependency_overrides[verify_token] = lambda: True
client = TestClient(app)


def test_v2_empty_body_is_rejected():
    """An empty body must fail validation rather than return a stand-in chart."""
    response = client.post("/v2/calculate", json={})
    assert response.status_code == 422

    missing = {tuple(err["loc"]) for err in response.json()["detail"]}
    for field in ("year", "month", "day", "hour", "minute"):
        assert ("body", field) in missing, f"{field} should be reported as missing"


def test_v2_partial_body_is_rejected():
    """A body missing only the time of day is still incomplete."""
    response = client.post("/v2/calculate", json={"year": 1968, "month": 2, "day": 21})
    assert response.status_code == 422


def test_v2_requires_place_or_coordinates():
    """Location cannot be guessed either."""
    response = client.post(
        "/v2/calculate",
        json={"year": 1968, "month": 2, "day": 21, "hour": 11, "minute": 0},
    )
    assert response.status_code == 422
    assert "latitude" in response.text and "longitude" in response.text


def test_v2_coordinates_satisfy_the_location_requirement():
    """Supplying coordinates instead of a place name passes validation."""
    from humandesign.schemas.v2.calculate import CalculateRequestV2

    model = CalculateRequestV2(
        year=1968, month=2, day=21, hour=11, minute=0, latitude=39.84, longitude=33.51
    )
    assert model.place is None


def test_v1_requires_birth_parameters():
    """The v1 query interface follows the same rule."""
    response = client.get("/calculate")
    assert response.status_code == 422


def test_v1_requires_place_or_coordinates():
    response = client.get("/calculate?year=1968&month=2&day=21&hour=11&minute=0")
    assert response.status_code == 422
