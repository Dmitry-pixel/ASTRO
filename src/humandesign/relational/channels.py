"""Short Russian labels for the 36 channels.

The reference database carries an English name, a type and several paragraphs of
description per channel. The product decision is that the API ships machine codes
and short Russian labels; the long English text stays behind `verbosity: full`,
where a consumer has explicitly asked for everything.

Only the Russian name lives here — the database has none. The type is still read
from the database, so neither fact has two sources.

Names were confirmed one by one by the product owner. Six of them do not follow
the literal translation of the English name and would have been wrong if guessed:

    2-14   The Beat        -> Канал Хранителя Ключей
    16-48  Mastery         -> Канал Мастерства
    20-57  Brainwave       -> Канал Блестящих идей
    26-44  Surrender       -> Канал Капитуляции
    33-13  The Prodigal    -> Канал Скитальца
    45-21  Money           -> Материальный канал
"""
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

from .. import hd_constants

LABELS_RU: Dict[Tuple[int, int], str] = {
    (2, 14):  "Канал Хранителя Ключей",
    (3, 60):  "Канал Мутации",
    (8, 1):   "Канал Вдохновения",
    (9, 52):  "Канал Концентрации",
    (10, 34): "Канал Исследования",
    (10, 57): "Канал Совершенной Формы",
    (11, 56): "Канал Любопытства",
    (12, 22): "Канал Открытости",
    (15, 5):  "Канал Ритма",
    (16, 48): "Канал Мастерства",
    (17, 62): "Канал Принятия",
    (18, 58): "Канал Суждения",
    (20, 10): "Канал Пробуждения",
    (20, 34): "Канал Харизмы",
    (20, 57): "Канал Блестящих идей",
    (25, 51): "Канал Инициации",
    (26, 44): "Канал Капитуляции",
    (28, 38): "Канал Борьбы",
    (30, 41): "Канал Распознавания",
    (31, 7):  "Канал Альфы",
    (32, 54): "Канал Трансформации",
    (33, 13): "Канал Скитальца",
    (35, 36): "Канал Непостоянства",
    (40, 37): "Канал Общности",
    (42, 53): "Канал Созревания",
    (43, 23): "Канал Структурирования",
    (45, 21): "Материальный канал",
    (46, 29): "Канал Открытия",
    (49, 19): "Канал Синтеза",
    (50, 27): "Канал Сохранения",
    (55, 39): "Канал Эмоций",
    (57, 34): "Канал Силы",
    (59, 6):  "Канал Интимности",
    (61, 24): "Канал Осознанности",
    (63, 4):  "Канал Логики",
    (64, 47): "Канал Абстракции",
}

#: `hd_data.sqlite` stores two spellings of the generating type — one of them with
#: a Cyrillic С (U+0421) where a Latin C belongs, on channel 10-34. The strings
#: look identical and group as two distinct buckets. Normalised on read rather
#: than patched in the database, which is baked read-only into the image.
_TYPE_FIX = {"Generating Сhannel": "Generating Channel"}

TYPE_LABELS_RU: Dict[str, str] = {
    "Generating Channel": "Генерируемый",
    "Manifesting Channel": "Манифестируемый",
    "Manifesting Generator's Channel": "Манифестирующего Генератора",
    "Projected Channel": "Проецируемый",
}

# The label table and the engine's channel table must describe the same 36
# channels. Fail at import if they ever drift.
assert set(LABELS_RU) == set(hd_constants.CHANNEL_MEANING_DICT), (
    "channel labels and CHANNEL_MEANING_DICT disagree: "
    f"only in labels {sorted(set(LABELS_RU) - set(hd_constants.CHANNEL_MEANING_DICT))}, "
    f"only in engine {sorted(set(hd_constants.CHANNEL_MEANING_DICT) - set(LABELS_RU))}"
)


def normalise_type(raw: Optional[str]) -> Optional[str]:
    """Repair the Cyrillic-С spelling before anything groups on the value."""
    if not raw:
        return None
    return _TYPE_FIX.get(raw, raw)


@lru_cache(maxsize=64)
def _type_of(g1: int, g2: int) -> Optional[str]:
    """Channel type from the reference database. Cached: there are 36 of them and
    a ten-person hybrid asks for the same ones across forty-five dyads."""
    try:
        from ..services.sqlite_repository import SQLiteRepository
        row = SQLiteRepository().get_channel(g1, g2) or {}
    except Exception:
        return None
    return normalise_type(row.get("type") or row.get("channel_type"))


def label(key: Tuple[int, int]) -> Dict[str, Any]:
    """Short reference for one channel: machine key, Russian name, type."""
    name_ru = LABELS_RU.get(key) or LABELS_RU.get((key[1], key[0]))
    typ = _type_of(key[0], key[1])
    out: Dict[str, Any] = {
        "key": f"{key[0]}-{key[1]}",
        "name_ru": name_ru,
    }
    if typ:
        out["type"] = typ
        out["type_ru"] = TYPE_LABELS_RU.get(typ, typ)
    return out


def name_ru(key: Tuple[int, int]) -> Optional[str]:
    return LABELS_RU.get(key) or LABELS_RU.get((key[1], key[0]))
