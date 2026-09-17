# Phase 0 research: Qualified frontend baselines

Research completed 2026-09-17 against the local source and the [evidence ledger](evidence.md). Two planning investigators inspected baseline reuse and descriptor integration independently; findings were reconciled with the parent review. No telemetry replay, fault-label inspection or production implementation was performed.

## 1. Runtime placement and dependencies

**Decision**: Implement a Python 3.12 standard-library package `rca.baselining`, with a shared prepared-trace access module under `rca.telemetry`. Keep typed values, deterministic policy/statistics, source adaptation and artifact I/O separate. Use `dataclasses`, `statistics`, `random`, `decimal`, `hashlib`, `json`, `csv` and `sqlite3`; no anomaly library or model calls.

**Rationale**: The [Dockerfile](../../Dockerfile) packages Python 3.12 and `rca/`. The [research contracts](../../experiments/short_window_baselining_v1/contracts.py) already demonstrate these numerical operations with the standard library. The [collection contract](../003-contextual-telemetry-evidence/contracts/collection.md) selects SQLite for reusable access. No new package is needed for this feature's selected median/excess scope.

**Alternatives considered**: Runtime imports from `experiments/` would carry local defaults and study machinery into the runner. A new detector library would not solve membership, source closure or qualification. Repeated full CSV scans would repeat preparation costs.

## 2. Retrieval is a prerequisite, not a capped response

**Decision**: Select every allowlisted blank-parent root by root start, then recover its recorded trace across the declared snapshot. Provide a format-aware scan reference and a SQLite prepared view with the same observation contract. Advance deterministic pages to exhaustion or report partial work; a response limit cannot define a complete reference population.

**Rationale**: Current [recover_traces](../../rca/telemetry/traces.py) selects any span in a time interval and returns at most 30 traces. It cannot directly implement all-root baselining. The [research index](../../experiments/short_window_baselining_v1/index.py) offers useful indexes and completion metadata, but hard-codes research days, paths and deployment assumptions. Its [observation builder](../../experiments/short_window_baselining_v1/observations.py) is a source of reviewed logic, not a certified reusable interface.

**Alternatives considered**: Increasing the cap cannot prove completeness. Importing the research index unchanged would require local files and make relocation change source identity. Feature 009 will implement the narrow trace access prerequisite under feature 003/005 contracts, without waiting for unrelated metric/log retrieval work.

## 3. Precision and reproducibility

**Decision**: Keep original numeric text. Parse integral epoch milliseconds without truncation and use exact integer microseconds where available; otherwise use finite nonnegative `Decimal` duration parsing for endpoint comparisons. Only compatible, declared provisional microsecond normalization enters the initial profile. Compute descriptive statistics with versioned Python binary64 arithmetic at full working precision; never round before support, width or sign decisions.

Use the existing linear quantile convention, sorted absolute-minute keys including empty interval bins, a local `random.Random(42)`, 200 resamples and 190 usable as the minimum. Persist sampled block indexes and resulting medians, plus arithmetic/RNG/runtime identifiers. An anchor need not be minute-aligned: use every absolute minute intersecting the clipped reference interval, which can yield six partial/full bins for a five-minute interval.

**Rationale**: [contracts.py](../../experiments/short_window_baselining_v1/contracts.py) defines the research quantile and block algorithm. Exact endpoint parsing prevents cutoff errors; recorded draws make uncertainty auditable beyond simply repeating the same function. Existing helpers accept negative finite values, so validation must precede any reuse.

**Alternatives considered**: An epsilon would change the declared screen. Resampling only occupied bins changes uncertainty. Using a global RNG couples results to call order. Changing numerical conventions without a version would conceal differences from the research profile.

## 4. Reference identity and state

**Decision**: A baseline set freezes one snapshot, deployment, anchor, profile and estimator version. Per-C1 baselines contain immutable member references and separate support, stability and statistic availability. Keep C0 structural populations before C1 filtering, including per-C0 unknown counts. Create assignments for every resolved query occurrence, including unmatched/unsupported cases.

**Rationale**: Research `stable_membership_hash` only uses trace/span identifiers, and the runner discards unsupported duration comparison rows. Neither is sufficient for source-bound reusable feature outputs. [ADR 0013](../../docs/adr/0013-qualified-short-window-frontend-baselines.md) requires explicit gaps and independent qualifications.

**Alternatives considered**: A single boolean valid flag conflates support and uncertainty. A membership-only cache key misses changed measurements and policies. Automatically expanding history would change the selected comparison.

## 5. Cost, partial work and durability

**Decision**: Build under the caller's output directory using a temporary index and publish a completion marker only after validation. Charge source hashing, parsing, indexing, retrieval, estimates and artifact writes separately. Reuse a verified snapshot handle within a run; reopening requires source validation. Process one trace batch/cohort at a time, spilling normalized observations to prepared storage.

**Rationale**: The [collection contract](../003-contextual-telemetry-evidence/contracts/collection.md) and [executor contract](../004-prompt-anomaly-integration/contracts/executor.md) prohibit treating interrupted or stale preparation as complete. The research scale exceeds 18 million source records, so full materialization is inappropriate. No measured runtime target for this new implementation exists.

**Alternatives considered**: Trusting path/mtime alone weakens source identity. Rehashing/reparsing all sources for each slice defeats reuse. Publishing partial membership as a supported frozen baseline makes concentration and coverage claims misleading. Completed baseline cohorts may remain inspectable, but an incomplete selection/recovery cannot certify the affected cohort.

## 6. Integration and acceptance

**Decision**: Ship the baseline library and an offline validation CLI first. Feature 010 consumes its versioned artifact/API. A later explicit feature 004 policy adapter may call it; do not replace `track1-discovery-v1` silently. Prove B01–B12 with independently authored fixtures, a scan/index differential, interruption/staleness tests and source-resolution checks. Replay the exposed research snapshot only as a separately requested regression, never as held-out evaluation.

**Rationale**: [discovery-policy.md](../004-prompt-anomaly-integration/contracts/discovery-policy.md) uses a frontend naming adapter and count-only support, whereas this profile has an exact allowlist and count/time/stability requirements. Existing discovery tests are not evidence for the new profile.

**Alternatives considered**: Promoting the prototype directly would change discovery behavior and erase policy distinctions. Running all study windows during planning would not validate an implementation that does not exist.

## 7. Duplicate and late-context policy

**Decision**: Collapse identical parsed records at one scoped span identity while retaining all locators; conflicting contents remain unresolved. Version this as `logical-span-dedup-v1` and reconcile differences from the research's conservative duplicate treatment. Construct baseline catalogs from reference candidates only. Query-only contexts return deterministic typed MissingContext outcomes without changing the frozen set.

**Rationale**: Support counts logical requests, not repeated source rows. The cross-review identified that adding a new catalog entry for a late query shape would undermine frozen identity even if existing membership stayed unchanged.

**Alternatives considered**: Treating every duplicate as usable inflates support; silently collapsing conflicts fabricates identity. Pre-scanning future queries to define a baseline catalog couples the reference identity to future observations. Mutating the catalog during assignment breaks reuse.

All planning unknowns are resolved by the decisions above. Extraction, evidence resolution and prepared access remain implementation dependencies with explicit acceptance gates, not unspecified design choices.
