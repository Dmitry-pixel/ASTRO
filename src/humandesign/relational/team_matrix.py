"""Team matrix over the four team-dynamics characteristics (model v1.1).

Section 10 of the methodology plus the statistical rules of
claude/hd-team-thresholds-2026-08-25.md:

* per axis: mean index, spread (std, min–max), pole coverage;
* one-sidedness — every member with a pole on the same side — is reported as a
  risk hypothesis for the consultant, with the probability of such a
  composition in a random draw;
* over-representation of a pole or a Decision mode against the population
  baseline, exact binomial; a client statement only at p < 0.0025, p < 0.05 is
  an internal marker; the number of tests run is reported;
* absence is evaluated only from 8 participants;
* polarisation is descriptive;
* bridging (Integration) applies to co-located work only.
"""
from __future__ import annotations

import itertools
import statistics
from math import comb
from typing import Any, Dict, List, Optional, Set

from .. import hd_constants
from ..features import team_axes as ta
from ..features.team_axes_baseline import DECISION_MODE_SHARES_PCT, POLE_SHARES_PCT
from .persons import Person

ALPHA_SIGNAL = 0.05
ALPHA_ROBUST = 0.0025
ABSENCE_MIN_SIZE = 8
ONE_SIDED_MIN = 3

RISK_RU = {
    ("transfer", "a"): "риск бюрократии: избыточные регламенты и документация",
    ("transfer", "b"): "риск потери информации: знания остаются в головах",
    ("processing", "a"): "риск игнорировать контекст и источник информации",
    ("processing", "b"): "риск уйти в субъективность и мнения отдельных людей",
    ("decision", "a"): "риск быстрых, но не согласованных решений",
    ("decision", "b"): "риск затягивания решений",
    ("execution", "a"): "риск медленной реакции на изменения",
    ("execution", "b"): "риск хаоса: план отбрасывается раньше, чем проверен",
}

REPORT_RULES_RU = [
    "Утверждение клиенту — только при p < 0.0025; p < 0.05 — внутренняя пометка «стоит посмотреть».",
    "Отсутствие оценивается только с 8 участников.",
    "Риски однородности — гипотезы для обсуждения, а не выводы о причинах.",
    "Поляризация — описательно, без слов «значимо» и «достоверно».",
    "Замыкание разрывов действует в очной совместной работе и не действует при удалённой.",
]


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k), X ~ Binomial(n, p). Exact."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def p_absent(n: int, p: float) -> float:
    return (1 - p) ** n


def _level(pv: float) -> Optional[str]:
    return "robust" if pv < ALPHA_ROBUST else ("signal" if pv < ALPHA_SIGNAL else None)


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
                    "text_ru": f"{b_name} замыкает разрыв {a_name} в очной работе "
                               f"({before} → {after} блок(а))."})
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


def _majority_letter(axis: str, summary: Dict[str, Any]) -> str:
    pa, pb = ta.POLES[axis]["a"], ta.POLES[axis]["b"]
    ka, kb = len(summary["poles"][pa["code"]]), len(summary["poles"][pb["code"]])
    return pa["letter"] if ka > kb else (pb["letter"] if kb > ka else "–")


def analyse_team(people: Dict[str, Person],
                 precision: Optional[Dict[str, Optional[float]]] = None) -> Dict[str, Any]:
    precision = precision or {}
    names = list(people)
    n = len(names)
    profiles = {nm: person_axes(people[nm], precision.get(nm)) for nm in names}

    rows = []
    for nm in names:
        r = profiles[nm]
        row: Dict[str, Any] = {"name": nm, "code": r["code"], "integration": r["integration"]["code"]}
        for a in ta.AXES:
            ax = r["axes"][a]
            row[a] = {"index": ax["index"], "band": ax["band"], "pole": ax["pole"], "letter": ax["letter"]}
        row["decision"]["mode"] = r["axes"]["decision"]["mode"]
        row["execution"]["basis"] = r["axes"]["execution"]["basis"]
        ts = r.get("time_stability")
        row["unstable_axes"] = ts["unstable_axes"] if ts else []
        rows.append(row)

    summary: Dict[str, Any] = {}
    tests = 0
    over: List[Dict[str, Any]] = []
    risks: List[Dict[str, Any]] = []
    polar: List[Dict[str, Any]] = []
    for a in ta.AXES:
        idx = [profiles[nm]["axes"][a]["index"] for nm in names]
        members: Dict[str, List[str]] = {"a": [], "b": [], "none": []}
        for nm in names:
            members[profiles[nm]["axes"][a]["side"] or "none"].append(nm)
        poles = ta.POLES[a]
        summary[a] = {
            "name_ru": ta.AXIS_NAME_RU[a],
            "mean_index": round(statistics.mean(idx), 1),
            "std_index": round(statistics.pstdev(idx), 1),
            "min_index": min(idx),
            "max_index": max(idx),
            "poles": {poles["a"]["code"]: members["a"], poles["b"]["code"]: members["b"],
                      "none": members["none"]},
            "summary_ru": f"{poles['a']['label_ru']} — {len(members['a'])}, "
                          f"{poles['b']['label_ru']} — {len(members['b'])}, "
                          f"без полюса — {len(members['none'])}",
        }
        for side in ("a", "b"):
            code = poles[side]["code"]
            pop = POLE_SHARES_PCT[a].get(code)
            if not pop:
                continue
            tests += 1
            k = len(members[side])
            if k < 2:
                continue
            pv = binom_sf(k, n, pop / 100.0)
            lvl = _level(pv)
            if lvl:
                over.append({
                    "axis": a, "kind": "pole", "value": code, "k": k, "n": n,
                    "members": members[side], "population_pct": pop,
                    "p_value": round(pv, 6), "level": lvl,
                    "statement_ru": (f"{k} из {n}: {ta.AXIS_NAME_RU[a].lower()} — "
                                     f"{poles[side]['label_ru'].lower()}. В популяции {pop:.1f}%. "
                                     f"Вероятность случайного состава — {pv:.4f}. Это след подбора, "
                                     f"а не совпадение.") if lvl == "robust" else None})
        for side, other in (("a", "b"), ("b", "a")):
            k = len(members[side])
            if k >= ONE_SIDED_MIN and not members[other]:
                code = poles[side]["code"]
                pv = ((POLE_SHARES_PCT[a].get(code) or 0) / 100.0) ** k
                risks.append({
                    "axis": a, "pole": code, "k": k, "n": n,
                    "without_pole": members["none"], "p_random": round(pv, 6),
                    "text_ru": (f"Все участники с присвоенным полюсом ({k} из {n}) — "
                                f"{poles[side]['label_ru'].lower()}. Гипотеза для обсуждения: "
                                f"{RISK_RU[(a, side)]}. Случайно такой состав встречается "
                                f"с вероятностью {pv:.3f}.")})
        if len(members["a"]) >= 2 and len(members["b"]) >= 2:
            polar.append({"axis": a,
                          "groups": {poles["a"]["code"]: members["a"], poles["b"]["code"]: members["b"]},
                          "text_ru": f"По оси «{ta.AXIS_NAME_RU[a]}» команда делится на две группы: "
                                     f"{len(members['a'])} — {poles['a']['label_ru'].lower()}, "
                                     f"{len(members['b'])} — {poles['b']['label_ru'].lower()}."})

    mode_members: Dict[str, List[str]] = {}
    for nm in names:
        m = profiles[nm]["axes"]["decision"]["mode"]
        if m:
            mode_members.setdefault(m, []).append(nm)
    for mode, mem in mode_members.items():
        pop = DECISION_MODE_SHARES_PCT.get(mode)
        if not pop:
            continue
        tests += 1
        if len(mem) < 2:
            continue
        pv = binom_sf(len(mem), n, pop / 100.0)
        lvl = _level(pv)
        if lvl:
            over.append({"axis": "decision", "kind": "mode", "value": mode, "k": len(mem), "n": n,
                         "members": mem, "population_pct": pop, "p_value": round(pv, 6), "level": lvl,
                         "statement_ru": (f"{len(mem)} из {n} принимают решение {ta.DECISION_MODE_RU[mode]}. "
                                          f"В популяции {pop:.1f}%. Вероятность случайного состава — {pv:.4f}.")
                         if lvl == "robust" else None})
    over.sort(key=lambda x: x["p_value"])

    if n < ABSENCE_MIN_SIZE:
        absence: Dict[str, Any] = {
            "evaluated": False, "items": [],
            "reason_ru": f"При {n} участниках отсутствие неотличимо от случайности. "
                         f"Оценивается с {ABSENCE_MIN_SIZE} участников."}
    else:
        items = []
        for mode, pop in DECISION_MODE_SHARES_PCT.items():
            if mode == "none" or mode in mode_members:
                continue
            pv = p_absent(n, pop / 100.0)
            if pv < ALPHA_ROBUST:
                items.append({"axis": "decision", "value": mode, "population_pct": pop, "p_value": round(pv, 6),
                              "statement_ru": f"Ни у кого в команде решение не формируется "
                                              f"{ta.DECISION_MODE_RU[mode]}. При {n} участниках это "
                                              f"отличается от случайного набора."})
        for a in ta.AXES:
            for side in ("a", "b"):
                code = ta.POLES[a][side]["code"]
                if summary[a]["poles"][code]:
                    continue
                pop = POLE_SHARES_PCT[a].get(code) or 0
                pv = p_absent(n, pop / 100.0)
                if pv < ALPHA_ROBUST:
                    items.append({"axis": a, "value": code, "population_pct": pop, "p_value": round(pv, 6),
                                  "statement_ru": f"Ни у кого в команде нет полюса "
                                                  f"«{ta.POLES[a][side]['label_ru']}» "
                                                  f"({ta.AXIS_NAME_RU[a].lower()}). При {n} участниках "
                                                  f"это отличается от случайного набора."})
        absence = {"evaluated": True, "items": items, "reason_ru": None}

    return {
        "model": ta.MODEL_ID,
        "model_version": ta.MODEL_VERSION,
        "size": n,
        "team_code": "·".join(_majority_letter(a, summary[a]) for a in ta.AXES),
        "team_code_legend_ru": "полюс большинства по каждой оси; «–» — поровну или ни у кого",
        "matrix": {"columns": ["name", "code", *ta.AXES, "integration"], "rows": rows},
        "axes_summary": summary,
        "risk_hypotheses": risks,
        "overrepresentation": over,
        "tests_run": tests,
        "expected_false_signals_at_0_05": round(tests * ALPHA_SIGNAL, 2),
        "absence": absence,
        "polarization": polar,
        "bridging": bridging(people),
        "bridging_note_ru": "Эффект проксимальный: действует при совместной работе в одном помещении, "
                            "при удалённой и одиночной работе не действует.",
        "profiles": profiles,
        "report_rules_ru": REPORT_RULES_RU,
        "disclaimer_ru": ta.DISCLAIMER_RU,
    }
