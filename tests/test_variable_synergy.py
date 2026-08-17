import pytest
from humandesign.services.composite import calculate_variable_synergy
from humandesign.schemas.response_models import VariableSynergyDetail

def test_variable_symmetrical_left():
    """Test two Strategic (Left-heavy) people."""
    # LLLL shorthand
    v1 = {"top_right": {"value": "left"}, "top_left": {"value": "left"}, "bottom_right": {"value": "left"}, "bottom_left": {"value": "left"}}
    v2 = {"top_right": {"value": "left"}, "top_left": {"value": "left"}, "bottom_right": {"value": "left"}, "bottom_left": {"value": "left"}}
    
    result = calculate_variable_synergy(v1, v2)
    
    assert isinstance(result, VariableSynergyDetail)
    assert result.alignment == "Symmetrical Force (Strategic)"
    assert "Execution" in result.operational_insight
    assert "Activity" in result.lifestyle_insight

def test_variable_polarized_motivation():
    """Test one Strategic, one Receptive Motivation (Top Right)."""
    v1 = {"top_right": {"value": "left"}} # Strategic
    v2 = {"top_right": {"value": "right"}} # Receptive
    
    result = calculate_variable_synergy(v1, v2)
    
    assert result.alignment == "Polarized Harmony"
    assert "Visionary" in result.operational_insight or "Artist" in result.operational_insight

def test_variable_neutral():
    """Test missing arrow data."""
    result = calculate_variable_synergy({}, {})
    assert result.alignment == "Individual Flow"
    assert "neutral" in result.shorthand_synergy.lower()
