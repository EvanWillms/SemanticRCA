> **Deferred historical artifact.** This describes the previous candidate-recall integration study, not the active first experiment. Use [the revised assertion plan](plan.md). No CLI, loader, fusion pipeline, or full benchmark run described below is required for the first test.

# Design evidence and decisions

Experiment design findings come from local supplied sources; ADR 0001 also cites the public product description for the scope distinction. No literature novelty claim is attempted.

## Failure definition and project goal

**Decision**: Diagnose benchmark-labelled incidents, represented by start time, root-cause component, and fault reason. The complete deliverable explains its evidence; experiment 001 evaluates only component shortlisting.
**Rationale**: Track 1 supplies the failure count and window, and scores recorded diagnosis fields. Establishing a customer-visible outage or SLO breach is not an additional requirement.
**Record**: [ADR 0001](../../docs/adr/0001-benchmark-failure-definition.md) records the evidence and distinction from the broader product.

## Baseline and evaluation

**Decision**: Reproduce the native baseline separately from a harmonized comparator.
**Rationale**: `analyse()` already exposes `ranked`; it reads only container/node metrics, drops MAD=0 series, and parses instruction times as UTC. The data guide documents UTC+8 answer times and mixed timestamp units. Audit the actual data before deciding a correction is necessary. The reported 0.073 score is not candidate recall.
**Alternatives considered**: Compare only with the native baseline (confounds data correctness with representation); implement a new metric baseline without retaining provenance (loses reproducibility).

## Gold labels and independence

**Decision**: Group related windows, combine only unambiguous partial labels, score each independent block once in the macro metric.
**Rationale**: Seven task types request different subsets of time/component/reason. Seventy rows cannot be assumed to be seventy independent incidents. The official scorer extracts only fields present in each scoring-points string.
**Alternatives considered**: Random row split (leakage); task_7-only evaluation (may unnecessarily discard compatible labels); infer missing gold (invalid).

## Minimal mechanism

**Decision**: Fixed robust-z states and persistent episodes, per-edge traces, equal late fusion, and a matched numerical control.
**Rationale**: Tests candidate localization without LLM, semantic log parsing, or motif training. Keeps partial-order trace structure and isolates at least the effect of symbolic quantization within the same feature pipeline.
**Alternatives considered**: SAX/SFA or motif learning (premature complexity); adding traces without N2 (cannot attribute lift to symbolism); treating abnormal callers/callees as proven causes (unsupported).

## Data readiness

**Decision**: Use the now-extracted organizer bundle at `data/track-1`; freeze incident split counts after grouping and label-completeness validation.
**Rationale**: During planning the local `track-1-Market-cloudbed-1.zip` was 334,635,008 bytes and `unzip -l` failed with a missing central directory. No extracted query file was available. This can indicate an incomplete download; its cause was not established. That historical blocker is superseded by the subsequent extracted-data audit: 18 CSVs are present; the query file has 70 rows and 57 distinct windows; all 9,132,857 rows in the March 20 trace file have the expected nine fields. This does not certify every other data file or independent incident count.
**Alternatives considered**: Invent a 50/20 row split (ignores incident dependence); download upstream data (would expose hidden answers).

## Source ledger

- Proposal: `docs/research/MantisGrid_HFCE_Multimodal_Symbolic_RCA.v1.md`, especially L1–L3 and A0–A3.
- Constitution: `.specify/memory/constitution.md` version 1.0.1, local draft with pending ratification date.
- Official repository: `../hackathon-2026-official`, revision `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`.
- Official files inspected: `track-1/docs/data.md`, `track-1/starter/agents/heuristic.py`, `track-1/starter/score.py`, `track-1/starter/README.md`, `track-1/starter/run.py`, `track-1/GET_DATA.md`.

## Actual trace audit, 2026-09-17

**Decision**: Amend trace retrieval, parsing, graph projection, and feature eligibility using measured source behavior. See [full audit and assumption ledger](../../docs/research/track-1-trace-audit.md).
**Evidence**: Three `gpt-5.6-terra` agents at medium reasoning independently audited full-day lexical schema, one full trace graph, and a bounded semantic sample. The primary agent cross-checked counts, source rows, exact integer timing, and the plan changes. No gold file or ranking was used.
**Corrections**: Read/filter the whole unsorted file; preserve opaque IDs and mixed status strings; blank type is valid; separate recording component from operation target; classify same-component parent links separately from cross-component calls; retain zero durations; duration units are provisionally microseconds based on dispatch/end alignment, independent of epoch-millisecond timestamps. Sub-millisecond apparent overlaps do not demonstrate concurrency. The guide's illustrative counts (27 operations/four statuses) differ from the measured March 20 counts (29/eight), so observed values and extensible parsing govern.
**Alternatives rejected**: Prefix-based graph completeness estimates; treating every parent link as a service edge; numeric/global status error rules; treating duration as milliseconds because timestamp is milliseconds; inferring causal/network latency from a start gap.

Residual empirical questions: actual independent incident groups and complete gold coverage; authoritative duration metadata and clock synchronization across emitters; full-day relationship integrity beyond the selected trace; trace feature/reference eligibility, including constant baselines; whether traces improve recall. Resolve using development data and the prescribed freeze policy, not holdout tuning.
