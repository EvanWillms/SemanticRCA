---
status: accepted
date: 2026-09-17
---

# Compress observations into descriptive symbols before comparison or diagnosis

We will represent telemetry as versioned descriptive symbols with execution relationships, measured attributes, observation quality, and source provenance. Comparison against contextual reference cohorts and diagnosis of benchmark incidents are separate derived products. This makes equivalent executions comparable without encoding the expected anomaly or fault answer into their descriptions.

The immediate thesis is **a multimodal symbolic evidence layer for efficient, explainable infrastructure root-cause analysis**. The longer direction is continuous recognition of emergent reliability behaviors from fused telemetry. Neither thesis is established by this decision; the first experiment tests the representation prerequisite on traces.

## Decision

1. **Give symbols stable meanings.** A versioned codebook maps validated instrumentation observations to operation/event meanings. A semantic token is a structured domain symbol, not necessarily one LLM token. Unknown operations and unresolved meanings remain explicit. Operation names do not certify business outcomes.
2. **Preserve execution relationships.** Describe the observed span graph and supported temporal relations. Distinguish recording component, service, replica, node, and inferred target. A parent reference alone proves neither a network call nor causality. Retain identity equality and distinctness when replacing opaque identifiers with scoped aliases.
3. **Separate reusable structure from measurements and provenance.** A pattern describes operations and relationships; an occurrence binds entities, timing, counts, statuses, context, and source records. Relative time has an absolute anchor and precision. Unsupported duration units or status interpretations remain unknown.
4. **Compress repetition under a declared fidelity contract.** Reuse operation dictionaries and structural patterns; retain multiplicity, participants, ordering/interleaving, and per-occurrence measurements required by the contract. A distribution or quantized value is a declared lossy summary. Access to raw records does not make a lossy packet lossless.
5. **Keep judgments typed and separate.** `cart_read(count=200)` is descriptive; a frequency deviation requires a reference and comparison policy; a retry storm or causal diagnosis requires additional evidence. Descriptive records are not rewritten when thresholds or diagnostic hypotheses change.
6. **Qualify references and missingness.** Compare compatible contexts and distributions of allowed variants. Call a cohort successful only when independent outcome verification supports that claim at the stated scope. Distinguish unobserved data from an observed absence using retrieval coverage, instrumentation limits, and window completion.
7. **Preserve the benchmark diagnostic contract.** An investigation scopes a window; each incident has an associated `(occurrence_time, component, reason)` tuple; each task requests a projection. Evidence can support several hypotheses or remain unassigned. A span start, behavior boundary, or deviation onset is not automatically the injected fault's onset. Multiple incidents retain separate field associations.

## Trade-offs and alternatives

Free-text summaries are readable but make equivalent behavior and omitted detail difficult to compare reproducibly. Flat operation sequences discard nesting and can invent an order between concurrent work. Direct anomaly or fault labels compress aggressively but bake the comparison or diagnosis into the input being tested. Opaque learned codes may be useful later, but do not satisfy an inspectable meaning contract on their own.

The chosen representation costs more metadata and codebook maintenance. Dictionary and provenance overhead may exceed savings for short traces. Its benefit must therefore be measured against both raw records and a simple normalized representation at equal fidelity; symbolic naming alone is not evidence of compression or LLM usefulness.

## Consequences and validation

The [active specification](../../specs/001-candidate-recall-experiment/spec.md) and [evidence contract](../../specs/001-candidate-recall-experiment/contracts/semantic-evidence.md) define the representation. The [plan](../../specs/001-candidate-recall-experiment/plan.md) separates semantic fidelity, size reduction, comparison validity, LLM use, multimodal fusion, and diagnosis into independently falsifiable assertions. Only a three-trace equivalence/contrast check is the next experiment; no implementation or empirical success is implied.

This supersedes earlier first-experiment scheduling (candidate recall and then direction-versus-level labels), while retaining the failure definition in [ADR 0001](0001-benchmark-failure-definition.md). Benchmark output rules are recorded in the [diagnostic contract](../../specs/001-candidate-recall-experiment/contracts/incident-diagnosis.md). The [trace audit](../research/track-1-trace-audit.md) constrains interpretation of actual data; the [taxonomy review](../research/reliability-behavior-taxonomies.md) grounds the distinction between behavior, mechanism, and fault. No novelty claim is made for symbolic temporal recognition or behavior classification.
