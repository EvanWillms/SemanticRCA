---
status: accepted
date: 2026-09-17
---

# Interpret errors through scoped mappings and preserve outcome boundaries

The audited Track-1 export mixes numeric and textual statuses, including `0`, `200`, `OK`, and `Ok`. The official data guide acknowledges nonuniform fields but provides no complete producer-specific error mapping. Its 15 injected-fault reasons are diagnostic categories, not status meanings. The nine trace columns do not include an exception message, retry-attempt identifier, or business-success verifier.

## Decision

1. Preserve the raw status string and its recording entity, raw operation/type, available producer/version context, and source pointers. Represent interpretation as `reported_error`, `reported_non_error`, `unknown`, or `conflicting`, with a mapping ID/version and supporting evidence. Unknown is an explicit value, not an omitted result or implicit success.
2. Apply a mapping only within its supported producer context. Record its exact applicability predicate and source. Familiar protocol codes and `type=http` alone do not establish the exporter’s semantics. Synthetic mapping fixtures must never become real-data mappings by default.
3. Keep span-reported error, enclosing-request outcome, business success, and benchmark incident separate. A handled child error may coexist with verified request success. Record the outcome criterion, scope and verifier; neither absence of error nor span completion verifies business success.
4. Keep extraction-quality errors separate from service error evidence. Missing parents, conflicting duplicates, malformed records, and unknown units describe evidence limitations; they do not establish a failed service. Preserve conflicting indicators rather than silently selecting a winner.
5. If error fractions are produced, retain mapped/unmapped counts, denominator policy and mapping coverage. Unknown spans are not successes. Multiple caller/receiver reports are not automatically independent failed requests or initiating faults.
6. Permit LLM descriptions of supported error evidence under [ADR 0010](0010-faceted-semantic-labeling.md). Unsupported meanings stay hypotheses or unknown. Log-based symptom normalization requires separately retrieved and linked log evidence; do not invent absent trace fields from operation names.

## Alternatives and consequences

A nonzero-is-error rule would misclassify familiar textual and numeric nonzero values. Treating every child error as request failure would erase handling/recovery boundaries. Using benchmark labels to resolve intermediate status meanings would leak a diagnostic answer into extraction.

Conservative interpretation will yield unknowns until mappings are established. This is measurable missing knowledge, not evidence of health. Real-data error precision/recall is unavailable for the current selected traces because no independently verified positive error ground truth has been established. Raw status preservation can still be tested exactly.

## Evidence and validation

The [trace audit](../research/track-1-trace-audit.md) reports 29 operation names and eight statuses for its March 20 source, versus the guide's summary of 27 and four. Inventories therefore remain source-versioned observations, not fixed runtime cardinalities. The [re-grounded proposal](../research/reliability-taxonomy-review.v1/06-selected-trace-semantic-encoding-experiment.v1.md) records the official guide's identity and unresolved mappings.

The [incremental handoff](../research/reliability-taxonomy-review.v1/07-incremental-experiments-handoff.v1.md) defines S06's unknown/mapped-error/mapped-non-error/handled-child-error controls and S09's isolated LLM check. These establish testable contracts, not completed validation. This decision refines ADRs 0002 and 0009 without changing final benchmark best-guess obligations under ADR 0007.
