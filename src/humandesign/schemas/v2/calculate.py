from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CalculateRequestV2(BaseModel):
    year: int = Field(1968, description="Birth year")
    month: int = Field(2, description="Birth month")
    day: int = Field(21, description="Birth day")
    hour: int = Field(11, description="Birth hour")
    minute: int = Field(0, description="Birth minute")
    second: int = Field(0, description="Birth second")
    place: str = Field("Kirikkale, Turkey", description="Birth place")
    gender: Optional[str] = Field("male", description="Gender")
    islive: Optional[bool] = Field(True, description="Whether alive")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    include: Optional[List[str]] = Field(None, description="Sections to include (e.g. ['general', 'personality_gates'])", example=["general", "personality_gates"])
    exclude: Optional[List[str]] = Field(None, description="Sections to exclude", example=["channels"])

class VariableItemV2(BaseModel):
    value: Optional[str] = None
    name: Optional[str] = None
    aspect: Optional[str] = None
    def_type: Optional[str] = None

class VariablesV2(BaseModel):
    top_right: Optional[VariableItemV2] = None
    bottom_right: Optional[VariableItemV2] = None
    top_left: Optional[VariableItemV2] = None
    bottom_left: Optional[VariableItemV2] = None
    short_code: Optional[str] = None

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


class CalculateResponseV2(BaseModel):
    general: Optional[GeneralSectionV2] = None
    centers: Optional[CentersV2] = None
    channels: Optional[List[Dict[str, Any]]] = None
    variables: Optional[VariablesV2] = None
    gates: Optional[GatesV2] = None
    mechanics: Optional[Dict[str, Any]] = None
    analytics: Optional[AnalyticsSectionV2] = None
    advanced: Optional[AdvancedSectionV2] = None
