---
status: accepted
date: 2026-09-17
---

# Separate label meaning, production method, and evidential support

The taxonomy review supports a faceted representation, not a mandatory hierarchy of reliability classes. “Deterministic versus LLM” describes how a claim is produced; “descriptive versus interpretive” describes what it asserts. Neither executable rules nor fluent model output establish causal truth.

This extends [ADR 0002](0002-descriptive-semantic-compression.md). Accepted status records an architectural decision; it does not establish empirical encoding or labeling quality.

## Decision

- Give every derived claim a semantic layer, production method (`code`, `llm`, or `human`), definition/version, scoped evidence references, limitations, and validation state. Record evidence strength separately from method. Observed, derived, hypothesized, and intervention-supported claims must remain distinguishable; model-generated confidence is not a calibrated probability.
- Use deterministic extraction for raw fields, scoped identities, recorded parent references, exact counts, identity equality/distinctness, quality flags, and supported timing calculations. Codebook aliases require explicit, versioned mappings; unknown operation names remain distinct.
- Make signed parent–child start offsets a required feature of the selected-trace timing experiment. Preserve same-emitter versus cross-emitter qualification. Timestamp subtraction does not require a duration-unit assumption; derived endpoints do. The official guide motivates edge timing for network investigations, but offsets are not pure network transit time or a network-fault verdict. [ADR 0009](0009-track1-trace-extraction.md) governs units and extraction.
- Permit an LLM to describe supplied facts and propose evidence-linked interpretations. Its annotations are separate records: they cannot rewrite measurements, resolve unknowns without evidence, or silently change the codebook. Proposed aliases remain proposals until reviewed and versioned.
- Describe reliability behavior using separate temporal-form, mechanism, participant/relation, regime/outcome, and evidence facets. Do not require every trace to have a behavior or mechanism label. Repetition alone is not retry; a parent edge alone is not causation; one request generally lacks the population/controller evidence for oscillation, synchronization, recovery cycles, or metastability.
- Keep organizer fault-reason vocabulary in the diagnostic layer under [ADR 0007](0007-evidence-backed-incident-diagnosis.md). It is not an observation vocabulary or a forced classification target for the encoder.

## Alternatives and consequences

A single flat label combines observations, hypotheses, and provenance too early. A rule-versus-model enum alone fails to express what either producer has actually established. A six-level hierarchy confuses participant scope with temporal complexity and mechanism. The selected design requires more metadata but makes disagreements and unsupported promotions auditable.

The initial representation is structured and inspectable, not a vector embedding. Embedding retrieval needs its own objective and evaluation. Automatic pattern discovery and continuous behavior recognition are deferred. No taxonomy novelty, causal capability, compression advantage, or model benefit is claimed.

## Evidence and validation

The [taxonomy synthesis](../research/reliability-taxonomy-review.v1/04-candidate-synthesis.v1.md) supplies the faceted design; the [dataset-grounded review](../research/reliability-taxonomy-review.v1/06-selected-trace-semantic-encoding-experiment.v1.md) maps it to available fields. Four inspected development traces demonstrate available structure/status/timing facts, not validated labels. [ADR 0012](0012-incremental-semantic-validation.md) governs testing; its initial structural experiment and later timing/LLM slices have no results yet.
