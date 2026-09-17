# Standalone deterministic trace semantics

The caller supplies a collection of traces already selected as fault related.
This library describes their recorded evidence; selection and diagnosis belong
to the caller. It performs no retrieval, model calls, anomaly detection, or
benchmark classification.

## Public boundary

Proposed for confirmation: `partition_traces(traces, policy)` returns accepted
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

## Acceptance

Authored public-boundary tests exercise mixed known/unknown evidence, exact raw
recovery, duplicate/conflict handling, cross-trace identity isolation, missing
parents/cycles, malformed input, units and status abstention, deterministic
serialization and independent installation. Existing repository tests remain a
regression check. Review every new code file and fix actionable findings.
