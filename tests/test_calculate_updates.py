from fastapi.testclient import TestClient
from humandesign.api import app
from humandesign.dependencies import verify_token

client = TestClient(app)

# Override the auth dependency for testing
def override_verify_token():
    return True

app.dependency_overrides[verify_token] = override_verify_token

def test_calculate_with_new_fields():
    """Verify that /calculate returns age and zodiac_sign and accepts new query params."""
    params = {
        "year": 1987,
        "month": 1,
        "day": 20,
        "hour": 4,
        "minute": 30,
        "place": "Europe/Berlin", # Using TZ name directly to avoid geocoding issues in tests
        "gender": "male",
        "islive": True
    }
    response = client.get("/calculate", params=params)
    assert response.status_code == 200
    data = response.json()
    
    # Check general fields
    assert "general" in data
    general = data["general"]
    assert "age" in general
    assert isinstance(general["age"], int)
    assert general["age"] >= 37 # 1987 to 2025
    assert "zodiac_sign" in general
    assert general["zodiac_sign"] == "Capricorn" # Jan 20 is Capricorn
    assert general["gender"] == "male"
    assert general["islive"] is True

def test_calculate_backward_compatibility():
    """Verify that /calculate still works without the new optional fields."""
    params = {
        "year": 1987,
        "month": 1,
        "day": 20,
        "hour": 4,
        "minute": 30,
        "place": "Europe/London"
    }
    response = client.get("/calculate", params=params)
    assert response.status_code == 200
    data = response.json()
    general = data["general"]
    assert general["gender"] == "male"
    assert general["islive"] is True
    assert "age" in general
    assert "zodiac_sign" in general
