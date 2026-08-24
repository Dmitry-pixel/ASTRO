"""Dyad / composite engine.

A dyad is the auric pair; the composite is the merged bodygraph the pair produces.
This module analyses the composite over the **full set of 36 channels**, which is
what makes the four Maia classes reachable:

    both hold the whole channel .................. companionship
    one holds the whole channel, other one gate .. compromise   (pressure)
    one holds the whole channel, other neither ... dominance    (fixed pattern)
    each holds one of the two gates .............. electromagnetic

The engine that shipped before this one classified only the channels that were
*new* to the composite. A new channel has, by construction, one gate from each
side, so it could only ever answer "electromagnetic"; on a five-person group that
hid 61 of 91 connections. Role-conflict diagnostics live exactly in the classes it
could not see.
"""
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import hd_constants
from . import channels
from . import semantics as S
from .persons import Person

VERBOSITY_LEVELS = ("compact", "standard", "full")
#: Legacy values accepted by the pre-3.5 contract.
VERBOSITY_ALIASES = {"all": "full", "partial": "compact"}

_CHANNELS: Tuple[Tuple[int, int], ...] = tuple(hd_constants.CHANNEL_MEANING_DICT.keys())
_CHANNEL_CENTRES = hd_constants.GATES_CHAKRA_DICT
_CENTRE_NAME = hd_constants.CHAKRA_NAMES_MAP
_ALL_CENTRES = [_CENTRE_NAME[c] for c in hd_constants.CHAKRA_LIST]


def normalise_verbosity(value: Optional[str]) -> str:
    v = (value or "standard").lower()
    v = VERBOSITY_ALIASES.get(v, v)
    return v if v in VERBOSITY_LEVELS else "standard"


def channel_for(gate_a: int, gate_b: int) -> Optional[Tuple[int, int]]:
    """The channel key formed by two gates, or None."""
    if (gate_a, gate_b) in hd_constants.CHANNEL_MEANING_DICT:
        return (gate_a, gate_b)
    if (gate_b, gate_a) in hd_constants.CHANNEL_MEANING_DICT:
        return (gate_b, gate_a)
    return None


def centres_of(channels: Sequence[Tuple[int, int]]) -> List[str]:
    out = set()
    for key in channels:
        pair = _CHANNEL_CENTRES.get(key)
        if pair:
            out.update(_CENTRE_NAME.get(c, c) for c in pair)
    return sorted(out)


def _circuit(key: Tuple[int, int]) -> Dict[str, str]:
    sorted_key = tuple(sorted(key))
    typ = hd_constants.circuit_typ_dict.get(sorted_key) \
        or hd_constants.circuit_typ_dict.get(key) \
        or hd_constants.circuit_typ_dict.get((key[1], key[0])) \
        or "Unknown"
    return S.sub_circuit(key, typ)


def classify(gates_a: set, gates_b: set, key: Tuple[int, int]) -> Optional[str]:
    """One of the four Maia codes, or None when the pair does not form the channel."""
    g1, g2 = key
    a_count = (g1 in gates_a) + (g2 in gates_a)
    b_count = (g1 in gates_b) + (g2 in gates_b)
    if a_count + b_count == 0:
        return None
    a_full, b_full = a_count == 2, b_count == 2

    if a_full and b_full:
        return "companionship"
    if a_full or b_full:
        other = b_count if a_full else a_count
        return "compromise" if other == 1 else "dominance"
    # neither holds it alone — is it completed jointly?
    union = gates_a | gates_b
    if g1 in union and g2 in union:
        return "electromagnetic"
    return None


# --------------------------------------------------------------------------- #
def _holder_block(person: Person, key: Tuple[int, int], verbosity: str) -> Dict[str, Any]:
    held = [g for g in key if g in person.gates]
    block: Dict[str, Any] = {
        "gates": held,
        "holds_full_channel": len(held) == 2,
    }
    if verbosity != "compact":
        block["triggers"] = {str(g): person.trigger_labels(g) for g in held}
    return block


def _channel_entry(a: Person, b: Person, key: Tuple[int, int], code: str,
                   verbosity: str, enricher) -> Dict[str, Any]:
    meaning = hd_constants.CHANNEL_MEANING_DICT.get(key, [])
    circuit = _circuit(key)
    a_block, b_block = _holder_block(a, key, verbosity), _holder_block(b, key, verbosity)

    direction = None
    if code in S.CONDITIONING_TYPES:
        if a_block["holds_full_channel"]:
            direction = {"conditions": a.name, "conditioned": b.name}
        else:
            direction = {"conditions": b.name, "conditioned": a.name}

    entry: Dict[str, Any] = {
        "channel": list(key),
        "key": f"{key[0]}-{key[1]}",
        "type": S.maia_type(code),
        "circuit": circuit,
        "centres": centres_of([key]),
        "held_individually_by": [p.name for p in (a, b) if key in p.channels],
        "new_in_composite": key not in a.channels and key not in b.channels,
        "holders": {a.name: a_block, b.name: b_block},
        "direction": direction,
        "meaning": list(meaning),
        "label": channels.label(key),
    }
    if verbosity == "full" and enricher is not None:
        reference = enricher.enrich_channel(key[0], key[1])
        if reference:
            entry["reference"] = reference
    return entry


def _centre_dynamics(a: Person, b: Person) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for centre in _ALL_CENTRES:
        in_a, in_b = centre in a.centres, centre in b.centres
        if in_a and in_b:
            code = "fixed"
        elif in_a:
            code = "conditions_a"
        elif in_b:
            code = "conditions_b"
        else:
            code = "open"
        entry = {"code": code, **S.CENTRE_DYNAMIC[code]}
        if code == "conditions_a":
            entry["from"], entry["to"] = a.name, b.name
        elif code == "conditions_b":
            entry["from"], entry["to"] = b.name, a.name
        out[centre] = entry
    return out


def _role_conflicts(a: Person, b: Person, channels: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Where the pair conditions each other — compromise and dominance channels."""
    load = {a.name: {"conditions": 0, "conditioned": 0}, b.name: {"conditions": 0, "conditioned": 0}}
    items: List[Dict[str, Any]] = []

    for ch in channels:
        if ch["type"]["code"] not in S.CONDITIONING_TYPES:
            continue
        d = ch["direction"]
        load[d["conditions"]]["conditions"] += 1
        load[d["conditioned"]]["conditioned"] += 1
        items.append({
            "channel": ch["channel"],
            "key": ch["key"],
            "type": ch["type"]["code"],
            "conditions": d["conditions"],
            "conditioned": d["conditioned"],
            "centres": ch["centres"],
            "circuit_group": ch["circuit"]["group"],
            "theme": (ch["meaning"][0] if ch["meaning"] else ch["key"]),
            "name_ru": ch["label"]["name_ru"],
        })

    diff = load[a.name]["conditions"] - load[b.name]["conditions"]
    if not items:
        balance = {"code": "none", "label": "No conditioning channels",
                   "label_ru": "Каналов обуславливания нет",
                   "reading_ru": "Пара не фиксирует друг друга ни в одном канале."}
    elif abs(diff) <= 1:
        balance = {"code": "mutual", "label": "Mutual conditioning", "label_ru": "Взаимное обуславливание",
                   "reading_ru": "Обуславливание идёт в обе стороны примерно поровну — "
                                 "конфликт ролей распределён, а не закреплён за одним."}
    else:
        lead = a.name if diff > 0 else b.name
        follow = b.name if diff > 0 else a.name
        balance = {"code": "asymmetric", "label": "Asymmetric conditioning",
                   "label_ru": "Асимметричное обуславливание", "lead": lead, "following": follow,
                   "reading_ru": f"{lead} фиксирует {follow} заметно чаще, чем наоборот "
                                 f"({abs(diff)} канала разницы). Это структурная позиция, "
                                 f"а не черта характера — но именно она читается как «давит»."}

    return {"balance": balance, "load": load, "channels": items, "count": len(items)}


# --------------------------------------------------------------------------- #
def analyse_dyad(a: Person, b: Person, verbosity: str = "standard",
                 enricher=None) -> Dict[str, Any]:
    """Full composite analysis of one auric pair."""
    verbosity = normalise_verbosity(verbosity)
    union = a.gates | b.gates

    classified: List[Tuple[Tuple[int, int], str]] = []
    for key in _CHANNELS:
        code = classify(a.gates, b.gates, key)
        if code:
            classified.append((key, code))

    composite_channels = [k for k, _ in classified]
    composite_centres = centres_of(composite_channels)
    defined_count = len(composite_centres)

    counts = {c: 0 for c in S.MAIA_TYPES}
    circuitry = {"Individual": 0, "Collective": 0, "Tribal": 0, "Integration": 0}
    entries: List[Dict[str, Any]] = []

    for key, code in classified:
        counts[code] += 1
        entry = _channel_entry(a, b, key, code, verbosity, enricher)
        group = entry["circuit"]["group"]
        if group in circuitry:
            circuitry[group] += 1
        entries.append(entry)

    dominant = max(circuitry, key=circuitry.get) if any(circuitry.values()) else None
    conflicts = _role_conflicts(a, b, entries)

    result: Dict[str, Any] = {
        "pair": [a.name, b.name],
        "composite": {
            "formula": S.centre_formula(defined_count),
            "defined_centres": composite_centres,
            "open_centres": [c for c in _ALL_CENTRES if c not in composite_centres],
            "channel_count": len(classified),
            "bridges_split": _bridges_split(a, b, defined_count),
        },
        "genetic_type": S.aura_dynamic(a.summary["energy_type"], b.summary["energy_type"]),
        "connections": {
            "totals": {**counts, "total": len(classified)},
            "circuitry": circuitry,
            "dominant_circuit": (
                {"group": dominant, **S.CIRCUIT_GROUP_READING.get(dominant, {})} if dominant else None
            ),
        },
        "role_conflicts": {
            "balance": conflicts["balance"],
            "load": conflicts["load"],
            "count": conflicts["count"],
        },
        "profile_resonance": S.profile_resonance(a.profile, b.profile),
        "variable_synergy": S.variable_synergy(a.summary.get("variables"), b.summary.get("variables")),
        "environmental_resonance": S.node_resonance(a.nodes, b.nodes, channel_for),
        "love_gates": [g for g in S.LOVE_GATES if g in union],
    }

    if verbosity != "compact":
        result["composite"]["centre_dynamics"] = _centre_dynamics(a, b)
        result["connections"]["channels"] = entries
        result["role_conflicts"]["channels"] = conflicts["channels"]

    return result


def _bridges_split(a: Person, b: Person, composite_defined: int) -> Dict[str, Any]:
    """Does the composite close a split that one of the two carries alone?"""
    split_carriers = [p.name for p in (a, b) if p.summary["definition_code"] not in ("1", "0")]
    bridged = bool(split_carriers) and composite_defined >= 8
    return {
        "bridged": bridged,
        "split_definitions": split_carriers,
        "reading_ru": (
            "Композит смыкает разрыв определения — рядом с этим человеком партнёр чувствует "
            "себя целым, и это же делает разрыв тяжелее в одиночестве."
            if bridged else
            "Композит не закрывает разрывов определения."
        ),
    }
