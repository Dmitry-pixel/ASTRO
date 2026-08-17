"""Guards against a silent precision regression.

``swe_set_ephe_path`` is stored in thread-local storage in this build of pysweph.
FastAPI runs non-async path operations in an anyio worker thread, so a path applied
once at import time is invisible to request handlers and Swiss Ephemeris quietly
degrades to the Moshier model there.

The effect is narrow but real: Type, Authority, Profile, Incarnation Cross and the
active centers are unchanged, while the Variables arrows differ on roughly 5% of
charts, because the lunar node shifts by up to ~13 arcseconds against a tone width
of ~94 arcseconds.

These tests fail if the per-thread re-application in ``ensure_ephe_path`` is removed.
"""

import concurrent.futures
import json
import os

import pytest

import humandesign.features as hd
from humandesign.features.core import _ephe_path
from humandesign.utils.health_utils import check_swisseph_health

pytestmark = pytest.mark.skipif(
    not _ephe_path or not os.path.isdir(_ephe_path),
    reason="Swiss Ephemeris data files are not available; Moshier is the only option",
)

# Every timestamp below was observed to flip its Variables arrows between the main
# thread and a worker thread before the fix, found by sampling 200 random charts.
SENSITIVE_TIMESTAMPS = [
    (1941, 2, 3, 22, 57, 0, -4.0),
    (1959, 8, 18, 15, 22, 0, 2.0),
    (1960, 4, 6, 17, 4, 0, -3.0),
    (1967, 6, 26, 8, 21, 0, 0.0),
    (1971, 4, 7, 17, 28, 0, -4.0),
    (1974, 1, 10, 23, 19, 0, 7.0),
    (1996, 1, 7, 8, 35, 0, -4.0),
    (1999, 8, 15, 21, 13, 0, 8.0),
    (2000, 1, 24, 17, 3, 0, 3.0),
    (2002, 2, 14, 11, 40, 0, 6.0),
    (2010, 9, 13, 14, 59, 0, 2.0),
]


def _variables(timestamp):
    return json.dumps(hd.calc_single_hd_features(timestamp)[11], sort_keys=True, default=str)


def _core_features(timestamp):
    unpacked = hd.unpack_single_features(hd.calc_single_hd_features(timestamp))
    return (
        unpacked["typ"],
        unpacked["auth"],
        tuple(unpacked["profile"]),
        tuple(sorted(unpacked["active_chakra"])),
    )


@pytest.mark.parametrize("timestamp", SENSITIVE_TIMESTAMPS)
def test_variables_identical_in_worker_thread(timestamp):
    """A chart must not depend on which thread computed it."""
    expected = _variables(timestamp)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        actual = pool.submit(_variables, timestamp).result()

    assert actual == expected, (
        "Variables differ between the main thread and a worker thread. "
        "The ephemeris path is thread-local: check that ensure_ephe_path() is still "
        "called from hd_features.__init__."
    )


def test_variables_identical_across_a_thread_pool():
    """Concurrent requests must all agree, not just a single worker."""
    expected = [_variables(ts) for ts in SENSITIVE_TIMESTAMPS]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        actual = list(pool.map(_variables, SENSITIVE_TIMESTAMPS))

    assert actual == expected


@pytest.mark.parametrize("timestamp", SENSITIVE_TIMESTAMPS[:3])
def test_core_mechanics_are_thread_independent(timestamp):
    """Type, Authority, Profile and centers were never affected - keep it that way."""
    expected = _core_features(timestamp)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        actual = pool.submit(_core_features, timestamp).result()

    assert actual == expected


def test_health_probe_reports_swiss_ephemeris_from_a_worker_thread():
    """The health endpoint runs in a worker thread and must not report Moshier."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        status = pool.submit(check_swisseph_health).result()

    assert "Moshier" not in status, f"health probe degraded to Moshier: {status!r}"
    assert status.startswith("ready"), status
