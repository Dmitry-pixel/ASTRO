from fastapi.testclient import TestClient
from humandesign.api import app

client = TestClient(app)

def test_health_check_endpoint():
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data
    assert "dependencies" in data
