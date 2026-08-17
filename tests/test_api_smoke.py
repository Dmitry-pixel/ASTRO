from fastapi.testclient import TestClient
from humandesign.api import app

client = TestClient(app)

def test_read_main():
    response = client.get("/docs")
    assert response.status_code == 200
