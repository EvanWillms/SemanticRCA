# RCA domain API design

Status: public seams follow the user-defined input/output objective; technical decisions for
implementation, not existing code. This refines [investigation.md](investigation.md).

## Public calls and ownership

`from_semantic_traces(envelopes, scope) -> EvidencePacket`

`investigate(evidence, assessor, operations, answer_policy, work_policy) -> InvestigationResult`

The package `rca_domain` owns immutable domain values, ingestion, bounded call
execution, assessment gating and deterministic answer selection. The repository
adapter owns `solve`, interpreting instruction text, telemetry retrieval, provider
configuration and output persistence. There is no runtime import from the package
back into `rca`, `agents` or experiments.

`Scope` contains case ID, deployment, inclusive incident-time bounds expressed as
UTC+8 datetimes, requested projection and positive incident count. Invalid scope
configuration fails before callbacks. Recorded traces can cross the incident
window; retaining their context is not a claim that every span occurred inside it.

## Supported semantic inputs

Two explicit envelopes are planned; the adapter never guesses positional fields.
The primary input is the actual standalone producer's `trace-description-v1`
output. The domain package accepts serialized data without importing the producer:

1. `format = s01-normalized-v1`: the actual S01 packet plus its provenance
   sidecar. Validate matching source digests, codebook/policy version identities,
   trace/deployment context, entity/symbol lookups, count membership and every
   node's evidence pointer. Resolve symbols from the supplied codebook. Raw row
   digests may be checked against reconstructed raw records; this does not verify
   a source file the library has not read.
2. `format = trace-description-v1`: an envelope with caller-supplied packet identity
   and a producer description with matching `schema_version`. Require `policy`,
   `meaning_dictionary`, `traces`, `deferred` and `counts`. Policy `version` agrees
   with the dictionary, and `operation_mappings` supplies exact raw-name meanings.
   Each trace retains deployment/trace identity, `raw`, `coverage`, physical
   `evidence`, logical `nodes`, `edges` and `counts`. Evidence retains producer
   `evidence_id`, raw row, locator and record. Nodes reference that evidence through
   `occurrences`, with explicit conflict/count information. Preserve all top-level
   and trace-local deferred facets, their evidence references and original raw data.

The exact native serialized example is a T04 artifact to publish before T05.
Native observations can retain missing/ambiguous/cyclic ancestry as qualifications;
unsupported topology must not become a resolved edge. S01 remains a restricted
compatibility adapter, not the definition of general supported evidence.

The earlier proposed `rca-semantic-v1` input is replaced by this actual producer
schema; do not implement the redundant producer format. Producer `coverage`
currently counts records, occurrences and conflicts; retrieval qualifications
such as `recorded_recovery` may instead live in retained trace `raw`. Preserve
both and never interpret counts as complete retrieval or instrumentation.
Deferred items may lack deployment; resolve them through scoped evidence
references and retain ambiguous association as a qualification.

Validate semantic meaning against policy, occurrence membership against raw
evidence and edge endpoints against scoped nodes. Keep arbitrary finite-JSON
locators as opaque provenance, separately qualifying missing snapshot or physical
record identity. A locator or digest-looking string does not verify a source file.

P01 and S02–S09 are not implicitly accepted. Their future adapters need separately
versioned schemas and provenance contracts. This excludes unversioned payloads,
not the general semantic-evidence-to-investigation flow.

Unsupported/malformed envelopes produce explicit ingestion issues retaining the
offending input and unaffected valid envelopes. Invalid caller scope/policy is a
configuration error. A conflicted record cannot contribute reliable support merely
because its reference exists; raw conflicting records remain inspectable.

## Evidence snapshots

Deep-copy and freeze every nested input at entry; immutable domain objects cannot
expose writable dictionaries or lists through properties or serialization. Returning
a fresh JSON-compatible copy is permitted. Callback inputs are detached snapshots.

Evidence identity is scoped by deployment, source snapshot, trace and record
locator; producer evidence IDs are retained as aliases within their packet.
The same identity and same content is one observation with multiple aliases.
Different content under the same identity is an explicit conflict, not another
independent corroborating observation.

Increment evidence revision on newly accepted evidence, newly established coverage
or conflict information. Pure failures, repeated content and rejected requests
do not change revision. Every operation attempt is still appended to history.
An assessment cites the exact revision it saw. A changed revision invalidates
an earlier completion assessment until reassessed.

## Assessment and operation protocols

`Assessment` contains decision enum, assessed revision, draft incident tuples,
support/contradiction references per tuple, causal explanation, alternatives with
their disposition and references, typed material gaps, and proposed action or
blocker. Adequacy is an explicit enum, not a confidence number.

The controller checks shape, reference resolution/scope/conflicts, current revision,
answer-policy legality, required explanations, and unresolved material gaps.
The assessor owns causal entailment and whether alternatives are adequately
addressed. Code must not claim independently to prove those judgments.

Each declared operation has an ID, validated arguments, supported scope and the
gap categories it can address. A blocker must inventory remaining material gaps
and explain why available matching operations cannot resolve them, citing earlier
attempts where applicable. Reject a blocker that ignores an untried declared
matching operation. Semantic suitability remains inspectable assessor judgment.

An operation returns observations through the same evidence validation boundary,
coverage updates, limitations, outcome, transient-failure flag and usage. Exactly
one operation is selected per assessment. A transient retry requires another
assessment decision, counts as another operation attempt, and is permitted once
for that request; it does not bypass reassessment or non-progress accounting.

## Enforced callback boundary and resource accounting

Use a spawned child process for each external assessor or operation callback.
Callables must be importable/pickleable with JSON-compatible domain inputs and
results; invalid call configuration is rejected before dispatch. No unbounded
in-process fallback is permitted. The parent waits only until the admitted call's
timeout/deadline, terminates then kills a non-cooperative child if needed, and
performs bounded cleanup. Timeout/cleanup reserves are part of the work policy.
The implementation must prove this with a non-cooperative callback acceptance test.

The work policy fixes maximum assessment/operation attempts, per-call timeout,
cleanup time, finalization reserve, maximum elapsed time and optional conservative
cost bounds per callback. Admit an operation only if time/cost and one assessment
slot remain for reassessment plus finalization. Charge the reserved upper cost
bound on dispatch; report actual usage separately and retain unknown usage as
unknown. A reported lower usage value cannot authorize work beyond the frozen cap.

At most one correction/retry follows a failed assessment while global capacity
remains. Malformed returns and invalid decisions consume assessment attempts.
Permanent operation failure cannot be repeated unchanged. Rejected requests
consume operation attempts. The default global limits remain four assessments,
three operations and two consecutive non-progress operations.

Event precedence: validate caller configuration first; at work admission check
hard deadline/reserve and counters before dispatch. On callback return, check
deadline before accepting the result, then callback success, then result validity.
A result received at or after the deadline cannot establish completion. Once a
terminal event is accepted, later callbacks cannot reopen the case. Final assembly
failure is recorded separately from that first investigation stop reason.

## Answer policy and finalization

`AnswerPolicy` supplies exact legal component and fault-reason vocabularies,
deterministic tie ordering and optional caller-authored fallback incident tuples.
Scope supplies requested fields/count and time bounds. These inputs are available
before any provider work; they are not labels or per-case archived answers.

Retain legally valid assessed incident selections first. Fill unsupported required
selections deterministically from legal fallback tuples, then a documented stable
selection over allowed identities/reasons and the scope start time. Respect the
requested count/projection and preserve tuple association. If repeated guesses
are needed, explicitly mark their distinctness as unsupported, never invent
independent evidence. Inferred fault time is distinct from observed span timing.

If a requested field has no legal value, record `no_legal_answer` and failed
assembly. Otherwise provider failure cannot justify blank output. Format/status
legality does not promote evidence adequacy. Returned `InvestigationResult`
contains incident selections, qualifications, stop reason, assembly outcome,
evidence/history snapshots and usage. The package does not persist files itself.

## Review obligations

The schema and planning audits found these decisions missing; implementation
must prove them through confirmed public boundaries. T04 still needs exact native
examples/value signatures, and no production code or tests have been written.
Keep the requirement matrix honest if an integration capability remains missing.
