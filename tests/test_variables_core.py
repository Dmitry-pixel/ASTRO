import pytest
from humandesign.features.core import calc_single_hd_features

def test_calc_single_hd_features_returns_variables():
    """Test that calc_single_hd_features now includes variables in its return."""
    # Kirikkale, Turkey: 1968-02-21 11:00:00, UTC+3
    timestamp = (1968, 2, 21, 11, 0, 0, 3.0)
    result = calc_single_hd_features(timestamp)
    
    # We expect variables to be part of the result now.
    # New return length is 12.
    assert len(result) == 12
    variables = result[11]
    assert isinstance(variables, dict)
    assert "top_right" in variables
    assert variables["top_right"]["value"] in ["left", "right"]
