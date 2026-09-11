"""Generate src/humandesign/features/team_axes_baseline.py.

Population distribution of the four team-dynamics characteristics on random
charts: pole shares, band shares, the full index distribution (for
percentiles), Decision modes and Integration. The team layer compares a group
with a random draw from this population, so these numbers are its null
hypothesis.

    SE_EPHE_PATH=$PWD/ephe PYTHONPATH=$PWD/src python scripts/gen_team_axes_baseline.py

Birth moments are uniform over 1960-01-01 … 2006-01-01 UTC. Deterministic: the
same --n and --seed give a byte-identical file.
"""
import argparse
import datetime as dt
import random
from collections import Counter
from pathlib import Path

from humandesign.features.core import hd_features
from humandesign.features.team_axes import AXES, MODEL_VERSION, compute_from_date_to_gate

OUT = Path(__file__).resolve().parents[1] / "src" / "humandesign" / "features" / "team_axes_baseline.py"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20260910)
    args = ap.parse_args()

    rnd = random.Random(args.seed)
    start = dt.datetime(1960, 1, 1)
    span = (dt.datetime(2006, 1, 1) - start).total_seconds()
    poles = {a: Counter() for a in AXES}
    bands = {a: Counter() for a in AXES}
    hist = {a: Counter() for a in AXES}
    modes, integ, basis, reading = Counter(), Counter(), Counter(), Counter()
    for _ in range(args.n):
        t = start + dt.timedelta(seconds=rnd.random() * span)
        r = compute_from_date_to_gate(
            hd_features(t.year, t.month, t.day, t.hour, t.minute, 0, 0).birth_creat_date_to_gate())
        for a in AXES:
            ax = r["axes"][a]
            poles[a][ax["pole"] or "none"] += 1
            bands[a][ax["band"]] += 1
            hist[a][int(ax["index"])] += 1
        modes[r["axes"]["decision"]["mode"] or "none"] += 1
        basis[r["axes"]["execution"]["basis"]] += 1
        integ[r["integration"]["code"]] += 1
        rd = r["axes"]["decision"]["integration_reading"]
        reading[rd["code"] if rd else "none"] += 1

    n = args.n
    pct = lambda c: {k: round(100.0 * v / n, 2) for k, v in sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0])))}
    cdf = {}
    for a in AXES:
        run, row = 0, []
        for i in range(101):
            run += hist[a].get(i, 0)
            row.append(round(100.0 * run / n, 2))
        cdf[a] = row

    lines = [
        '"""Population distribution of the team-dynamics characteristics. GENERATED — do not edit.',
        "",
        "    python scripts/gen_team_axes_baseline.py --n %d --seed %d" % (n, args.seed),
        "",
        "INDEX_CDF_PCT[axis][i] is the share of the population whose index is <= i.",
        '"""',
        "MODEL_VERSION = %r" % MODEL_VERSION,
        "N = %d" % n,
        "SEED = %d" % args.seed,
        "DATE_RANGE = ('1960-01-01', '2006-01-01')",
        "",
        "POLE_SHARES_PCT = {",
        *["    %r: %r," % (a, pct(poles[a])) for a in AXES],
        "}",
        "",
        "BAND_SHARES_PCT = {",
        *["    %r: %r," % (a, pct(bands[a])) for a in AXES],
        "}",
        "",
        "DECISION_MODE_SHARES_PCT = %r" % pct(modes),
        "EXECUTION_BASIS_SHARES_PCT = %r" % pct(basis),
        "INTEGRATION_SHARES_PCT = %r" % pct(integ),
        "DECISION_READING_SHARES_PCT = %r" % pct(reading),
        "",
        "INDEX_CDF_PCT = {",
        *["    %r: %r," % (a, cdf[a]) for a in AXES],
        "}",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("written", OUT)
    for a in AXES:
        print(" ", a, "poles", pct(poles[a]))
        print(" ", " " * len(a), "bands", pct(bands[a]))
    print("  decision modes", pct(modes))
    print("  execution basis", pct(basis))
    print("  integration", pct(integ))
    print("  decision × integration", pct(reading))


if __name__ == "__main__":
    main()
