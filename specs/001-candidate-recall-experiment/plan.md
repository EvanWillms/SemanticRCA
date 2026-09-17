# Plan: descriptive compression before comparison and diagnosis

**Updated**: 2026-09-17
**Status**: Planning only; no implementation or experiment result
**Specification**: [spec.md](spec.md)
**Decision**: [ADR 0002](../../docs/adr/0002-descriptive-semantic-compression.md)

## Architecture and boundaries

```text
telemetry → validated observations → descriptive evidence packet
                                         ↓
qualified reference cohort → comparison findings
                                         ↓
                 behavior interpretation / incident hypotheses
                                         ↓
                  requested incident-tuple projection
```

The arrows express data dependencies, not a mandatory serial diagnostic search. An investigator may revise when, where, and why jointly. Comparison is one possible source of evidence; neither novelty nor a behavior label is required to exist before a hypothesis can be considered.

The encoder takes observations and frozen coding/fidelity rules. It cannot take benchmark answers, healthy/fault labels, comparison thresholds, or a target diagnosis. The comparison stage takes packets, eligible reference cohorts, and comparison rules. Hypothesis generation takes evidence and scope, with explicit uncertainty. Changing one policy does not silently rewrite another stage's output.

Use the existing audited CSV sources for later data grounding. The immediate fixture experiment needs only a small local deterministic encoder/decoder and human-readable output; no production pipeline, model call, paid service, Docker build, or full-day scan. No new runtime or library choice is required in this documentation revision.

## Independently falsifiable assertions

Independence means each claim can be tested with authored or separately checked inputs; it does not mean statistical independence. All assertions start **not tested**.

| ID | Assertion | Isolated evidence and measurement | Falsifier / limit |
| --- | --- | --- | --- |
| A1 | Symbols make equivalent observed structure comparable while preserving a difference. | Three authored graphs and a fact sheet fixed before encoder implementation; structural matching and exact fact recovery. | Renaming changes structure, entity distinctions vanish, or an extra operation disappears. Fixture success is not production validity. |
| A2 | Timing, identity, and observation quality survive coding. | Separate fixtures changing one parent, replica, interval, status interpretation, or retrieval boundary at a time. Check independent fact sheets. | Invented serial order, target, success, duration unit, or absence; lost changed fact. |
| A3 | Compression reduces representation size at equal required fidelity. | Independently prepared correct packets and normalized controls; fixed factual questions, bytes, then actual model tokens if a tokenizer is available. | Fact loss or no size advantage after metadata. Does not require A1's encoder to work. |
| A4 | A secondary comparator identifies descriptive differences using eligible context. | Hand-authored packets/cohorts covering six difference types and invalid success/coverage claims. | Wrong context creates an unconditional anomaly; missing evidence becomes missing behavior; reason labels enter inputs. |
| A5 | An LLM can use the packet to answer specified comparison questions efficiently. | Frozen independently validated packets, same model/questions, raw and normalized controls, repeated runs and known answers. | Worse factual accuracy, unsupported conclusions, or no token/time benefit. Model/routing/thresholds require a separate preregistered plan. |
| A6 | Multimodal evidence aligns without invented corroboration. | Authored trace/metric/log observations with known IDs/clocks, conflicts and duplication. | False join, double counting, erased conflict, or missing channel presented as agreement. |
| A7 | Temporal behavior descriptions have defensible meaning beyond single faults. | Frozen literature-grounded definitions and independently annotated multi-request/controller episodes, including negative examples. | Reviewers cannot distinguish observed behavior from hypothesized mechanism, or recognizer fails clear cases. No taxonomy novelty assumed. |
| A8 | Evidence helps diagnose benchmark incidents. | Held-out incident groups, gold available only to evaluation, fair numerical/normalized controls. Measure requested when/where/why and field association. | No reliable improvement or leakage; shortlist recall cannot stand in for full diagnosis. |

A1 is the next experiment. A2–A8 are a research backlog, not simultaneous implementation work. A correct authored packet can test A3/A4/A5 even if the encoder fails; integration remains blocked on any required failed assertion.

## First experiment: three traces, one difference

**Question**: Can a frozen descriptive code preserve the same execution structure across incidental changes while retaining one added operation?

Create a synthetic seven-span trace with declared millisecond timestamps/durations and these observed parent links:

```text
frontend#1 request.handle
├─ checkout#1 cart.get
│  └─ cart#1 cart.get
│     └─ cart#1 db.hget
├─ catalog#1 catalog.get_product
├─ catalog#1 catalog.get_product
└─ catalog#2 catalog.get_product
```

These are synthetic recording components and parent links. They do not establish RPC roles or the DB target. Two catalog spans use the same entity, and the third uses a distinct entity. The repeated siblings may share a structural template; instance bindings and counts must survive. Raw synthetic records contain verbose operation names and opaque IDs, mapped by a fixed small codebook. All business outcomes are unknown.

Prepare before implementing the encoder:

- **T0**: the seven-span trace above, explicit intervals, stable context, and a manually reviewed fact sheet.
- **T1**: T0 with trace/span IDs bijectively renamed and source records shuffled. Entity identities, operation meanings, measurements, and graph remain unchanged. Expected structural equivalence and all facts are recorded in advance.
- **T2**: T0 with a fourth catalog child bound to `catalog#1`, with its own declared timing. Expected difference: catalog count 3 → 4, total span count 7 → 8, exactly one added child under the root; existing observations stay unchanged.

Freeze the codebook, pattern definition, equivalence policy, fixture hashes, and fact sheets before seeing encoded outputs. The fact sheets come from authored graphs, not a second invocation of encoder logic. Keep expected answers out of encoder inputs.

Run a single proposed encoder; expand its packet without consulting raw records. Check operation identities, parent edges, counts, and entity equality/distinctness against the independent sheet. Compare T0/T1 by graph structure with scoped aliases, not byte equality of provenance. Check T0/T2 yields the specified delta without deleting or rewriting existing facts. Source links and raw-ID mappings must resolve separately.

**Acceptance**: all contracted structural facts in all three fixtures recover exactly, T0/T1 match, and T2's extra child/count remain distinguishable. Unknown or omitted required facts fail this unambiguous fixture gate. A constant labeler fails the contrast check. Any failure is reported with the first differing fact; do not compensate with a diagnosis score.

**Output**: a compact report with the three graphs, codebook, packets, fact comparisons, size accounting, and the bounded conclusion. Report bytes descriptively, but do not require tiny fixtures to show a compression advantage or infer model savings. Stop after A1; do not automatically run the other experiments.

## Later checks, separately scoped

A2 adds one-variable contrasts for changed parent, serial versus supported overlap, same versus different replica, changed duration, unresolved parent, truncated retrieval, mixed raw status, and unknown units. Precision must permit any claimed temporal distinction. It also checks version compatibility and exact provenance. A3 then measures a repeated-pattern corpus against raw CSV and a compact normalized graph under the same fidelity contract; count dictionary/setup overhead both cold and amortized, recording the reuse population.

A4 uses independently supplied packets for novel, missing, structural, frequency, attribute, and contextual differences. A cohort known only as typical must stay so. Include a completed-but-incorrect business operation and a trace outside injected-fault windows to challenge unsupported successful-reference selection. It does not require a real successful cohort to exist.

After those local checks, separately annotate a small, label-free sample of actual traces against the frozen definitions. The [trace audit](../../docs/research/track-1-trace-audit.md) supplies source constraints, not truth about success or behavior classes. Record exposure and sampling bias. Raw-annotation disagreement challenges meaning; encoder disagreement with clear annotations challenges extraction. Do not use fault gold to settle either.

A5–A8 require new scoped plans before implementation. Behavior episodes may span requests, resources, and controllers; a per-request trace packet alone cannot establish them. The final diagnostic adapter must pass the [incident contract](contracts/incident-diagnosis.md), including two-incident projection, before a benchmark result is claimed.

## Governance and traceability

The [evidence contract](contracts/semantic-evidence.md), [data model](data-model.md), [design basis](research.md), and [validation guide](quickstart.md) are active. The [old integration plan](deferred-candidate-recall.md), deferred data/research/quickstart files, and [old CLI](contracts/experiment-cli.md) are historical. The [label-validation plan](superseded-label-validation.md) is superseded, not a prerequisite.

Constitution 1.0.2 check: evidence/provenance and bounded access are explicit; reproducibility and independent references are required; incident and final output obligations are retained. Scope exception: routed versus single-model evaluation, full unseen-case diagnosis, Docker, and submission artifacts belong to later integration, since the user requested an isolated representation experiment. Owner: project maintainer. Follow-up: generate separate integration tasks and verify those obligations before any submission-complete claim. This documentation change neither implements nor submits an agent.

Requirement coverage: A1 covers FR-001/003/005/010; A2 covers FR-002/003/004/006/012; A3 covers FR-005/011; A4 covers FR-002/007/008; the later consumer check and A8 cover FR-009. A5–A7 extend the thesis without being assumed by A1. Generate implementation tasks only for A1 next; no tasks or tests were executed in this revision.
