"""Флаги граничности подструктуры Human Design.

Отличает значение, устойчиво лежащее внутри ячейки (линия/цвет/тон/база),
от значения у самой границы, где ответ определяется не корректностью кода,
а версией файлов эфемерид и точностью времени рождения.

Измерения (20 000 карт + сверка с ASTRO):
  * ширина тона 93.75", ширина базы 18.75";
  * осциллирующий истинный узел между версиями файлов эфемерид расходится до 5";
  * между файлами Swiss Ephemeris и теорией Moshier — до 15.5";
  * Солнце к выбору эфемерид устойчиво, но смещается на 2.46" за минуту
    неточности времени рождения;
  * у 10% людей значение ближе 5% ширины тона к границе, у 20% — ближе 10%.
"""
from __future__ import annotations

GATE_DEG = 360.0 / 64
LINE_DEG = GATE_DEG / 6
COLOR_DEG = LINE_DEG / 6
TONE_DEG = COLOR_DEG / 6
BASE_DEG = TONE_DEG / 5

LEVELS = (("line", LINE_DEG), ("color", COLOR_DEG),
          ("tone", TONE_DEG), ("base", BASE_DEG))

IGING_OFFSET = 58.0

EPHEMERIS_UNCERTAINTY_ARCSEC = {
    "sun": 0.1, "earth": 0.1, "moon": 1.0,
    "north_node": 6.0, "south_node": 6.0, "_default": 1.0,
}

TYPICAL_SPEED_DEG_PER_DAY = {
    "sun": 0.9856, "earth": 0.9856, "moon": 13.176,
    "north_node": 0.20, "south_node": 0.20,
    "mercury": 1.383, "venus": 1.200, "mars": 0.524,
    "jupiter": 0.083, "saturn": 0.034, "uranus": 0.012,
    "neptune": 0.006, "pluto": 0.004, "_default": 1.0,
}


def _key(body):
    return (body or "").strip().lower().replace(" ", "_")


def required_margin_arcsec(body, time_uncertainty_min=1.0, speed_deg_per_day=None):
    """Запас до границы, при котором ячейка считается устойчивой."""
    k = _key(body)
    ephem = EPHEMERIS_UNCERTAINTY_ARCSEC.get(
        k, EPHEMERIS_UNCERTAINTY_ARCSEC["_default"])
    speed = speed_deg_per_day
    if speed is None:
        speed = TYPICAL_SPEED_DEG_PER_DAY.get(
            k, TYPICAL_SPEED_DEG_PER_DAY["_default"])
    time_arcsec = abs(speed) * 3600.0 * (float(time_uncertainty_min) / 1440.0)
    return {
        "ephemeris_arcsec": round(ephem, 3),
        "time_arcsec": round(time_arcsec, 3),
        "required_arcsec": round(max(ephem, time_arcsec), 3),
        "driver": "time" if time_arcsec > ephem else "ephemeris",
    }


def evaluate(longitude, body, time_uncertainty_min=1.0,
             speed_deg_per_day=None, offset=IGING_OFFSET):
    """Расстояние до ближайшей границы на каждом уровне подструктуры."""
    req = required_margin_arcsec(body, time_uncertainty_min, speed_deg_per_day)
    need = req["required_arcsec"]
    angle = (float(longitude) + offset) % 360.0
    levels = {}
    for name, width in LEVELS:
        pos = angle % width
        margin_deg = min(pos, width - pos)
        margin_arcsec = margin_deg * 3600.0
        levels[name] = {
            "margin_arcsec": round(margin_arcsec, 3),
            "required_arcsec": need,
            "fraction_of_cell": round(margin_deg / width, 4),
            "stable": margin_arcsec > need,
        }
    return {
        "body": _key(body),
        "longitude": float(longitude),
        "uncertainty": req,
        "levels": levels,
        "stable": all(v["stable"] for v in levels.values()),
    }


def arrow_from_tone(tone):
    """Тоны 1-3 — левая стрелка, 4-6 — правая."""
    return "left" if int(tone) <= 3 else "right"


def arrow_with_stability(tone, longitude, body, time_uncertainty_min=1.0,
                         speed_deg_per_day=None, offset=IGING_OFFSET):
    """Стрелка Variable вместе с оценкой надёжности. Стрелка есть всегда."""
    ev = evaluate(longitude, body, time_uncertainty_min,
                  speed_deg_per_day, offset)
    t = ev["levels"]["tone"]
    return {
        "value": arrow_from_tone(tone),
        "tone": int(tone),
        "stable": t["stable"],
        "confidence": "high" if t["stable"] else "low",
        "margin_arcsec": t["margin_arcsec"],
        "required_arcsec": t["required_arcsec"],
        "limiting_factor": ev["uncertainty"]["driver"],
    }
