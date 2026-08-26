"""Тесты флагов граничности. Эфемериды не требуются."""
from humandesign.features import boundary as B


def test_widths():
    assert round(B.TONE_DEG * 3600, 2) == 93.75
    assert round(B.BASE_DEG * 3600, 2) == 18.75


def test_center_of_tone_is_stable():
    lon = (10 * B.TONE_DEG + B.TONE_DEG / 2) - B.IGING_OFFSET
    assert B.evaluate(lon, "north_node", 1.0)["levels"]["tone"]["stable"] is True


def test_exact_boundary_is_unstable():
    lon = (10 * B.TONE_DEG) - B.IGING_OFFSET
    assert B.evaluate(lon, "north_node", 1.0)["levels"]["tone"]["stable"] is False


def test_sun_needs_precise_birth_time():
    lon = (10 * B.TONE_DEG + 3.0 / 3600) - B.IGING_OFFSET
    assert B.evaluate(lon, "sun", 1)["levels"]["tone"]["stable"] is True
    assert B.evaluate(lon, "sun", 30)["levels"]["tone"]["stable"] is False


def test_arrow_always_present():
    lon = (10 * B.TONE_DEG) - B.IGING_OFFSET
    a = B.arrow_with_stability(4, lon, "north_node", 1.0)
    assert a["value"] == "right"
    assert a["confidence"] == "low"


def test_arrow_direction():
    assert B.arrow_from_tone(1) == "left"
    assert B.arrow_from_tone(4) == "right"
