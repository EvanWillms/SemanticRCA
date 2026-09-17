# Implementation Plan: Qualified short-window frontend baselines

**Feature context**: `009-qualified-short-baselines` | **Date**: 2026-09-17 | **Spec**: [spec.md](spec.md)

**Git branch at planning**: `008-featherless-trace-semantics`. Setup used an explicit feature directory; its returned BRANCH is the feature-context identifier, not a newly created Git branch.

**Input**: `specs/009-qualified-short-baselines/spec.md`

**Status**: Phase 0 research and Phase 1 design complete. Implementation, feature acceptance execution and discovery promotion remain pending.

## Summary

Build a deterministic reference producer under `rca.baselining`. It selects all frontend roots under the explicit five-minute C1 pooled policy, recovers recorded executions through shared snapshot-bound access, and freezes membership for six query slices. Support, center stability and statistic availability remain independent. Export immutable baselines, C0 structural populations, observations, query assignments and coverage for feature 010.

The existing research algorithms supply reviewed starting points, but the current discovery path and study output schemas do not meet this contract. Implement the narrow extraction/index prerequisite under features 003/005, without importing research code or replacing the current discovery policy implicitly. Decisions and alternatives are in [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12, matching the existing container.

**Primary Dependencies**: Standard library only: dataclasses, csv, sqlite3, statistics, random, decimal, hashlib, json, pathlib and unittest. No network, credentials or model calls.

**Storage**: Rebuildable SQLite trace/observation preparation and versioned JSON/JSONL artifacts beneath caller-supplied output. Canonical artifact hashes exclude runtime paths and timing; snapshot identity includes declared relative source paths and content hashes.

**Testing**: Independently authored unittest fixtures, scan/index differential, golden resampling expectations, corruption/interruption tests, relocation and six-slice reuse integration, plus existing harness regression checks after code changes.

**Target Platform**: Existing Linux Python 3.12 container; local Python 3.12 for development.

**Project Type**: Internal runtime library with an offline developer validation CLI. No new required official-runner flags.

**Performance Goals**: One complete preparation per verified snapshot, no full CSV reparse for six slices, one bootstrap per baseline identity, and shared trace recovery across overlapping selections. Record cold/warm time, peak RSS, source bytes/records, index size and estimator work. No elapsed-time target or claimed speedup is established before measurement.

**Constraints**: Bounded source batches, exact source identity and root selection, no implicit fallback/refresh, finite values, complete unavailable outcomes, atomic publication, explicit partial coverage and deterministic work accounting. A response page cannot certify a population.

**Scale/Scope**: Initial profile is one deployment and frontend-0/1/2. The exposed study has 18,160,322 source rows and 57 supplied windows; these motivate streaming/reuse, not mandatory planning reruns or independent-trial claims.

## Constitution Check

The pre-research gate passed for this design scope. The post-design review passed with the same boundaries:

| Principle/gate | Design evidence and outcome |
| --- | --- |
| I: evidence-first | Each baseline/statistic retains members, source references and qualifications. No health or diagnosis conclusion. PASS |
| II: bounded access | Snapshot allowlists, exact-root selection, prepared lookup, source batches and partial receipts. PASS |
| III: cost-aware routing | No model calls; preparation/reuse/estimation costs are measured. Routing remains the later agent's obligation. PASS |
| IV: reproducible evaluation | Independent B01–B12 fixtures, frozen policy/draw evidence and explicit exposed-data regression boundary. No claim of unseen diagnostic accuracy. PASS |
| V: runtime/submission | Standard-library container, output-contained derived artifacts and no author-local cache dependency. Official runner interface and final outputs remain compatible. PASS |
| Workflow | Specification and accepted ADR precede this plan. Tasks and implementation are subsequent commands. PASS |

The constitution's pre-existing ratification-date placeholder is a governance item for the project maintainer; this plan does not change or claim to resolve it. No substantive principle exception or amendment is required. Source-access and artifact gates below must pass before integration can claim this feature works.

## Project Structure

### Documentation

```text
specs/009-qualified-short-baselines/
├── spec.md, acceptance.md, evidence.md
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/
│   ├── baseline.md          # existing semantic authority
│   └── producer.md          # planned API, artifact and CLI interface
└── checklists/
    ├── requirements.md
    └── design-review.md
```

`tasks.md` is deliberately left for `$speckit-tasks`.

### Planned source layout

```text
rca/telemetry/trace_index.py       # shared snapshot-bound scan/index access
rca/baselining/
├── __init__.py                   # narrow public producer API
├── contracts.py                  # immutable values and validation
├── observations.py               # extraction adapter; C0/C1/C2
├── statistics.py                 # support diagnostics and estimator evidence
├── policy.py                     # frozen membership, outcomes and coverage
├── artifacts.py                  # bundle validation, publication and loading
└── __main__.py                   # offline build/validate interface
tests/unit/test_baseline_*.py
tests/integration/test_baseline_pipeline.py
tests/fixtures/qualified_baselines/   # authored synthetic sources/expectations
```

**Structure Decision**: Reuse `rca/` packaging and keep generic prepared access in telemetry. The producer owns reference evidence; feature 010 owns differences and review views. Existing `rca.telemetry.traces.compare_traces` remains a distinct legacy policy until an explicit discovery integration change is approved through its own plan.

## Delivery sequence and gates

1. **Source and observation boundary (B01–B03, B09, B12)**: Implement immutable identities, raw/normalized measurement evidence and duplicate/conflict handling. Build exact-root scan selection and prepared lookup with complete recorded recovery. Compare scan/index results on the same authored inventory. Publication requires matching source/count validation; interrupted builds remain unusable.
2. **Reference and estimator core (B04–B06)**: Apply five-minute membership, all failing support reasons, independent stability and per-statistic availability. Retain draw indexes, quantiles and sensitivity diagnostics. Exact zero, count, minute, concentration and width boundaries are release checks, not tunable heuristics.
3. **Frozen reuse and coverage (B07–B10)**: Freeze baseline sets, construct C0 populations, retain query assignments including typed missing-context outcomes for absent C1/C0 keys, and reuse through six slices. Keep the catalog reference-only; a new context first appearing in the last slice cannot alter frozen set/catalog/member identities. Reconcile counts per slice/class/replica and distinguish overlapping occurrences. If a budget stops required reference recovery, mark affected baselines unavailable rather than estimating from a convenient prefix.
4. **Artifact and consumer boundary (B11–B12)**: Validate semantic content, source resolution, finite JSON and canonical identifiers. Run the offline CLI from fresh output and after dataset relocation. Export an artifact that feature 010 can consume without recalculating selection. Use independently authored benchmark-shaped cases for low support, large centers and unstable centers.
5. **Joint gate with feature 010**: Run the producer→descriptor fixture and verify that unsupported/unstable/zero cases preserve their exact meanings. No diagnostic result is required. A future feature 004 adapter must explicitly select this profile and preserve metric discovery, receipts and submission outputs.

This sequence is implementation planning, not a substitute for dependency-ordered tasks. Feature 010's pure tests can proceed against authored bundles while extraction is built; its integration acceptance requires the actual producer.

## Validation and evaluation impact

[acceptance.md](acceptance.md) is authoritative for B01–B12 and FR/SC coverage. [quickstart.md](quickstart.md) defines future runnable validation. Retain machine-readable expected/actual memberships, failure reasons, draw evidence, coverage and source-resolution results. Test budgets with deterministic work counters/fake clocks; compare partial replay only at identical recorded boundaries.

Numerical comparisons against the old research output report full-precision differences under the declared arithmetic version. Assertions may use documented numerical tolerances for float equality, but those tolerances must never alter production support, screen or ranking rules. Reconciliation differences trigger inspection, not automatic gate relaxation. Report preparation cost separately from reuse; validate that cache hits avoid repeated parsing/estimation through counters, not timing alone.

No model routing, incident inference, held-out score or alert calibration changes here. A complete 57-window replay is an optional later regression with supplied telemetry; authored contract cases are the normal acceptance path.

## Complexity Tracking

No constitution violations require an exception. SQLite is the existing collection decision, not an additional service. The narrow prepared-access prerequisite and a scan oracle add code but are necessary to establish complete membership and reuse independently of the current capped discovery function.
