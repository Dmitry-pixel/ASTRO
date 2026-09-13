"""Four operational characteristics of team dynamics from a Human Design chart.

Model ``hd-team-dynamics`` v1.2, agreed 2026-09-13. Supersedes v1.1.

    Transfer    Структурированная ↔ Неформальная   structured / emergent   S / N
    Processing  Фиксированная    ↔ Относительная   fixed      / relative   F / R
    Decision    Компетентный     ↔ Гармоничный     internal   / relational C / H
    Execution   Целенаправленное ↔ Импульсивное    planned    / adaptive   P / A
    Integration — closed / bridged, read together with Decision

They describe how a person prefers to take part in a team's information and work
process. Not personality traits, not a psychological diagnosis, not evidence of
competence, not grounds for hiring decisions.

What changed from v1.1
----------------------
* Transfer carries the complete set of 13 Throat channels (16-48 and 21-45 were
  missing); 8-1 moved to the emergent pole. Centre status weighs 2.
* Processing: the individual circuit (43-23, 24-61) drops to weight 2 — a fixed
  conviction is not reusable across similar situations, which is what the Fixed
  pole claims, so it stays the weakest of the three circuits (logic 3, abstract
  2, individual 2) while still outweighing a single dangling gate. Centre status
  weighs 2.
* Dangling gates are the gates of the axis' own centre only. Gate 64 (Head) left
  Processing, gate 24 (Ajna) joined it.
* Each axis is scored on its own table at full weight; a channel shared by two
  axes is no longer discounted in the secondary one. Consequence, measured on
  20 000 charts: the Transfer pole shifts the Processing pole (68% F among S
  against 26% F among N), so the team layer must not treat them as two
  independent observations.
* Decision is categorical: the authority is the pole. No index, no band — v1.1
  produced five bands out of one categorical variable, which was false
  precision. The G centre is a support profile and never moves the pole.
* Perspective enters Execution only, weight 1. Measured cost of adding it to
  Transfer as well: Transfer × Execution dependence 0.063 → 0.187, no gain in
  coverage.
* Root/Sacral definition is a separate field, never a vote for P or A: in v0.4 it
  measured the presence of a Sacral centre, not a style of execution.
* Integration is reported as closed / bridged. I1…I4 stay in the payload as raw
  data: I4 is under 1% of the population and ranking I3 above I2 has no basis.
* ``insufficient`` is gone. Every chart gets a pole or ``mixed`` on every axis.

Algorithm
---------
Every axis collects evidence for its first pole (A) and its second pole (B).
Weights are the agreed table (see ``RULES``). The index is

    index = 100 * (B + 1) / (A + B + 2)

0 is the first pole, 100 the second. The +1/+2 pulls a thin case towards 50, so
one marker never produces an extreme value. Bands:

    < 25 strong_a · 25–45 moderate_a · 45–55 mixed · 55–75 moderate_b · > 75 strong_b

Execution resting on the Perspective arrow alone keeps its pole and is marked
``basis: perspective_only`` with Hypothesis status.
"""
from __future__ import annotations

import datetime as _dt
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

MODEL_ID = "hd-team-dynamics"
MODEL_VERSION = "1.2"

CORE, SUPPORTING, HYPOTHESIS = "core", "supporting", "hypothesis"
AXES = ("transfer", "processing", "decision", "execution")
SCORED_AXES = ("transfer", "processing", "execution")
PERSPECTIVE_WEIGHT = 1.0

# Gates of the centres the scored axes stand on. Dangling gates are counted from
# the axis' own centre only — agreed 2026-09-13, applied to both axes alike.
CENTRE_GATES: Dict[str, Set[int]] = {
    "TT": {62, 23, 56, 16, 20, 31, 8, 33, 35, 12, 45},
    "AA": {47, 24, 4, 17, 11, 43},
    "RT": {58, 38, 54, 53, 60, 52, 19, 39, 41},
    "SL": {34, 5, 14, 29, 59, 9, 3, 42, 27},
}

# --------------------------------------------------------------------------- #
# Poles
# --------------------------------------------------------------------------- #
POLES: Dict[str, Dict[str, Dict[str, str]]] = {
    "transfer": {
        "a": {"code": "structured", "letter": "S", "label_ru": "Структурированная",
              "meaning_ru": "информация передаётся через оформленные каналы: повестка, документ, "
                            "зафиксированная договорённость"},
        "b": {"code": "emergent", "letter": "N", "label_ru": "Неформальная",
              "meaning_ru": "информация передаётся в живом разговоре, через рассказ и опыт, по ходу"},
    },
    "processing": {
        "a": {"code": "fixed", "letter": "F", "label_ru": "Фиксированная",
              "meaning_ru": "информация складывается в устойчивую концепцию, которую можно "
                            "применить повторно в сходной ситуации"},
        "b": {"code": "relative", "letter": "R", "label_ru": "Относительная",
              "meaning_ru": "информация рассматривается в контексте и допускает несколько "
                            "интерпретаций, окончательная фиксация не требуется"},
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
}
CENTRE_STATUS_RU = {
    "defined": "собственный устойчивый механизм",
    "undefined": "собственного устойчивого механизма нет; есть активированные потенциальные",
    "open": "активированных потенциальных механизмов нет",
}

# --------------------------------------------------------------------------- #
# Rules: (kind, key, side, weight, status, note_ru)
#   kind: centre_defined | centre_open | channel | dangling_gate
# --------------------------------------------------------------------------- #
Rule = Tuple[str, Any, str, float, str, str]

RULES: Dict[str, List[Rule]] = {
    "transfer": [
        ("centre_defined", "TT", "a", 2.0, CORE, "определённое Горло — устойчивая форма выражения"),
        ("channel", (17, 62), "a", 3.0, SUPPORTING, "мнение → детализация → формулировка"),
        ("channel", (16, 48), "a", 3.0, HYPOTHESIS, "знание → навык → демонстрация компетенции"),
        ("channel", (7, 31), "a", 2.0, SUPPORTING, "направление → формулирование позиции для группы"),
        ("channel", (23, 43), "a", 2.0, SUPPORTING, "инсайт → структурирование → понятная формулировка"),
        ("channel", (21, 45), "a", 2.0, HYPOTHESIS, "управление → распоряжение ресурсами"),
        ("centre_open", "TT", "b", 2.0, CORE, "открытое Горло — гибкая форма выражения"),
        ("channel", (35, 36), "b", 3.0, SUPPORTING, "переживание → опыт → эмоциональная передача"),
        ("channel", (12, 22), "b", 3.0, SUPPORTING, "состояние → эмоциональная выразительность"),
        ("channel", (20, 57), "b", 3.0, SUPPORTING, "интуитивное распознавание → мгновенное выражение"),
        ("channel", (13, 33), "b", 2.0, SUPPORTING, "опыт → память → рассказ"),
        ("channel", (11, 56), "b", 2.0, SUPPORTING, "идеи → история, повествование"),
        ("channel", (1, 8), "b", 2.0, SUPPORTING, "индивидуальное вдохновение → творческое выражение"),
        ("channel", (10, 20), "b", 2.0, SUPPORTING, "самоощущение → непосредственное выражение"),
        ("channel", (20, 34), "b", 2.0, SUPPORTING, "энергия отклика → непосредственное действие"),
        ("dangling_gate", 62, "a", 1.0, HYPOTHESIS, "ворота 62 — детализация"),
        ("dangling_gate", 23, "a", 1.0, HYPOTHESIS, "ворота 23 — формулирование инсайта"),
        ("dangling_gate", 16, "a", 1.0, HYPOTHESIS, "ворота 16 — демонстрация навыка"),
        ("dangling_gate", 31, "a", 1.0, HYPOTHESIS, "ворота 31 — организационный голос"),
        ("dangling_gate", 45, "a", 1.0, HYPOTHESIS, "ворота 45 — распоряжение ресурсом"),
        ("dangling_gate", 56, "b", 1.0, HYPOTHESIS, "ворота 56 — повествование"),
        ("dangling_gate", 8, "b", 1.0, HYPOTHESIS, "ворота 8 — вклад"),
        ("dangling_gate", 33, "b", 1.0, HYPOTHESIS, "ворота 33 — пересказ пережитого"),
        ("dangling_gate", 35, "b", 1.0, HYPOTHESIS, "ворота 35 — передача перемен"),
        ("dangling_gate", 12, "b", 1.0, HYPOTHESIS, "ворота 12 — выражение состояния"),
        ("dangling_gate", 20, "b", 1.0, HYPOTHESIS, "ворота 20 — выражение в моменте"),
    ],
    "processing": [
        ("centre_defined", "AA", "a", 2.0, CORE, "определённая Аджна — собственный механизм обработки"),
        ("channel", (4, 63), "a", 3.0, SUPPORTING, "вопрос → проверка → ответ"),
        ("channel", (17, 62), "a", 3.0, SUPPORTING, "мнение → структурирование → концепция"),
        ("channel", (43, 23), "a", 2.0, HYPOTHESIS, "инсайт → концептуализация; индивидуальный контур"),
        ("channel", (24, 61), "a", 2.0, HYPOTHESIS, "поиск внутреннего объяснения; индивидуальный контур"),
        ("centre_open", "AA", "b", 2.0, CORE, "открытая Аджна — обработка меняется с контекстом"),
        ("channel", (47, 64), "b", 2.0, SUPPORTING, "опыт → переработка → поиск смысла"),
        ("channel", (11, 56), "b", 2.0, SUPPORTING, "идеи → варианты → повествование"),
        ("dangling_gate", 4, "a", 1.0, HYPOTHESIS, "ворота 4 — ответ на вопрос"),
        ("dangling_gate", 17, "a", 1.0, HYPOTHESIS, "ворота 17 — мнение"),
        ("dangling_gate", 43, "a", 1.0, HYPOTHESIS, "ворота 43 — инсайт"),
        ("dangling_gate", 24, "a", 1.0, HYPOTHESIS, "ворота 24 — возвращение к вопросу"),
        ("dangling_gate", 11, "b", 1.0, HYPOTHESIS, "ворота 11 — идеи"),
        ("dangling_gate", 47, "b", 1.0, HYPOTHESIS, "ворота 47 — переработка опыта"),
    ],
    "execution": [
        ("channel", (9, 52), "a", 2.0, SUPPORTING, "фокус и доведение до результата"),
        ("channel", (53, 42), "a", 2.0, SUPPORTING, "последовательность: цикл от начала до завершения"),
        ("channel", (2, 14), "a", 2.0, SUPPORTING, "направление плюс ресурс для движения по нему"),
        ("channel", (5, 15), "a", 2.0, SUPPORTING, "собственный устойчивый ритм"),
        ("channel", (46, 29), "a", 2.0, SUPPORTING, "упорство: вхождение в путь и доведение его до конца"),
        ("channel", (54, 32), "a", 1.0, HYPOTHESIS, "длительная работа на трансформацию"),
        ("channel", (3, 60), "b", 2.0, SUPPORTING, "адаптация через мутацию, импульсный ритм"),
        ("channel", (20, 34), "b", 2.0, SUPPORTING, "непосредственное действие в моменте"),
        ("channel", (57, 34), "b", 2.0, SUPPORTING, "мгновенное интуитивное распознавание и действие"),
        ("channel", (20, 57), "b", 2.0, SUPPORTING, "спонтанное действие по распознаванию"),
        ("channel", (34, 10), "b", 1.0, HYPOTHESIS, "проявление через поведение"),
        ("channel", (38, 28), "b", 1.0, HYPOTHESIS, "мобилизация через вызов"),
    ],
}

# authority code (features.mechanics.get_auth) -> side, status, mode
DECISION_RULES: Dict[str, Tuple[str, str, str]] = {
    "SL":    ("a", CORE, "response"),
    "SN":    ("a", CORE, "instant"),
    "HT":    ("a", CORE, "will"),          # ego-manifested
    "HT_GC": ("a", CORE, "will"),          # ego-projected
    "GC":    ("a", CORE, "articulated"),   # self-projected
    "SP":    ("b", CORE, "delayed"),
    "outer": ("b", CORE, "external"),      # mental / environmental
    "lunar": ("b", HYPOTHESIS, "lunar"),
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
DECISION_MODE_LABEL_RU = {
    "response": "Отклик на вопрос",
    "instant": "Мгновенное распознавание",
    "will": "Взятое обязательство",
    "articulated": "Проговаривание вслух",
    "delayed": "Пауза до ясности",
    "external": "Обсуждение и смена обстановки",
    "lunar": "Наблюдение в течение цикла",
}
ENTRY_CONDITION = {
    "Generator":             ("response", "отклик на поставленный вопрос"),
    "Manifesting Generator": ("response", "отклик на поставленный вопрос"),
    "Projector":             ("invitation", "приглашение и признание роли"),
    "Manifestor":            ("inform", "информирование затронутых до действия"),
    "Reflector":             ("lunar_cycle", "наблюдение в течение цикла"),
}

# G-centre channels — a support profile for Decision. They never move the pole:
# the authority is categorical, channels and gates are quantitative, and three
# C channels must not outweigh an H authority.
G_CHANNELS: List[Tuple[Tuple[int, int], str, float, str]] = [
    ((1, 8), "c", 3.0, "самовыражение через собственный уникальный вклад"),
    ((7, 31), "c", 3.0, "определение направления и влияние на коллектив"),
    ((25, 51), "c", 3.0, "действие из внутреннего принципа, испытание и трансформация"),
    ((2, 14), "c", 3.0, "внутреннее направление плюс ресурс для движения"),
    ((10, 57), "c", 3.0, "интуитивное распознавание корректности поведения"),
    ((10, 34), "c", 3.0, "действие из собственной природы"),
    ((13, 33), "c", 2.0, "осмысление собственного опыта"),
    ((10, 20), "c", 2.0, "мгновенное выражение собственной идентичности"),
    ((46, 29), "h", 3.0, "вхождение в опыт и следование выбранному пути"),
    ((15, 5), "h", 3.0, "настройка на естественный ритм"),
]
G_GATES: Dict[int, Tuple[str, str]] = {
    7: ("c", "направление и роль в группе"), 1: ("c", "уникальное самовыражение"),
    13: ("c", "восприятие опыта других"), 25: ("c", "верность внутреннему принципу"),
    2: ("c", "внутреннее направление"), 10: ("c", "корректность собственного поведения"),
    46: ("h", "открытость опыту"), 15: ("h", "чувствительность к собственному ритму"),
}

# Root / Sacral — the energetic field of Execution. A separate field, never a
# vote for P or A: it answers whether the person has an own stable energy
# mechanism, not how that mechanism organises action.
ENERGY_PROFILE_RU = {
    "autonomous": ("Autonomous", "Автономное исполнение",
                   "собственное давление к движению и собственная энергия исполнения"),
    "stimulus_led": ("Stimulus-led", "Ведомое стимулом",
                     "собственный стимул к движению есть, энергия исполнения зависит от контекста"),
    "energy_led": ("Energy-led", "Ведомое энергией",
                   "собственная энергия исполнения есть, стимул к движению приходит извне"),
    "context_dependent": ("Context-dependent", "Зависит от контекста",
                          "и стимул к движению, и энергия исполнения зависят от контекста"),
}

INTEGRATION_LABEL_RU = {
    "closed": "Замкнутый механизм",
    "bridged": "Собран из блоков",
    "reflector": "Полностью открыт окружению",
}
INTEGRATION_RU = {
    "closed": "Механизм решения замкнут внутри: для перехода к действию внешние участники не требуются.",
    "bridged": "Механизм решения собран из блоков, между которыми нет собственного моста. "
               "В совместной работе роль внешнего замыкания выше.",
    "reflector": "Определённых центров нет: механизм полностью открыт окружению.",
}
# Decision pole × Integration — the agreed 2×2 reading. This is the only place
# where Integration earns its keep: Decision says by what mechanism the person
# arrives at a choice, Integration says whether anyone else is needed for it.
DECISION_READING = {
    ("a", "closed"):  ("internal_closed",
                       "Переходит к действию сам: механизм решения замкнут внутри, внешнее обсуждение не требуется."),
    ("a", "bridged"): ("internal_bridged",
                       "Решение внутреннее, но окончательно собирается при участии других."),
    ("b", "closed"):  ("relational_closed",
                       "Нужна пауза до ясности: требуется время, а не участники."),
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


def _band(index: float) -> str:
    if index < 25:
        return "strong_a"
    if index < 45:
        return "moderate_a"
    if index <= 55:
        return "mixed"
    if index <= 75:
        return "moderate_b"
    return "strong_b"


def _centre_status(centre: str, gates: Set[int], centres: Set[str]) -> str:
    """defined — own mechanism · undefined — gates but no channel · open — nothing."""
    if centre in centres:
        return "defined"
    return "undefined" if gates & CENTRE_GATES[centre] else "open"


def _baseline():
    try:
        from . import team_axes_baseline as b
        return b
    except ImportError:  # pragma: no cover — generated file
        return None


def _population(axis: str, index: float, pole: Optional[str]) -> Dict[str, Optional[float]]:
    b = _baseline()
    if b is None or axis not in getattr(b, "INDEX_CDF_PCT", {}):
        return {"index_percentile": None, "pole_pct": None}
    cdf = b.INDEX_CDF_PCT.get(axis)
    pct = cdf[max(0, min(100, int(index)))] if cdf else None
    return {"index_percentile": pct,
            "pole_pct": b.POLE_SHARES_PCT.get(axis, {}).get(pole) if pole else None}


def _collect(axis: str, gates: Set[int], centres: Set[str]) -> List[Dict[str, Any]]:
    rules = RULES[axis]
    complete = {frozenset(r[1]) for r in rules if r[0] == "channel" and set(r[1]) <= gates}
    fired: List[Dict[str, Any]] = []
    for kind, key, side, weight, status, note in rules:
        if kind == "centre_defined":
            hit, label = key in centres, f"{key} определён"
        elif kind == "centre_open":
            hit, label = key not in centres, f"{key} открыт"
        elif kind == "channel":
            hit, label = set(key) <= gates, _channel_key(*key)
        else:  # dangling_gate — active, not inside a complete channel of this axis
            hit = key in gates and not any(key in ch for ch in complete)
            label = f"ворота {key}"
        if hit:
            fired.append({"kind": kind, "key": label, "side": side, "weight": weight,
                          "status": status, "note_ru": note})
    return fired


def _axis(axis: str, evidence: List[Dict[str, Any]],
          extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    a = sum(e["weight"] for e in evidence if e["side"] == "a")
    b = sum(e["weight"] for e in evidence if e["side"] == "b")
    total = a + b
    idx = _index(a, b)
    band = _band(idx)
    side = "a" if band in ("strong_a", "moderate_a") else ("b" if band in ("strong_b", "moderate_b") else None)
    pole = POLES[axis][side] if side else None
    hyp = sum(e["weight"] for e in evidence if e["status"] == HYPOTHESIS)
    out = {
        "name_ru": AXIS_NAME_RU[axis],
        "poles": POLES[axis],
        "kind": "index",
        "index": idx,
        "evidence_a": round(a, 2),
        "evidence_b": round(b, 2),
        "confidence": round(total / (total + 2.0), 2),
        "band": band,
        "band_ru": BAND_RU[band],
        "side": side,
        "pole": pole["code"] if pole else "mixed",
        "letter": pole["letter"] if pole else "~",
        "pole_label_ru": pole["label_ru"] if pole else "Смешанная",
        "pole_meaning_ru": pole["meaning_ru"] if pole else
                           "признаки обоих полюсов присутствуют и уравновешены; "
                           "устойчивого предпочтения нет",
        "hypothesis_share": round(hyp / total, 2) if total else None,
        "evidence": evidence,
        "population": _population(axis, idx, pole["code"] if pole else "mixed"),
    }
    if extra:
        out.update(extra)
    return out


def _field(centre: str, gates: Set[int], centres: Set[str]) -> Dict[str, Any]:
    status = _centre_status(centre, gates, centres)
    return {"basis": centre, "status": status, "status_ru": CENTRE_STATUS_RU[status],
            "defined": status == "defined"}


def _g_support(gates: Set[int]) -> Dict[str, Any]:
    ev: List[Dict[str, Any]] = []
    complete: Set[int] = set()
    for pair, side, weight, note in G_CHANNELS:
        if set(pair) <= gates:
            complete |= set(pair)
            ev.append({"kind": "channel", "key": _channel_key(*pair), "side": side,
                       "weight": weight, "note_ru": note})
    for gate, (side, note) in G_GATES.items():
        if gate in gates and gate not in complete:
            ev.append({"kind": "dangling_gate", "key": f"ворота {gate}", "side": side,
                       "weight": 1.0, "note_ru": note})
    c = sum(e["weight"] for e in ev if e["side"] == "c")
    h = sum(e["weight"] for e in ev if e["side"] == "h")
    return {"c_signal": round(c, 1), "h_signal": round(h, 1), "evidence": ev,
            "note_ru": "Профиль поддержки из центра Джи. Показывает, на что опирается "
                       "механизм решения, и полюс не меняет."}


def _energy_profile(gates: Set[int], centres: Set[str]) -> Dict[str, Any]:
    root = _centre_status("RT", gates, centres)
    sacral = _centre_status("SL", gates, centres)
    rd, sd = root == "defined", sacral == "defined"
    code = ("autonomous" if rd and sd else "stimulus_led" if rd else
            "energy_led" if sd else "context_dependent")
    label, label_ru, text = ENERGY_PROFILE_RU[code]
    return {"root": root, "sacral": sacral, "code": code, "label": label,
            "label_ru": label_ru, "text_ru": text,
            "note_ru": "Отвечает на вопрос, есть ли собственный устойчивый энергетический "
                       "механизм исполнения. Полюс P/A определяют каналы, а не это поле."}


def _integration(definition: Any) -> Dict[str, Any]:
    try:
        n = int(definition)
    except (TypeError, ValueError):
        n = -1
    raw = "R" if n == 0 else (f"I{n}" if 1 <= n <= 4 else None)
    reading = None if raw is None else ("reflector" if raw == "R" else
                                        "closed" if n == 1 else "bridged")
    return {"reading": reading, "raw": raw, "components": n if n >= 0 else None,
            "closed": (n == 1) if n >= 0 else None,
            "label_ru": INTEGRATION_LABEL_RU.get(reading) if reading else None,
            "text_ru": INTEGRATION_RU.get(reading) if reading else None}


def _entry(energy_type: str) -> Dict[str, Optional[str]]:
    code, ru = ENTRY_CONDITION.get(energy_type, (None, None))
    return {"energy_type": energy_type, "entry_condition": code, "entry_condition_ru": ru}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def compute_axes(gates: Iterable[int], active_chakras: Iterable[str], authority: str,
                 energy_type: str, definition: Any, perspective: Optional[str] = None,
                 perspective_confidence: Optional[str] = None) -> Dict[str, Any]:
    """The four characteristics plus Integration for one chart."""
    g = {int(x) for x in gates}
    ck = set(active_chakras)
    flags: List[Dict[str, str]] = []

    transfer = _axis("transfer", _collect("transfer", g, ck),
                     extra={"field": _field("TT", g, ck)})
    processing = _axis("processing", _collect("processing", g, ck),
                       extra={"field": _field("AA", g, ck)})

    # Decision — the authority is the pole. Categorical: no index, no band.
    rule = DECISION_RULES.get(authority)
    integration = _integration(definition)
    side, status, mode = rule if rule else (None, None, None)
    pole = POLES["decision"][side] if side else None
    decision: Dict[str, Any] = {
        "name_ru": AXIS_NAME_RU["decision"],
        "poles": POLES["decision"],
        "kind": "categorical",
        "index": None,
        "band": None,
        "band_ru": None,
        "side": side,
        "pole": pole["code"] if pole else None,
        "letter": pole["letter"] if pole else "–",
        "pole_label_ru": pole["label_ru"] if pole else None,
        "pole_meaning_ru": pole["meaning_ru"] if pole else None,
        "authority": authority,
        "authority_ru": AUTHORITY_RU.get(authority),
        "status": status,
        "mode": mode,
        "mode_label_ru": DECISION_MODE_LABEL_RU.get(mode) if mode else None,
        "mode_ru": DECISION_MODE_RU.get(mode) if mode else None,
        "field": _entry(energy_type),
        "g_support": _g_support(g),
    }
    reading = None
    if side and integration["reading"] in ("closed", "bridged"):
        code, text = DECISION_READING[(side, integration["reading"])]
        reading = {"code": code, "integration": integration["reading"], "text_ru": text}
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
    execution = _axis("execution", e_ev, extra={
        "basis": basis,
        "perspective": {"value": perspective, "confidence": perspective_confidence},
        "field": _entry(energy_type),
        "energy_profile": _energy_profile(g, ck),
    })

    axes = {"transfer": transfer, "processing": processing,
            "decision": decision, "execution": execution}

    for a in SCORED_AXES:
        if axes[a]["band"] == "mixed":
            flags.append({"axis": a, "code": "mixed",
                          "text_ru": f"«{AXIS_NAME_RU[a]}»: признаки обоих полюсов уравновешены — "
                                     f"смешанный стиль, а не отсутствие данных."})
    if basis == "perspective_only":
        flags.append({"axis": "execution", "code": "perspective_only",
                      "text_ru": "«Исполнение» определено только по стрелке Perspective — рабочая гипотеза."})
    elif basis == "none":
        flags.append({"axis": "execution", "code": "no_basis",
                      "text_ru": "«Исполнение»: ни одного канала и нет стрелки Perspective."})
    if perspective_confidence == "low":
        flags.append({"axis": "execution", "code": "perspective_near_boundary",
                      "text_ru": "Стрелка Perspective близка к границе тона: её направление зависит от точности "
                                 "времени рождения и версии эфемерид."})
    if rule and status == HYPOTHESIS:
        flags.append({"axis": "decision", "code": "hypothesis",
                      "text_ru": "Лунный авторитет отнесён к гармоничному полюсу по нашему допущению."})

    code = "·".join(axes[a]["letter"] for a in AXES)
    return {
        "model": MODEL_ID,
        "model_version": MODEL_VERSION,
        "code": code,
        "code_legend_ru": "Передача · Обработка · Решение · Исполнение; «~» — смешанный стиль",
        "index_legend_ru": "0 — первый полюс, 100 — второй; 45–55 — смешанный стиль. "
                           "У Решения индекса нет: полюс задаёт авторитет.",
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
    """Recompute the characteristics across the stated birth-time uncertainty."""
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
        idx = [c["axes"][a]["index"] for c in charts if c["axes"][a]["index"] is not None]
        out["axes"][a] = {
            "poles": {k: round(v / n, 3) for k, v in letters.most_common()},
            "index_min": min(idx) if idx else None,
            "index_max": max(idx) if idx else None,
            "pole_stable": len(letters) == 1,
            "base_pole_share": round(letters.get(base["axes"][a]["letter"] or "–", 0) / n, 3),
        }
    ints = Counter(c["integration"]["reading"] for c in charts)
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
