from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator

from ...utils.date_utils import validate_calendar_date

class CalculateRequestV2(BaseModel):
    year: int = Field(..., description="Birth year")
    month: int = Field(..., ge=1, le=12, description="Birth month (1-12)")
    day: int = Field(..., ge=1, le=31, description="Birth day (1-31, checked against the month)")
    hour: int = Field(..., ge=0, le=23, description="Birth hour (0-23)")
    minute: int = Field(..., ge=0, le=59, description="Birth minute (0-59)")
    second: int = Field(0, ge=0, le=59, description="Birth second (0-59)")
    place: Optional[str] = Field(
        None,
        description="Birth place (city, country) or IANA timezone. Required unless latitude and longitude are both supplied.",
    )
    gender: Optional[str] = Field(None, description="Gender")
    islive: Optional[bool] = Field(True, description="Whether alive")
    latitude: Optional[float] = Field(None, description="Latitude; bypasses geocoding when given with longitude")
    longitude: Optional[float] = Field(None, description="Longitude; bypasses geocoding when given with latitude")
    time_precision_min: float = Field(
        1.0, ge=0.0, le=1440.0,
        description=(
            "How precisely the birth time is known, in minutes. "
            "1 = to the minute, 30 = the hour is known but not the minute, "
            "720 = time unknown and noon was substituted. Drives the confidence "
            "flag on each Variable arrow and, from 5 minutes up, the "
            "team_dynamics.time_stability scan; it changes neither the arrows "
            "nor the axes themselves."
        ),
    )

    @model_validator(mode="after")
    def _require_place_or_coordinates(self):
        if self.place is None and (self.latitude is None or self.longitude is None):
            raise ValueError("Provide 'place', or both 'latitude' and 'longitude'.")
        return self

    @model_validator(mode="after")
    def _require_existing_date(self):
        validate_calendar_date(self.year, self.month, self.day)
        return self
    
    include: Optional[List[str]] = Field(
        None,
        description=(
            "Sections to keep in the response. "
            "Available: general, centers, channels, gates, variables, analytics, "
            "advanced, mechanics, team_dynamics. Dot paths narrow further, e.g. "
            "'team_dynamics.axes'. "
            "None or [] returns every section; a non-empty list returns only "
            "the sections it names. Unknown names are ignored."
        ),
        example=["general", "centers"],
    )
    exclude: Optional[List[str]] = Field(
        None,
        description=(
            "Sections to drop from the response, applied after 'include'. "
            "Unknown names are ignored."
        ),
        example=["channels"],
    )

class VariableItemV2(BaseModel):
    value: Optional[str] = None
    name: Optional[str] = None
    aspect: Optional[str] = None
    def_type: Optional[str] = None
    # Reliability of the arrow. The arrow is always returned; these fields
    # say how far the underlying tone sits from its cell boundary and what
    # limits it - the ephemeris files or the stated precision of the time.
    lon: Optional[float] = None
    tone: Optional[int] = None
    speed: Optional[float] = None
    confidence: Optional[str] = None
    margin_arcsec: Optional[float] = None
    required_arcsec: Optional[float] = None
    limiting_factor: Optional[str] = None

class VariablesV2(BaseModel):
    top_right: Optional[VariableItemV2] = None
    bottom_right: Optional[VariableItemV2] = None
    top_left: Optional[VariableItemV2] = None
    bottom_left: Optional[VariableItemV2] = None
    short_code: Optional[str] = None
    low_confidence_arrows: Optional[List[str]] = None
    all_arrows_confident: Optional[bool] = None
    time_precision_min: Optional[float] = None

class CentersV2(BaseModel):
    defined: Optional[List[str]] = None
    undefined: Optional[List[str]] = None

class GatesV2(BaseModel):
    personality: Optional[Dict[str, 'GateV2']] = None
    design: Optional[Dict[str, 'GateV2']] = None

class GeneralSectionV2(BaseModel):
    birth_date: Optional[str] = None
    create_date: Optional[str] = None
    birth_place: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    islive: Optional[bool] = None
    zodiac_sign: Optional[str] = None
    energy_type: Optional[str] = None
    strategy: Optional[str] = None
    signature: Optional[str] = None
    not_self: Optional[str] = None
    aura: Optional[str] = None
    inner_authority: Optional[str] = None
    inc_cross: Optional[str] = None
    profile: Optional[str] = None
    definition: Optional[str] = None

class GateV2(BaseModel):
    gate: int
    line: int
    color: int
    tone: int
    base: int
    lon: float
    gate_name: Optional[str] = None
    gate_summary: Optional[str] = None
    line_name: Optional[str] = None
    line_description: Optional[str] = None
    fixation: Optional[Dict[str, Any]] = None

class DreamRaveOutput(BaseModel):
    activated_centers: List[str]
    activated_gates: List[int]
    status: str

class GlobalCycleOutput(BaseModel):
    great_cycle: str
    cycle_cross: str
    gates: List[int]
    description: str

class AdvancedSectionV2(BaseModel):
    dream_rave: Optional[DreamRaveOutput] = None
    global_cycle: Optional[GlobalCycleOutput] = None


# --- Analytics Section (quarter, line_counts, sun_roles, yin_yang, contour) ---

class QuarterV2(BaseModel):
    number: Optional[int] = None
    name: Optional[str] = None

class SunRoleItemV2(BaseModel):
    hexagram: Optional[str] = None
    role: Optional[str] = None

class SunRolesV2(BaseModel):
    prs_sun: Optional[SunRoleItemV2] = None
    des_sun: Optional[SunRoleItemV2] = None

class ClassBreakdownV2(BaseModel):
    """Classification result with planet-gate values and share percentage."""
    values: Optional[Dict[str, str]] = None
    share_pct: Optional[int] = None
    total: Optional[int] = None

class ContourV2(BaseModel):
    """Contour analysis: realization, mind, decision, big_o classifications."""
    realization: Optional[Dict[str, ClassBreakdownV2]] = None
    mind: Optional[Dict[str, ClassBreakdownV2]] = None
    decision: Optional[Dict[str, ClassBreakdownV2]] = None
    big_o: Optional[Dict[str, ClassBreakdownV2]] = None

class LineCountsV2(BaseModel):
    prs: Optional[Dict[str, int]] = None
    des: Optional[Dict[str, int]] = None
    total: Optional[Dict[str, int]] = None

class YinYangBalanceV2(BaseModel):
    Yang: Optional[ClassBreakdownV2] = None
    Yin: Optional[ClassBreakdownV2] = None
    Balance: Optional[ClassBreakdownV2] = None

class AnalyticsSectionV2(BaseModel):
    """Extended analytics: quarter, line counts, sun roles, yin/yang, contour."""
    motivation: Optional[str] = None
    perspective: Optional[str] = None
    quarter: Optional[QuarterV2] = None
    line_counts: Optional[LineCountsV2] = None
    sun_roles: Optional[SunRolesV2] = None
    yin_yang_balance: Optional[YinYangBalanceV2] = None
    contour: Optional[ContourV2] = None


# --------------------------------------------------------------------------- #
# Team dynamics — four operational characteristics (features/team_axes.py, v1.1)
# All fields optional so dot-path include/exclude keeps validating.
# --------------------------------------------------------------------------- #
class TeamEvidenceV2(BaseModel):
    kind: Optional[str] = Field(None, description="centre_defined | centre_open | channel | dangling_gate | authority | variable")
    key: Optional[str] = Field(None, description="'TT определён', '31-7', 'ворота 4', 'SP', 'perspective_left'")
    side: Optional[str] = Field(None, description="a — first pole, b — second pole")
    weight: Optional[float] = None
    status: Optional[str] = Field(None, description="core | supporting | hypothesis")
    note_ru: Optional[str] = None


class TeamPoleV2(BaseModel):
    code: Optional[str] = None
    letter: Optional[str] = None
    label_ru: Optional[str] = None
    meaning_ru: Optional[str] = None


class TeamPolesV2(BaseModel):
    a: Optional[TeamPoleV2] = None
    b: Optional[TeamPoleV2] = None


class TeamPopulationV2(BaseModel):
    index_percentile: Optional[float] = Field(None, description="Share of the population with an index at or below this one, %")
    pole_pct: Optional[float] = Field(None, description="Share of the population carrying this pole, %")


class TeamAxisFieldV2(BaseModel):
    basis: Optional[str] = Field(None, description="TT | AA for the scored information axes")
    status: Optional[str] = Field(None, description="defined | undefined | open — level 1 of the reading")
    status_ru: Optional[str] = None
    defined: Optional[bool] = None
    energy_type: Optional[str] = None
    entry_condition: Optional[str] = Field(None, description="response | invitation | inform | lunar_cycle")
    entry_condition_ru: Optional[str] = None


class TeamGSupportEvidenceV2(BaseModel):
    kind: Optional[str] = None
    key: Optional[str] = None
    side: Optional[str] = Field(None, description="c — competent, h — harmonious")
    weight: Optional[float] = None
    note_ru: Optional[str] = None


class TeamGSupportV2(BaseModel):
    """G-centre support profile for Decision. Never moves the pole."""

    c_signal: Optional[float] = None
    h_signal: Optional[float] = None
    evidence: Optional[List[TeamGSupportEvidenceV2]] = None
    note_ru: Optional[str] = None


class TeamEnergyProfileV2(BaseModel):
    """Root/Sacral field of Execution. Never votes for P or A."""

    root: Optional[str] = Field(None, description="defined | undefined | open")
    sacral: Optional[str] = Field(None, description="defined | undefined | open")
    code: Optional[str] = Field(None, description="autonomous | stimulus_led | energy_led | context_dependent")
    label: Optional[str] = None
    label_ru: Optional[str] = None
    text_ru: Optional[str] = None
    note_ru: Optional[str] = None


class TeamIntegrationReadingV2(BaseModel):
    code: Optional[str] = Field(None, description="internal_closed | internal_bridged | relational_closed | relational_bridged")
    integration: Optional[str] = Field(None, description="closed | bridged")
    text_ru: Optional[str] = None


class TeamPerspectiveV2(BaseModel):
    value: Optional[str] = None
    confidence: Optional[str] = None


class TeamAxisV2(BaseModel):
    name_ru: Optional[str] = None
    poles: Optional[TeamPolesV2] = None
    kind: Optional[str] = Field(None, description="index — scored axis; categorical — Decision, where the authority is the pole")
    index: Optional[float] = Field(None, description="0 — first pole, 100 — second; 100*(B+1)/(A+B+2). null on Decision")
    evidence_a: Optional[float] = None
    evidence_b: Optional[float] = None
    confidence: Optional[float] = Field(None, description="(A+B)/(A+B+2)")
    band: Optional[str] = Field(None, description="strong_a | moderate_a | mixed | moderate_b | strong_b. null on Decision")
    band_ru: Optional[str] = None
    side: Optional[str] = Field(None, description="a | b | null")
    pole: Optional[str] = Field(None, description="structured/emergent, fixed/relative, internal/relational, planned/adaptive, or 'mixed'")
    letter: Optional[str] = Field(None, description="S/N, F/R, C/H, P/A; '~' for a mixed style")
    pole_label_ru: Optional[str] = None
    pole_meaning_ru: Optional[str] = None
    hypothesis_share: Optional[float] = None
    evidence: Optional[List[TeamEvidenceV2]] = None
    population: Optional[TeamPopulationV2] = None
    field: Optional[TeamAxisFieldV2] = None
    # decision only
    mode: Optional[str] = Field(None, description="Decision: response | instant | will | articulated | delayed | external | lunar")
    mode_label_ru: Optional[str] = None
    mode_ru: Optional[str] = None
    authority: Optional[str] = None
    authority_ru: Optional[str] = None
    status: Optional[str] = Field(None, description="Decision: core | hypothesis — status of the authority rule")
    g_support: Optional[TeamGSupportV2] = None
    integration_reading: Optional[TeamIntegrationReadingV2] = None
    # execution only
    basis: Optional[str] = Field(None, description="Execution: channels | perspective_only | none")
    perspective: Optional[TeamPerspectiveV2] = None
    energy_profile: Optional[TeamEnergyProfileV2] = None


class TeamAxesSetV2(BaseModel):
    transfer: Optional[TeamAxisV2] = None
    processing: Optional[TeamAxisV2] = None
    decision: Optional[TeamAxisV2] = None
    execution: Optional[TeamAxisV2] = None


class TeamIntegrationV2(BaseModel):
    reading: Optional[str] = Field(None, description="closed | bridged | reflector — what the report uses")
    raw: Optional[str] = Field(None, description="I1…I4, or R for a Reflector — raw data, not for the report")
    components: Optional[int] = None
    closed: Optional[bool] = None
    label_ru: Optional[str] = None
    text_ru: Optional[str] = None


class TeamFlagV2(BaseModel):
    axis: Optional[str] = None
    code: Optional[str] = None
    text_ru: Optional[str] = None


class TeamTimeAxisV2(BaseModel):
    poles: Optional[Dict[str, float]] = None
    index_min: Optional[float] = None
    index_max: Optional[float] = None
    pole_stable: Optional[bool] = None
    base_pole_share: Optional[float] = None


class TeamTimeStabilityV2(BaseModel):
    precision_min: Optional[float] = None
    samples: Optional[int] = None
    offsets_min: Optional[List[float]] = None
    axes: Optional[Dict[str, TeamTimeAxisV2]] = None
    integration: Optional[Dict[str, float]] = None
    unstable_axes: Optional[List[str]] = None
    summary_ru: Optional[str] = None


class TeamDynamicsV2(BaseModel):
    """Four operational characteristics of team dynamics, model v1.1. Not a
    psychological diagnosis — see disclaimer_ru."""
    model: Optional[str] = None
    model_version: Optional[str] = None
    code: Optional[str] = Field(None, description="Transfer·Processing·Decision·Execution·Integration, e.g. F·R·H·A·I2")
    code_legend_ru: Optional[str] = None
    index_legend_ru: Optional[str] = None
    axes: Optional[TeamAxesSetV2] = None
    integration: Optional[TeamIntegrationV2] = None
    flags: Optional[List[TeamFlagV2]] = None
    time_stability: Optional[TeamTimeStabilityV2] = None
    disclaimer_ru: Optional[str] = None


class CalculateResponseV2(BaseModel):
    general: Optional[GeneralSectionV2] = None
    centers: Optional[CentersV2] = None
    channels: Optional[List[Dict[str, Any]]] = None
    variables: Optional[VariablesV2] = None
    gates: Optional[GatesV2] = None
    mechanics: Optional[Dict[str, Any]] = None
    analytics: Optional[AnalyticsSectionV2] = None
    advanced: Optional[AdvancedSectionV2] = None
    team_dynamics: Optional[TeamDynamicsV2] = None
