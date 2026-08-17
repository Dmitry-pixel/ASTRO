import pytest
import numpy as np
from humandesign.utils.calculations import sanitize_to_native

def test_sanitize_to_native_numpy_types():
    # Setup test data with various numpy types
    numpy_data = {
        "int64": np.int64(42),
        "int32": np.int32(100),
        "float64": np.float64(3.14159),
        "float32": np.float32(1.23),
        "array": np.array([1, 2, 3]),
        "nested": {
            "inner_array": np.array([4, 5, 6]),
            "inner_int": np.int64(999)
        },
        "list_of_arrays": [np.array([7, 8]), np.int64(10)]
    }

    # Execute
    clean_data = sanitize_to_native(numpy_data)

    # Verify
    assert isinstance(clean_data["int64"], int)
    assert clean_data["int64"] == 42
    
    assert isinstance(clean_data["int32"], int)
    assert clean_data["int32"] == 100
    
    assert isinstance(clean_data["float64"], float)
    assert abs(clean_data["float64"] - 3.14159) < 1e-5
    
    assert isinstance(clean_data["float32"], float)
    
    assert isinstance(clean_data["array"], list)
    assert clean_data["array"] == [1, 2, 3]
    
    assert isinstance(clean_data["nested"]["inner_array"], list)
    assert clean_data["nested"]["inner_array"] == [4, 5, 6]
    assert isinstance(clean_data["nested"]["inner_int"], int)
    
    assert isinstance(clean_data["list_of_arrays"][0], list)
    assert clean_data["list_of_arrays"][0] == [7, 8]
    assert isinstance(clean_data["list_of_arrays"][1], int)

def test_sanitize_to_native_passthrough():
    # Setup standard python data
    standard_data = {
        "x": 1,
        "y": [1, 2],
        "z": "string"
    }
    
    # Execute
    clean_data = sanitize_to_native(standard_data)
    
    # Verify exact match
    assert clean_data == standard_data

from unittest.mock import patch

@patch("humandesign.features.calc_single_hd_features")
def test_enrich_transit_metadata(mock_calc):
    from humandesign.utils.calculations import enrich_transit_metadata
    
    # Setup mock return (12 items)
    mock_calc.return_value = (
         "Generator", # b_typ
         "Solar Plexus", # b_auth
         "Right Angle Cross of Sphinx", # b_inc_cross
         "Right Angle", # b_inc_cross_typ
         (1, 3), # b_profile (Investigator Martyr)
         1, # b_definition (Single)
         {}, # b_date_to_gate
         {"Sacral", "Solar Plexus"}, # b_active_chakras
         {"meaning": [("Channel X", "Desc X")], "gate": [1], "ch_gate": [2]}, # b_active_channels
         "1980-01-01", # b_date_str
         "1980-01-01 12:00", # b_create_date_str
         {} # b_variables
    )
     
    composite_data = {
         "transit_date": "2026-01-01T12:00:00Z",
         "composite_authority": "Emotional",
         "new_defined_centers": ["Throat"],
         "new_defined_channels": [(10, 20)],
         "new_channel_meanings": [("Channel Y", "Desc Y")],
         "raw_transit_gates": {"planets": ["Sun"], "gate": [10], "line": [1], "color": [1], "tone": [1], "base": [1], "lon": [0.0]}
    }
     
    # Call
    result = enrich_transit_metadata(
         birth_timestamp=(1980, 1, 1, 12, 0, 0, 0),
         transit_year=2026, transit_month=1, transit_day=1, transit_hour=12, transit_minute=0,
         place="London", calculation_place="Paris",
         composite_data=composite_data
    )
     
    # Verify
    meta = result["meta"]
    assert meta["energy_type"] == "Generator"
    assert "1/3" in meta["profile"]
    assert meta["calculation_place"] == "Paris"
    assert meta["birth_date"] == "1980-01-01T12:00:00Z"
    
    # Verify structure
    assert "composite_changes" in result
    assert "planetary_transits" in result
    assert len(result["planetary_transits"]) == 1
    assert result["planetary_transits"][0]["planets"] == "Sun"

