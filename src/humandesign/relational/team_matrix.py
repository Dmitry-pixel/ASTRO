"""Team matrix over the four team-dynamics characteristics (model v1.2).

Descriptive only, agreed 2026-09-13: the team layer reports **who has which
characteristic and how many people share it**. Nothing else.

Removed in v1.2 and deliberately not to be reinstated:

* over-representation against the population baseline (exact binomial, p-values,
  ``tests_run``) and the "след подбора" statements built on it;
* absence statements and the eight-participant minimum they needed;
* one-sidedness risk hypotheses (``RISK_RU``);
* polarisation as a named finding;
* ``mean_index`` / ``std_index`` / ``min_index`` / ``max_index`` — an average
  between a structured and an emergent participant is not a mixed team, it is an
  artefact of averaging an ordinal scale.

Two consequences worth keeping in mind. First, the thresholds of
``claude/hd-team-thresholds-2026-08-25.md`` no longer apply to anything here.
Second, in v1.2 each axis is scored on its own table at full weight, so Transfer
and Processing share channels and are not independent observations — which is
exactly why a statistical reading of a composition would have overstated the
effect. Counting has no such problem.

``bridging`` stays: it is a mechanical fact about two charts (whose defined
centres fall into fewer blocks in the union), not a claim about probability. It
is reported per pair with a plain sentence naming who closes whose split; the
scope ("в очной работе") is carried inside that sentence rather than as a
separate caveat field.

Every counted value ships as an English code plus a Russian label and a sentence
of what it means, so a bare count like ``bridged — 3`` is readable without the
methodology at hand.

Participants are addressed by the identifier the caller supplied as the key of
``participants``. In production that is an opaque id — sites send place, date and
time, not names — so every sentence that mentions participants also ships as
``*_template_ru`` with ``{bridge}`` / ``{closes_for}`` placeholders the caller
substitutes with whatever it displays. Response order follows request order.
"""
from __future__ import annotations

import itertools
from typing import Any, Dict, List, Optional, Set

from .. import hd_constants
from ..features import team_axes as ta
from .persons import Person


# --------------------------------------------------------------------------- #
# Bridging over the centre graph
# --------------------------------------------------------------------------- #
_CHANNEL_CENTRES = {frozenset(k): v for k, v in hd_constants.GATES_CHAKRA_DICT.items()}


def _channels(gates: Set[int]) -> Set[frozenset]:
    return {ch for ch in _CHANNEL_CENTRES if ch <= gates}


def _component_of(channels: Set[frozenset]) -> Dict[str, str]:
    parent: Dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for ch in channels:
        a, b = _CHANNEL_CENTRES[ch]
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return {c: find(c) for c in parent}


def _count_over(centres: Set[str], channels: Set[frozenset]) -> int:
    comp = _component_of(channels)
    return len({comp[c] for c in centres if c in comp})


def bridging(people: Dict[str, Person]) -> List[Dict[str, Any]]:
    """B closes A's split when, in the union of both charts, A's own defined
    centres fall into fewer connected components than in A alone.

    ``channels`` — channels the pair forms inside A's connected area;
    ``critical_channels`` — those whose removal alone undoes the closure
    (empty when several channels close it redundantly).
    """
    key = lambda ch: "-".join(str(g) for g in sorted(ch))
    out: List[Dict[str, Any]] = []
    for a_name, b_name in itertools.permutations(people, 2):
        a, b = people[a_name], people[b_name]
        a_ch = _channels(set(a.gates))
        a_centres = {c for ch in a_ch for c in _CHANNEL_CENTRES[ch]}
        before = _count_over(a_centres, a_ch)
        if before < 2:
            continue
        u_ch = _channels(set(a.gates) | set(b.gates))
        after = _count_over(a_centres, u_ch)
        if after >= before:
            continue
        comp = _component_of(u_ch)
        roots = {comp[c] for c in a_centres}
        formed = sorted(key(ch) for ch in (u_ch - a_ch)
                        if comp[next(iter(_CHANNEL_CENTRES[ch]))] in roots)
        critical = sorted(key(ch) for ch in (u_ch - a_ch)
                          if _count_over(a_centres, u_ch - {ch}) > after)
        out.append({"bridge": b_name, "closes_for": a_name,
                    "components_before": before, "components_after": after,
                    "channels": formed, "critical_channels": critical,
                    "text_ru": f"Замыкает — {b_name}, кому — {a_name}. В очной работе "
                               f"определённые центры собираются из {before} блоков в {after}: "
                               f"переход от решения к действию даётся легче, чем в одиночку.",
                    "text_template_ru": "Замыкает — {bridge}, кому — {closes_for}. В очной работе "
                                        f"определённые центры собираются из {before} блоков "
                                        f"в {after}: переход от решения к действию даётся легче, "
                                        f"чем в одиночку.",
                    "channels_ru": ("Соединяют каналы: " + ", ".join(formed)) if formed else None})
    return out


# --------------------------------------------------------------------------- #
# Team
# --------------------------------------------------------------------------- #
def person_axes(p: Person, precision_min: Optional[float] = None) -> Dict[str, Any]:
    u = p.raw
    br = (u.get("variables") or {}).get("bottom_right") or {}
    res = ta.compute_axes(u["date_to_gate_dict"]["gate"], u["active_chakra"], u["auth"],
                          u["typ"], u["definition"], br.get("value"), br.get("confidence"))
    if precision_min:
        res["time_stability"] = ta.time_stability(p.timestamp, precision_min, baseline=res)
    return res


def _majority_letter(axis: str, counts: Dict[str, List[str]]) -> str:
    """The value most participants carry. '–' on a tie — a count, not a verdict."""
    ranked = sorted(counts.items(), key=lambda kv: -len(kv[1]))
    if not ranked or not ranked[0][1]:
        return "–"
    if len(ranked) > 1 and len(ranked[1][1]) == len(ranked[0][1]):
        return "–"
    top = ranked[0][0]
    for side in ("a", "b"):
        if ta.POLES[axis][side]["code"] == top:
            return ta.POLES[axis][side]["letter"]
    return "~"


def analyse_team(people: Dict[str, Person],
                 precision: Optional[Dict[str, Optional[float]]] = None) -> Dict[str, Any]:
    """Composition of a team: the per-person matrix plus counts per value."""
    precision = precision or {}
    names = list(people)
    n = len(names)
    profiles = {nm: person_axes(people[nm], precision.get(nm)) for nm in names}

    rows = []
    for nm in names:
        r = profiles[nm]
        row: Dict[str, Any] = {"id": nm, "code": r["code"],
                               "integration": r["integration"]["reading"]}
        for a in ta.AXES:
            ax = r["axes"][a]
            row[a] = {"pole": ax["pole"], "letter": ax["letter"], "side": ax["side"],
                      "band": ax["band"], "index": ax["index"]}
        row["decision"]["mode"] = r["axes"]["decision"]["mode"]
        row["execution"]["basis"] = r["axes"]["execution"]["basis"]
        row["execution"]["energy_profile"] = r["axes"]["execution"]["energy_profile"]["code"]
        ts = r.get("time_stability")
        row["unstable_axes"] = ts["unstable_axes"] if ts else []
        rows.append(row)

    composition: Dict[str, Any] = {}
    for a in ta.AXES:
        values: Dict[str, List[str]] = {}
        for side in ("a", "b"):
            values[ta.POLES[a][side]["code"]] = []
        if a in ta.SCORED_AXES:
            values["mixed"] = []
        for nm in names:
            values.setdefault(profiles[nm]["axes"][a]["pole"] or "none", []).append(nm)
        items, parts = [], []
        for code, mem in values.items():
            side = next((x for x in ("a", "b") if ta.POLES[a][x]["code"] == code), None)
            label = ta.POLES[a][side]["label_ru"] if side else "Смешанная"
            meaning = (ta.POLES[a][side]["meaning_ru"] if side else
                       "признаки обоих полюсов уравновешены; устойчивого предпочтения нет")
            items.append({"code": code, "label_ru": label, "count": len(mem),
                          "members": mem, "meaning_ru": meaning})
            parts.append(f"{label} — {len(mem)}")
        composition[a] = {
            "name_ru": ta.AXIS_NAME_RU[a],
            "values": values,
            "counts": {code: len(mem) for code, mem in values.items()},
            "items": items,
            "summary_ru": " · ".join(parts),
        }

    modes: Dict[str, List[str]] = {}
    for nm in names:
        m = profiles[nm]["axes"]["decision"]["mode"]
        if m:
            modes.setdefault(m, []).append(nm)
    decision_modes = {
        "name_ru": "Механизм принятия решения",
        "values": modes,
        "counts": {m: len(v) for m, v in modes.items()},
        "items": [{"code": m, "label_ru": ta.DECISION_MODE_LABEL_RU[m], "count": len(v),
                   "members": v, "meaning_ru": "решение формируется " + ta.DECISION_MODE_RU[m]}
                  for m, v in modes.items()],
        "summary_ru": " · ".join(f"{ta.DECISION_MODE_LABEL_RU[m]} — {len(v)}"
                                 for m, v in modes.items()),
    }

    integ: Dict[str, List[str]] = {}
    for nm in names:
        integ.setdefault(profiles[nm]["integration"]["reading"] or "none", []).append(nm)
    integration = {
        "name_ru": "Интеграция механизма решения",
        "values": integ,
        "counts": {k: len(v) for k, v in integ.items()},
        "items": [{"code": k, "label_ru": ta.INTEGRATION_LABEL_RU.get(k, k), "count": len(v),
                   "members": v, "meaning_ru": ta.INTEGRATION_RU.get(k)}
                  for k, v in integ.items()],
        "summary_ru": " · ".join(f"{ta.INTEGRATION_LABEL_RU.get(k, k)} — {len(v)}"
                                 for k, v in integ.items()),
    }

    energy: Dict[str, List[str]] = {}
    for nm in names:
        energy.setdefault(profiles[nm]["axes"]["execution"]["energy_profile"]["code"], []).append(nm)
    energy_items = [{"code": k, "label_ru": ta.ENERGY_PROFILE_RU[k][1], "count": len(v),
                     "members": v, "meaning_ru": ta.ENERGY_PROFILE_RU[k][2]}
                    for k, v in energy.items()]

    return {
        "model": ta.MODEL_ID,
        "model_version": ta.MODEL_VERSION,
        "kind": "composition",
        "size": n,
        "team_code": "·".join(_majority_letter(a, composition[a]["values"]) for a in ta.AXES),
        "team_code_legend_ru": "значение, которое встречается у большинства участников; "
                               "«–» — поровну",
        "matrix": {"columns": ["id", "code", *ta.AXES, "integration"], "rows": rows},
        "composition": composition,
        "decision_modes": decision_modes,
        "integration": integration,
        "energy_profiles": {
            "name_ru": "Энергетический механизм исполнения",
            "values": energy,
            "counts": {k: len(v) for k, v in energy.items()},
            "items": energy_items,
            "summary_ru": " · ".join(f"{i['label_ru']} — {i['count']}" for i in energy_items),
        },
        "bridging": bridging(people),
        "bridging_legend_ru": "Замыкание разрыва: если механизм решения участника собран из "
                              "нескольких несвязанных блоков, присутствие другого человека "
                              "соединяет эти блоки в очной работе. Читается по парам: кто кому "
                              "замыкает разрыв.",
        "profiles": profiles,
        "reading_note_ru": "Слой описывает состав команды: кто какую характеристику несёт и сколько "
                           "таких участников. Оценок состава, утверждений об отсутствии и "
                           "вероятностей здесь нет. Участники адресуются идентификатором из "
                           "запроса; порядок ответа совпадает с порядком запроса.",
        "disclaimer_ru": ta.DISCLAIMER_RU,
    }
