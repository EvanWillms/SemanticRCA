# Descriptive semantic evidence contract

**Version**: design v1, 2026-09-17. Planned logical contract; no implemented serializer or encoder is claimed.
**Authority**: [ADR 0002](../../../docs/adr/0002-descriptive-semantic-compression.md), [specification](../spec.md).

## Layers and inputs

| Product | Allowed meaning | Required support |
| --- | --- | --- |
| Descriptive observation | Observed operation, relation, measured attribute, count, coverage | Source records and frozen extraction definitions |
| Structural pattern occurrence | A reusable arrangement instantiated with entity and measurement bindings | Pattern definition, occurrence membership, expansion rules |
| Comparison finding | Difference from a qualified contextual reference | Observation IDs, cohort, comparison policy, uncertainty |
| Behavior interpretation | A temporally extended behavior under an operational definition | Supporting and contradicting observations, temporal scope, recognition rule |
| Diagnostic hypothesis | Proposed incident time, component, and reason | Evidence links, inference, alternatives and uncertainty |

The encoder accepts observations, context, and coding/fidelity policies. No `scoring_points`, gold tuples, reference-relative anomaly thresholds, or expected diagnostic answers enter it. Learned extraction rules, if introduced later, require a separate training/exposure policy. A raw error/status is an observation; declaring it an error or successful operation requires a producer-specific interpretation. A descriptive rule may transform observations but must identify that transformation.

## Packet envelope and dictionaries

Each packet declares:

- `packet_id`, schema/codebook/extraction/fidelity/equivalence policy versions, and input/source fingerprints.
- Scope: execution/trace or episode, deployment, entity namespace, time interval, absolute anchor, clock and precision information. A trace is not an incident; an episode can span many traces.
- Context: operation, environment, deployment/code version, input/workload class, cache state, concurrency, and code region **where available**. Each unavailable field is unknown or unavailable, never fabricated. Comparators specify which fields matter for their question.
- Operation dictionary: stable ID, definition, valid source mappings, raw-name distinctions, and mapping provenance. Known wrapper aliases require explicit rules; unrecognized names remain distinguishable as opaque operations. Do not collapse every unknown operation into one symbol.
- Entity bindings: scoped alias, original identity and namespace, role/service/node/replica mappings with evidence or unresolved state. One source identity has one binding in scope; distinct identities remain distinct. Cross-packet comparison uses explicit bindings and preserves original identity in provenance.
- Observation quality: retrieval filters/boundaries, scanned/indexed coverage, unresolved ancestry, deduplication/conflicts, sampling/instrumentation limits, and completion state. Completed retrieval does not prove complete instrumentation.
- Declared retained questions/facts, omitted information, decoding dependencies, and links to the provenance sidecar.

Version changes that alter meaning cannot silently reuse symbols. A comparison either applies a documented migration or reports incompatible versions. Display aliases may vary; semantic equality is evaluated under the declared equivalence policy and bindings.

## Span facts and relations

A span fact binds `id`, `trace`, `recording_entity`, `operation`, `parent_reference`, relative start, duration, type, status, and provenance. Parent resolution is explicitly `root_marker`, `resolved`, `unresolved`, or `conflicting`. Preserve conflicting duplicate records; do not choose one silently. Empty type, zero duration, and raw status strings are valid observations.

Timing includes raw values, units, conversion evidence, resolution, and clock uncertainty. Unknown duration units permit raw-duration comparisons only under an explicitly compatible producer context; they do not permit derived end times. Relative starts retain their absolute anchor for correlation and later fault-onset reasoning. Overlap or order finer than the known precision remains indeterminate. Source-file order is not execution order.

Relations distinguish observed parent references, explicit trace links, supported temporal relations, and inferred interactions. The retained graph MUST NOT convert siblings into a total order merely to serialize them. Parent links and temporal precedence do not prove causality. Collapse of apparent caller/receiver spans requires validated instrumentation semantics and preservation of the original observations; it is outside the first experiment.

An `HGET` observation recorded by a cart component does not establish a Redis target identity. A `payment.charge` observation does not establish payment success. A trace outside a query window does not establish successful business execution.

## Patterns, repetition, and fidelity

A pattern defines operations and relationships using role variables. An occurrence binds those variables to observed entities and supplies span membership, measurements, timing, status, quality, and evidence. Pattern recognition in v1 is an explicit structural match, not automatic discovery or a reliability-behavior diagnosis.

Illustrative notation below is explanatory, not an implemented serialization. All numbers and evidence keys are synthetic:

```text
PATTERN cart_read/v1:
  x: SPAN operation=cart.get entity=$caller
  y: SPAN operation=cart.get entity=$cart PARENT=x
  z: SPAN operation=db.hget  entity=$cart PARENT=y

OCCURRENCE p1 pattern=cart_read/v1 parent_of_x=s0
  bind: $caller=checkout#1, $cart=cart#1
  spans: [s1,s2,s3]
  start_offsets_ms: [2,3,4]
  durations_ms: [8,6,1]
  raw_statuses: ["0","0","Ok"]
  status_interpretation: unknown
  business_outcome: unknown
  evidence: [synthetic:r2,synthetic:r3,synthetic:r4]

REPEAT operation=catalog.get_product parent=s0 count=3
  members: [s4,s5,s6]
  entities: [catalog#1,catalog#1,catalog#2]
  start_offsets_ms: [12,16,20]
  durations_ms: [2,2,3]
  evidence: [synthetic:r5,synthetic:r6,synthetic:r7]
```

The full packet also contains the envelope, root, raw type/status facts for every member, and dictionary definitions. `cart_read` names observed structure, not health, retry intent, or cause. The pattern definition cannot assert an interaction role merely because its variables are named caller/cart; these names are illustrative roles, with observed recording components authoritative.

The initial fidelity policy preserves operation identity, graph edges, exact counts, identity equality/distinctness, available timing/precision, raw type/status, quality, and evidence links. Repeated groups retain member identities, timings, and relations to observations outside the group so interleaving remains recoverable. Repetition alone does not imply retries; retry semantics require additional correlation/attempt evidence.

A repeat cannot be represented only as `count=200` if the contracted question concerns serial/parallel behavior, retry intervals, distinct participants, or a long-tail duration. Replacing member values with quantiles is a different, explicitly lossy fidelity policy. Record which questions it no longer supports, and retain a way to retrieve detail without calling the packet lossless.

## Three separately measured sizes

1. **Model-visible payload**: serialized packet plus required dictionaries, definitions, context, and reference data supplied to the model. For independent calls count cold overhead; for reuse report the declared amortization population as well.
2. **Supporting storage**: provenance sidecar, indexes, dictionaries, and retained raw records, with shared storage distinguished from per-packet storage.
3. **Expansion/retrieval cost**: bytes/tokens fetched, runtime, and extra calls needed to answer questions not retained in the packet.

The decoder used for the fidelity check may use included/shared declared dictionaries but cannot consult raw records to answer retained questions. Raw records are available separately to audit evidence. Compare against raw CSV and a compact normalized graph with the same fidelity; stripping IDs/formatting alone must not be credited as proof that higher-level symbols helped. Byte reduction, tokenizer reduction, and model cost/accuracy are separate findings.

## Secondary comparison

The detailed selection, qualification, and difference rules are specified by the [baseline contract](../../003-contextual-telemetry-evidence/contracts/baselining.md). [Collection](../../003-contextual-telemetry-evidence/contracts/collection.md) supplies recorded-source coverage, and [resource relationships](../../003-contextual-telemetry-evidence/contracts/resource-relationships.md) distinguish exact ancestry from contextual associations. These are separately planned capabilities, not prerequisites added to the first representation check.

A reference cohort records selection rule and version, compatible context, members, sample counts, allowed structural variants, attribute/count distributions, and eligibility limitations. Successful-reference eligibility additionally requires independently established outcome criterion, verifier/source, scope, and result; it is not inferred from the encoder or absence of faults. Unknown success supports a reference/usual cohort, not a successful one.

Each finding records a kind, observed fact IDs and values, reference cohort/version, comparison rule/version, context compatibility, uncertainty, and evidence. Kinds are:

| Kind | Question | Guard |
| --- | --- | --- |
| Novel event | Is this operation absent from the eligible reference vocabulary? | Unrecognized parsing is not proof of novel system behavior. |
| Missing event | Is an expected observation absent after its observation interval is complete? | Require expectation and sufficient coverage; otherwise mark unobserved/unknown. |
| Structural change | Did a parent, branch, link, or participant relationship change? | Compare compatible roles without erasing actual identity. |
| Frequency change | Did count/rate change? | Include exposure/window length, input/workload size, and reference variation. |
| Attribute change | Did duration, intensity, or a measured value change? | Compatible units, precision, producer semantics, and context. |
| Contextual mismatch | Does behavior disagree with the context's expected variants? | Unknown context qualifies or prevents the judgment. |

For example, the packet may retain `catalog.get_product count=200`. A separate finding may state the reference count distribution and a frequency deviation under policy v1. Neither record establishes retry amplification, failure, or originating cause. If the reference selection or threshold changes, recompute the finding without rewriting the descriptive observations.

## Diagnostic consumption

The [incident contract](incident-diagnosis.md) governs when/where/why outputs. Preserve observed onset intervals separately from inferred fault occurrence time; exact component identities separately from service-role aliases; and temporal behavior descriptions separately from the organizer's fault-reason vocabulary. Findings may be shared evidence for multiple incident hypotheses. Uncertainty remains visible in evidence even when the final benchmark answer requires a best guess.
