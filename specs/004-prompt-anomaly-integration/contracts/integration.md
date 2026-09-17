# Track 1 integration contract

## Stage boundaries

The runner passes one original query identity/instruction and any optional task metadata to interpretation. Interpretation returns a supported scope or an explicit error. Only supported scopes enter discovery. Discovery consumes that scope, a source snapshot, frozen policies and remaining budgets, and returns findings/candidates or a qualified partial result. Evidence rendering joins the scope and result; final diagnosis is absent.

Use timezone-aware bounds and half-open observation-selection intervals `[start, end)`. A same-date prompt ending at 00:00 may roll into the next day only when the explicitly documented Track 1 convention yields its required 30-minute interval; otherwise require explicit consistent date information and flag unsupported scope. Expansion to complete recorded traces is independent of selection bounds and records its coverage. No prompt-extraction rule may silently repair conflicting dates, count or metadata.

| task_index (when supplied) | Ordered requested fields |
|---|---|
| task_1 | occurrence datetime |
| task_2 | reason |
| task_3 | component |
| task_4 | occurrence datetime, reason |
| task_5 | occurrence datetime, component |
| task_6 | component, reason |
| task_7 | occurrence datetime, component, reason |

Extract the instruction's projection and cross-check this mapping rather than using task_index or row_id to invent scope. Optional metadata absence does not block a fully interpretable instruction. Scope stores supporting character ranges/phrases and interpretation version; timezone supplied by the benchmark convention is labeled as convention-derived.

## Per-case output

Retain the CLI and original row-ID association. Proposed public artifact names for this integration:

- `predictions.csv`: original IDs with blank prediction strings for this milestone.
- `evidence/<row_id>.md`: Answer (diagnosis pending), Confidence (discovery qualifications; no calibrated diagnosis probability), Evidence (actual observations and scope), Ruled out (only supported exclusions, otherwise none established).
- `usage.jsonl`: original ID, measured case wall time, zero calls/input/output tokens and empty models. Per-stage timing plus shared preparation accounting is reported separately; do not call a zero-duration stub measurement full investigation time.
- `cases/<row_id>/scope.json`: interpretation status, original instruction and identity, deployment/window/count/projection when valid, supporting extraction provenance, optional metadata consistency and error reasons when invalid. Unsupported scope fields are absent/null with explicit failure, not guessed.
- `cases/<row_id>/findings.json`: result status; candidate/observation/reference IDs; supported, qualified and unavailable findings; evidence locators; inspected/uninspected source families; selection/expansion coverage; policy/source versions; stage timings and stop reason. Invalid interpretation yields not_run with its reason.
- `discovery-run.json`: selected mode and policies, shared preparation identity/time, total time/budgets, original-case status inventory, shared-window associations and completion counts.

Prepared views and other temporary outputs remain beneath --out and must be declared in the run record. Never depend on the neighboring official checkout, ignored development selection files, previously sealed case artifacts, or a scope.csv register. Ship only the approved policy definitions and runtime source needed to rebuild from the supplied bundle.

## States and exit behavior

Interpretation: `interpreted` or `unsupported` with reasons. Discovery: `completed`, `partial`, `unavailable`, or `not_run`. Comparison eligibility remains the independent `eligible`/`qualified`/`unavailable` dimension from feature 003. An empty candidate list may be completed if declared discovery ran with adequate coverage; it never asserts no failure.

A fully processed run with completed cases, including qualified findings, or a valid empty query inventory exits zero. Any nonempty scope-only run remains not_run and exits nonzero. Numeric project exit codes are defined in [prompt-input.md](prompt-input.md#exit-behavior); Track 1 itself does not prescribe them. Any unsupported scope, partial/unavailable discovery or unexpected case failure produces a nonzero final exit and explicit mixed/failure status while retaining successful cases. Global malformed CSV/invalid path/nonempty output is a preflight failure before analysis. Failed output persistence terminates visibly and preserves earlier published rows; durable storage failure cannot promise a new error artifact. No in-place resume is introduced by this feature.

Per-case analysis artifacts and evidence must be persisted before publishing that case's prediction checkpoint. Interrupted/failed work is never marked completed. Best-effort cleanup cannot be described as a transaction spanning every file.

## Discovery channels and selection

[discovery-policy.md](discovery-policy.md) binds the initial selection, reference,
comparison and packet rules. These are versioned project choices; official Track 1
docs define schemas and judging obligations, not an anomaly-detection algorithm.


Trace discovery reports empirical duration departure and structural changes separately. Metric discovery reports relevant scoped resource changes independently of frontend trace selection. Targeted logs report observations answering a declared follow-up question; no log detector-training subsystem is included. Each supplied family is recorded as inspected, unavailable, or not inspected with a reason; not inspected does not mean normal.

Resource binding uses the current dataset and feature 003's typed/time-supported relationships. A mesh source/destination identity, service-to-replica mapping or shared host association remains contextual unless an exact request link exists. A candidate may reference several findings, and a finding may support several later hypotheses. Failure count does not control candidate count.

Keep priority lists per comparison channel unless a declared tested policy defines a combined ordering. Retain selected candidates, tie handling, count of unselected findings and truncation reason. Unavailable comparisons remain in the audit trail; do not serialize NaN/Infinity as strong evidence. Raw duration units retain their documented qualification until independently established.

The five-minute pooled C1 policy may seed the trace comparison only within its declared support and qualification. Do not silently transplant its three named development replicas, introduce undeclared same-replica fallback, label it healthy, or extend its median/excess claim to p95/p99 or incident sensitivity. The selected policy must be made portable and reviewed in planning.

## Compatibility and acceptance

### Inventory and operation records

Validate the governing Track 1 schema conventions against each mounted inventory before retrieval. Preserve raw source field/value and conversion policy; unsupported fields and uncertain units must be surfaced. Enumerate available KPI/resource identities instead of trusting OpenRCA's static prompt candidates. Neither a known operation name nor a naming resemblance establishes an exact resource join.

Add `cases/<row_id>/operations.jsonl` beneath --out: operation ID, question, type, bounded arguments, source/policy identity, referenced observations, coverage, timing, status and stop reason. Record rejected and unsuccessful attempts; a valid empty result is distinct from invalid arguments, missing source, failed execution or truncation. Shared prepared work is referenced rather than charged repeatedly. These records are deterministic discovery audit records, not an LLM conversation requirement. Feature 007 may append diagnosis operations with distinct IDs/stage identity while preserving the discovery records.

The default CLI advances from stub to discovery once this feature is implemented. Preserve an explicit stub agent/mode to run feature 002's empty-output regressions. Keep the existing placeholder validator strict for stub mode; add separate discovery validation that checks declared artifact sets, case coverage, provenance/status invariants and truthful non-diagnostic evidence. Discovery validation must not be presented as the official answer scorer.

All runtime data access and writes, resource limits, model endpoint restrictions if later introduced, and final release obligations remain under feature 002. The current feature is no-call and no-key. Cold preparation must be included in budget rehearsal and must not consume all available case/finalization capacity.
