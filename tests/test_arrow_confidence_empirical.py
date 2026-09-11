"""confidence=high must mean the arrow does not turn inside the stated doubt.

Brute force against the engine: for a fixed sample of birth moments, every
arrow reported ``high`` at precision u must keep its direction at t-u and t+u.
Until 3.10.1 the flag used the tone boundary (every 93.75") instead of the
arrow boundary (every 281.25") and flagged roughly three times too often; the
design side also ignored that the design moment moves 0.95-1.05x the birth
shift. Both are covered here: over-flagging by the rate check, under-flagging
by the brute-force check.
"""
import datetime as dt
import random

import pytest

from humandesign.features.attributes import get_variables
from humandesign.features.core import hd_features

ARROWS = ("top_right", "bottom_right", "top_left", "bottom_left")
_rnd = random.Random(20260910)
_START = dt.datetime(1960, 1, 1)
_SPAN = (dt.datetime(2006, 1, 1) - _START).total_seconds()
MOMENTS = [_START + dt.timedelta(seconds=int(_rnd.random() * _SPAN)) for _ in range(60)]


def _vars(t, u=1.0):
    d = hd_features(t.year, t.month, t.day, t.hour, t.minute, t.second, 0).birth_creat_date_to_gate()
    return get_variables(d, time_uncertainty_min=u)


@pytest.mark.parametrize("u", [15, 30])
def test_high_never_turns_inside_the_window(u):
    checked = 0
    for t in MOMENTS:
        v = _vars(t, u)
        lo = _vars(t - dt.timedelta(minutes=u))
        hi = _vars(t + dt.timedelta(minutes=u))
        for a in ARROWS:
            if v[a]["confidence"] == "high":
                checked += 1
                assert lo[a]["value"] == v[a]["value"] == hi[a]["value"], (t, u, a, v[a])
    assert checked > 60


def test_solar_flag_rate_matches_geometry_at_15_minutes():
    """Sun: 2.46"/min x 15 = 36.9" of 140.6" half-width -> ~26% low, not ~79%."""
    low = sum(_vars(t, 15)[a]["confidence"] == "low"
              for t in MOMENTS for a in ("top_right", "top_left"))
    rate = low / (2 * len(MOMENTS))
    assert 0.10 < rate < 0.45, rate
