"""Group engines: Penta (3-5) and WA-scale aggregate (6+).

Penta delegates to `features.core.get_penta` — the Sovereign Standard engine that
already ships in the product — and only adds the participant layer around it.

The WA is the entity formed from ten people upward, and unlike the Penta — which
is scored over twelve gates in six fixed channels — it is built on the **whole
bodygraph**: all 64 gates, all 36 channels, all 9 centres. That is what this
module computes for a group of that size: every channel the group defines
collectively, every centre, who is the sole holder of what, and where the field
is thin enough that one departure breaks it.

Six to nine people form neither entity. They are still analysed, with the same
mechanics, but labelled `aggregate` and flagged `doctrine_implemented: False` so
no consumer reads them as a WA.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .. import features as hd
from .. import hd_constants
from . import blocks
from . import channels
from . import oc16
from . import semantics as S
from .engine import centres_of, normalise_verbosity, _circuit
from .persons import Person

_CHANNELS: Tuple[Tuple[int, int], ...] = tuple(hd_constants.CHANNEL_MEANING_DICT.keys())
_ALL_CENTRES = [hd_constants.CHAKRA_NAMES_MAP[c] for c in hd_constants.CHAKRA_LIST]

PENTA_MIN, PENTA_MAX = 3, 5
# The Penta is canonically 3-5 and is sometimes extended to 8. The WA begins at
# 9, with its full mechanics structured from 9 to 16.
PENTA_EXTENDED_MAX = 8
WA_MIN = 9
GROUP_MAX = 64


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def classify_entity(size: int) -> Dict[str, Any]:
    if size == 2:
        return {"code": "dyad", "label": "Dyad", "label_ru": "Диада", "size": size,
                "doctrine_implemented": True}
    if PENTA_MIN <= size <= PENTA_MAX:
        return {"code": "penta", "label": "Penta", "label_ru": "Пента", "size": size,
                "doctrine_implemented": True}
    if PENTA_MAX < size <= PENTA_EXTENDED_MAX:
        return {"code": "extended_penta", "label": "Extended Penta",
                "label_ru": "Расширенная Пента", "size": size,
                "doctrine_implemented": True,
                "note": f"The Penta is canonically {PENTA_MIN}-{PENTA_MAX} and extends to "
                        f"{PENTA_EXTENDED_MAX}. Below the WA threshold of {WA_MIN}.",
                "note_ru": f"Пента канонически {PENTA_MIN}–{PENTA_MAX} и расширяется до "
                           f"{PENTA_EXTENDED_MAX}. До порога WA в {WA_MIN} человек."}
    return {"code": "wa", "label": "WA", "label_ru": "WA", "size": size,
            "doctrine_implemented": True,
            "note": "The WA is built on the whole bodygraph but operates through OC16: "
                    "six departmental channels carrying twelve gates, plus four bridging "
                    "gates. Full mechanics are structured from 9 to 16 people.",
            "note_ru": f"WA — сущность от {WA_MIN} человек. Строится на полном бодиграфе, "
                       "но оперирует через OC16: шесть каналов-департаментов (12 ворот) "
                       "плюс четыре связующих ворот. Полная механика — от 9 до 16."}


# --------------------------------------------------------------------------- #
# Penta
# --------------------------------------------------------------------------- #
def analyse_penta(people: Dict[str, Person], group_type: str = "business",
                  verbosity: str = "standard") -> Dict[str, Any]:
    verbosity = normalise_verbosity(verbosity)
    penta = hd.get_penta({n: p.penta_input() for n, p in people.items()}, group_type=group_type)

    size = len(people)
    result: Dict[str, Any] = {
        "meta": {
            "engine": "Penta 2.0 (Sovereign Standard)",
            "group_type": group_type,
            "entity": classify_entity(size),
            "scale": {
                "canonical_range": [PENTA_MIN, PENTA_MAX],
                "extended_max": PENTA_EXTENDED_MAX,
                "extended": size > PENTA_MAX,
                "note_ru": ("Группа больше канонической Пенты, но ещё не WA: механика "
                            "Пенты применена к расширенному составу."
                            if size > PENTA_MAX else
                            "Каноническая Пента."),
            },
            "generated_at": now_iso(),
        },
        "analytical_metrics": penta.get("analytical_metrics"),
        "functional_roles": penta.get("functional_roles"),
        "hiring_logic": penta.get("hiring_logic"),
    }
    if verbosity != "compact":
        result["penta_anatomy"] = penta.get("penta_anatomy")
    return result


# --------------------------------------------------------------------------- #
# WA-scale aggregate
# --------------------------------------------------------------------------- #
def analyse_group_field(people: Dict[str, Person], group_type: str = "business",
                        verbosity: str = "standard", enricher=None) -> Dict[str, Any]:
    """Group bodygraph over any number of participants."""
    verbosity = normalise_verbosity(verbosity)
    names = list(people)
    size = len(names)

    union_gates = set()
    for p in people.values():
        union_gates |= p.gates

    holders: Dict[Tuple[int, int], List[str]] = {}
    solo_holders: Dict[Tuple[int, int], List[str]] = {}
    for key in _CHANNELS:
        g1, g2 = key
        contributors = [n for n in names if g1 in people[n].gates or g2 in people[n].gates]
        if g1 in union_gates and g2 in union_gates:
            holders[key] = contributors
            solo_holders[key] = [n for n in names if key in people[n].channels]

    defined_channels = sorted(holders)
    defined_centres = centres_of(defined_channels)

    # gate scarcity: which gates only one person in the group carries
    gate_owners: Dict[int, List[str]] = {}
    for n, p in people.items():
        for g in p.gates:
            gate_owners.setdefault(g, []).append(n)
    keystone_gates = sorted(g for g, owners in gate_owners.items() if len(owners) == 1)

    # a keystone channel is one that breaks if a single person leaves
    keystone_channels = []
    for key in defined_channels:
        critical = [n for n in names
                    if not _channel_survives_without(key, people, n)]
        if critical:
            keystone_channels.append({
                "channel": list(key), "key": f"{key[0]}-{key[1]}",
                "depends_on": critical,
                "circuit_group": _circuit(key)["group"],
                "theme": hd_constants.CHANNEL_MEANING_DICT[key][0],
                "label": channels.label(key),
            })

    circuit_coverage = {"Individual": {"defined": 0, "total": 0},
                        "Collective": {"defined": 0, "total": 0},
                        "Tribal": {"defined": 0, "total": 0},
                        "Integration": {"defined": 0, "total": 0}}
    missing: List[Dict[str, Any]] = []
    for key in _CHANNELS:
        group = _circuit(key)["group"]
        if group in circuit_coverage:
            circuit_coverage[group]["total"] += 1
            if key in holders:
                circuit_coverage[group]["defined"] += 1
        if key not in holders:
            g1, g2 = key
            missing.append({
                "channel": list(key), "key": f"{key[0]}-{key[1]}",
                "missing_gates": [g for g in key if g not in union_gates],
                "circuit_group": group,
                "theme": hd_constants.CHANNEL_MEANING_DICT[key][0],
                "label": channels.label(key),
            })
    for group, cov in circuit_coverage.items():
        cov["share_pct"] = round(100 * cov["defined"] / cov["total"]) if cov["total"] else 0

    contributions = []
    for n, p in people.items():
        unique = sorted(g for g in p.gates if len(gate_owners[g]) == 1)
        contributions.append({
            "name": n,
            "gates": len(p.gates),
            "unique_gates": unique,
            "unique_gate_count": len(unique),
            "own_channels": len(p.channels),
            "energy_type": p.summary["energy_type"],
            "defined_centres": sorted(p.centres),
        })
    contributions.sort(key=lambda c: (-c["unique_gate_count"], c["name"]))

    type_mix: Dict[str, int] = {}
    for p in people.values():
        type_mix[p.summary["energy_type"]] = type_mix.get(p.summary["energy_type"], 0) + 1

    result: Dict[str, Any] = {
        "meta": {
            "engine": "WA / group field v1",
            "group_type": group_type,
            "entity": classify_entity(size),
            "generated_at": now_iso(),
        },
        "structure": {
            "gates": 64,
            "channels": len(_CHANNELS),
            "centres": 9,
            "note": "The substrate is the whole bodygraph. What the WA operates through is "
                    "OC16, reported separately under `oc16`.",
            "note_ru": "Субстрат — полный бодиграф. То, через что WA оперирует, — OC16, "
                       "он отдаётся отдельным блоком `oc16`.",
        },
        "coverage": {
            "gates_defined": len(union_gates),
            "gates_total": 64,
            "gates_share_pct": round(100 * len(union_gates) / 64),
            "channels_defined": len(defined_channels),
            "channels_total": len(_CHANNELS),
            "channels_share_pct": round(100 * len(defined_channels) / len(_CHANNELS)),
            "centres_defined": len(defined_centres),
            "centres_total": 9,
            "by_circuit": circuit_coverage,
        },
        "centres": {
            "defined": defined_centres,
            "open": [c for c in _ALL_CENTRES if c not in defined_centres],
        },
        "type_mix": type_mix,
        "fragility": {
            "keystone_gates": keystone_gates,
            "keystone_gate_count": len(keystone_gates),
            "keystone_channels": keystone_channels if verbosity != "compact" else None,
            "keystone_channel_count": len(keystone_channels),
            "reading_ru": _fragility_reading(len(keystone_channels), len(defined_channels)),
        },
        "contributions": contributions if verbosity != "compact" else contributions[:5],
        "gaps": {
            "missing_channel_count": len(missing),
            "channels": missing if verbosity != "compact" else missing[:5],
        },
    }

    if size >= WA_MIN:
        result["oc16"] = oc16.analyse(people, verbosity)
        result["penta_blocks"] = blocks.analyse(
            people, result["oc16"]["alpha"], verbosity)

    if verbosity == "full":
        result["channels"] = [{
            "channel": list(key), "key": f"{key[0]}-{key[1]}",
            "theme": hd_constants.CHANNEL_MEANING_DICT[key][0],
            "label": channels.label(key),
            "circuit": _circuit(key),
            "centres": centres_of([key]),
            "contributors": holders[key],
            "solo_holders": solo_holders[key],
            "reference": (enricher.enrich_channel(key[0], key[1]) if enricher else None),
        } for key in defined_channels]

    return result


def _channel_survives_without(key: Tuple[int, int], people: Dict[str, Person], drop: str) -> bool:
    g1, g2 = key
    has1 = any(g1 in p.gates for n, p in people.items() if n != drop)
    has2 = any(g2 in p.gates for n, p in people.items() if n != drop)
    return has1 and has2


def _fragility_reading(keystone_channels: int, defined: int) -> str:
    if defined == 0:
        return "Группа не определяет ни одного канала."
    share = keystone_channels / defined
    if share >= 0.5:
        return (f"{keystone_channels} из {defined} каналов держатся на одном человеке. "
                f"Уход почти любого участника меняет механику группы — это не риск «ключевого "
                f"сотрудника», а структурная зависимость.")
    if share >= 0.2:
        return (f"{keystone_channels} из {defined} каналов держатся на одном человеке. "
                f"Точки хрупкости есть, но большая часть определения дублирована.")
    return (f"Только {keystone_channels} из {defined} каналов зависят от одного человека. "
            f"Определение группы устойчиво к уходу отдельного участника.")
