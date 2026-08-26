import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from humandesign.api import app

client = TestClient(app)

def test_health_check_pysweph_success():
    """Test health check when pysweph is working."""
    with patch('swisseph.calc_ut') as mock_calc:
        # Mock successful calculation: returns (xx, retflag, serr).
        # retflag must carry SEFLG_SWIEPH (2): the ephemeris guard reads it to
        # tell Swiss Ephemeris from a silent Moshier fallback. retflag=0 is not
        # a value pyswisseph ever returns for a successful call.
        mock_calc.return_value = ([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 2, "")
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["dependencies"]["pysweph"].startswith("ready")

def test_health_check_pysweph_failure():
    """Test health check when pysweph fails."""
    # Patch at the source where it's called in health_utils
    with patch('humandesign.utils.health_utils.swe.calc_ut', side_effect=Exception("Ephemeris files not found")):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["dependencies"]["pysweph"] == "error"
