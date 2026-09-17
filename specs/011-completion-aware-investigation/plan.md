# Implementation plan: semantic traces into RCA investigation

Status: planning in progress; public TDD seams awaiting user confirmation.

## Objective and ownership

Deliver a separately installable RCA domain library that accepts semantic encoded
traces, preserves their evidence and uncertainty, and drives the completion-aware
investigation loop in this feature. The library must execute an end-to-end
semantic-packet → evidence → assessment → bounded operation → reassessment →
result flow, not just define value objects or reimplement a trace encoder.

Use `libraries/rca_domain`, Python standard-library runtime dependencies and an
independent test suite. Do not modify `libraries/trace_semantics`, which currently
contains a producer scaffold, or assume that producer is implemented. Do not
change the submitted runner's default agent. Provider clients and telemetry
operations are injected boundaries; no paid model calls are needed for acceptance.

## Proposed public boundaries

The TDD skill requires confirmation before tests are written. Confirmation has
been requested for these two boundaries:

1. `from_semantic_traces(...)`: translate supplied versioned semantic packets,
   definition/provenance information and case scope into an evidence packet.
2. `investigate(...)`: take that evidence packet, an assessor, a declared operation
   executor and a work policy; return the retained answer, evidence, assessment
   history, usage and explicit terminal outcome.

Public immutable value types support these calls. Concrete signatures and adapter
schemas will be frozen before parallel implementation. Neither boundary reads
raw files, labels or a remote provider implicitly.

## Evidence handoff

Inspect actual producer formats before choosing adapters. Existing inputs include
S01's `s01-normalized-v1` packets with operation dictionaries and evidence IDs,
and P01's symbolic/normalized request payloads with packet-local evidence IDs.
P01 payloads do not carry a standalone schema/codebook identity; their adapter
must receive explicit format and versioned definitions rather than guessing the
positional field order or importing the experimental runner.

Evidence identity includes deployment, packet/source identity, trace and original
record reference. Parent/span IDs are trace-local. Preserve recording component,
symbol and raw operation, raw times/status, units, coverage and unknowns. A symbol
is descriptive, never a reason-vocabulary selection, retry assertion, request
success or root cause. Source references remain pointers to supplied evidence;
an evidence ID alone is not verification of its underlying raw file.

Validate unsupported versions, definition mismatches, malformed references and
conflicting identities explicitly. Duplicate observations must not manufacture
independent corroboration. Input validation must not mutate caller-owned packets.
The adapter does no baseline selection, anomaly detection or retrieval.

## Investigation and finalization

Implement the existing loop contract with one assessor and one operation at a
time. Validate evidence references, legal incident fields/count and current
evidence revision before accepting completion. Assess semantic adequacy through
explicit supported/contradicted/gap judgments; code checks cannot prove causality.

Declare allowed operations and their scope; reject unavailable/out-of-scope work
before execution. Preserve failed/empty/rejected results and every charged
attempt. Enforce the three-operation/four-assessment toy profile, one bounded
repair/retry, non-progress detection, and finalization reserves. Clock and external
call boundaries must permit deterministic timeout/budget tests. A callback that
ignores timeouts must not be presented as a hard execution guarantee; planning
must choose a cancellable boundary or narrow the runtime guarantee explicitly.

Return structured outcomes with stop reason independent from adequacy and
execution status. Feature 007 controls legal best-guess assembly. Finalization
uses retained state and a frozen deterministic fallback over caller-supplied legal
choices, never an additional live generation call. Unsupported guesses remain
qualified and cannot invent evidence or established independent incidents.

## Parallel TDD and review

After seam confirmation and shared contract freeze, use Luna (`gpt-5.6-luna`,
`xhigh`) workers for disjoint vertical slices: semantic ingestion and bounded
investigation. Each worker records a failing public-boundary test, then the
minimal implementation, one behavior at a time. A separate integration slice
proves that real encoded fixture packets reach the assessor and final result.

Review every new production module, test, example and packaging file in this
task. Pin the review baseline to current HEAD
`fd49fbc98fc96b89552e2e7df95e74fac024a220` and an explicit file inventory: the
library is initially absent and unrelated uncommitted work predates this task.
Standards and spec reviews run independently in parallel, followed by TDD repairs
and a current-file hash inventory. User authorization covers review of all code
in this task; it does not imply modifying unrelated concurrent work.

## Verification and completion evidence

- Authored adapter fixtures verify provenance, definitions, unknowns, identity
  isolation and preservation of raw values.
- Loop trajectories cover L01–L18, including initial sufficiency, useful follow-up,
  rejected completion, false blocker, repetition, malformed assessments, provider
  failure and hard resource stops. Any unsupported trajectory remains incomplete.
- A public end-to-end example starts with actual semantic encoded data, not a
  manually fabricated post-adapter state.
- Copy and install the package independently, then execute the example outside
  this repository. No imports from experiments, agents or `rca` are permitted.
- Run repository regressions and targeted producer experiment regressions.
- Resolve actionable findings from both reviews and reconcile requirements to
  exact tests and current source files before claiming the goal complete.

## Constitution and coordination

This follows the existing specification before planning/tasks/implementation and
preserves evidence-first reasoning, query bounds, cost accounting and blind
evaluation. Offline fixtures establish library behavior, not held-out accuracy.
Record task-local artifacts explicitly rather than changing the shared branch or
`.specify/feature.json` while other agents work. The earlier branch hook failed
on read-only Git metadata. The user subsequently authorized semantic commits at
meaningful checkpoints; commit only this task's explicitly owned paths and keep
other agents' staged changes out of each commit. Publication and a default runtime
switch remain outside this work.
