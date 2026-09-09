import swisseph as swe
import logging

logger = logging.getLogger(__name__)

def check_swisseph_health() -> str:
    """
    Checks if Swiss Ephemeris is functioning correctly by performing a simple calculation.
    Returns "ready (Swiss Ephemeris / DE431)" if .se1 files are loaded,
    "degraded (moseph)" if Swiss Ephemeris silently fell back to Moshier,
    or "error" if something is broken.
    """
    try:
        # The ephemeris path is thread-local; this probe runs in whichever worker
        # thread served the request, so apply it here too. Without this the health
        # endpoint reports Moshier while the main thread is on DE431.
        from ..features.core import ensure_ephe_path
        from ..features.ephemeris_guard import ephemeris_status

        try:
            ensure_ephe_path()
        except RuntimeError:
            # Путь применён до строгой проверки; источник определим сами,
            # чтобы /health отвечал "чем именно считаем", а не просто "error".
            pass

        # Источник берётся из retflag фактического вызова, а не из текста serr:
        # сообщение библиотеки — не контракт, retflag — контракт.
        st = ephemeris_status()
        if st["ok"]:
            return "ready (Swiss Ephemeris / DE431)"
        if "error" in st["sources"]:
            return "error"
        return "degraded (%s)" % "+".join(st["sources"])
    except Exception as e:
        logger.error(f"Swiss Ephemeris health check failed: {e}")
        return "error"
