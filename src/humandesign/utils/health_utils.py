import swisseph as swe
import logging

logger = logging.getLogger(__name__)

def check_swisseph_health() -> str:
    """
    Checks if Swiss Ephemeris is functioning correctly by performing a simple calculation.
    Returns "ready (Swiss Ephemeris)" if .se1 files are loaded,
    "ready (Moshier)" if falling back to built-in Moshier,
    or "error" if something is broken.
    """
    try:
        # Perform a test calculation for the Sun at J2000.0
        result = swe.calc_ut(2451545.0, swe.SUN)
        # In pysweph, result is (xx, retflags, serr)
        # serr will mention "using Moshier" if .se1 files are not found
        serr = result[2] if len(result) > 2 else ""
        if "Moshier" in serr:
            return "ready (Moshier)"
        return "ready (Swiss Ephemeris / DE431)"
    except Exception as e:
        logger.error(f"Swiss Ephemeris health check failed: {e}")
        return "error"
