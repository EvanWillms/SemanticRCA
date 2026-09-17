# Deterministic executor data model

Design only; fields below extend the existing QueryRow/Solution seam. Schema version: `discovery-v1`. All IDs must be stable from source/rule identity and canonical content, excluding elapsed time and run UUIDs.

| Entity | Fields and validation | Relationships |
|---|---|---|
| QueryRow | Original unique integer row_id, exact instruction, optional task_index | One InterpretationResult per row |
| InterpretationResult | interpreted/unsupported, parser version, instruction hash/text, errors, extraction ranges; scope only if supported | Scope includes deployment, aware UTC+8 half-open 30-minute interval, positive failure_count, canonical ordered requested_fields |
| ExtractionSupport | Field, zero-based half-open Unicode character range, exact excerpt, or named benchmark convention | Each scope value has support; metadata only cross-checks |
| SourceSnapshot | Deployment, allowed source paths/content hashes, schema/conversion versions, file/record counts, completion, missing/rejected inventory | Shared across compatible scopes; no labels or prior answers |
| RecordedObservation | ID, snapshot, modality, logical identity, raw fields/units, normalized values where supported, time precision, source locators, independent coverage/identity/graph/timing flags | Trace identity includes deployment and trace ID; span identity adds span ID; all duplicates/conflicts preserved |
| SourceLocator | Dataset-relative path, source digest, logical CSV record number (header=1), optional raw field | Resolves each fact to immutable source; physical lines are separate |
| ResourceRelationship | Kind, participants, supported time interval, evidence IDs, qualifications | Distinguishes ancestry, dependency, placement, endpoint and temporal association; recording identity is not automatically target |
| ReferenceCohort | ID, frozen policy/context, observation IDs, eligibility, support/coverage, exclusions, estimator and qualifications | Historical/query memberships kept separate; typical does not mean healthy |
| ComparisonFinding | Observation/cohort IDs, channel, raw/reference values, signed difference, unit, eligibility, limitations | eligible/qualified/unavailable; undefined ratios/scores null with reason, never NaN/Infinity |
| Candidate | ID, finding IDs, observed interval, resource, channel-specific priority/tie rationale, truncation | Candidate count independent of failure_count; not an incident or diagnosis |
| OperationRequest | ID, stage, question, declared operation name, bounded args, source/policy IDs, motivating observation IDs, limits | One terminal receipt for every attempt, including rejected requests |
| OperationReceipt | Status, result IDs, coverage, elapsed work, scanned/returned/withheld counts, stop reason, continuation, last completed batch and recorded stop decision | Distinguishes valid empty, invalid args, missing source, failed, truncated and budget exhaustion |
| CaseDiscoveryResult | row_id, interpretation, findings/candidates/relationships, stage statuses, source-family coverage, operation references, timings, stop reason | Each case retains its original projection/count even when work is shared |
| RunContext/Record | Monotonic limits, pending cases, reserve, policy versions, prepared handles, shared-work ledger, case status inventory | Initialized once; no global mutable policy or per-case re-indexing |
| Solution extension | Existing prediction/evidence/usage plus optional structured case result and explicit case status | OutputWriter owns persistence; missing extension leaves explicit stub unchanged |

## States

Interpretation: pending → interpreted or unsupported. Unsupported interpretation prevents telemetry access and yields discovery not_run.

Prepared view: absent → building → complete; failure/interruption → incomplete. Only complete views with matching content and extraction identity can be reused. A stale view is rebuilt or rejected, never treated as current.

Discovery: pending → running → completed / partial / unavailable / not_run. Completed requires every operation required by the declared capability to finish; a scope-only slice records full discovery not_run. An empty candidate list alone says nothing about status or absence of fault.

Case publication: pending → sidecars/evidence/usage durable → prediction checkpoint published. Failure before publication preserves prior published rows; an orphan sidecar does not certify completion. Recoverable analysis failure proceeds to later rows; writer failure aborts visibly. No cross-file transaction or resume guarantee is implied.

## Invariants

Raw observation meaning does not change with a comparison or diagnostic hypothesis. Reused evidence is not independent corroboration. Reference selection never consults gold onset/component/reason. Partial coverage and unresolved targets survive every downstream serialization. Usage for this feature is measured local wall time, models={}, and zero model calls/tokens. Shared work is recorded once, not repeated as each case's work.
