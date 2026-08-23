"""Semantic tables for relational analysis.

Pure data plus tiny pure lookups — no ephemeris, no I/O, no pydantic. Everything
here is a stable machine `code` paired with English and Russian labels, so the
consuming application can interpret the JSON in either language without a second
round trip.

Extracted and rewritten from the semantics that used to sit inline inside
`services/composite.py`, then extended: the four Maia classes now carry their own
mechanics text, the variable synergy covers all four arrows instead of Motivation
alone, and the aura table states the task of the union rather than a bare label.
"""
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# 1. Centre formula — how many of the nine centres the composite defines
# --------------------------------------------------------------------------- #
CENTRE_FORMULA: Dict[int, Dict[str, str]] = {
    9: {
        "code": "9+0",
        "label": "Nowhere to hide",
        "label_ru": "Нигде не скрыться",
        "reading": "All nine centres are defined. The pair has no open window onto the "
                   "outside world and little room to rest from each other. A very dense "
                   "bond that can turn airless.",
        "reading_ru": "Определены все девять центров. В отношениях нет «окна» во внешний мир "
                      "и почти нет возможности отдохнуть друг от друга. Очень плотная связь, "
                      "порой удушающая.",
    },
    8: {
        "code": "8+1",
        "label": "Room to grow",
        "label_ru": "Есть куда расти",
        "reading": "Eight defined, one open. The balance that carries long unions: shared "
                   "chemistry plus one zone of freedom and common interest.",
        "reading_ru": "Восемь определены, один открыт. Идеальный баланс для долгого союза: "
                      "общая химия и одна зона свободы и совместного интереса.",
    },
    7: {
        "code": "7+2",
        "label": "Work to do",
        "label_ru": "Работать есть над чем",
        "reading": "Two open centres. The union asks for awareness — both are open to "
                   "outside authorities and conditioning through those centres.",
        "reading_ru": "Два открытых центра. Отношения требуют осознанности: партнёры часто "
                      "отвлекаются на внешние авторитеты и обуславливание.",
    },
    6: {
        "code": "6+3",
        "label": "Not enough glue",
        "label_ru": "Не хватает клея",
        "reading": "Three open centres. There may simply not be enough energetic glue to "
                   "hold the two together without deliberate effort.",
        "reading_ru": "Три открытых центра. Энергетического «клея», чтобы удерживаться "
                      "вместе, может банально не хватать.",
    },
}
_LOW_FORMULA = {
    "label": "Not enough glue",
    "label_ru": "Не хватает клея",
    "reading": "Four or more open centres. Very little shared definition; the bond needs "
               "an external reason to exist.",
    "reading_ru": "Четыре и более открытых центра. Общего определения почти нет; связи "
                  "нужна внешняя причина существовать.",
}


def centre_formula(defined_count: int) -> Dict[str, Any]:
    """Return the formula block for a composite with `defined_count` centres."""
    entry = CENTRE_FORMULA.get(defined_count)
    if entry is None:
        entry = dict(_LOW_FORMULA, code=f"{defined_count}+{9 - defined_count}")
    return {
        "defined": defined_count,
        "open": 9 - defined_count,
        **entry,
    }


# --------------------------------------------------------------------------- #
# 2. The four Maia connection classes
# --------------------------------------------------------------------------- #
MAIA_TYPES: Dict[str, Dict[str, str]] = {
    "electromagnetic": {
        "label": "Electromagnetic",
        "label_ru": "Электромагнетизм",
        "short": "Attraction and friction",
        "short_ru": "Притяжение и борьба",
        "mechanics": "One holds one gate of the channel, the other holds the opposite gate. "
                     "The spark — strong attraction, and the pair's main point of conflict.",
        "mechanics_ru": "У одного одни ворота канала, у другого — противоположные. Это искра, "
                        "сильное притяжение и одновременно главная точка конфликтов.",
    },
    "compromise": {
        "label": "Compromise",
        "label_ru": "Компромисс",
        "short": "Pressure zone",
        "short_ru": "Зона давления",
        "mechanics": "One holds the whole channel, the other only one of its gates. The one "
                     "with the single gate always yields and gets conditioned, which "
                     "accumulates as resentment.",
        "mechanics_ru": "У одного канал определён целиком, у другого — только одни ворота. "
                        "Тот, у кого только ворота, всегда уступает и обуславливается, что "
                        "накапливается как обида.",
    },
    "dominance": {
        "label": "Dominance",
        "label_ru": "Доминанта",
        "short": "Teacher and student",
        "short_ru": "Учитель и ученик",
        "mechanics": "One holds the whole channel, the other holds neither gate. The owner "
                     "sets a fixed pattern; the other reflects and absorbs the quality.",
        "mechanics_ru": "У одного канал определён полностью, у другого пуст. Обладатель канала "
                        "задаёт фиксированный паттерн, второй отражает и перенимает качество.",
    },
    "companionship": {
        "label": "Companionship",
        "label_ru": "Партнёрство",
        "short": "Friendship",
        "short_ru": "Дружба",
        "mechanics": "Both hold the same channel in full. A zone of complete agreement — "
                     "nothing needs explaining between them here.",
        "mechanics_ru": "Один и тот же канал определён целиком у обоих. Зона полного согласия: "
                        "здесь им не нужно ничего объяснять друг другу.",
    },
}

#: Classes that create conditioning pressure and therefore role conflict.
CONDITIONING_TYPES = ("compromise", "dominance")


def maia_type(code: str) -> Dict[str, str]:
    return {"code": code, **MAIA_TYPES[code]}


# --------------------------------------------------------------------------- #
# 3. Genetic type of the union
# --------------------------------------------------------------------------- #
_AURA: Dict[Tuple[str, str], Dict[str, str]] = {
    ("Generator", "Generator"): {
        "label": "Energetic tandem",
        "label_ru": "Энергетический тандем",
        "task": "Both must move from their own sacral response rather than from each other's.",
        "task_ru": "Обоим важно двигаться из собственного сакрального отклика, а не из чужого.",
    },
    ("Generator", "Projector"): {
        "label": "Union of direction",
        "label_ru": "Союз направления",
        "task": "The projector is here to read and correctly steer the generator's sacral energy.",
        "task_ru": "Проектор призван считывать и корректно направлять сакральную энергию генератора.",
    },
    ("Generator", "Manifestor"): {
        "label": "Request and inform",
        "label_ru": "Запрос и информирование",
        "task": "The manifestor must inform before acting, or the generator's response has "
                "nothing to work with.",
        "task_ru": "Манифестору необходимо информировать до действия, иначе отклику генератора "
                   "не на что опереться.",
    },
    ("Generator", "Reflector"): {
        "label": "Sustainability and sampling",
        "label_ru": "Устойчивость и сэмплирование",
        "task": "The reflector samples the generator's energy; decisions need a lunar cycle.",
        "task_ru": "Рефлектор сэмплирует энергию генератора; решениям нужен лунный цикл.",
    },
    ("Generator", "Manifesting Generator"): {
        "label": "Mixed build-through cycle",
        "label_ru": "Смешанный цикл доведения",
        "task": "Same fuel, different pace — the MG skips steps the generator completes.",
        "task_ru": "Топливо одно, темп разный: MG пропускает шаги, которые генератор доводит.",
    },
    ("Manifesting Generator", "Manifesting Generator"): {
        "label": "High-velocity build-through",
        "label_ru": "Скоростное доведение",
        "task": "Two engines at speed; the shared risk is starting more than either finishes.",
        "task_ru": "Два скоростных двигателя; общий риск — начинать больше, чем удаётся завершить.",
    },
    ("Manifesting Generator", "Projector"): {
        "label": "Speed and efficiency",
        "label_ru": "Скорость и эффективность",
        "task": "The projector's guidance is what keeps the MG's speed from becoming waste.",
        "task_ru": "Направление проектора удерживает скорость MG от превращения в потери.",
    },
    ("Manifesting Generator", "Manifestor"): {
        "label": "Initiating velocity",
        "label_ru": "Инициирующая скорость",
        "task": "Two initiators; informing is the only thing that stops collision.",
        "task_ru": "Два инициатора; единственное, что предотвращает столкновение, — информирование.",
    },
    ("Manifesting Generator", "Reflector"): {
        "label": "Power and reflection",
        "label_ru": "Мощность и отражение",
        "task": "The reflector will mirror the MG's pace back — including its overload.",
        "task_ru": "Рефлектор отразит темп MG обратно — вместе с его перегрузом.",
    },
    ("Projector", "Projector"): {
        "label": "Mutual guidance",
        "label_ru": "Взаимное направление",
        "task": "Neither carries sustained energy; recognition has to come from outside the pair.",
        "task_ru": "Ни у кого нет устойчивой энергии; признание должно приходить извне пары.",
    },
    ("Manifestor", "Projector"): {
        "label": "Strategy and impact",
        "label_ru": "Стратегия и воздействие",
        "task": "The projector sees the system, the manifestor moves it — informing links the two.",
        "task_ru": "Проектор видит систему, манифестор её двигает; связывает их информирование.",
    },
    ("Projector", "Reflector"): {
        "label": "Guidance and sampling",
        "label_ru": "Направление и сэмплирование",
        "task": "Two non-energy beings; the environment decides more than either of them.",
        "task_ru": "Два неэнергетических типа; среда решает больше, чем каждый из них.",
    },
    ("Manifestor", "Manifestor"): {
        "label": "Impact and mutual informing",
        "label_ru": "Воздействие и взаимное информирование",
        "task": "Both initiate; without informing each other, every move reads as suppression.",
        "task_ru": "Оба инициируют; без взаимного информирования любой шаг читается как подавление.",
    },
    ("Manifestor", "Reflector"): {
        "label": "Inform and reflect",
        "label_ru": "Информирование и отражение",
        "task": "The reflector is the most exposed to an uninformed manifestor's impact.",
        "task_ru": "Рефлектор наиболее уязвим к воздействию неинформирующего манифестора.",
    },
    ("Reflector", "Reflector"): {
        "label": "Lunar harmony",
        "label_ru": "Лунная гармония",
        "task": "Both sample the field; the pair has almost no fixed identity of its own.",
        "task_ru": "Оба сэмплируют поле; у пары почти нет собственной фиксированной идентичности.",
    },
}


def aura_dynamic(type_a: Optional[str], type_b: Optional[str]) -> Dict[str, Any]:
    """Genetic type of the union. Order-independent."""
    a, b = (type_a or "Unknown"), (type_b or "Unknown")
    entry = _AURA.get(tuple(sorted((a, b))))
    if entry is None:
        return {
            "types": [a, b], "label": "Neutral dynamic", "label_ru": "Нейтральная динамика",
            "task": "Type data incomplete.", "task_ru": "Данных о типах недостаточно.",
        }
    return {"types": sorted((a, b)), **entry}


# --------------------------------------------------------------------------- #
# 4. Profile resonance
# --------------------------------------------------------------------------- #
_HARMONIC_LINES = {(1, 4), (4, 1), (2, 5), (5, 2), (3, 6), (6, 3)}


def _profile_lines(profile: Any) -> Optional[List[int]]:
    if isinstance(profile, (tuple, list)) and len(profile) == 2:
        try:
            return [int(profile[0]), int(profile[1])]
        except (TypeError, ValueError):
            return None
    if isinstance(profile, str):
        head = profile.split(":")[0].strip()
        parts = head.split("/")
        if len(parts) == 2:
            try:
                return [int(parts[0]), int(parts[1])]
            except ValueError:
                return None
    return None


def profile_resonance(profile_a: Any, profile_b: Any) -> Dict[str, Any]:
    la, lb = _profile_lines(profile_a), _profile_lines(profile_b)
    if not la or not lb:
        return {"code": "unknown", "label": "Unknown", "label_ru": "Неизвестно",
                "harmonic_pairs": [], "reading": "Profile data incomplete.",
                "reading_ru": "Данных о профилях недостаточно."}

    pairs = [[x, y] for x in la for y in lb if (x, y) in _HARMONIC_LINES]

    if la == lb:
        return {"code": "identity", "label": "Profile identity", "label_ru": "Идентичность профилей",
                "harmonic_pairs": pairs,
                "reading": "The same profile on both sides. Instant recognition, and the same "
                           "blind spot twice over.",
                "reading_ru": "Один и тот же профиль с обеих сторон. Мгновенное узнавание — и "
                              "одна и та же слепая зона в двойном размере."}
    if len(pairs) >= 2:
        return {"code": "deeply_harmonic", "label": "Deeply harmonic", "label_ru": "Глубоко гармоничные",
                "harmonic_pairs": pairs,
                "reading": "Both lines resonate. Profile glue — the pair holds together at the "
                           "level of life role, not only mechanics.",
                "reading_ru": "Резонируют обе линии. «Клей» профилей: пара держится на уровне "
                              "жизненной роли, а не только механики."}
    if len(pairs) == 1:
        return {"code": "harmonic", "label": "Harmonic resonance", "label_ru": "Гармоничный резонанс",
                "harmonic_pairs": pairs,
                "reading": "One resonant line pair. A working point of mutual recognition.",
                "reading_ru": "Одна резонансная пара линий. Рабочая точка взаимного узнавания."}
    return {"code": "neutral", "label": "Neutral partnership", "label_ru": "Нейтральное партнёрство",
            "harmonic_pairs": [],
            "reading": "No line resonance. The union rests on mechanics rather than on role.",
            "reading_ru": "Резонанса линий нет. Союз держится на механике, а не на роли."}


# --------------------------------------------------------------------------- #
# 5. Variable synergy — all four arrows
# --------------------------------------------------------------------------- #
#: arrow key -> (name, ru name, left type, right type, business framing)
ARROWS: Dict[str, Dict[str, str]] = {
    "top_left": {"name": "Digestion", "name_ru": "Питание", "left": "Active", "right": "Passive",
                 "domain": "how the body takes information in",
                 "domain_ru": "как тело принимает информацию"},
    "bottom_left": {"name": "Environment", "name_ru": "Среда", "left": "Observed", "right": "Observer",
                    "domain": "where the body needs to be",
                    "domain_ru": "где телу нужно находиться"},
    "top_right": {"name": "Motivation", "name_ru": "Мотивация", "left": "Strategic", "right": "Receptive",
                  "domain": "what drives the decision",
                  "domain_ru": "что движет решением"},
    "bottom_right": {"name": "Perspective", "name_ru": "Перспектива", "left": "Focused", "right": "Peripheral",
                     "domain": "how attention is aimed",
                     "domain_ru": "как направлено внимание"},
}

_ARROW_MATCH = {
    ("top_left", True): ("Shared intake rhythm",
                         "Общий ритм усвоения",
                         "Both digest the same way — meals, information and workload can run on "
                         "one schedule.",
                         "Оба усваивают одинаково: питание, информация и нагрузка могут идти по "
                         "одному графику."),
    ("top_left", False): ("Split intake rhythm",
                          "Разный ритм усвоения",
                          "Opposite digestion. Shared meals and shared reading pace will quietly "
                          "cost one of them.",
                          "Противоположное питание. Общая еда и общий темп чтения тихо обходятся "
                          "дорого одному из двоих."),
    ("bottom_left", True): ("Shared environment",
                            "Общая среда",
                            "The same kind of space works for both — one office, one home layout.",
                            "Обоим подходит один тип пространства — один офис, одна планировка."),
    ("bottom_left", False): ("Divergent environment",
                             "Расходящаяся среда",
                             "Opposite environment needs. The place that settles one unsettles "
                             "the other; separate workspaces are not a preference.",
                             "Противоположные требования к среде. Место, которое успокаивает "
                             "одного, выбивает второго; раздельные рабочие места — не каприз."),
    ("top_right", True): ("Symmetrical drive",
                          "Симметричная мотивация",
                          "The same motivation. Fast alignment on why, and the same blind spot "
                          "about it.",
                          "Одинаковая мотивация. Быстрое согласие в «зачем» — и общая слепая зона."),
    ("top_right", False): ("Polarised drive",
                           "Полярная мотивация",
                           "The architect and the artist: one supplies the plan, the other the "
                           "depth. The most productive of the four mismatches.",
                           "Архитектор и художник: один даёт план, другой — глубину. Самое "
                           "продуктивное из четырёх расхождений."),
    ("bottom_right", True): ("Shared perspective",
                             "Общая перспектива",
                             "Attention lands in the same place. Efficient, and prone to missing "
                             "the same thing.",
                             "Внимание падает в одну точку. Эффективно — и одинаково слепо."),
    ("bottom_right", False): ("Complementary perspective",
                              "Дополняющая перспектива",
                              "One narrows, the other scans. Good coverage if neither dismisses "
                              "the other's read.",
                              "Один сужает, другой сканирует. Хорошее покрытие, если каждый "
                              "принимает прочтение другого."),
}


def _arrow_value(variables: Optional[Dict[str, Any]], key: str) -> Optional[str]:
    if not isinstance(variables, dict):
        return None
    node = variables.get(key)
    if isinstance(node, dict):
        v = node.get("value")
        return v if v in ("left", "right") else None
    return None


def variable_synergy(vars_a: Optional[Dict[str, Any]],
                     vars_b: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare all four arrows, not Motivation alone."""
    arrows: List[Dict[str, Any]] = []
    matches = 0
    compared = 0

    for key, meta in ARROWS.items():
        va, vb = _arrow_value(vars_a, key), _arrow_value(vars_b, key)
        if va is None or vb is None:
            arrows.append({"arrow": key, "name": meta["name"], "name_ru": meta["name_ru"],
                           "a": va, "b": vb, "code": "unknown",
                           "label": "Unknown", "label_ru": "Неизвестно",
                           "reading": "Arrow data missing.", "reading_ru": "Данных по стрелке нет."})
            continue
        compared += 1
        same = va == vb
        matches += int(same)
        label, label_ru, reading, reading_ru = _ARROW_MATCH[(key, same)]
        arrows.append({
            "arrow": key, "name": meta["name"], "name_ru": meta["name_ru"],
            "domain": meta["domain"], "domain_ru": meta["domain_ru"],
            "a": va, "b": vb,
            "a_type": meta["left"] if va == "left" else meta["right"],
            "b_type": meta["left"] if vb == "left" else meta["right"],
            "code": "aligned" if same else "polarised",
            "label": label, "label_ru": label_ru,
            "reading": reading, "reading_ru": reading_ru,
        })

    if compared == 0:
        return {"alignment": {"code": "unknown", "label": "Unknown", "label_ru": "Неизвестно"},
                "matched_arrows": 0, "compared_arrows": 0, "arrows": arrows,
                "shorthand": None}

    if matches == compared:
        alignment = {"code": "mirrored", "label": "Mirrored cognition", "label_ru": "Зеркальная когнитивность",
                     "reading": "All arrows agree. Effortless daily logistics, identical blind spots.",
                     "reading_ru": "Все стрелки совпали. Быт складывается сам, слепые зоны общие."}
    elif matches == 0:
        alignment = {"code": "inverted", "label": "Inverted cognition", "label_ru": "Инвертированная когнитивность",
                     "reading": "No arrow agrees. Maximum complementarity and maximum friction in "
                                "everyday logistics — food, space, pace, focus.",
                     "reading_ru": "Ни одна стрелка не совпала. Максимальная взаимодополняемость "
                                   "и максимальное трение в быту — еда, пространство, темп, фокус."}
    elif matches >= compared / 2:
        alignment = {"code": "mostly_aligned", "label": "Mostly aligned", "label_ru": "Преимущественно совпадают",
                     "reading": "Majority of arrows agree; the mismatches are where the friction lives.",
                     "reading_ru": "Большинство стрелок совпадает; трение живёт в расхождениях."}
    else:
        alignment = {"code": "mostly_polarised", "label": "Mostly polarised", "label_ru": "Преимущественно расходятся",
                     "reading": "Most arrows differ. The pair covers more ground than either alone, "
                                "at the cost of a shared routine.",
                     "reading_ru": "Большинство стрелок расходится. Пара охватывает больше, чем "
                                   "каждый по отдельности, ценой общего распорядка."}

    return {
        "alignment": alignment,
        "matched_arrows": matches,
        "compared_arrows": compared,
        "shorthand": f"{matches}/{compared}",
        "arrows": arrows,
    }


# --------------------------------------------------------------------------- #
# 6. Sub-circuitry
# --------------------------------------------------------------------------- #
SUB_CIRCUIT: Dict[str, Dict[str, str]] = {
    "Knowledge":   {"group": "Individual", "label": "Individual — Knowing",   "label_ru": "Индивидуальный — Знание"},
    "Centre":      {"group": "Individual", "label": "Individual — Centering", "label_ru": "Индивидуальный — Центрирование"},
    "Realize":     {"group": "Collective", "label": "Collective — Logic",     "label_ru": "Коллективный — Логика"},
    "Sense":       {"group": "Collective", "label": "Collective — Abstract",  "label_ru": "Коллективный — Абстракция"},
    "Ego":         {"group": "Tribal",     "label": "Tribal — Ego",           "label_ru": "Племенной — Эго"},
    "Protect":     {"group": "Tribal",     "label": "Tribal — Defense",       "label_ru": "Племенной — Защита"},
    "Integration": {"group": "Integration","label": "Integration",            "label_ru": "Интеграция"},
}

CIRCUIT_GROUP_READING: Dict[str, Dict[str, str]] = {
    "Individual": {"label_ru": "Индивидуальный",
                   "reading": "Mutation and empowerment. The pair changes things; melancholy is "
                              "part of the price.",
                   "reading_ru": "Мутация и наделение силой. Пара меняет вещи; меланхолия — часть цены."},
    "Collective": {"label_ru": "Коллективный",
                   "reading": "Sharing. The bond is oriented outward — patterns, experiments, "
                              "the wider audience.",
                   "reading_ru": "Разделение. Связь развёрнута наружу: паттерны, эксперименты, "
                                 "широкая аудитория."},
    "Tribal":     {"label_ru": "Племенной",
                   "reading": "Support and bargain. Resources, agreements and loyalty are the "
                              "currency of this bond.",
                   "reading_ru": "Поддержка и сделка. Валюта этой связи — ресурсы, договорённости "
                                 "и лояльность."},
    "Integration":{"label_ru": "Интеграция",
                   "reading": "Self-preservation. Raw, immediate, about survival of the self "
                              "inside the union.",
                   "reading_ru": "Самосохранение. Сырое и мгновенное, про выживание себя внутри союза."},
}


def sub_circuit(channel_key: Tuple[int, int], circuit_typ: str) -> Dict[str, str]:
    entry = SUB_CIRCUIT.get(circuit_typ, {"group": "Unknown", "label": circuit_typ,
                                          "label_ru": circuit_typ})
    return {"code": circuit_typ, **entry}


# --------------------------------------------------------------------------- #
# 7. Nodal / environmental resonance
# --------------------------------------------------------------------------- #
def node_resonance(nodes_a: Any, nodes_b: Any, channel_lookup) -> Dict[str, Any]:
    """`channel_lookup(g1, g2)` returns the channel key if the two gates form one."""
    sa, sb = set(nodes_a or ()), set(nodes_b or ())
    common = sorted(sa & sb)
    if common:
        return {
            "code": "shared_frequency", "label": "Shared frequency", "label_ru": "Общая частота",
            "gates": common, "channel": None,
            "operational": f"The same environmental themes trigger both (gates {common}). "
                           f"Shared industry or niche.",
            "operational_ru": f"Обоих запускают одни и те же темы среды (ворота {common}). "
                              f"Общая индустрия или ниша.",
            "lifestyle": "Shared social frequency — the same people and the same places.",
            "lifestyle_ru": "Общая социальная частота — одни и те же люди и места.",
        }
    for g1 in sorted(sa):
        for g2 in sorted(sb):
            key = channel_lookup(g1, g2)
            if key:
                return {
                    "code": "harmonic_pull", "label": "Harmonic pull", "label_ru": "Гармоническое притяжение",
                    "gates": sorted([g1, g2]), "channel": list(key),
                    "operational": "The nodes bridge into a channel: together they close each "
                                   "other's environmental gap.",
                    "operational_ru": "Узлы смыкаются в канал: вместе они закрывают друг другу "
                                      "провал по среде.",
                    "lifestyle": "The environments pull toward each other rather than compete.",
                    "lifestyle_ru": "Среды тянутся друг к другу, а не конкурируют.",
                }
    return {
        "code": "individual_path", "label": "Individual path", "label_ru": "Индивидуальный путь",
        "gates": [], "channel": None,
        "operational": "Separate environmental trajectories. Career direction stays personal.",
        "operational_ru": "Раздельные траектории по среде. Карьерное направление остаётся личным.",
        "lifestyle": "No environmental overlap — healthy independence in social circles.",
        "lifestyle_ru": "Пересечения по среде нет — здоровая независимость в социальных кругах.",
    }


# --------------------------------------------------------------------------- #
# 8. Centre conditioning
# --------------------------------------------------------------------------- #
CENTRE_DYNAMIC: Dict[str, Dict[str, str]] = {
    "fixed":        {"label": "Fixed in both",   "label_ru": "Фиксирован у обоих"},
    "conditions_a": {"label": "A conditions B",  "label_ru": "A обуславливает B"},
    "conditions_b": {"label": "B conditions A",  "label_ru": "B обуславливает A"},
    "open":         {"label": "Open in both",    "label_ru": "Открыт у обоих"},
}

#: G-centre and sacral gates that carry the theme of love and direction.
LOVE_GATES = (10, 15, 25, 46, 5, 2, 29)
