# Research: prompt interpretation and deterministic discovery

**Date**: 2026-09-17. This is planning research, not implementation or a parser accuracy result.

## Evidence inspected

Read the existing feature 004 specification/integration contract, ADR 0006, constitution 1.0.2, the current run.py/rca input and result interfaces, and the public Track 1 query.csv. No telemetry or development-answer files were needed. The supplied public inventory has 70 distinct instructions and columns row_id, task_index, instruction. Task counts are 12/10/8/7/10/12/11 for task_1 through task_7. Seventy is a validation inventory size, not a runtime limit.

The current CSV reader preserves row ID/instruction but drops optional task_index. The current agent returns a placeholder and does not interpret prompts. Earlier experiment scope parsing depends on a development lookup and fixed March dates; it is not the implementation to promote.

## Decisions

### 1. Deterministic, bounded interpretation

**Decision**: Use Python 3.12 standard-library CSV, regular-expression matching and datetime validation. Support the actual Track 1 English prompt grammar and explicit documented variations; return unsupported for missing/conflicting/unknown grammar. No model calls, generated code, telemetry or external service.

**Rationale**: Queries express a small finite set of scope fields in recurring forms. Interpretation can be tested exactly and must not turn uncertain prose into a guessed scope.

**Alternatives considered**: Model-assisted parsing adds nondeterminism, credentials and cost without a requirement; a generic natural-language/date parser broadens accepted input silently; fixed row-ID lookup would fail on another supplied query set.

### 2. Original text and extraction support

**Decision**: Preserve the decoded instruction string and UTF-8 SHA-256 identity. Match case-insensitively with whitespace-aware grammar directly against that string; evidence uses zero-based half-open Unicode character offsets and exact text excerpts. Record convention-derived timezone and date inheritance separately.

**Rationale**: Whitespace normalization must not corrupt source offsets. A reviewer should verify each value from the source prompt without executing the parser.

**Alternatives considered**: Offsets into a normalized string are misleading; free-text explanations alone are harder to validate; confidence scores are unnecessary for deterministic grammar acceptance.

### 3. Explicit field extraction and metadata cross-check

**Decision**: Extract requested fields from the explicit request clause, using the observed aliases for occurrence time/datetime, affected/root-cause component(s), and reason(s). Canonical order is datetime, component, reason. Examine all supported explicit request clauses and reject conflicting projections. task_index is optional and can only confirm the derived projection.

**Rationale**: Descriptive background sentences mention unknown facts that are not necessarily requested. Requests can change field order and use “affected component” or “reason behind this issue.”

**Alternatives considered**: Whole-prompt keyword detection can add unrequested fields; deriving projection from task_index hides prompt errors; taking only the last directive silently resolves contradictions.

### 4. Dates and timezone

**Decision**: Use an explicit English month map and fixed UTC+08:00 offset. Parse the declared calendar date and 24-hour clock bounds, including an explicitly repeated end date and optional “at”. Validate real calendar dates and exactly 30 minutes. A missing end date inherits the start date; the narrowly permitted 23:30→00:00 rollover is convention-derived. An explicit non-increasing/conflicting end date is never repaired.

**Rationale**: Public rows 26 and 66 explicitly cross midnight to the next calendar day; row 66 also includes “at”. Local timezone and March-only parsing are incorrect dependencies.

**Alternatives considered**: Host-locale strptime and naive timestamps risk platform-dependent behavior; inferring arbitrary overnight windows can repair invalid prompts into unintended scopes.

### 5. Count and deployment

**Decision**: Extract the event's count from occurrence assertions (“experienced”/“encountered”, including auxiliary “has”), and cross-check explicit repeated count assertions such as “There is one known failure”. Recognize a/a single/one and two, plus positive decimal counts; additional number-word grammar is unsupported unless explicitly added with fixtures. Extract the deployment identifier from the system-identification clause using the Track 1 identifier syntax, with a variable identifier value. Collect repeated explicit values and reject contradictions.

**Rationale**: Repeated mentions of “this failure” describe an incident rather than assert another count. The deployment comes from the prompt, not a dataset path or development constant.

**Alternatives considered**: Counting occurrences of the word failure, defaulting missing count to one, fixing cloudbed-1, or resolving the deployment through telemetry all violate the stage boundary.

### 6. Minimal runner handoff

**Decision**: Extend QueryRow with optional task_index, introduce a pure interpretation result, and attach it optionally to Solution. A prompt-input agent produces that result and truthful placeholder evidence; OutputWriter persists scope.json before the prediction checkpoint. Keep the existing submission stub available explicitly. Unsupported prompts are returned as data, processed without telemetry, and cause a nonzero final run exit after later valid rows are processed.

**Rationale**: This uses the existing three-flag CLI and agent seam without building a discovery controller. The writer continues to own persistence.

**Alternatives considered**: Having the agent write arbitrary side files duplicates persistence rules; raising ordinary exceptions for unsupported text would stop subsequent rows under the current runner; adding discovery state or operations is outside this request.

### 7. Validation boundaries

**Decision**: Validate public input, pure interpretation, and CLI artifacts as separate seams. Create independent human-reviewed expectations from the public query text, never by serializing parser output or consulting a scope register. Retain synthetic edge cases and stub regression tests. Use a prompt-output validator distinct from the strict empty-output validator.

**Rationale**: Matching an implementation-derived oracle proves nothing. Existing synthetic harness instructions intentionally lack interpretable scope and should continue to work only in explicit stub mode.

**Alternatives considered**: Reusing anomaly/diagnosis evaluation would couple interpretation to unrelated behavior; loosening placeholder validation hides mode mistakes.

## Resolved technical context

No new package, storage service, model or telemetry adapter is needed. Target remains Python 3.12/Linux Docker with only --out writable. Performance target for this small stage is under five seconds for the 70-prompt inventory, including output writing, measured under the existing 2-CPU/8-GB envelope; this is a planned target, not an observed result. Final judging performance and resource preparation remain outside this slice.

## Independent Luna xhigh research cross-check

The read-only review independently confirmed the 70-row inventory, task distribution and both midnight cases without reading telemetry or answer files. Counts are 44 single-failure and 26 two-failure cases; 57 unique windows must remain 70 independent rows. Required extra grammar includes standalone capitalized “Cloudbed-1” as event subject (row 32), “within the timeframe”, “within the specified time range”, “On … from …”, “may have experienced two failures”, “confirmed there was one failure” (row 60), and “reason for this failure” (row 54). Identifier matching is case-insensitive with lowercase canonical identity and exact source spelling retained as evidence. These forms are now explicit in the contract and must each have an independent fixture.

## Executor sequence amendment — 2026-09-17

The earlier sections intentionally researched prompt interpretation only. The current user request expands planning to the full deterministic preparation sequence and onward to a submittable executor. The following decisions extend, rather than discard, that research. This remains design work, not implementation evidence.

### 8. Always-running vertical slices

**Decision**: Preserve the runner/solve/writer seams and explicit stub. Deliver scope, inventory, trace retrieval, independent metrics, comparisons and bounded corroboration as separately runnable increments. The first ten-minute implementation attempt targets the scope slice; full discovery readiness requires all feature 004 gates. Incomplete work uses the existing optional agent selector and explicit capability/status. Promote the default only at accepted mode boundaries.

**Rationale**: Current runtime contains no scope parser or telemetry access. All 26 existing tests passed during planning. A small integrated result can be reviewed and rolled back without destabilizing the existing CLI. Existing synthetic harness queries cannot double as interpretation acceptance fixtures.

**Alternatives considered**: Rewrite the runner; construct all preprocessing before integrating any artifact; switch the default to an incomplete implementation; describe blank predictions as submission-ready. Each would weaken either feedback speed or the status contract.

### 9. Standard-library kernels and portable prepared views

**Decision**: Adapt implementation concepts from `experiments/frontend_blind_v1/build_index.py` under ADR 0003, and the more explicit provenance/comparison kernels in `experiments/short_window_baselining_v1/`. Promote validated functions into runtime `rca/` modules, using SQLite, streaming CSV and standard-library statistics. Keep independent scan fixtures as the correctness reference. No direct runtime imports from experiment packages.

**Rationale**: Read-only research identified reusable `build_observation`, `signature_for_root`, `support_diagnostics`, and `compare_duration` functions. The Dockerfile packages only run.py, agents and rca. The newer index code has source provenance/completion concepts but also hardcoded expected days, repeated scans/hashes, unbounded fetches and no deadline. The older index covers metric/log schemas but lacks robust manifest compatibility and eagerly builds modalities. Both require adaptation and acceptance tests.

**Alternatives considered**: Add pandas/PyOD and a dependency installation path immediately; copy the old experiment coordinator wholesale; depend on development indexes. None is needed for the first descriptive median/difference pipeline. Experiment performance or correctness does not transfer automatically to runtime.

### 10. Independent modalities and scoped semantics

**Decision**: Run the metric discovery path independently of frontend traces. Discover resource/KPI identity and supported long/wide schema mappings from mounted sources; preserve unknown units and counter semantics. Use logs only for a concrete bounded question.

**Rationale**: Existing frontend-blind retrieval requires sealed trace results and a restricted metric rescue, which conflicts with feature 004's independent resource investigation. Long-format resource metrics and service wide fields require explicit adapters; recording identity is not automatically called-service identity.

**Alternatives considered**: Metrics only after a slow frontend; eager all-log ingestion; matching resources by name resemblance. These hide masked faults or invent relationships.

### 11. Reproducible first comparison policy

**Decision**: Freeze the plan's limited five-minute historical/median policy, explicit support threshold, context keys, bounds and no-fallback rule before implementation validation. Preserve incompatible and unmatched structures, source qualifications and per-channel priority. Treat these as descriptive engineering defaults, not calibrated detectors.

**Rationale**: The reference contract deliberately supplies no universal statistical threshold. A concrete initial policy lets fixtures verify behavior while keeping later policy changes versioned. Unknown units, sampling gaps, constant references and contaminated history remain visible.

**Alternatives considered**: Optimize thresholds per case, pool unrelated KPIs into a global score, call historical periods healthy, or turn unsupported ratios into large scores. These undermine evidence integrity.

### 12. Shared budgets and downstream submission boundary

**Decision**: Introduce one run context, monotonic deadlines, bounded operations, case allocation and finalization reserves before substantial indexing. Count preparation once. Feature 007 adds associated hypotheses, legal answer assembly and provider/agent behavior; feature 002 retains clean-image, cost, evidence and held-out comparison requirements.

**Rationale**: Current solve calls have no shared run state, and the runner aborts on any exception. Recoverable analysis failures need typed outcomes and continued processing; storage failure remains fatal. A runnable no-call preparation milestone cannot satisfy the final nonblank answer requirement.

**Alternatives considered**: Per-case rebuilds, unconstrained background preprocessing, treating budget exhaustion as no anomalies, or waiving final submission checks to meet a development deadline.

## Research closure

Local source inspection and the earlier delegated read-only reuse audit informed the integration/technology choices for feature 004. The official-doc alignment below and the initial discovery-policy contract supersede earlier prompt-only runner/default/artifact decisions in sections 6–7. No external library/API choice or paid experiment is required for this plan. Future GLM routing and release evaluation must be planned under their owning features; they are not unresolved dependencies of deterministic preparation. See plan.md and contracts/discovery-policy.md for the initial project policy/budgets and the explicit R7–R9 roadmap. These defaults require authored-fixture validation; official documentation does not establish their detection quality.


## Official-doc alignment — 2026-09-17

Read all four official Track 1 docs pinned in source-notes.md. Final best guesses,
GLM routing/fallback, mounted-input/output boundaries and external caps remain
feature 007/002 obligations. The older prompt-only default/artifact design is
superseded by the R1–R6 executor seam. `contracts/prompt-input.md` now delegates
mode behavior to that seam and retains the pure grammar contract.

The initial policy now specifies C1 set conditioning with separate multiplicity,
qualified discovered frontend role binding, per-sample metric differences,
independent structural comparisons and display sampling after comparisons.
Those choices come from project design, not official detector guidance. Completed
replay and controlled replay of partial work are distinct from live deadline
variation. No implementation, paid experiment or policy effectiveness is claimed.
