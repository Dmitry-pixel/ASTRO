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
    # 9 тонов от начала цвета = граница 3|4 следующего цвета: стрелка меняется здесь
    lon = (9 * B.TONE_DEG) - B.IGING_OFFSET
    a = B.arrow_with_stability(4, lon, "north_node", 1.0)
    assert a["value"] == "right"
    assert a["confidence"] == "low"


def test_arrow_width_is_three_tones():
    assert round(B.ARROW_DEG * 3600, 2) == 281.25


def test_tone_boundary_inside_a_half_colour_does_not_flag_the_arrow():
    """Tone 4 -> 5 keeps the arrow right; being next to it is not a risk."""
    lon = (10 * B.TONE_DEG + 1.0 / 3600) - B.IGING_OFFSET   # 1" into tone 5
    a = B.arrow_with_stability(5, lon, "north_node", 1.0)
    assert a["value"] == "right"
    assert a["confidence"] == "high"
    assert round(a["margin_arcsec"], 1) == round(93.75 + 1.0, 1)


def test_design_time_scale_widens_the_requirement():
    base = B.required_margin_arcsec("sun", 30, 1.0)["time_arcsec"]
    scaled = B.required_margin_arcsec("sun", 30, 1.0, time_scale=1.05)["time_arcsec"]
    assert scaled > base


def test_arrow_direction():
    assert B.arrow_from_tone(1) == "left"
    assert B.arrow_from_tone(4) == "right"
