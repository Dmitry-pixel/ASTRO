from fastapi.testclient import TestClient
from humandesign.api import app

client = TestClient(app)

def test_calculate_endpoint_variables():
    """Test that /calculate returns dynamic variables."""
    # Data for a known chart
    headers = {"Authorization": "Bearer 12345678"}
    response = client.get("/calculate?year=1968&month=2&day=21&hour=11&minute=0&place=Europe/Istanbul&gender=male", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    variables = data["general"]["variables"]
    assert isinstance(variables, dict)
    assert "top_right" in variables
    assert "bottom_right" in variables
    assert "top_left" in variables
    assert "bottom_left" in variables
    
    # Values should be "left" or "right"
    # Values should be "left" or "right"
    # Filter out 'short_code' or strict check keys
    direction_keys = ["top_right", "bottom_right", "top_left", "bottom_left"]
    for k in direction_keys:
        v = variables[k]
        assert v["value"] in ["left", "right"]

    # Optional: Compare with another date to potentially see different variables
    response2 = client.get("/calculate?year=1990&month=1&day=1&hour=12&minute=0&place=Europe/London&gender=female", headers=headers)
    assert response2.status_code == 200
    data2 = response2.json()
    variables2 = data2["general"]["variables"]
    
    # While it could be the same, this checks the structure is consistent
    assert isinstance(variables2, dict)
