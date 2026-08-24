# Relational Analysis

This directory (`src/humandesign/relational`) computes what happens between people: the dyad and
its composite, the Penta, and the group field at WA scale. It backs the four `/analyze/*`
endpoints and replaces the deleted `services/composite.py`.

## Modules

- **[`semantics.py`](semantics.py)** — data tables only, no I/O and no logic. The centre formula
  (`9+0` … `5+4`), the four Maia connection classes with their mechanics, the genetic type of a
  union, profile resonance, sub-circuitry, nodal resonance, and variable synergy across all four
  arrows. Every block carries a machine `code` alongside `label` and `label_ru`, so the consuming
  application interprets in either language and never has to parse prose.
- **[`persons.py`](persons.py)** — the single path from birth data to a chart for every
  `/analyze/*` endpoint. UTC offsets stay floats, so Mumbai remains +05:30 rather than +05:00.
  Activations are keyed by `(polarity, planet)`, so a chart keeps all 26 rather than the 13 that
  survive keying by planet alone. A participant that cannot be resolved raises
  `PersonResolutionError` and the router turns it into a 422 naming that participant — failures are
  never swallowed into a partial 200.
- **[`engine.py`](engine.py)** — the dyad and its composite. Classification runs over the **full
  set of 36 channels**, which is the whole point: the old engine classified only the channels new
  to the pair, and such a channel has one gate from each side by construction, so it could only
  ever come back Electromagnetic. Compromise, Dominance and Companionship were unreachable —
  61 of 91 connections on a ten-person reference set never reached the response, and those are
  precisely the connections a role-conflict diagnosis is built from.
- **[`groups.py`](groups.py)** — Penta (3-5), which delegates to `features.core.get_penta` and adds
  the participant layer, and the group field (6+), which computes coverage of the 64 gates,
  36 channels and 9 centres, circuit balance, per-person contribution, and the channels that break
  if one specific person leaves.

## Entities

`classify_entity(size)` reports what a group of that size actually forms, and
`meta.entity.doctrine_implemented` is `true` only where it forms a canonical one:

| Size | Entity | Doctrine |
|---|---|---|
| 2 | dyad | yes |
| 3-5 | penta | yes |
| 6-9 | aggregate | **no** — forms neither a Penta nor a WA |
| 10+ | wa | yes — built on the whole bodygraph |

The 6-9 case is analysed with the same mechanics but must not be read as a WA.

## Rules to keep

- **One resolution path.** Birth data becomes a chart in `persons.py` and nowhere else.
- **Failures raise.** Never return a 200 that quietly omits a participant.
- **`semantics.py` holds data, not logic.** If a table needs a branch, the branch belongs in the
  engine.
- **Do not claim doctrine that is not implemented.** `doctrine_implemented` is a promise to the
  consumer, not a formality.

## Background

`docs/relational-decision-2026-08-23.md` records why `services/composite.py` was rebuilt rather
than restored, the ten defects the old file carried, and the licensing question the rewrite
surfaced.
