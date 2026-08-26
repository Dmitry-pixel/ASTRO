"""Проверка того, что Swiss Ephemeris действительно читает файлы.

Без файлов .se1 swisseph молча переходит на теорию Moshier: ошибки нет,
флаг SEFLG_SWIEPH принимается, расчёт идёт. Солнце остаётся точным, а
осциллирующий истинный узел уходит на 15.5 угловых секунд — при ширине
тона 93.75" это переворачивает стрелку Variable примерно у каждого
десятого профиля.

Проверять надо retflag фактического вызова и в том же потоке, где идёт
расчёт: swisseph держит путь в thread-local, воркеры FastAPI его не наследуют.
"""
from __future__ import annotations

import logging
import os

import swisseph as swe

_PROBES = (("sun", swe.SUN), ("moon", swe.MOON), ("north_node", swe.TRUE_NODE))
_PROBE_JD = 2451545.0

log = logging.getLogger(__name__)


def ephemeris_status(jd=_PROBE_JD):
    """Какой источник реально используется прямо сейчас, в этом потоке."""
    bodies, sources = {}, set()
    for name, code in _PROBES:
        try:
            _res = swe.calc_ut(jd, code, swe.FLG_SWIEPH)
            retflag = _res[1]
        except Exception as exc:
            bodies[name] = {"source": "error", "detail": str(exc)}
            sources.add("error")
            continue
        if retflag < 0:
            src = "error"
        elif retflag & swe.FLG_SWIEPH:
            src = "swieph"
        elif retflag & swe.FLG_MOSEPH:
            src = "moseph"
        elif retflag & swe.FLG_JPLEPH:
            src = "jpleph"
        else:
            src = "unknown"
        bodies[name] = {"source": src, "retflag": int(retflag)}
        sources.add(src)

    ok = sources in ({"swieph"}, {"jpleph"})
    return {
        "ok": ok,
        "sources": sorted(sources),
        "bodies": bodies,
        "ephe_path_env": os.environ.get("SE_EPHE_PATH"),
        "message": ("Файлы эфемерид загружены." if ok else
                    "Swiss Ephemeris работает без файлов (Moshier). Узел "
                    "уходит до 15.5 угловых секунд, стрелки Variable "
                    "недостоверны."),
    }


def assert_ephemeris(strict=True, jd=_PROBE_JD):
    """Падать сразу, а не отдавать тихо неверные Variables."""
    st = ephemeris_status(jd)
    if not st["ok"]:
        if strict:
            raise RuntimeError(
                "%s Источники: %s. SE_EPHE_PATH=%r"
                % (st["message"], st["sources"], st["ephe_path_env"]))
        log.warning("%s Источники: %s", st["message"], st["sources"])
    return st


def ensure_and_verify(ephe_path=None, strict=True):
    """Задать путь и сразу проверить — вызывать в начале каждого воркера."""
    if ephe_path:
        swe.set_ephe_path(ephe_path)
    return assert_ephemeris(strict)
