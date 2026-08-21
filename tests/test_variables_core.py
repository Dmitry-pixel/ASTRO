import pytest
from humandesign.features.core import calc_single_hd_features

# Positional contract of calc_single_hd_features, mirroring the mapping the
# function itself uses when it builds its result dict. The tuple grew from 12
# to 18 entries when quarter, cross_name, line_counts, sun_roles,
# yin_yang_balance and contour were added; this test still pinned the old
# length and had been failing ever since.
FIELDS = [
    "typ", "auth", "inc_cross", "inc_cross_typ", "profile", "definition",
    "date_to_gate_dict", "active_chakra", "active_channel", "birth_date",
    "create_date", "variables", "quarter", "cross_name", "line_counts",
    "sun_roles", "yin_yang_balance", "contour",
]
VARIABLES_INDEX = FIELDS.index("variables")


@pytest.fixture(scope="module")
def result():
    # Kirikkale, Turkey: 1968-02-21 11:00:00, UTC+3
    return calc_single_hd_features((1968, 2, 21, 11, 0, 0, 3.0))


def test_return_matches_the_positional_contract(result):
    """Every field the caller unpacks by index must be present."""
    assert len(result) == len(FIELDS)


def test_calc_single_hd_features_returns_variables(result):
    variables = result[VARIABLES_INDEX]
    assert isinstance(variables, dict)
    assert "top_right" in variables
    assert variables["top_right"]["value"] in ["left", "right"]


def test_all_four_variable_corners_are_present(result):
    variables = result[VARIABLES_INDEX]
    for corner in ("top_right", "bottom_right", "top_left", "bottom_left"):
        assert corner in variables, f"{corner} missing from variables"
        assert variables[corner]["value"] in ["left", "right"]
