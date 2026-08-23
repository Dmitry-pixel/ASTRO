# Relational analysis: what was built and why the old engine was not restored

Date: 2026-08-23. Release 3.5.0. Supersedes the open item in
`claude/astro-hd-api-divergence-2026-08-21.md`.

## The decision

`services/composite.py` — 752 lines removed in `ce733ce` — was restored in an
isolated contour, given the API layer it never had, and run against real birth
data. It works. It is still not coming back, for one structural reason plus nine
smaller ones.

**The structural reason.** `classify_maia_connection` was fed `new_channels`, and
`composite_chakras_channels` defines those as the channels neither person held
alone. Such a channel has one gate from each side by construction, so the
function could only ever return `Electromagnetic`. Compromise, Dominance and
Companionship were unreachable through that input. Measured over ten dyads:

| | Electromagnetic | Compromise | Dominance | Companionship | Total |
|---|---|---|---|---|---|
| Actually present | 30 | 28 | 30 | 3 | 91 |
| Reported by the old engine | 30 | 0 | 0 | 0 | 30 |

61 of 91 connections — 67% — never reached the response. Compromise and
Dominance are precisely the material a role-conflict diagnosis is built from:
one partner holds a channel whole, the other holds one gate and yields on it
every time.

The fix is not a patch to `classify_maia_connection`; the function is correct.
It is a different input: the full set of 36 channels. That change reaches into
both orchestration functions, which are 388 of the file's 752 lines and carry
every one of the remaining defects. What was worth keeping — 254 lines of
semantic tables — was rewritten into `relational/semantics.py` and extended.

## What ships

```
src/humandesign/relational/
    semantics.py   data tables only: centre formula, four Maia classes, genetic
                   type of the union, profile resonance, sub-circuitry, nodal
                   resonance, variable synergy across all four arrows
    persons.py     one birth-data resolution path for every endpoint
    engine.py      dyad / composite over the full channel set
    groups.py      Penta 2.0 wrapper and the group-field aggregate
src/humandesign/schemas/analyze.py    pydantic v2 request models
src/humandesign/routers/analyze.py    the four endpoints
```

| Endpoint | Participants | Engine |
|---|---|---|
| `POST /analyze/composite` | exactly 2 | `relational.engine` |
| `POST /analyze/penta` | 3-5 | `features.core.get_penta`, unchanged |
| `POST /analyze/wa` | 6+ | `relational.groups.analyse_group_field` |
| `POST /analyze/maia-penta` | 2+ | every dyad plus the fitting group layer |

All four take `verbosity` (`compact` / `standard` / `full`; `partial` and `all`
map onto the first and last) and, except `composite`, `group_type`
(`business` / `family`).

### Dyad and composite

A dyad is the auric pair; the composite is the merged bodygraph it produces. The
response carries, in this order of use:

1. **Centre formula** — `9+0` … `5+4` with the reading. Nine defined means no
   window onto the outside world; eight and one is the balance long unions run
   on; seven and two asks for awareness; six and below may lack the glue.
2. **Connections** — every channel the pair forms, classified, with its circuit,
   which gates each side holds, which planets activate them (personality and
   design named separately), and the conditioning direction where there is one.
3. **Role conflicts** — the compromise and dominance channels rolled up: a
   conditioning load per person and a verdict of mutual or asymmetric. This is
   the block that answers "why does it feel like they are pushing".
4. **Genetic type of the union** — the task the pair's two types set, not a
   label: a Generator and a Projector are a union of direction; two Manifestors
   need mutual informing or every move reads as suppression.
5. **Centre dynamics** — for each of the nine, fixed / open / who conditions whom.
6. Profile resonance, variable synergy across all four arrows, nodal resonance.

### Penta

`features.core.get_penta` is untouched: six channels across upper and lower
Penta, functional roles, gap severity with impact, hiring logic, and the vision /
action / stability metrics. The endpoint enforces 3-5 and adds the participant
layer. Its frozen `analysis_timestamp` is now real.

### WA

The WA is the entity formed from ten people upward. Where the Penta is scored
over twelve gates in six fixed channels, the WA is built on the whole bodygraph —
all 64 gates, 36 channels and 9 centres — and the payload states that structure
explicitly under `group_field.structure`.

The endpoint shipped in the first cut of 3.5.0 with
`meta.entity.doctrine_implemented: false`, because the upstream project this code
descends from does not implement a WA at all (`Wa` appears there once, inside a
schema description string) and I would not invent doctrine. The structure was
confirmed by the product owner on the day of release, so the flag is now `true`
for a WA; it stays `false` for the 6-9 aggregate, which forms no canonical entity.

What the endpoint returns:

- coverage of the 64 gates, 36 channels and 9 centres, plus circuit balance;
- per-person contribution, including gates nobody else in the group carries;
- **fragility** — the channels that break if one specific person leaves. On the
  ten-person reference group: 62 of 64 gates, 34 of 36 channels, all 9 centres,
  and only 6 of 34 channels depending on a single individual.

Groups of 6-9 form neither entity and are labelled `aggregate`.

## Defects fixed on the way

| Defect | Where it was |
|---|---|
| Maia classification could only return `Electromagnetic` | `composite.py` |
| `int(offset)` truncated +05:30 to +05:00 | `composite.py` |
| Activation matrix keyed by planet only: 13 of 26 survived | `composite.py` |
| Failed participant swallowed, response still 200 | `composite.py` |
| `group_type` and `verbosity` accepted and never read | `composite.py` |
| Variable synergy read Motivation and reported it as all four arrows | `composite.py` |
| `new_chakra` depended on participant order | `features/core.py` |
| Booleans serialised as `0` / `1` | `composite.py` |
| Penta `analysis_timestamp` hardcoded to `2026-01-19T00:00:00Z` | `features/core.py` |
| `response_models.py` could not validate the engine's own output | `schemas/` |

The last four rows lived in code that is still in `main`; the timestamp and the
order-dependence were fixed here, the rest went away with the rewrite.

## What does not exist

**The Grounded 10x Interpretation Engine is not code.** The changelog entry that
introduces it describes an upgrade to "the Professional Maia Relational
*prompt*". There is no prompt in this repository, none in `hd_data.sqlite`, and
none in the upstream project at v4.0.2 — its changelog references interpretation
prompts for daily transit, question, solar return and penta, but ships no prompt
files. Nothing can be ported. The interpretation layer has to be designed as its
own component, and the natural place for it is the consuming application, which
already receives everything it needs in the JSON.

## Licensing — provenance established

Not legal advice; verify with a lawyer. The facts, checked against the git
history of both repositories rather than from memory:

| | |
|---|---|
| `LICENSE` in this repository | **GNU GPL v3** — plain GPL, not Affero. Byte-identical to upstream's `LICENSE` as it stood before its v4.0.0 release. |
| Upstream licence 2024-10-11 → 2026-04-22 | GPL v3 (`dturkuler/humandesign_api`, added in `f02b149`, last carried at `ee4b640`, version 3.4.1). No SPDX headers in source, no licence field in `pyproject.toml`, no licence section in the README — the `LICENSE` file was the whole statement. |
| Upstream relicensing | `71637f0`, 2026-04-22, "Release version 4.0.0" — replaced `LICENSE` and added `LICENSE-AGPL` + `LICENSE-COMMERCIAL`, i.e. `AGPL-3.0-or-later OR LicenseRef-DevAIble-Commercial`. |
| This repository's snapshot | Uploaded `6e6edd1` / `a1ca984` (2026-03-25) and `7749361` (2026-03-26), at upstream version 3.4.1 — **about four weeks before the relicensing**. |

**The AGPL does not reach this code.** Relicensing is prospective: it governs
what the author publishes afterwards, not the grant already made on a version
someone received. The snapshot taken in March 2026 came under GPL v3 and stays
under GPL v3.

**Practical consequence, and it is the important one:** GPL v3 has no
network-use clause. Running a modified GPL v3 program as a hosted service is not
*conveying* it, so customers calling this API over HTTP acquire no right to the
source. Closing that gap is precisely why the AGPL exists — and the AGPL is the
licence this code is not under. The SaaS model is unaffected.

Obligations that do exist, all triggered only by **conveying** the software
itself (shipping the image, the source or a tarball to a third party):
the complete corresponding source, the GPL v3 text, and notices marking the
modified files. Hosting alone triggers none of them. The original `relational`
package is this project's own copyright, but as part of a GPL v3 derivative work
it is licensed under GPL v3 when conveyed.

Two things to keep straight going forward:

1. `pyproject.toml` declared `license = {text = "MIT"}`. Nothing in the chain was
   ever MIT — upstream simply had no licence field, and its `LICENSE` file was
   GPL v3. Corrected to `GPL-3.0-only`. Upstream never published an "or later"
   statement anywhere, so "only" is the conservative reading; if a lawyer prefers
   `GPL-3.0-or-later`, it is a one-word edit.
2. **Do not pull code from upstream 4.0.x.** Everything at `ee4b640` and earlier
   is available under GPL v3; everything from `71637f0` onward is AGPL or
   commercial. Cherry-picking a later fix would import those terms.

## Verification

102 tests pass, 27 of them new, none networked. The new suite pins the
behaviours this document claims: that all four Maia classes appear, that the
composite is order-independent, that Mumbai stays at +05:30, that a chart keeps
26 activations, that an unresolvable participant returns 422 naming itself, that
the three verbosity levels differ in both content and size, and that
`group_type` actually changes the output.
