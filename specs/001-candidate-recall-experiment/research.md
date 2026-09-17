# Design basis: descriptive compression and secondary comparison

**Updated**: 2026-09-17. This records the design basis, not experimental findings. The [older integration research](deferred-research.md) remains historical.

## Existing evidence

- The [actual trace audit](../../docs/research/track-1-trace-audit.md) establishes that source rows are instrumentation spans with mixed raw status strings, incomplete type values, out-of-order storage, and uncertain duration semantics. Parent links include local nesting and plausible caller/receiver pairs; a graph cannot be interpreted as a service-call sequence without further evidence.
- The audited 37-span trace has no unresolved parent in its retrieved records, but this does not prove complete instrumentation or successful business execution. Its placement outside declared query windows does not establish a healthy reference.
- The [taxonomy synthesis](../../docs/research/reliability-behavior-taxonomies.md) supplies primary-source grounding for emergent misbehavior, distributed control, metastability, infrastructure interdependence, and chronicle/episode recognition. Behavior descriptions, triggers, sustaining mechanisms, and root causes must remain distinct. No new taxonomy is claimed here.
- The official [data guide](../../../hackathon-2026-official/track-1/docs/data.md) and [scoring guide](../../../hackathon-2026-official/track-1/docs/scoring.md) define requested incident fields and exact output constraints. A prompt supplies investigation scope; telemetry supplies evidence; scoring points supply evaluator-only expected answers.

## Decisions encoded

| Decision | Rationale | Alternative / consequence |
| --- | --- | --- |
| Versioned descriptive symbols before comparison | Stable meanings permit reference changes without relabeling observations. | Direct anomaly tokens mix facts and judgments. |
| Graph structure and scoped identity bindings | Preserve parent relationships and replica distinctions across incidental ID changes. | Flat strings or bags lose structural differences. |
| Patterns plus occurrence measurements | Reuse common structure without hiding counts, timings, or participants. | A single behavior label can discard the evidence needed to distinguish mechanisms. |
| Explicit unknowns, quality, provenance | Current source semantics do not justify universal status/error/success or duration interpretations. | Forced interpretation manufactures certainty. |
| Contextual distributions and independent success verification | Successful executions can vary; typical execution can fail silently. | One canonical sequence or absence of errors is an unreliable success definition. |
| Separate fidelity, size, and LLM checks | A readable or short symbol is not proof of useful compression. | End-to-end diagnostic accuracy alone cannot identify which representational assumption held. |
| Trace-first isolated test | Test comparability and a retained difference without fault labels. | The earlier candidate-recall test bundled too many assumptions; the direction/level fixture missed the structural compression thesis. |

## Open empirical questions and ownership

No outcome verifier for real traces is assumed available. Until one is identified and checked, reference cohorts are described as contextual/typical, not successful. Producer-specific operation/status semantics and authoritative duration metadata remain data-audit questions. Pattern frequency and size break-even, LLM interpretability, multimodal alignment, behavior-recognition validity, and diagnostic improvement each need separate evidence.

The project maintainer owns resolving these before promoting the affected assertion to integration. None blocks documenting the design or running the synthetic A1 fixture test with explicitly authored meanings. Follow the [plan](plan.md) for scoped tests and the [evidence contract](contracts/semantic-evidence.md) for handling unresolved values.
