"""Four operational characteristics of team dynamics from a Human Design chart.

Model ``hd-team-dynamics`` v1.1, agreed 2026-09-10.

    Transfer    Структурированная ↔ Неформальная     structured / emergent     S / F
    Processing  Фиксированная    ↔ Относительная     consistent / contextual   D / R
    Decision    Компетентный     ↔ Гармоничный       internal   / relational   C / H
    Execution   Целенаправленное ↔ Импульсивное      planned    / adaptive     P / A
    Integration — definition count, read together with Decision (I1…I4, R)

They describe how a person prefers to take part in a team's information and work
process. Not personality traits, not a psychological diagnosis, not evidence of
competence, not grounds for hiring decisions.

Algorithm
---------
Every axis collects evidence for its first pole (A) and its second pole (B).
Weights are the agreed table (see ``RULES``). The index is

    index = 100 * (B + 1) / (A + B + 2)

0 is the first pole, 100 the second. The +1/+2 pulls a thin case towards 50,
so one marker never produces an extreme value. Bands:

    < 25 strong_a · 25–45 moderate_a · 45–55 mixed · 55–75 moderate_b · > 75 strong_b

A band — and a pole — is assigned only when A + B >= 2. The one exception is
Execution resting on the Perspective arrow alone: it keeps its pole and is
marked ``basis: perspective_only`` with Hypothesis status.

Agreed exclusions: open centres and Root/Sacral definition do not enter any
index; Perspective enters Execution only; Definition stays a separate field.
Section 7 of the methodology wins over the tables: 43-23 and 17-62 belong to
Processing (×0.5 in Transfer), 11-56 to Transfer (×0.5 in Processing), 20-34
and 20-57 to Execution (×0.5 in Transfer).
"""
from __future__ import annotations

import datetime as _dt
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

MODEL_ID = "hd-team-dynamics"
MODEL_VERSION = "1.1"

CORE, SUPPORTING, HYPOTHESIS = "core", "supporting", "hypothesis"
AXES = ("transfer", "processing", "decision", "execution")
MIN_EVIDENCE = 2.0
PERSPECTIVE_WEIGHT = 1.0

# --------------------------------------------------------------------------- #
# Poles
# --------------------------------------------------------------------------- #
POLES: Dict[str, Dict[str, Dict[str, str]]] = {
    "transfer": {
        "a": {"code": "structured", "letter": "S", "label_ru": "Структурированная",
              "meaning_ru": "информация передаётся через оформленные каналы: повестка, документ, "
                            "зафиксированная договорённость"},
        "b": {"code": "emergent", "letter": "F", "label_ru": "Неформальная",
              "meaning_ru": "информация передаётся в живом разговоре, через рассказ и опыт, по ходу"},
    },
    "processing": {
        "a": {"code": "consistent", "letter": "D", "label_ru": "Фиксированная",
              "meaning_ru": "интерпретация опирается на данные и устойчивую внутреннюю логику, "
                            "источник информации значит меньше, чем её содержание"},
        "b": {"code": "contextual", "letter": "R", "label_ru": "Относительная",
              "meaning_ru": "интерпретация учитывает контекст, источник и доверие к тому, кто "
                            "принёс информацию"},
    },
    "decision": {
        "a": {"code": "internal", "letter": "C", "label_ru": "Компетентный",
              "meaning_ru": "переход к действию опирается на собственный внутренний механизм "
                            "решения и не требует длительной паузы"},
        "b": {"code": "relational", "letter": "H", "label_ru": "Гармоничный",
              "meaning_ru": "переходу к действию нужна пауза до ясности либо внешний контур "
                            "обсуждения"},
    },
    "execution": {
        "a": {"code": "planned", "letter": "P", "label_ru": "Целенаправленное",
              "meaning_ru": "работа держится на цикле, ритме и фокусе и доводится до завершения"},
        "b": {"code": "adaptive", "letter": "A", "label_ru": "Импульсивное",
              "meaning_ru": "работа идёт по ходу: в моменте, рывками или под давлением ситуации"},
    },
}
AXIS_NAME_RU = {
    "transfer": "Передача информации",
    "processing": "Обработка информации",
    "decision": "Принятие решений / переход к действию",
    "execution": "Исполнение",
}
BAND_RU = {
    "strong_a": "выраженный первый полюс",
    "moderate_a": "умеренный первый полюс",
    "mixed": "смешанный стиль",
    "moderate_b": "умеренный второй полюс",
    "strong_b": "выраженный второй полюс",
    "insufficient": "недостаточно признаков",
}

# --------------------------------------------------------------------------- #
# Rules: (kind, key, side, weight, status, note_ru)
#   kind: centre_defined | centre_open | channel | dangling_gate
# --------------------------------------------------------------------------- #
Rule = Tuple[str, Any, str, float, str, str]

RULES: Dict[str, List[Rule]] = {
    "transfer": [
        ("centre_defined", "TT", "a", 1.0, CORE, "определённое Горло — устойчивая форма выражения"),
        ("channel", (43, 23), "a", 1.0, SUPPORTING, "структурирование инсайта (основная ось — Обработка, ×0.5)"),
        ("channel", (17, 62), "a", 0.5, SUPPORTING, "оформление мнения и деталей (основная ось — Обработка, ×0.5)"),
        ("channel", (31, 7), "a", 1.0, SUPPORTING, "ролевое, организационное выражение"),
        ("channel", (8, 1), "a", 1.0, SUPPORTING, "выражение вклада и модели"),
        ("centre_open", "TT", "b", 1.0, CORE, "открытое Горло — гибкое выражение"),
        ("channel", (11, 56), "b", 2.0, SUPPORTING, "рассказ, идеи, живой обмен"),
        ("channel", (35, 36), "b", 2.0, SUPPORTING, "передача через опыт и перемены"),
        ("channel", (12, 22), "b", 2.0, SUPPORTING, "настроение, социальная выразительность"),
        ("channel", (33, 13), "b", 1.0, SUPPORTING, "пересказ пережитого"),
        ("channel", (20, 10), "b", 1.0, SUPPORTING, "выражение через поведение"),
        ("channel", (20, 34), "b", 0.5, SUPPORTING, "выражение в моменте (основная ось — Исполнение, ×0.5)"),
        ("channel", (20, 57), "b", 0.5, SUPPORTING, "спонтанное выражение (основная ось — Исполнение, ×0.5)"),
    ],
    "processing": [
        ("centre_defined", "AA", "a", 2.0, CORE, "определённая Ajna — стабильная концептуализация"),
        ("channel", (63, 4), "a", 3.0, SUPPORTING, "логика, проверка, доказательства"),
        ("channel", (43, 23), "a", 2.0, SUPPORTING, "структурирование"),
        ("channel", (17, 62), "a", 2.0, SUPPORTING, "фиксация мнения и деталей"),
        ("channel", (61, 24), "a", 1.0, SUPPORTING, "внутреннее осмысление"),
        ("dangling_gate", 4, "a", 1.0, HYPOTHESIS, "ворота 4 — детализация"),
        ("dangling_gate", 17, "a", 1.0, HYPOTHESIS, "ворота 17 — мнение"),
        ("dangling_gate", 43, "a", 1.0, HYPOTHESIS, "ворота 43 — структура"),
        ("centre_open", "AA", "b", 2.0, CORE, "открытая Ajna — вариативная обработка"),
        ("channel", (64, 47), "b", 2.0, SUPPORTING, "абстракция, переработка опыта"),
        ("channel", (11, 56), "b", 0.5, SUPPORTING, "исследование идей (основная ось — Передача, ×0.5)"),
        ("dangling_gate", 47, "b", 1.0, HYPOTHESIS, "ворота 47 — абстракция"),
        ("dangling_gate", 64, "b", 1.0, HYPOTHESIS, "ворота 64 — переработка опыта"),
        ("dangling_gate", 11, "b", 1.0, HYPOTHESIS, "ворота 11 — исследование"),
    ],
    "execution": [
        ("channel", (5, 15), "a", 2.0, SUPPORTING, "ритм, регулярность"),
        ("channel", (9, 52), "a", 2.0, SUPPORTING, "фокус, доведение"),
        ("channel", (42, 53), "a", 2.0, SUPPORTING, "цикл развития и завершения"),
        ("channel", (46, 29), "a", 2.0, SUPPORTING, "упорство до завершения"),
        ("channel", (54, 32), "a", 1.0, SUPPORTING, "длительная работа на трансформацию"),
        ("channel", (20, 34), "b", 2.0, SUPPORTING, "действие в моменте"),
        ("channel", (20, 57), "b", 2.0, SUPPORTING, "спонтанное действие"),
        ("channel", (34, 57), "b", 1.0, SUPPORTING, "интуитивная мощность"),
        ("channel", (34, 10), "b", 1.0, SUPPORTING, "проявление через поведение"),
        ("channel", (3, 60), "b", 1.0, SUPPORTING, "прорыв, мутация"),
        ("channel", (38, 28), "b", 1.0, SUPPORTING, "мобилизация через вызов"),
    ],
}

# authority code (features.mechanics.get_auth) -> side, weight, status, mode
DECISION_RULES: Dict[str, Tuple[str, float, str, str]] = {
    "SL":    ("a", 3.0, CORE, "response"),
    "SN":    ("a", 3.0, CORE, "instant"),
    "HT":    ("a", 3.0, CORE, "will"),          # ego-manifested
    "HT_GC": ("a", 3.0, CORE, "will"),          # ego-projected
    "GC":    ("a", 2.0, CORE, "articulated"),   # self-projected
    "SP":    ("b", 2.0, CORE, "delayed"),
    "outer": ("b", 3.0, CORE, "external"),      # mental / environmental
    "lunar": ("b", 3.0, HYPOTHESIS, "lunar"),
}
AUTHORITY_RU = {
    "SL": "сакральный", "SN": "селезёночный", "HT": "эго-манифестированный",
    "HT_GC": "эго-проецированный", "GC": "самопроецированный", "SP": "эмоциональный",
    "outer": "ментальный (средовой)", "lunar": "лунный",
}
DECISION_MODE_RU = {
    "response": "через отклик на конкретно поставленный вопрос или предложение",
    "instant": "одномоментным распознаванием; повторно возвращаться к вопросу бесполезно",
    "will": "как принятое на себя обязательство",
    "articulated": "в проговаривании вслух: нужно услышать собственную формулировку",
    "delayed": "не сразу: нужна пауза до ясности; решение на пике обсуждения будет пересмотрено",
    "external": "через обсуждение и смену обстановки",
    "lunar": "в течение цикла, через наблюдение окружения",
}
ENTRY_CONDITION = {
    "Generator":             ("response", "отклик на поставленный вопрос"),
    "Manifesting Generator": ("response", "отклик на поставленный вопрос"),
    "Projector":             ("invitation", "приглашение и признание роли"),
    "Manifestor":            ("inform", "информирование затронутых до действия"),
    "Reflector":             ("lunar_cycle", "наблюдение в течение цикла"),
}

INTEGRATION_RU = {
    "I1": "Механизм решения замкнут внутри.",
    "I2": "Механизм решения собран из 2 блоков без собственного моста между ними.",
    "I3": "Механизм решения собран из 3 блоков без собственного моста между ними.",
    "I4": "Механизм решения собран из 4 блоков без собственного моста между ними.",
    "R":  "Определённых центров нет: механизм полностью открыт окружению.",
}
# Decision pole × Integration — the agreed 2×2 reading.
DECISION_READING = {
    ("a", "closed"):  ("internal_closed",
                       "Переходит к действию сам: механизм решения замкнут внутри, внешнее обсуждение не требуется."),
    ("a", "bridged"): ("internal_bridged",
                       "Решение внутреннее, но окончательно собирается при участии других: в совместной работе "
                       "роль внешнего замыкания выше."),
    ("b", "closed"):  ("relational_closed",
                       "Нужна пауза до ясности; требуется время, а не участники."),
    ("b", "bridged"): ("relational_bridged",
                       "Нужны и пауза, и контакт: решение созревает во времени и в обсуждении."),
}

DISCLAIMER_RU = (
    "Модель описывает предпочтительный способ участия в командном информационном и рабочем "
    "процессе. Это не психологическая диагностика, не оценка компетентности и не основание "
    "для кадровых решений. Веса — проекция методологии на терминологию Human Design, а не "
    "свойство системы; правила со статусом hypothesis помечены."
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _channel_key(a: int, b: int) -> str:
    return f"{a}-{b}"


def _index(a: float, b: float) -> float:
    return round(100.0 * (b + 1.0) / (a + b + 2.0), 1)


def _band(index: float, total: float, allow_thin: bool = False) -> str:
    if total < MIN_EVIDENCE and not allow_thin:
        return "insufficient"
    if index < 25:
        return "strong_a"
    if index < 45:
        return "moderate_a"
    if index <= 55:
        return "mixed"
    if index <= 75:
        return "moderate_b"
    return "strong_b"


def _baseline():
    try:
        from . import team_axes_baseline as b
        return b
    except ImportError:  # pragma: no cover — generated file
        return None


def _population(axis: str, index: float, pole: Optional[str]) -> Dict[str, Optional[float]]:
    b = _baseline()
    if b is None:
        return {"index_percentile": None, "pole_pct": None}
    cdf = b.INDEX_CDF_PCT.get(axis)
    pct = None
    if cdf:
        i = max(0, min(100, int(index)))   # share of the population at or below this index
        pct = cdf[i]
    return {"index_percentile": pct,
            "pole_pct": b.POLE_SHARES_PCT.get(axis, {}).get(pole) if pole else None}


def _collect(axis: str, gates: Set[int], centres: Set[str]) -> List[Dict[str, Any]]:
    rules = RULES[axis]
    complete = {frozenset(r[1]) for r in rules if r[0] == "channel" and set(r[1]) <= gates}
    fired: List[Dict[str, Any]] = []
    for kind, key, side, weight, status, note in rules:
        if kind == "centre_defined":
            hit = key in centres
            label = f"{key} определён"
        elif kind == "centre_open":
            hit = key not in centres
            label = f"{key} открыт"
        elif kind == "channel":
            hit = set(key) <= gates
            label = _channel_key(*key)
        else:  # dangling_gate — active, but not inside a complete channel of this axis
            hit = key in gates and not any(key in ch for ch in complete)
            label = f"ворота {key}"
        if hit:
            fired.append({"kind": kind, "key": label, "side": side, "weight": weight,
                          "status": status, "note_ru": note})
    return fired


def _axis(axis: str, evidence: List[Dict[str, Any]], allow_thin: bool = False,
          extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    a = sum(e["weight"] for e in evidence if e["side"] == "a")
    b = sum(e["weight"] for e in evidence if e["side"] == "b")
    total = a + b
    idx = _index(a, b)
    band = _band(idx, total, allow_thin)
    side = "a" if band in ("strong_a", "moderate_a") else ("b" if band in ("strong_b", "moderate_b") else None)
    pole = POLES[axis][side] if side else None
    hyp = sum(e["weight"] for e in evidence if e["status"] == HYPOTHESIS)
    out = {
        "name_ru": AXIS_NAME_RU[axis],
        "poles": POLES[axis],
        "index": idx,
        "evidence_a": round(a, 2),
        "evidence_b": round(b, 2),
        "confidence": round(total / (total + 2.0), 2),
        "band": band,
        "band_ru": BAND_RU[band],
        "side": side,
        "pole": pole["code"] if pole else None,
        "letter": pole["letter"] if pole else None,
        "pole_label_ru": pole["label_ru"] if pole else None,
        "pole_meaning_ru": pole["meaning_ru"] if pole else None,
        "hypothesis_share": round(hyp / total, 2) if total else None,
        "evidence": evidence,
        "population": _population(axis, idx, pole["code"] if pole else None),
    }
    if extra:
        out.update(extra)
    return out


def _integration(definition: Any) -> Dict[str, Any]:
    try:
        n = int(definition)
    except (TypeError, ValueError):
        n = -1
    code = "R" if n == 0 else (f"I{n}" if 1 <= n <= 4 else None)
    return {"code": code, "components": n if n >= 0 else None,
            "closed": (n == 1) if n >= 0 else None,
            "text_ru": INTEGRATION_RU.get(code) if code else None}


def _entry(energy_type: str) -> Dict[str, Optional[str]]:
    code, ru = ENTRY_CONDITION.get(energy_type, (None, None))
    return {"energy_type": energy_type, "entry_condition": code, "entry_condition_ru": ru}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def compute_axes(gates: Iterable[int], active_chakras: Iterable[str], authority: str,
                 energy_type: str, definition: Any, perspective: Optional[str] = None,
                 perspective_confidence: Optional[str] = None) -> Dict[str, Any]:
    """The four characteristics plus Integration for one chart.

    ``perspective`` is the Personality-Nodes arrow (``variables.bottom_right.value``),
    ``perspective_confidence`` its boundary flag (``high`` / ``low``).
    """
    g = {int(x) for x in gates}
    ck = set(active_chakras)
    flags: List[Dict[str, str]] = []

    transfer = _axis("transfer", _collect("transfer", g, ck), extra={
        "field": {"basis": "throat", "defined": "TT" in ck,
                  "stability": "stable" if "TT" in ck else "conditioned"}})
    processing = _axis("processing", _collect("processing", g, ck), extra={
        "field": {"basis": "ajna", "defined": "AA" in ck,
                  "stability": "stable" if "AA" in ck else "conditioned"}})

    # Decision — authority only
    rule = DECISION_RULES.get(authority)
    integration = _integration(definition)
    if rule:
        side, weight, status, mode = rule
        d_ev = [{"kind": "authority", "key": authority, "side": side, "weight": weight,
                 "status": status, "note_ru": f"{AUTHORITY_RU[authority]} авторитет"}]
    else:
        mode, d_ev = None, []
    decision = _axis("decision", d_ev, extra={
        "mode": mode,
        "mode_ru": DECISION_MODE_RU.get(mode) if mode else None,
        "authority": authority,
        "field": _entry(energy_type),
    })
    reading = None
    if decision["side"] and integration["closed"] is not None:
        code, text = DECISION_READING[(decision["side"], "closed" if integration["closed"] else "bridged")]
        reading = {"code": code, "integration": integration["code"], "text_ru": text}
    decision["integration_reading"] = reading

    # Execution — channels plus the Perspective arrow
    e_ev = _collect("execution", g, ck)
    has_channels = bool(e_ev)
    if perspective in ("left", "right"):
        e_ev.append({"kind": "variable", "key": f"perspective_{perspective}",
                     "side": "a" if perspective == "left" else "b",
                     "weight": PERSPECTIVE_WEIGHT, "status": HYPOTHESIS,
                     "note_ru": ("Perspective Left — сфокусированное следование выбранной линии"
                                 if perspective == "left" else
                                 "Perspective Right — периферийное восприятие, подстройка по ходу")})
    basis = "channels" if has_channels else ("perspective_only" if perspective in ("left", "right") else "none")
    execution = _axis("execution", e_ev, allow_thin=(basis == "perspective_only"), extra={
        "basis": basis,
        "perspective": {"value": perspective, "confidence": perspective_confidence},
        "field": _entry(energy_type),
    })

    axes = {"transfer": transfer, "processing": processing,
            "decision": decision, "execution": execution}

    for a in AXES:
        ax = axes[a]
        if ax["band"] == "insufficient":
            flags.append({"axis": a, "code": "insufficient",
                          "text_ru": f"«{AXIS_NAME_RU[a]}»: признаков меньше порога, полюс не присваивается."})
        elif ax["band"] == "mixed":
            flags.append({"axis": a, "code": "mixed",
                          "text_ru": f"«{AXIS_NAME_RU[a]}»: признаки обоих полюсов уравновешены."})
    if basis == "perspective_only":
        flags.append({"axis": "execution", "code": "perspective_only",
                      "text_ru": "«Исполнение» определено только по стрелке Perspective — рабочая гипотеза."})
    if perspective_confidence == "low":
        flags.append({"axis": "execution", "code": "perspective_near_boundary",
                      "text_ru": "Стрелка Perspective близка к границе тона: её направление зависит от точности "
                                 "времени рождения и версии эфемерид."})
    if decision["band"] != "insufficient" and rule and rule[2] == HYPOTHESIS:
        flags.append({"axis": "decision", "code": "hypothesis",
                      "text_ru": "Лунный авторитет отнесён к гармоничному полюсу по нашему допущению."})

    code = "·".join([(axes[a]["letter"] or "–") for a in AXES] + [integration["code"] or "–"])
    return {
        "model": MODEL_ID,
        "model_version": MODEL_VERSION,
        "code": code,
        "code_legend_ru": "Передача · Обработка · Решение · Исполнение · Интеграция; «–» — полюс не присвоен",
        "index_legend_ru": "0 — первый полюс, 100 — второй; 45–55 — смешанный стиль",
        "axes": axes,
        "integration": integration,
        "flags": flags,
        "time_stability": None,
        "disclaimer_ru": DISCLAIMER_RU,
    }


def compute_from_result(single_result: Sequence[Any]) -> Dict[str, Any]:
    """Build from the tuple returned by ``features.core.calc_single_hd_features``."""
    typ, auth, definition = single_result[0], single_result[1], single_result[5]
    variables = single_result[11] or {}
    br = variables.get("bottom_right") or {}
    return compute_axes(single_result[6]["gate"], single_result[7], auth, typ, definition,
                        br.get("value"), br.get("confidence"))


def compute_from_date_to_gate(d: Dict[str, Any], time_uncertainty_min: float = 1.0) -> Dict[str, Any]:
    from .attributes import get_variables
    from .mechanics import get_auth, get_channels_and_active_chakras, get_definition, get_typ
    ch, ck = get_channels_and_active_chakras(d)
    br = get_variables(d, time_uncertainty_min).get("bottom_right") or {}
    return compute_axes(d["gate"], ck, get_auth(ck, ch), get_typ(ch, ck), get_definition(ch, ck),
                        br.get("value"), br.get("confidence"))


def _axes_at(ts: Tuple[Any, ...]) -> Dict[str, Any]:
    from .core import hd_features
    return compute_from_date_to_gate(hd_features(*ts).birth_creat_date_to_gate())


def _shift(ts: Tuple[Any, ...], minutes: float) -> Tuple[Any, ...]:
    y, mo, d, h, mi, s, tz = ts
    t = _dt.datetime(int(y), int(mo), int(d), int(h), int(mi), int(s)) + _dt.timedelta(minutes=minutes)
    return (t.year, t.month, t.day, t.hour, t.minute, t.second, tz)


def time_stability(timestamp: Tuple[Any, ...], precision_min: Optional[float],
                   baseline: Optional[Dict[str, Any]] = None,
                   samples: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Recompute the characteristics across the stated birth-time uncertainty.

    ``None`` below five minutes. Otherwise evenly spaced offsets across
    ``[-precision, +precision]`` (capped at ±12 h, ~30 min apart, 5–49 points)
    plus the stated time; a chart costs about a millisecond.
    """
    if precision_min is None or precision_min < 5:
        return None
    span = min(float(precision_min), 720.0)
    steps = int(samples) if samples else min(49, max(5, int(2 * span / 30) + 1))
    steps = max(2, steps)
    offsets = [-span + 2 * span * i / (steps - 1) for i in range(steps)]
    if 0.0 not in offsets:
        offsets.append(0.0)
    charts = [baseline if (o == 0.0 and baseline is not None) else _axes_at(_shift(timestamp, o))
              for o in offsets]
    base = baseline or charts[offsets.index(0.0)]
    n = len(charts)
    out: Dict[str, Any] = {"precision_min": float(precision_min), "samples": n,
                           "offsets_min": [round(o, 1) for o in offsets], "axes": {}}
    for a in AXES:
        letters = Counter(c["axes"][a]["letter"] or "–" for c in charts)
        idx = [c["axes"][a]["index"] for c in charts]
        out["axes"][a] = {
            "poles": {k: round(v / n, 3) for k, v in letters.most_common()},
            "index_min": min(idx),
            "index_max": max(idx),
            "pole_stable": len(letters) == 1,
            "base_pole_share": round(letters.get(base["axes"][a]["letter"] or "–", 0) / n, 3),
        }
    ints = Counter(c["integration"]["code"] for c in charts)
    out["integration"] = {k: round(v / n, 3) for k, v in ints.most_common()}
    unstable = [a for a in AXES if not out["axes"][a]["pole_stable"]]
    out["unstable_axes"] = unstable
    out["summary_ru"] = (
        "Все четыре полюса устойчивы в пределах заявленной точности времени."
        if not unstable else
        "Меняются в пределах заявленной точности времени: "
        + ", ".join(AXIS_NAME_RU[a] for a in unstable)
        + ". Для этих осей нужно более точное время рождения.")
    return out
