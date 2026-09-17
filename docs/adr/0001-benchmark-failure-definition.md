---
status: accepted
date: 2026-09-17
---

# Define failure by the Track 1 benchmark contract

**A failure is a labelled incident in the supplied benchmark, represented by its occurrence time, root-cause component, and fault reason.** Occurrence time is the fault's start time. The complete SymbolicRCA deliverable reconstructs those incidents from telemetry and explains its evidence; the first experiment tests only whether the correct component reaches the shortlist.

## Basis for the decision

- The [Track 1 README](../../../hackathon-2026-official/track-1/README.md) supplies telemetry and a set of failures, and asks for start time, responsible component, and cause.
- The [data guide](../../../hackathon-2026-official/track-1/docs/data.md) establishes that operators injected and labelled faults in an instrumented microservice system. Each query supplies a 30-minute window and the number of failures; task types request different subsets of diagnosis fields.
- The [scoring contract](../../../hackathon-2026-official/track-1/docs/scoring.md) requires the supplied failure count, exact recorded component and reason strings, and recorded onset within 60 seconds when requested. Its documented example identifies `shippingservice-1` with `container read I/O load`. It does not additionally require proving a customer-visible outage or SLO breach.

## Boundary and consequences

MantisGrid's [public product description](https://www.mantisgrid.ai/) (checked 2026-09-17) describes user-defined quality, reliability, performance, and cost outcomes and detection of deviations from those contracts. Interpreting failure as relative to required business or workload outcomes is a broader product interpretation; that page does not supply a universal formal failure definition or threshold. We do not import that interpretation as an extra benchmark eligibility or scoring rule.

We therefore reject requiring independent outage or SLO-breach detection before diagnosing a supplied incident. Fault labels establish what must be diagnosed; they remain evaluator-only and are not ranking inputs. Telemetry supports the inferred diagnosis and its explanation, not a new decision about whether the designated incident counts as a failure.

Component recall@1/@3 measures only a necessary stage of diagnosis. A successful shortlist experiment does not demonstrate correct onset, fault reason, complete incident reconstruction, or a completed submission. Full diagnosis and evidence obligations remain in the [SpecKit goal](../../.specify/memory/constitution.md); the bounded experiment is specified in [experiment 001](../../specs/001-candidate-recall-experiment/spec.md).
