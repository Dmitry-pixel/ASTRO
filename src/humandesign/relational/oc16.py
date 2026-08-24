"""OC16 — the functional layer of the WA.

The WA is built on the whole bodygraph, but it *operates* through sixteen gates:
six channels that carry twelve of them, plus four bridging gates. The six
channels are the departments a large organisation needs to survive; the four
bridges are the connective tissue that binds separate Pentas into one field.

Two facts worth keeping in view, both checked against `hd_constants` rather than
assumed:

1. The four bridging gates — 1, 8, 7, 31 — are exactly the gates of the two
   **upper Penta** channels, `8-1` Implementation and `31-7` Planning. The
   doctrine says the WA binds Pentas together; mechanically, the binding is the
   upper Penta itself.
2. `31-7` is named "The Alpha" in the engine's own channel table. The Alpha is
   not an added concept — it is the channel the bridging gates form.

Data only in the tables below; the analysis functions read them and never
hard-code a gate number.
"""
from typing import Any, Dict, List, Tuple

from .. import hd_constants

# --------------------------------------------------------------------------- #
# The six departments
# --------------------------------------------------------------------------- #
DEPARTMENTS: Tuple[Dict[str, Any], ...] = (
    {
        "code": "management",
        "key": "21-45",
        "channel": (45, 21),
        "label": "Management & Finance",
        "label_ru": "Управление и Финансы",
        "channel_name_ru": "Материальный канал",
        "function_ru": "Жизнеобеспечение, иерархия и капитал.",
        "gap_ru": "Департамент не образован: у организации нет ни операционного "
                  "контроля, ни распоряжения активами — иерархия и капитал "
                  "остаются без механики.",
        "gates": {
            21: {"name_ru": "Контроль / Охотник",
                 "process_ru": "Операционный контроль, жёсткое администрирование, "
                               "управление кадрами, распределение ежедневных "
                               "обязанностей, надзор за исполнением контрактов."},
            45: {"name_ru": "Владение / Король",
                 "process_ru": "Стратегическое распределение бюджета, владение "
                               "активами, защита интеллектуальной и материальной "
                               "собственности, надзор за налогами и инвестициями."},
        },
    },
    {
        "code": "competitiveness",
        "key": "25-51",
        "channel": (25, 51),
        "label": "Competitiveness & Marketing",
        "label_ru": "Конкуренция и Маркетинг",
        "channel_name_ru": "Канал Инициации",
        "function_ru": "Выживание компании в агрессивной рыночной среде.",
        "gap_ru": "Департамент не образован: компания будет постоянно проигрывать "
                  "конкурентам из-за отсутствия маркетинговой агрессии.",
        "gates": {
            25: {"name_ru": "Принятие / Невинность",
                 "process_ru": "Корпоративная этика, миссия бренда, удержание духа "
                               "компании в кризис, чистая репутация."},
            51: {"name_ru": "Шок / Инициация",
                 "process_ru": "Агрессивный маркетинг, конкурентная борьба, прорывы, "
                               "выход на новые рынки раньше соперников."},
        },
    },
    {
        "code": "direction",
        "key": "2-14",
        "channel": (2, 14),
        "label": "Direction & Resources",
        "label_ru": "Направление и Ресурсы",
        "channel_name_ru": "Канал Хранителя Ключей",
        "function_ru": "Вектор движения бизнеса и его топливо.",
        "gap_ru": "Департамент не образован: у бизнеса нет ни навигации, ни "
                  "материального потока, питающего остальные блоки.",
        "gates": {
            2: {"name_ru": "Направление / Высшее Знание",
                "process_ru": "Логистика, долгосрочное планирование, навигация "
                              "бизнеса, выбор того, куда вкладываются время и силы."},
            14: {"name_ru": "Силовые ресурсы / Обладание в великой мере",
                 "process_ru": "Финансовое и энергетическое топливо организации, "
                               "генерация материального потока, бесперебойная работа "
                               "Пента-блоков."},
        },
    },
    {
        "code": "logical_enforcement",
        "key": "27-50",
        "channel": (50, 27),
        "label": "Laws & Stability",
        "label_ru": "Законы и Стабильность",
        "channel_name_ru": "Канал Сохранения",
        "function_ru": "Безопасность и внутренние правила.",
        "gap_ru": "Департамент не образован: нет ни поддержки сотрудников, ни "
                  "правил — ни удержания кадров, ни комплаенса.",
        "gates": {
            27: {"name_ru": "Забота / Питание",
                 "process_ru": "Социальный пакет, условия труда, тимбилдинг, "
                               "удержание ценных кадров поддержкой внутри коллектива."},
            50: {"name_ru": "Ценности / Законодатель",
                 "process_ru": "Юридический отдел, комплаенс, должностные инструкции, "
                               "системы штрафов и поощрений, контроль качества."},
        },
    },
    {
        "code": "interaction",
        "key": "6-59",
        "channel": (59, 6),
        "label": "Communication & HR",
        "label_ru": "Коммуникация и HR",
        "channel_name_ru": "Канал Интимности",
        "function_ru": "Связи и воспроизводство организации.",
        "gap_ru": "Департамент не образован: организация не нанимает, не заключает "
                  "партнёрств и не умеет разводить конфликты.",
        "gates": {
            59: {"name_ru": "Близость / Сексуальность",
                 "process_ru": "Наём персонала, партнёрские соглашения, привлечение "
                               "клиентов, способность размножать филиалы и франшизы."},
            6: {"name_ru": "Трение / Конфликт",
                "process_ru": "Медиация, урегулирование споров, барьеры и фильтры — "
                              "кому открывать доступ к информации, а кого изолировать."},
        },
    },
    {
        "code": "innovation",
        "key": "3-60",
        "channel": (3, 60),
        "label": "Innovation & Production",
        "label_ru": "Инновации и Производство",
        "channel_name_ru": "Канал Мутации",
        "function_ru": "Развитие и модернизация.",
        "gap_ru": "Департамент не образован: ни внедрения нового, ни удержания "
                  "рисков — организация не меняется и не сдерживает изменения.",
        "gates": {
            3: {"name_ru": "Упорядочивание / Начальные трудности",
                "process_ru": "Внедрение инноваций, адаптация технологий, "
                              "реструктуризация хаотичных процессов в систему."},
            60: {"name_ru": "Ограничение / Принятие",
                 "process_ru": "Работа с жёсткими дедлайнами, бюджетирование в "
                               "дефиците, консервативное сдерживание рисков."},
        },
    },
)

# --------------------------------------------------------------------------- #
# The four bridging gates
# --------------------------------------------------------------------------- #
BRIDGE_GATES: Dict[int, Dict[str, str]] = {
    1: {"name_ru": "Самовыражение / Творчество",
        "process_ru": "УТП, дизайн продукта, брендинг, эстетическое позиционирование "
                      "на рынке."},
    8: {"name_ru": "Вклад / Содействие",
        "process_ru": "PR и реклама, презентация успехов широкой публике, привлечение "
                      "инвесторов."},
    7: {"name_ru": "Роль Я / Армия",
        "process_ru": "Иерархическая субординация: кто кому подчиняется, распределение "
                      "статусов должностей."},
    31: {"name_ru": "Влияние / Лидерство",
         "process_ru": "Голос компании: публичные манифесты, официальные заявления "
                       "руководства, способность вести за собой массы."},
}

BRIDGE_NOTE_RU = (
    "Четыре связующих активации не образуют департаментов OC16 — они работают как "
    "клей между Пентами. Механически это ровно ворота двух каналов верхней Пенты: "
    "8-1 Implementation и 31-7 Planning."
)

# --------------------------------------------------------------------------- #
# Alpha
# --------------------------------------------------------------------------- #
ALPHA_CHANNEL: Tuple[int, int] = (31, 7)
_MATERIAL_CHANNEL: Tuple[int, int] = (45, 21)
_INSPIRATION_CHANNEL: Tuple[int, int] = (8, 1)
_ALPHA_TYPES = ("Projector", "Manifestor")
_ENTHUSIASM_GATE = 16

ALPHA_NOTE_RU = (
    "Канал 31-7 проецируемый: доктрина требует, чтобы коллектив сам признал и выбрал "
    "Альфу. Поэтому здесь перечислены кандидаты с их активациями, а не назначенный "
    "лидер. Ворота 16 не входят в OC16 и учтены отдельно, как контекст."
)

PROFILE_NOTE_RU = (
    "Профиль не определяет, может ли человек быть Альфой — Альфой может быть любой "
    "профиль. Он определяет стиль руководства и то, как большая система его считывает. "
    "Поэтому профиль не участвует в ранжировании и вынесен в отдельный блок `style`. "
    "Мнение, что подходят только 5/1 и 5/2, — распространённое заблуждение."
)

PRIORITY_NOTE_RU = (
    "Порядок важности для удержания позиции: канал 31-7, затем сила Эго-центра "
    "(канал 21-45 — контроль ресурсов), затем корректное проживание своего Типа и "
    "Авторитета. Последнее — поведение, а не активация: API отдаёт Тип и Авторитет, "
    "но судить о том, живёт ли человек по ним, из карты нельзя."
)

#: Style of leadership by profile line — not eligibility.
PROFILE_LINE_STYLES: Dict[int, Dict[str, str]] = {
    1: {"code": "expertise", "label_ru": "Авторитет через экспертность",
        "note_ru": "Руководит на основе глубоких проверенных знаний. Система "
                   "подчиняется, потому что он лучше всех знает матчасть, скрытые "
                   "риски и фундамент бизнеса."},
    2: {"code": "called", "label_ru": "Избранный лидер",
        "note_ru": "Его замечают и вызывают на роль за природный, часто "
                   "неосознаваемый талант. Эффективен, пока занят своим делом и не "
                   "увязает в микроменеджменте."},
    3: {"code": "practitioner", "label_ru": "Лидер-практик",
        "note_ru": "Руководит на основе личных ошибок и антикризисных кейсов. "
                   "Система уважает его за стрессоустойчивость и гибкость."},
    4: {"code": "network", "label_ru": "Влияние через связи",
        "note_ru": "Строит руководство на нетворкинге, лояльности и доверии. "
                   "Расставляет своих надёжных людей на ключевые узлы структуры."},
    5: {"code": "crisis", "label_ru": "Лидерский магнетизм кризис-менеджера",
        "note_ru": "На него автоматически ложится проекция «знает, что делать, и "
                   "спасёт нас». Обратная сторона: если практического решения нет, "
                   "поле мгновенно сжигает репутацию и низвергает с позиции."},
    6: {"code": "role_model", "label_ru": "Ролевая модель",
        "note_ru": "Руководит с позиции объективного наблюдателя — в полной мере "
                   "примерно после 50 лет. Не борется за власть; система подчиняется "
                   "целостности и стратегическому видению сверху."},
}

_TIERS = {
    "canonical": "Канал 31-7 «Альфа» определён целиком.",
    "partial": "Определены не оба конца канала 31-7.",
    "supporting": "Канала 31-7 нет; есть только вспомогательные активации.",
    "none": "Признаков Альфы не найдено.",
}

# --------------------------------------------------------------------------- #
OC16_GATES: Tuple[int, ...] = tuple(sorted(
    set(BRIDGE_GATES) | {g for d in DEPARTMENTS for g in d["gates"]}
))

# Fail loudly at import if a table drifts away from the engine's own constants.
assert len(OC16_GATES) == 16, f"OC16 must carry 16 gates, got {len(OC16_GATES)}"
for _d in DEPARTMENTS:
    assert _d["channel"] in hd_constants.CHANNEL_MEANING_DICT, \
        f"{_d['key']} is not a channel in CHANNEL_MEANING_DICT"
    assert set(_d["channel"]) == set(_d["gates"]), \
        f"{_d['key']} gate table does not match its channel"
assert ALPHA_CHANNEL in hd_constants.CHANNEL_MEANING_DICT


# --------------------------------------------------------------------------- #
def _holders(people, gate: int) -> List[str]:
    return sorted(n for n, p in people.items() if gate in p.gates)


def analyse(people: Dict[str, Any], verbosity: str = "standard") -> Dict[str, Any]:
    """The OC16 layer for a group that forms a WA."""
    names = list(people)
    union = set()
    for p in people.values():
        union |= p.gates

    departments = []
    for d in DEPARTMENTS:
        g1, g2 = d["channel"]
        defined = g1 in union and g2 in union
        gates_block = {}
        for gate in sorted(d["gates"]):
            who = _holders(people, gate)
            gates_block[str(gate)] = {
                "name_ru": d["gates"][gate]["name_ru"],
                "process_ru": d["gates"][gate]["process_ru"],
                "held_by": who,
                "sole_holder": who[0] if len(who) == 1 else None,
            }
        entry = {
            "code": d["code"],
            "key": d["key"],
            "label": d["label"],
            "label_ru": d["label_ru"],
            "channel_name_ru": d["channel_name_ru"],
            "function_ru": d["function_ru"],
            "status": "defined" if defined else "missing",
            "gates": gates_block,
            "missing_gates": [] if defined else [g for g in d["channel"] if g not in union],
            "whole_channel_holders": sorted(
                n for n, p in people.items() if d["channel"] in p.channels),
        }
        if not defined:
            entry["gap_ru"] = d["gap_ru"]
        departments.append(entry)

    bridges = {}
    for gate in sorted(BRIDGE_GATES):
        who = _holders(people, gate)
        bridges[str(gate)] = {
            "name_ru": BRIDGE_GATES[gate]["name_ru"],
            "process_ru": BRIDGE_GATES[gate]["process_ru"],
            "held_by": who,
            "sole_holder": who[0] if len(who) == 1 else None,
        }

    defined_departments = [d for d in departments if d["status"] == "defined"]
    gates_defined = sorted(g for g in OC16_GATES if g in union)

    return {
        "structure": {
            "gates": len(OC16_GATES),
            "gate_numbers": list(OC16_GATES),
            "channels": len(DEPARTMENTS),
            "bridge_gates": sorted(BRIDGE_GATES),
            "note_ru": "WA строится на полном бодиграфе, но оперирует через OC16: "
                       "шесть каналов (12 ворот) плюс четыре связующих ворот.",
            "bridge_note_ru": BRIDGE_NOTE_RU,
        },
        "coverage": {
            "departments_defined": len(defined_departments),
            "departments_total": len(DEPARTMENTS),
            "departments_share_pct": round(100 * len(defined_departments) / len(DEPARTMENTS)),
            "gates_defined": len(gates_defined),
            "gates_total": len(OC16_GATES),
            "gates_missing": [g for g in OC16_GATES if g not in union],
        },
        "departments": departments,
        "bridge_gates": bridges,
        "alpha": alpha_candidates(people, verbosity),
    }


def alpha_candidates(people: Dict[str, Any], verbosity: str = "standard") -> Dict[str, Any]:
    """Rank participants by the activations the doctrine names for an Alpha.

    Ranking uses mechanical markers only, in the order the doctrine gives them:
    the channel 31-7, then Ego-centre strength (21-45 and gate 45), then 1-8.
    Profile, Type and gate 16 describe *how* someone would lead and how the field
    reads them; they never move a candidate up the list. Any profile can hold the
    position.

    Reports evidence, never a verdict: 31-7 is a projected channel, so the
    doctrine requires the collective to recognise the Alpha rather than a chart
    to appoint one.
    """
    tier_rank = {"canonical": 0, "partial": 1, "supporting": 2, "none": 3}
    rows = []
    for name, p in people.items():
        ev: List[Dict[str, str]] = []

        has_channel = ALPHA_CHANNEL in p.channels
        if has_channel:
            ev.append({"code": "channel_31_7", "weight": "decisive",
                       "label_ru": "Канал 31-7 «Альфа» — голос и направление руководства"})
        else:
            if 31 in p.gates:
                ev.append({"code": "gate_31", "weight": "partial",
                           "label_ru": "Ворота 31 — голос лидера"})
            if 7 in p.gates:
                ev.append({"code": "gate_7", "weight": "partial",
                           "label_ru": "Ворота 7 — роль и стиль управления"})

        if _MATERIAL_CHANNEL in p.channels:
            ev.append({"code": "channel_21_45", "weight": "strong",
                       "label_ru": "Канал 21-45 — Эго-центр: контроль бюджетов и иерархии"})
        elif 45 in p.gates:
            ev.append({"code": "gate_45", "weight": "supporting",
                       "label_ru": "Ворота 45 «Король» — владение ресурсом"})
        if _INSPIRATION_CHANNEL in p.channels:
            ev.append({"code": "channel_1_8", "weight": "supporting",
                       "label_ru": "Канал 1-8 — творческий ролевой пример"})

        if has_channel:
            tier = "canonical"
        elif 31 in p.gates or 7 in p.gates:
            tier = "partial"
        elif ev:
            tier = "supporting"
        else:
            tier = "none"

        lines = list(p.summary.get("profile_lines") or [])
        style = [dict(PROFILE_LINE_STYLES[ln], line=ln) for ln in lines
                 if ln in PROFILE_LINE_STYLES]

        context: List[Dict[str, str]] = []
        etype = p.summary.get("energy_type")
        if etype in _ALPHA_TYPES:
            context.append({"code": "type_directs", "label_ru":
                            f"Тип {etype} видит и направляет чужую энергию, находясь над ней."})
        elif etype:
            context.append({"code": "type_responds", "label_ru":
                            f"Тип {etype}: руководить может, но из отклика — иначе "
                            f"администрирование истощает."})
        if _ENTHUSIASM_GATE in p.gates:
            context.append({"code": "gate_16", "label_ru":
                            "Ворота 16 — энтузиазм: помогает зажигать Пенты. Вне OC16."})

        rows.append({
            "name": name,
            "tier": tier,
            "tier_ru": _TIERS[tier],
            "evidence_count": len(ev),
            "evidence": ev,
            "energy_type": etype,
            "inner_authority": p.summary.get("inner_authority"),
            "profile": p.summary.get("profile"),
            "profile_lines": lines,
            "style": style,
            "context": context,
        })

    rows.sort(key=lambda r: (tier_rank[r["tier"]], -r["evidence_count"], r["name"]))
    if verbosity == "compact":
        rows = [r for r in rows if r["tier"] != "none"][:3]

    canonical = [r["name"] for r in rows if r["tier"] == "canonical"]
    return {
        "channel": list(ALPHA_CHANNEL),
        "channel_key": "31-7",
        "note_ru": ALPHA_NOTE_RU,
        "profile_note_ru": PROFILE_NOTE_RU,
        "priority_note_ru": PRIORITY_NOTE_RU,
        "ranked_by": ["channel_31_7", "channel_21_45", "gate_45", "channel_1_8"],
        "not_ranked_by": ["profile", "energy_type", "gate_16"],
        "canonical_holders": canonical,
        "reading_ru": _alpha_reading(canonical, rows),
        "candidates": rows,
    }


def _alpha_reading(canonical: List[str], rows: List[Dict[str, Any]]) -> str:
    if len(canonical) == 1:
        return (f"Канал 31-7 целиком определён у одного участника — {canonical[0]}. "
                f"Механически это единственный кандидат в Альфу; признание "
                f"коллективом остаётся условием, а не следствием.")
    if len(canonical) > 1:
        return (f"Канал 31-7 определён у {len(canonical)} участников: "
                f"{', '.join(canonical)}. Механика не выбирает между ними — "
                f"выбор делает коллектив, и конкуренция за позицию здесь заложена "
                f"в структуре.")
    partial = [r["name"] for r in rows if r["tier"] == "partial"]
    if partial:
        return (f"Канала 31-7 нет ни у кого целиком. Половину держат: "
                f"{', '.join(partial)} — позиция Альфы не закрыта, и поле будет "
                f"собирать её из двух человек.")
    return ("Ни канала 31-7, ни его ворот в группе нет. Позиция Альфы не обеспечена "
            "механически: WA останется без единого центра трансляции.")
