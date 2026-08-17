import pytest
from humandesign.features.core import get_penta
from humandesign.hd_constants import PENTA_GATES, PENTA_ZONES, PENTA_DEFINITIONS

def test_penta_constants_exist():
    """Verify that constants are correctly imported and structured."""
    assert "Upper" in PENTA_ZONES
    assert "upper_penta" in PENTA_DEFINITIONS

@pytest.fixture
def mock_rich_input():
    # User1: 8/1 (Implementation) - Design
    # User2: 31/7 (Planning) - Personality
    return {
        "User1": {
            "gate": [1, 8, 1], # 1 appears twice
            "line": [2, 3, 2], # Duplicate instance
            "label": ["des", "des", "des"]
        },
        "User2": {
            "gate": [7, 31],
            "line": [4, 5],
            "label": ["prs", "prs"]
        },
        "User3": {
            "gate": [13, 2], # 13, 2. No 33 or 14.
            "line": [1, 6],
            "label": ["prs", "des"]
        }
    }

def test_get_penta_v2_gold_standard(mock_rich_input):
    """Verify Gold Standard structure (Hierarchy, De-dup, Metrics)."""
    result = get_penta(mock_rich_input)
    
    # 1. Meta
    assert result["meta"]["penta_type"] in ["Family", "Business"]
    
    # 2. Anatomy Hierarchy
    anatomy = result["penta_anatomy"]
    assert "upper_penta" in anatomy
    assert "lower_penta" in anatomy
    
    # 3. Contributors & Deduplication
    # Channel 8-1 (User1 DOM). User1 defined Gate 1 twice in mock. Should appear simplified.
    ch_8_1 = anatomy["upper_penta"]["channels"]["8-1"]
    assert ch_8_1["status"] == "Active"
    assert ch_8_1["type"] == "DOM"
    
    contribs = ch_8_1["contributors"]
    assert "User1" in contribs
    # Check structure: User1 -> gate_1 -> {lines, polarities}
    g1_data = contribs["User1"]["gate_1"]
    assert 2 in g1_data["lines"]
    assert "Design" in g1_data["polarities"]

    # 4. Metrics
    metrics = result["analytical_metrics"]
    assert "vision_score" in metrics
    assert "action_score" in metrics
    assert metrics["stability_score"] == 10 # 0/3 backbone (2-14, 15-5, 46-29 missing)
    
    # 5. Gap Analysis
    # Channel 15-5 (Lower Penta) is Void
    ch_15_5 = anatomy["lower_penta"]["channels"]["15-5"]
    assert ch_15_5["status"] == "Inactive"
    gap = ch_15_5["gap_analysis"]
    assert gap is not None
    assert 15 in gap["missing_gates"]
    assert gap["severity"] == "CRITICAL" # 15-5 is backbone
    
    # 6. Hiring
    hiring = result["hiring_logic"]
    assert 14 in hiring["urgent_needs"]

def test_get_penta_v2_business_type(mock_rich_input):
    """Verify group_type override."""
    result = get_penta(mock_rich_input, group_type="business")
    assert result["meta"]["penta_type"] == "Business"

def test_penta_v2_semantics_diamond(mock_rich_input):
    """Verify Diamond Standard: Roles & Contextual Shadows."""
    # Mock has: User1(8,1), User2(7,31), User3(13,2).
    # Active Channels: 8-1 ("Implementation"), 31-7 ("Planning").
    
    # --- Test 1: Functional Roles (Who is the Planner?) ---
    result_biz = get_penta(mock_rich_input, group_type="business")
    
    assert "functional_roles" in result_biz
    roles = result_biz["functional_roles"]
    
    # 31-7 is Planning. User2 has both gates (7,31).
    # Logic note: Our mock says User2 has [7, 31]. 
    # So User2 should be in "Planning" role.
    assert "Planning" in roles
    assert "User2" in roles["Planning"]
    
    # 8-1 is Implementation. User1 has [1, 8, 1].
    assert "Implementation" in roles
    assert "User1" in roles["Implementation"]

    # --- Test 2: Contextual Shadows (Business vs Family) ---
    
    # Gate 2 is owned by User3.
    # Gate 14 is MISSING.
    # In Business, missing 14 = "Lack of Resources".
    # In Family, missing 14 = "Lack of Means".
    
    # Business Check
    ch_res_biz = result_biz["penta_anatomy"]["lower_penta"]["channels"]["2-14"]
    assert "Lack of Resources" in ch_res_biz["gap_analysis"]["shadow_themes"]
    
    # Family Check
    result_fam = get_penta(mock_rich_input, group_type="family")
    ch_res_fam = result_fam["penta_anatomy"]["lower_penta"]["channels"]["2-14"]
    assert "Lack of Means" in ch_res_fam["gap_analysis"]["shadow_themes"]
    
    # Check Skills Labels
    # Business: Gate 31 = Administration
    ch_plan_biz = result_biz["penta_anatomy"]["upper_penta"]["channels"]["31-7"]
    assert "Administration" in ch_plan_biz["business_label"]
    
    # Family: Gate 31 = Discipline
    ch_plan_fam = result_fam["penta_anatomy"]["upper_penta"]["channels"]["31-7"]
    assert "Discipline" in ch_plan_fam["business_label"]


def test_penta_v2_friction_gold():
    """Verify Friction/Competition logic with Gold Standard Codes."""
    # User1: [1, 8], User2: [1]
    mock = {
        "User1": {"gate": [1, 8], "line": [1,1], "label": ["prs","prs"]},
        "User2": {"gate": [1], "line": [2], "label": ["des"]},
        "User3": {"gate": [13], "line": [3], "label": ["prs"]} 
    }
    result = get_penta(mock)
    ch = result["penta_anatomy"]["upper_penta"]["channels"]["8-1"]
    
    # Upper Penta 8-1
    assert ch["status"] == "Active"
    
    # Type should be MIXED (Solo + EM)
    assert ch["type"] == "MIXED"
    assert "Mixed" in ch["label"]


def test_penta_v2_sovereign_semantics():
    """Verify Sovereign Standard: Line Semantics."""
    # User6 has Line 6. User1 has Line 1.
    mock = {
        "User6": {"gate": [8], "line": [6], "label": ["prs"]}, # 6 = Administrator
        "User1": {"gate": [1], "line": [1], "label": ["des"]}  # 1 = Authoritarian
    }
    result = get_penta(mock)
    ch = result["penta_anatomy"]["upper_penta"]["channels"]["8-1"]
    
    assert ch["status"] == "Active"
    
    # Check User6 Line Label
    # Contributor -> User6 -> gate_8 -> line_labels
    u6_labels = ch["contributors"]["User6"]["gate_8"]["line_labels"]
    assert "Administrator (Objective)" in u6_labels
    
    # Check User1 Line Label
    u1_labels = ch["contributors"]["User1"]["gate_1"]["line_labels"]
    assert "Authoritarian (Foundational)" in u1_labels
