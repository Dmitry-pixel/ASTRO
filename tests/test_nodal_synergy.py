import pytest
from humandesign.services.composite import get_detailed_node_resonance
from humandesign.schemas.response_models import EnvironmentalResonanceDetail

def test_nodal_shared_frequency():
    """Test same gate nodal resonance."""
    p1_nodes = {11, 48} # North/South nodes
    p2_nodes = {11, 32}
    
    result = get_detailed_node_resonance(p1_nodes, p2_nodes)
    
    assert isinstance(result, EnvironmentalResonanceDetail)
    assert result.resonance_type == "Shared Frequency"
    assert 11 in result.gates
    assert "Industry" in result.operational_insight
    assert "social" in result.lifestyle_insight

def test_nodal_harmonic_pull():
    """Test opposite gates forming a nodal channel."""
    p1_nodes = {11, 48}
    p2_nodes = {56, 32} # 11-56 is a channel
    
    result = get_detailed_node_resonance(p1_nodes, p2_nodes)
    
    assert result.resonance_type == "Harmonic Pull"
    assert set(result.gates) == {11, 56}

def test_nodal_individual():
    """Test no resonance."""
    p1_nodes = {1, 2}
    p2_nodes = {3, 4}
    
    result = get_detailed_node_resonance(p1_nodes, p2_nodes)
    assert result.resonance_type == "Individual Path"
    assert len(result.gates) == 0
