"""Request models for the relational endpoints.

Pydantic v2 field validators throughout — no `@validator`, no `Union[int, str]`
coercion. Range constraints live on the fields so they land in `openapi.yaml` and
produce the standard FastAPI 422 body, matching what `routers/general.py` and
`routers/v2/general.py` do since 3.4.3.
"""
from typing import Annotated, Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from ..utils.date_utils import validate_calendar_date

GroupType = Literal["business", "family"]
Verbosity = Literal["compact", "standard", "full"]


class ParticipantInput(BaseModel):
    """One person's birth data."""

    place: Annotated[str, Field(min_length=1, max_length=200,
                                description="City, Country — or an IANA zone such as Europe/Moscow",
                                examples=["Berlin, Germany"])]
    year: Annotated[int, Field(ge=1800, le=2100, examples=[1985])]
    month: Annotated[int, Field(ge=1, le=12, examples=[6])]
    day: Annotated[int, Field(ge=1, le=31, examples=[15])]
    hour: Annotated[int, Field(ge=0, le=23, examples=[14])]
    minute: Annotated[int, Field(ge=0, le=59, examples=[30])]
    latitude: Optional[Annotated[float, Field(ge=-90, le=90)]] = Field(
        None, description="Skips geocoding when supplied together with longitude")
    longitude: Optional[Annotated[float, Field(ge=-180, le=180)]] = None

    @model_validator(mode="after")
    def _check_calendar(self):
        validate_calendar_date(self.year, self.month, self.day)
        return self


class _GroupRequest(BaseModel):
    participants: Dict[str, ParticipantInput]
    group_type: GroupType = Field("business", description="Switches the semantic vocabulary")
    verbosity: Verbosity = Field(
        "standard",
        description="compact — roll-ups only; standard — plus per-channel detail; "
                    "full — plus hd_data.sqlite channel reference and all 26 activations "
                    "per participant. Legacy values 'all' and 'partial' are accepted.",
    )

    @field_validator("verbosity", mode="before")
    @classmethod
    def _legacy_verbosity(cls, v: Any) -> Any:
        return {"all": "full", "partial": "compact"}.get(str(v).lower(), v)

    @field_validator("group_type", mode="before")
    @classmethod
    def _lower_group_type(cls, v: Any) -> Any:
        return str(v).lower() if isinstance(v, str) else v

    @field_validator("participants")
    @classmethod
    def _names(cls, v: Dict[str, ParticipantInput]) -> Dict[str, ParticipantInput]:
        for name in v:
            if not name.strip():
                raise ValueError("participant names must not be blank")
        return v


class CompositeRequest(_GroupRequest):
    """Exactly two people — the dyad and its composite bodygraph."""

    model_config = {"json_schema_extra": {"examples": [{
        "verbosity": "standard",
        "participants": {
            "Anna": {"place": "Moscow, Russia", "year": 1985, "month": 3, "day": 14,
                     "hour": 9, "minute": 25},
            "Boris": {"place": "Berlin, Germany", "year": 1979, "month": 11, "day": 2,
                      "hour": 17, "minute": 40},
        },
    }]}}

    @field_validator("participants")
    @classmethod
    def _exactly_two(cls, v):
        if len(v) != 2:
            raise ValueError(f"composite analysis takes exactly 2 participants, got {len(v)}")
        return v


class PentaRequest(_GroupRequest):
    """Three to eight people — the Penta entity, canonically 3-5 and extended to 8."""

    model_config = {"json_schema_extra": {"examples": [{
        "group_type": "business", "verbosity": "standard",
        "participants": {
            "Anna": {"place": "Moscow, Russia", "year": 1985, "month": 3, "day": 14,
                     "hour": 9, "minute": 25},
            "Boris": {"place": "Berlin, Germany", "year": 1979, "month": 11, "day": 2,
                      "hour": 17, "minute": 40},
            "Chen": {"place": "Singapore", "year": 1991, "month": 7, "day": 21,
                     "hour": 6, "minute": 5},
        },
    }]}}

    @field_validator("participants")
    @classmethod
    def _three_to_eight(cls, v):
        if not (3 <= len(v) <= 8):
            raise ValueError(f"penta analysis takes 3-8 participants (3-5 canonical, "
                             f"extended to 8), got {len(v)}. A WA begins at 9 — "
                             f"use /analyze/wa.")
        return v


class WaRequest(_GroupRequest):
    """Six or more people. Nine or more is a WA and carries the OC16 layer;
    six to eight is an extended Penta seen through the group-field mechanics."""

    @field_validator("participants")
    @classmethod
    def _six_or_more(cls, v):
        if len(v) < 6:
            raise ValueError(f"group-field analysis takes 6 or more participants, got {len(v)}. "
                             f"Use /analyze/composite for 2 or /analyze/penta for 3-8. "
                             f"A WA proper begins at 9.")
        if len(v) > 64:
            raise ValueError(f"at most 64 participants, got {len(v)}")
        return v


class HybridRequest(_GroupRequest):
    """Two or more people — every dyad plus whichever group layer fits the size."""

    @field_validator("participants")
    @classmethod
    def _two_or_more(cls, v):
        if len(v) < 2:
            raise ValueError(f"hybrid analysis takes 2 or more participants, got {len(v)}")
        if len(v) > 64:
            raise ValueError(f"at most 64 participants, got {len(v)}")
        return v
