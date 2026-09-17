# Standalone deterministic trace semantics

## Delivery checkpoints

The user subsequently prioritized "ready to demo as soon as possible" and
"minimal happy-path with only core TDD coverage." The current checkpoint
therefore accepts the public two-stage API on complete authored Track-1 records
with string identifiers, exact blank-string root markers and a caller-declared
operation/unit policy. Acceptance is one nonempty executable demo plus the
focused core test suite. The broader requirements below remain the domain
library's target; review gaps are explicit follow-up work, not demo blockers.

The user subsequently explicitly requested continuing the remaining library
work. The authored demo remains available on the shared branch. Completion of
this follow-up requires addressing the documented correctness and efficiency
gaps against the requirements below; demo success alone is not full acceptance.
The follow-up is isolated on `fix/trace-semantics-robustness` so concurrent
fixture-demo work remains independent.

The caller supplies a collection of traces already selected as fault related.
This library describes their recorded evidence; selection and diagnosis belong
to the caller. It performs no retrieval, model calls, anomaly detection, or
benchmark classification.

## Public boundary

`partition_traces(traces, policy)` returns accepted
facts and deferred items before `describe(partition)` creates a description set.
`encode_traces(traces, policy)` composes both stages. Deferral is at the facet or
record level: an unknown operation meaning must not suppress a recorded parent
reference or raw duration. A malformed trace must not prevent unrelated valid
traces from being processed.

## Requirements

1. Preserve every supplied JSON record, its locator, trace context and coverage.
   Repeated records remain recoverable; distinct span occurrence counts must not
   increase for identical copies. Conflicting identities have explicit deferrals.
2. Scope identity and parent lookup to a trace within its supplied deployment.
   Missing, ambiguous, self-referential and cyclic ancestry must not be promoted
   to resolved execution structure. Preserve the original parent references.
3. Use only caller-supplied, versioned operation definitions. Preserve raw
   operation/type/component/status values; unmapped meaning is deferred.
4. Never infer retry, business success, request failure, target service or root
   cause. Unknown status interpretation remains unknown. Timing conversion is
   permitted only with explicit supported units; preserve original values.
5. Deferred items identify the affected evidence, facet, stable reason and raw
   data needed by a downstream processor. They are available after partitioning
   without constructing the final description set.
6. Descriptions preserve multiplicity, distinct recording identities, observed
   graph links and per-occurrence measurements. Stable versioned symbols and
   deterministic serialization are reproducible for the same supplied evidence.
   Sorting evidence must not invent temporal or causal order.
7. Empty input returns an empty result. Invalid policy is a clear caller error;
   malformed evidence produces explicit deferral without losing other traces.
8. The package installs and runs independently with the Python standard library,
   without imports from `rca`, `agents`, experiments or repository data paths.

## Interpretation details

Inputs are finite JSON-compatible values. Malformed records within that domain
are preserved and deferred; arbitrary Python objects, cycles in Python
containers, NaN and infinity are outside the transport contract and produce a
clear caller error. Numeric strings such as `"NaN"` remain raw evidence and
yield a timing deferral.

A logical occurrence is an unambiguous span identity within its supplied trace
and deployment. Exact raw duplicates with different locators support the same
occurrence. Different raw rows for one span identity are conflicting evidence,
not additional known occurrences. Physical records, resolved occurrences and
conflicting identities must have separate counts.

Unit declarations belong to the encoding policy applied to the collection;
source context remains retained evidence. A caller with incompatible source
unit conventions must partition its input by policy. The library must not
silently replace an explicitly contradictory source declaration. A versioned
operation mapping is a caller-supplied interpretation, not independently
verified instrumentation semantics.

Determinism means identical supplied evidence and policy produce identical
serialized descriptions. It does not claim graph isomorphism, equivalence of
different locators or identifiers, or a total execution order. Whole input trace
objects are retained so callers can recover extra fields and original ordering.

## Acceptance

Authored public-boundary tests exercise mixed known/unknown evidence, exact raw
recovery, duplicate/conflict handling, cross-trace identity isolation, missing
parents/cycles, malformed input, units and status abstention, deterministic
serialization and independent installation. Existing repository tests remain a
regression check. Review every new code file and fix actionable findings.

## Final three-step scope

The user then requested wrapping up with only the three most material steps:
(1) finish the current partition identity/evidence/parent-link fixes,
(2) finish description validation and context qualifications, and
(3) verify, commit and hand off the isolated branch. Further hardening and
additional capabilities are deferred; this does not establish diagnostic
accuracy, telemetry authenticity, compression savings or production readiness.
