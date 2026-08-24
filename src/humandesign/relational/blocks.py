"""How a WA falls apart into Penta blocks.

The doctrine: a WA does not divide people by type or by personal chemistry. The
aura of a large group seeks the most stable cell it knows — a Penta of three to
five — so it settles into blocks, and the Alpha is pushed out above them.

What decides the grouping is **function**: the twelve business gates of the Penta,
grouped into three zones. A block that covers all three zones can plan, can show
its work, and has the energy to finish it. A block missing a zone does not fail
loudly; it just underperforms in a way nobody traces back to the composition —
which is exactly what this module is for.

Two things this module deliberately does not do:

- It does not group by electromagnetic attraction. The doctrine is explicit that
  the WA overwrites personal chemistry, so channels between people are not part
  of the objective.
- It does not name the head of a block or assemble the Управляющая Пента. That
  is a role, not an activation; no rule for deriving it from a chart was given,
  and inventing one would be worse than leaving the block out.
"""
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import hd_constants

# --------------------------------------------------------------------------- #
# The twelve functional gates, in three zones
# --------------------------------------------------------------------------- #
# Gate 13 sits in zone 2 with its own channel partner 33. The doctrine's zone
# table placed gate 42 here, which was a slip for 13; 13 is neither Sacral nor
# Spleen, so zone 3 was not available to it. Zone 2 already carries both ends of
# 8-1, and CHANNEL_MEANING_DICT describes a missing 33-13 as poor customer
# relations and lost memory — outward-facing, which is what zone 2 is. Moving it
# is a one-line change if the product owner decides otherwise.
ZONES: Tuple[Dict[str, Any], ...] = (
    {
        "code": "direction",
        "label": "Planning & Direction",
        "label_ru": "Планирование и Направление",
        "centre_ru": "Джи-центр",
        "function_ru": "Куда движется группа, какова её культура и как распределяются роли.",
        "gap_ru": "Блок не знает, куда идёт: некому задать вектор, ритм и роли.",
        "gates": {
            7:  {"name_ru": "Общественная роль / Администратор",
                 "process_ru": "Управление, иерархия и субординация внутри блока, "
                               "назначение должностей, контроль дисциплины."},
            15: {"name_ru": "Культура / Поведение",
                 "process_ru": "Корпоративная культура, тайм-менеджмент, адаптация к "
                               "изменениям, общий ритм работы."},
            46: {"name_ru": "Координация / Интеграция",
                 "process_ru": "Физическое пространство, координация усилий, удержание "
                               "людей вместе, быть в правильном месте в правильное время."},
            2:  {"name_ru": "Ориентация / Навигация",
                 "process_ru": "Видение материального потенциала, понимание рынка, "
                               "стратегический вектор блока."},
        },
    },
    {
        "code": "demonstration",
        "label": "Demonstration & Sales",
        "label_ru": "Демонстрация и Продажи",
        "centre_ru": "Горловой центр",
        "function_ru": "Манифестация результатов блока во внешний мир и внутренние "
                       "коммуникации.",
        "gap_ru": "Блок может отлично производить, но об этом никто не узнает — "
                  "включая Альфу. Процесс буксует на презентации.",
        "gates": {
            31: {"name_ru": "Лидерство / Общественное признание",
                 "process_ru": "Направление коллектива через инструкции, презентация "
                               "проектов, голос отдела перед Альфа-лидером."},
            8:  {"name_ru": "Продвижение / PR",
                 "process_ru": "Маркетинг, реклама, привлечение внимания к продукту "
                               "блока, умение продать результат своей работы."},
            33: {"name_ru": "Анализ / Опыт",
                 "process_ru": "Архивация, отчётность, подведение итогов, извлечение "
                               "уроков из прошлых ошибок."},
            13: {"name_ru": "Координация вовне / Слушатель",
                 "process_ru": "Отношения с клиентами и партнёрами, сбор и удержание "
                               "информации, память блока о договорённостях."},
            1:  {"name_ru": "Визуализация / Творчество",
                 "process_ru": "Дизайн, уникальный стиль, новые концепты, "
                               "инновационный подход к задачам."},
        },
    },
    {
        "code": "production",
        "label": "Production & Reliability",
        "label_ru": "Производство и Надёжность",
        "centre_ru": "Сакральный центр",
        "function_ru": "Энергетический мотор и система безопасности блока.",
        "gap_ru": "У блока будет много идей и планов, но не будет сил и ресурсов "
                  "довести дело до конца.",
        "gates": {
            14: {"name_ru": "Ресурсы / Материальное обеспечение",
                 "process_ru": "Финансирование, распределение бюджетов внутри блока, "
                               "материальная база и инструменты."},
            29: {"name_ru": "Обязательства / Упорство",
                 "process_ru": "Работоспособность, готовность вкладывать силы, "
                               "доведение задач до конца."},
            5:  {"name_ru": "Стабильность / Шаблоны",
                 "process_ru": "Надёжность, рутинные процессы, автоматизация, "
                               "стабильный поток производства."},
        },
    },
)

ZONE_OF_GATE: Dict[int, str] = {
    g: z["code"] for z in ZONES for g in z["gates"]
}
FUNCTIONAL_GATES: Tuple[int, ...] = tuple(sorted(ZONE_OF_GATE))

BLOCK_MIN, BLOCK_MAX = 3, 5

# The twelve gates are the Penta's own; the zones are a different cut of them,
# not a different set. Fail at import if that ever stops being true.
assert set(FUNCTIONAL_GATES) == set(hd_constants.PENTA_GATES), (
    f"functional zones cover {sorted(FUNCTIONAL_GATES)}, "
    f"PENTA_GATES is {sorted(hd_constants.PENTA_GATES)}"
)
assert len(FUNCTIONAL_GATES) == 12


# --------------------------------------------------------------------------- #
def _coverage(members: Sequence[str], people: Dict[str, Any]) -> Dict[str, Any]:
    gates = set()
    for n in members:
        gates |= people[n].gates & set(FUNCTIONAL_GATES)
    zones = {z["code"] for g in gates for z in ZONES if g in z["gates"]}
    return {"gates": sorted(gates), "zones": zones}


def _score(blocks: List[List[str]], people: Dict[str, Any]) -> Tuple[int, int, int]:
    """Higher is better. Zone completeness first, then gates covered, then balance.

    Zone completeness dominates because the doctrine says a block missing a zone
    is the thing that makes a WA sag — not a block that merely covers fewer gates.
    """
    complete = 0
    gates = 0
    for b in blocks:
        cov = _coverage(b, people)
        gates += len(cov["gates"])
        if len(cov["zones"]) == len(ZONES):
            complete += 1
    spread = -(max(len(b) for b in blocks) - min(len(b) for b in blocks)) if blocks else 0
    return (complete, gates, spread)


def _sizes(n: int) -> Optional[List[int]]:
    """Block sizes for n people: as few blocks as possible, as even as possible."""
    if n < BLOCK_MIN:
        return None
    for k in range(-(-n // BLOCK_MAX), n // BLOCK_MIN + 1):
        if k * BLOCK_MIN <= n <= k * BLOCK_MAX:
            base, extra = divmod(n, k)
            return [base + 1] * extra + [base] * (k - extra)
    return None


def _partition(names: List[str], people: Dict[str, Any],
               sizes: List[int]) -> List[List[str]]:
    """Deterministic greedy seed, then pairwise local improvement to a fixpoint.

    Exhaustive search is out — the number of partitions of eleven people is in
    the hundreds of thousands and grows past any useful group size. Greedy plus
    swap-until-stable lands on the same answer for the same input, which matters
    more here than optimality: a consultant must be able to re-run a group and
    get the same blocks.
    """
    order = sorted(names)
    blocks: List[List[str]] = [[] for _ in sizes]

    # seed: one person per block, most functional gates first
    seeds = sorted(order, key=lambda n: (-len(people[n].gates & set(FUNCTIONAL_GATES)), n))
    for i, n in enumerate(seeds[:len(sizes)]):
        blocks[i].append(n)
    placed = set(seeds[:len(sizes)])

    for n in order:
        if n in placed:
            continue
        best, best_key = None, None
        for i, b in enumerate(blocks):
            if len(b) >= sizes[i]:
                continue
            cov = _coverage(b + [n], people)
            key = (len(cov["zones"]), len(cov["gates"]), -i)
            if best_key is None or key > best_key:
                best, best_key = i, key
        blocks[best].append(n)
        placed.add(n)

    # local improvement: swap two members between blocks while the score rises.
    # The first improving swap is taken and the scan restarts, so the result does
    # not depend on how far a stale scan had got.
    for _ in range(256):
        current = _score(blocks, people)
        swap = None
        for i in range(len(blocks)):
            for j in range(i + 1, len(blocks)):
                for a in sorted(blocks[i]):
                    for b in sorted(blocks[j]):
                        trial = [list(x) for x in blocks]
                        trial[i][trial[i].index(a)] = b
                        trial[j][trial[j].index(b)] = a
                        if _score(trial, people) > current:
                            swap = (i, j, a, b)
                            break
                    if swap:
                        break
                if swap:
                    break
            if swap:
                break
        if not swap:
            break
        i, j, a, b = swap
        blocks[i][blocks[i].index(a)] = b
        blocks[j][blocks[j].index(b)] = a

    return [sorted(x) for x in sorted(blocks, key=sorted)]


# --------------------------------------------------------------------------- #
def analyse(people: Dict[str, Any], alpha: Optional[Dict[str, Any]] = None,
            verbosity: str = "standard") -> Dict[str, Any]:
    """Split a WA into Penta blocks by functional coverage."""
    names = sorted(people)

    alpha_name: Optional[str] = None
    alpha_note = ("Альфа не выделен: канал 31-7 целиком не определён ни у кого "
                  "либо определён у нескольких. Разбиение сделано по всем участникам.")
    if alpha:
        holders = alpha.get("canonical_holders") or []
        if len(holders) == 1:
            alpha_name = holders[0]
            alpha_note = (f"{alpha_name} вынесен из блоков: механика WA держит Альфу "
                          f"вне Пент, на аурической дистанции.")

    pool = [n for n in names if n != alpha_name]
    sizes = _sizes(len(pool))
    if sizes is None:
        return {
            "alpha": alpha_name,
            "alpha_note_ru": alpha_note,
            "blocks": [],
            "note_ru": f"Из {len(pool)} человек нельзя собрать блоки по "
                       f"{BLOCK_MIN}–{BLOCK_MAX}.",
            "zones": _zone_reference(),
        }

    raw = _partition(pool, people, sizes)

    blocks = []
    for idx, members in enumerate(raw, 1):
        cov = _coverage(members, people)
        held = {g: sorted(n for n in members if g in people[n].gates)
                for g in FUNCTIONAL_GATES}
        zone_rows = []
        for z in ZONES:
            zg = [g for g in z["gates"] if g in cov["gates"]]
            row = {
                "code": z["code"], "label_ru": z["label_ru"],
                "covered_gates": zg,
                "missing_gates": [g for g in z["gates"] if g not in cov["gates"]],
                "status": "covered" if zg else "gap",
            }
            if not zg:
                row["gap_ru"] = z["gap_ru"]
            zone_rows.append(row)

        blocks.append({
            "index": idx,
            "members": members,
            "size": len(members),
            "entity": "penta" if BLOCK_MIN <= len(members) <= 5 else "block",
            "zones": zone_rows,
            "zones_covered": len(cov["zones"]),
            "gates_covered": cov["gates"],
            "gates_missing": [g for g in FUNCTIONAL_GATES if g not in cov["gates"]],
            "viable": len(cov["zones"]) == len(ZONES),
            "gate_holders": {str(g): v for g, v in held.items() if v} if verbosity != "compact" else None,
            "type_mix": _type_mix(members, people),
        })

    viable = [b for b in blocks if b["viable"]]
    return {
        "alpha": alpha_name,
        "alpha_note_ru": alpha_note,
        "block_count": len(blocks),
        "viable_blocks": len(viable),
        "blocks": blocks,
        "reading_ru": _reading(blocks, alpha_name),
        "method_ru": ("Блоки собраны по покрытию двенадцати функциональных ворот Пенты: "
                      "система тасует людей так, чтобы в каждом блоке были ворота из всех "
                      "трёх зон. Личная химия каналов в расчёт не берётся — доктрина "
                      "прямо говорит, что WA её стирает."),
        "not_computed_ru": ("Управляющая Пента и главы блоков не вычисляются: это роли, "
                            "а не активации, и правила их вывода из карты нет."),
        "zones": _zone_reference(),
    }


def _type_mix(members: Sequence[str], people: Dict[str, Any]) -> Dict[str, int]:
    mix: Dict[str, int] = {}
    for n in members:
        t = people[n].summary.get("energy_type", "Unknown")
        mix[t] = mix.get(t, 0) + 1
    return mix


def _zone_reference() -> List[Dict[str, Any]]:
    return [{
        "code": z["code"], "label": z["label"], "label_ru": z["label_ru"],
        "centre_ru": z["centre_ru"], "function_ru": z["function_ru"],
        "gap_ru": z["gap_ru"],
        "gates": {str(g): z["gates"][g] for g in sorted(z["gates"])},
    } for z in ZONES]


def _reading(blocks: List[Dict[str, Any]], alpha: Optional[str]) -> str:
    total = len(blocks)
    viable = sum(1 for b in blocks if b["viable"])
    head = (f"WA распалась на {total} блока(ов); "
            + (f"Альфа — {alpha}, вне блоков. " if alpha else "Альфа не выделен. "))
    if viable == total:
        return head + "В каждом блоке закрыты все три зоны — просадок по составу нет."
    weak = []
    for b in blocks:
        gaps = [z["label_ru"] for z in b["zones"] if z["status"] == "gap"]
        if gaps:
            weak.append(f"блок {b['index']} ({', '.join(b['members'])}) — нет зоны "
                        f"«{'», «'.join(gaps)}»")
    return (head + f"Полных блоков {viable} из {total}. Просадки: " + "; ".join(weak)
            + ". Это те места, где бизнес будет нести убытки, не понимая причины.")
