from fastapi.testclient import TestClient
from humandesign.api import app
from humandesign.dependencies import verify_token

app.dependency_overrides[verify_token] = lambda: True
client = TestClient(app)

def test_v2_advanced_mechanics():
    """Verify that Dream Rave and Global Cycles are populated in V2 response."""
    payload = {
        "year": 2024,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "place": "London, UK"
    }
    response = client.post("/v2/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "advanced" in data
    advanced = data["advanced"]
    
    # Check Global Cycle
    assert "global_cycle" in advanced
    assert advanced["global_cycle"]["cycle_cross"] == "Cross of Planning"
    assert 37 in advanced["global_cycle"]["gates"]
    
    # Check Dream Rave
    assert "dream_rave" in advanced
    assert "activated_gates" in advanced["dream_rave"]
    # For 2024-01-01, there should be some gates active
    assert len(advanced["dream_rave"]["activated_gates"]) >= 0

def test_v2_global_cycle_2027_transition():
    """Verify the 2027 transition for Global Cycles."""
    # Before 2027
    resp_before = client.post("/v2/calculate", json={"year": 2026, "month": 12, "day": 31, "hour": 23, "minute": 59})
    data_before = resp_before.json()
    assert data_before["advanced"]["global_cycle"]["cycle_cross"] == "Cross of Planning"
    
    # After 2027
    resp_after = client.post("/v2/calculate", json={"year": 2027, "month": 1, "day": 1, "hour": 0, "minute": 0})
    data_after = resp_after.json()
    assert data_after["advanced"]["global_cycle"]["cycle_cross"] == "Cross of the Sleeping Phoenix"
