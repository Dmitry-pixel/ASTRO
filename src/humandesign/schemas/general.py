from pydantic import BaseModel, Field
from typing import Dict

class HealthResponse(BaseModel):
    """Schema for the health check response."""
    status: str = Field(..., description="Operational status of the API")
    version: str = Field(..., description="Current version of the API")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the response")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Status of core dependencies")
