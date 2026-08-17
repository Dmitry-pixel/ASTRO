import pytest
from pydantic import ValidationError
from datetime import datetime
from humandesign.schemas.general import HealthResponse

def test_health_response_schema_valid():
    """Test the HealthResponse schema with valid data."""
    data = {
        "status": "ok",
        "version": "1.5.1",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {"pysweph": "ready"}
    }
    schema = HealthResponse(**data)
    assert schema.status == "ok"
    assert schema.version == "1.5.1"
    assert "pysweph" in schema.dependencies

def test_health_response_schema_invalid():
    """Test the HealthResponse schema with invalid data."""
    data = {
        "status": "ok",
        # missing version
        "timestamp": datetime.now().isoformat(),
        "dependencies": {}
    }
    with pytest.raises(ValidationError):
        HealthResponse(**data)
