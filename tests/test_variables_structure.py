from fastapi.testclient import TestClient
from humandesign.api import app

client = TestClient(app)

def test_variables_nested_structure():
    """Test that variables are returned as a nested object with metadata."""
    headers = {"Authorization": "Bearer 12345678"}
    # Kirikkale, Turkey: 1968-02-21 11:00:00
    response = client.get("/calculate?year=1968&month=2&day=21&hour=11&minute=0&place=Kirikkale, Turkey&gender=male", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    variables = data["general"]["variables"]
    
    # Check top_left (Digestion)
    assert "top_left" in variables
    tl = variables["top_left"]
    assert isinstance(tl, dict)
    assert tl["value"] in ["left", "right"]
    assert tl["name"] == "Digestion"
    assert tl["aspect"] == "Design (Brain)"
    assert "def_type" in tl
    assert tl["def_type"] in ["Active", "Passive"]
    
    # Check bottom_left (Environment)
    bl = variables["bottom_left"]
    assert isinstance(bl, dict)
    assert bl["name"] == "Environment"
    assert bl["aspect"] == "Design (Body)"
    assert bl["def_type"] in ["Observed", "Observer"]

    # Check top_right (Motivation)
    tr = variables["top_right"]
    assert isinstance(tr, dict)
    assert tr["name"] == "Motivation"
    assert tr["aspect"] == "Personality (Mind)"
    assert tr["def_type"] in ["Strategic", "Receptive"]

    # Check bottom_right (Perspective)
    br = variables["bottom_right"]
    assert isinstance(br, dict)
    assert br["name"] == "Perspective"
    assert br["aspect"] == "Personality (View)"
    assert br["def_type"] in ["Focused", "Peripheral"]
