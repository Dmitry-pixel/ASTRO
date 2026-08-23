"""Resolve a birth input into everything the relational engines need.

One place, one contract. Mirrors `routers/v2/general.py` exactly on the two points
where the deleted `services/composite.py` diverged from production:

* the UTC offset stays a float, so +05:30 is +05:30 and not +05:00;
* the activation matrix is keyed by (polarity, planet), so a chart keeps all 26
  activations instead of the design half overwriting the personality half.

Geocoding failures raise; nothing is swallowed and no participant disappears
silently from a group result.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from zoneinfo import ZoneInfo

from .. import features as hd
from .. import hd_constants
from ..services.geolocation import get_latitude_longitude, tf


class PersonResolutionError(ValueError):
    """Raised when a participant cannot be turned into a chart."""

    def __init__(self, name: str, reason: str):
        self.name = name
        self.reason = reason
        super().__init__(f"{name}: {reason}")


_NODE_PLANETS = ("North_Node", "South_Node")
_POLARITY = {"prs": "personality", "des": "design"}


def _profile_key(profile: Any) -> Any:
    return tuple(profile) if isinstance(profile, list) else profile


class Person:
    """A resolved participant. Attribute access, not a dict, so typos raise."""

    __slots__ = ("name", "place", "latitude", "longitude", "tz", "utc_offset",
                 "timestamp", "raw", "gates", "gate_planets", "nodes",
                 "channels", "centres", "activations", "profile", "summary")

    def __init__(self, name: str, payload: Dict[str, Any]):
        self.name = name
        place = payload.get("place") or ""
        self.place = place

        lat, lon = payload.get("latitude"), payload.get("longitude")
        if lat is None or lon is None or (lat == 0.0 and lon == 0.0):
            lat, lon = get_latitude_longitude(place)
        if lat is None or lon is None:
            raise PersonResolutionError(name, f"geocoding failed for '{place}'")
        self.latitude, self.longitude = float(lat), float(lon)

        self.tz = place if "/" in place else (tf.timezone_at(lat=self.latitude, lng=self.longitude)
                                              or "Etc/UTC")
        birth_time = (int(payload["year"]), int(payload["month"]), int(payload["day"]),
                      int(payload["hour"]), int(payload["minute"]), 0)
        try:
            self.utc_offset = float(hd.get_utc_offset_from_tz(birth_time, self.tz))
        except Exception as exc:  # unknown zone
            raise PersonResolutionError(name, f"timezone '{self.tz}' unusable: {exc}") from exc

        self.timestamp: Tuple[Any, ...] = tuple(list(birth_time) + [self.utc_offset])

        try:
            raw = hd.calc_single_hd_features(self.timestamp, report=False, channel_meaning=True)
            self.raw = hd.unpack_single_features(raw)
        except Exception as exc:
            raise PersonResolutionError(name, f"ephemeris calculation failed: {exc}") from exc

        self._unpack(birth_time)

    # ------------------------------------------------------------------ #
    def _unpack(self, birth_time: Tuple[int, ...]) -> None:
        u = self.raw
        d = u["date_to_gate_dict"]

        self.gates: Set[int] = set()
        self.gate_planets: Dict[int, List[Dict[str, Any]]] = {}
        self.nodes: Set[int] = set()
        self.activations: List[Dict[str, Any]] = []

        for i in range(len(d["gate"])):
            gate = int(d["gate"][i])
            planet = d["planets"][i]
            polarity = _POLARITY.get(d["label"][i], d["label"][i])
            act = {
                "gate": gate,
                "line": int(d["line"][i]),
                "color": int(d["color"][i]),
                "tone": int(d["tone"][i]),
                "base": int(d["base"][i]),
                "planet": planet,
                "polarity": polarity,
                "position": round(float(d["lon"][i]), 4),
            }
            self.activations.append(act)
            self.gates.add(gate)
            self.gate_planets.setdefault(gate, []).append(
                {"planet": planet, "polarity": polarity, "line": act["line"]}
            )
            if planet in _NODE_PLANETS:
                self.nodes.add(gate)

        self.channels = {
            key for key in hd_constants.CHANNEL_MEANING_DICT
            if key[0] in self.gates and key[1] in self.gates
        }
        self.centres = {hd_constants.CHAKRA_NAMES_MAP.get(c, c) for c in u["active_chakra"]}
        self.profile = _profile_key(u["profile"])

        type_code = u["typ"]
        type_details = hd_constants.TYPE_DETAILS_MAP.get(type_code, {})
        birth_iso = self._iso(birth_time)

        self.summary: Dict[str, Any] = {
            "name": self.name,
            "place": self.place,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "tz": self.tz,
            "utc_offset": self.utc_offset,
            "birth_date_utc": birth_iso,
            "energy_type": type_code,
            "strategy": type_details.get("strategy"),
            "signature": type_details.get("signature"),
            "not_self": type_details.get("not_self"),
            "aura": type_details.get("aura"),
            "inner_authority": hd_constants.INNER_AUTHORITY_NAMES_MAP.get(u["auth"], u["auth"]),
            "profile": hd_constants.PROFILE_DB.get(self.profile, str(self.profile)),
            "profile_lines": list(self.profile) if isinstance(self.profile, tuple) else None,
            "definition": hd_constants.DEFINITION_DB.get(str(u["definition"]), str(u["definition"])),
            "definition_code": str(u["definition"]),
            "incarnation_cross": self._cross(),
            "defined_centres": sorted(self.centres),
            "open_centres": sorted({hd_constants.CHAKRA_NAMES_MAP.get(c, c)
                                    for c in hd_constants.CHAKRA_LIST} - self.centres),
            "defined_channels": [list(k) for k in sorted(self.channels)],
            "variables": u.get("variables"),
            "lunar_phase": hd.get_lunar_phase(u["date_to_gate_dict"]),
            "activation_count": len(self.activations),
        }

    def _iso(self, birth_time: Tuple[int, ...]) -> str:
        try:
            local = datetime(*birth_time, tzinfo=ZoneInfo(self.tz))
            return local.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return "unknown"

    def _cross(self) -> str:
        u = self.raw
        try:
            sun_gate = u["date_to_gate_dict"]["gate"][0]
            info = hd_constants.CROSS_DB.get(sun_gate)
            typ = u["inc_cross_typ"]
            if info and typ in info:
                return info[typ]
        except Exception:
            pass
        return str(u.get("inc_cross", ""))

    # ------------------------------------------------------------------ #
    def penta_input(self) -> Dict[str, List[Any]]:
        """The shape `features.core.get_penta` expects."""
        d = self.raw["date_to_gate_dict"]
        return {
            "gate": [int(g) for g in d["gate"]],
            "line": [int(x) for x in d["line"]],
            "label": list(d["label"]),
        }

    def trigger_labels(self, gate: int) -> List[str]:
        """`Sun (personality)` style labels for every activation of a gate."""
        return [f"{a['planet']} ({a['polarity']})" for a in self.gate_planets.get(gate, [])]


def resolve_all(participants: Dict[str, Dict[str, Any]]) -> Dict[str, Person]:
    """Resolve every participant or raise on the first failure.

    Sequential rather than threaded: the ephemeris call is a few milliseconds and
    a thread pool here only made the old code harder to reason about.
    """
    resolved: Dict[str, Person] = {}
    for name, payload in participants.items():
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload)
        resolved[name] = Person(name, data)
    return resolved
