# Feature Specification: Descriptive semantic compression for execution comparison

**Feature Branch**: `001-candidate-recall-experiment` (retained for continuity)
**Updated**: 2026-09-17
**Status**: Design specified; implementation and experiments not run
**Input**: Compress noisy telemetry into meaningful symbols that support comparison, then diagnosis; test the representation without assuming labeling succeeds.
**Decision**: [ADR 0002](../../docs/adr/0002-descriptive-semantic-compression.md)

## Goal and scope

Represent equivalent observed execution consistently while preserving enough context to explain differences. Descriptive symbols encode observations and relationships; comparison findings and diagnostic hypotheses remain separate. The full research direction covers multimodal, temporally extended reliability behavior. This feature starts with trace structure, measured attributes, and evidence quality.

The next experiment is deliberately small: one synthetic trace, one equivalent renamed/reordered copy, and one copy with an extra operation. It tests one prerequisite: equivalent structure remains comparable while a known difference survives compression. It does not test fault recognition, general behavior recognition, successful-run classification, LLM usefulness, or diagnostic accuracy.

The later Track 1 consumer identifies requested fields of `(occurrence time, component, reason)` within a bounded window. Prompt scope does not supply diagnostic evidence. See the [incident contract](contracts/incident-diagnosis.md). Representation design must support this consumer without importing its answer labels.

The separate [contextual telemetry evidence specification](../003-contextual-telemetry-evidence/spec.md) now details collection, qualified references, and external-resource relationships under ADRs 0003–0005. It extends the later comparison/investigation boundary and does not enlarge this feature's first representation experiment.

## User Scenarios & Testing

### User Story 1 — Compare equivalent execution descriptions (Priority: P1)

As a researcher, I need equivalent observed operations and relationships to remain comparable despite changes in trace IDs, span IDs, or record arrival order.

**Independent test**: Encode a known trace and a bijectively renamed, shuffled copy using a frozen vocabulary; compare their structure under explicit entity bindings.

**Acceptance scenarios**:

1. Given the same observed graph with different incidental IDs, encoding preserves the same operation meanings, parent relationships, multiplicity, and identity equality/distinctness.
2. Given one additional child operation, its count and parent remain visible; the changed trace does not collapse into the same description.
3. Given different actual replicas, a common role pattern may match, but original replica identity remains available for context and exact component diagnosis.

### User Story 2 — Inspect what compression retained (Priority: P1)

As a researcher, I need to answer specified factual questions from the packet and inspect the source behind each answer.

**Independent test**: Use authored graphs and independently written fact sheets, including nested, overlapping, ambiguous, and incomplete observations.

**Acceptance scenarios**:

1. Every retained operation, edge, count, and measurement maps to source observations and a versioned extraction rule.
2. Expanding a structural pattern recovers its contracted facts; any omitted or quantized facts are declared.
3. Incomplete retrieval or unknown status semantics remain unknown. The packet does not infer success, causal order, or an absent operation from unavailable evidence.

### User Story 3 — Compare with a qualified reference (Priority: P2; separate experiment)

As an investigator, I need differences interpreted against relevant reference executions and their allowed variation.

**Independent test**: Compare hand-authored valid packets and reference cohorts; no working encoder or fault labels are needed.

**Acceptance scenarios**:

1. A frequency difference records observed count, reference distribution, context, and comparison policy without changing the descriptive observation.
2. A reference known only to be typical is not called successful. Verified success states its criterion, scope, and independent verification source.
3. The same count may be expected for a large batch and unusual for an interactive request; absent context produces a qualification or no comparison.
4. A missing expected event and unavailable instrumentation produce different findings.

### User Story 4 — Support incident diagnosis without pre-labeling evidence (Priority: P3; later integration)

As a diagnostic consumer, I need to link supporting and conflicting evidence to separate incident hypotheses and return the requested fields.

**Independent test**: Use supplied hypotheses and evidence links to check a two-incident projection without running an encoder or diagnosing real faults.

**Acceptance scenarios**:

1. Time, component, and reason remain associated with their incident when projecting or reordering answers.
2. Evidence may support multiple hypotheses or remain unassigned; the requested failure count does not force a partition of observations.
3. An observed behavior onset is not relabeled as fault onset without an explicit diagnostic inference.

### Edge cases

Concurrent siblings; interrupted or interleaved repeats; repeated work without retry evidence; same operation recorded at caller and receiver; different replica bindings; missing parents and conflicting duplicate IDs; partial windows and out-of-order records; unknown units and mixed status encodings; sparse or missing instrumentation; unavailable success/context metadata; two incidents with overlapping effects; incompatible codebook versions.

## Requirements

### Functional Requirements

- **FR-001 — Stable meaning**: Symbols MUST use versioned definitions and validated observation mappings. Unknown meanings MUST remain explicit and distinguishable through raw evidence. A token need not be one model token.
- **FR-002 — Typed separation**: Descriptions, reference-relative findings, behavior interpretations, and diagnostic hypotheses MUST be separately identifiable. Updating a comparison policy MUST NOT alter the base observation meaning.
- **FR-003 — Identity and structure**: Preserve observed parent/link relationships, entity equality/distinctness, service/replica/node distinctions, and supported partial order. Do not invent targets, network edges, or causal relationships.
- **FR-004 — Measurement fidelity**: Preserve contracted counts, timing anchors, precision, duration units/uncertainty, raw statuses, and outcome scope. Measured values and inferred interpretations MUST remain distinguishable.
- **FR-005 — Pattern compression**: Reusable patterns and repeat groups MUST retain contracted occurrence bindings, multiplicity, interleaving, and outliers. Declare omitted information and any quantization or distribution replacement.
- **FR-006 — Provenance and quality**: Each descriptive assertion MUST resolve to evidence and its extraction/coding versions. Retrieval scope, instrumentation limits, missingness, and contradictory records MUST remain visible.
- **FR-007 — Contextual reference**: Comparison MUST declare cohort selection, context compatibility, allowed variation, and reference versions; successful cohorts require independent success verification with scope and source.
- **FR-008 — Findings**: Novel, missing, structural, frequency, attribute, and contextual differences MUST identify the observations and reference supporting them. Novelty or deviation alone MUST NOT assert causation.
- **FR-009 — Diagnostic compatibility**: Retain original component identities and temporal anchors for later incident tuples. Requested-field projections MUST preserve incident associations and uncertainty in evidence. Gold answers MUST be excluded from encoder, reference selection, and diagnostic inputs.
- **FR-010 — Falsifiability**: Each assertion MUST have an independently established reference, declared comparison questions, and a falsifier. Record all outcomes, including failures and unknowns; no downstream score can substitute for representation validation.
- **FR-011 — Honest efficiency**: Measure representation size separately from fidelity, including dictionaries and metadata. Distinguish bytes, actual model tokens, retrieval overhead, runtime, and full storage; no cost or LLM claim follows from symbol count alone.
- **FR-012 — Evolution and scope**: Version the fidelity and equivalence policies. Incompatible meanings MUST require an explicit migration or a refused comparison. Cross-trace episodes and additional modalities are separate extensions, not assumptions of the trace experiment.

### Key Entities

Descriptive symbol; operation definition; observed span relationship; entity binding; structural pattern and occurrence; evidence packet; provenance record; observation-quality statement; fidelity contract; reference cohort; success verification; comparison finding; behavior interpretation; incident hypothesis and requested projection; assertion result.

Detailed planned fields are in [data-model.md](data-model.md) and the [semantic evidence contract](contracts/semantic-evidence.md).

## Success Criteria

- **SC-001 — Equivalence and contrast**: On the three-trace first experiment, the two equivalent inputs match under the frozen structural equivalence policy, while the extra operation's exact count and parent are recoverable in the third. All independently specified structural facts agree; zero invented or omitted contracted facts are permitted.
- **SC-002 — Quality preservation**: A separate ambiguity/missingness check preserves every planted unknown, contradiction, and coverage limitation, with zero unsupported success or causal assertions.
- **SC-003 — Measured compression**: A separate size experiment reports raw, normalized, and symbolic sizes at equal declared fidelity, with zero contracted fact loss. A compression benefit is supported only where symbolic size is smaller than the normalized control including required decoding metadata; otherwise report no demonstrated benefit.
- **SC-004 — Valid secondary comparison**: A separate hand-authored comparison check accounts for all six difference classes in FR-008 and refuses or qualifies every deliberately ineligible reference. Successful-reference claims all have independent verification.
- **SC-005 — Consumer integrity**: A later projection check covers all seven task types and preserves both incidents' field associations for two-incident cases. It is an output-contract check, not a diagnosis result.
- **SC-006 — Reviewable outcomes**: Each experiment reports its own evidence, denominators, errors, unknowns, and limitations. A falsified representation is a valid research outcome and is not promoted to downstream use on the failed assumption.

## Assumptions

Only SC-001 is the next experiment. Other criteria define separate planned checks and do not enlarge that experiment. The audited real trace supplies interpretation constraints, not verified success labels. Synthetic observations have declared units and meanings; real telemetry must earn those mappings. The design assumes no production success oracle, annotated behavior corpus, or proven LLM benefit. Historical experiments are preserved in [the deferred integration plan](deferred-candidate-recall.md) and [the superseded label plan](superseded-label-validation.md).

## Featherless annotation extension

[ADR 0015](../../docs/adr/0015-featherless-trace-semantics-and-prefix-caching.md) and [feature 008](../008-featherless-trace-semantics/spec.md) specialize the later A5 model study. This feature retains FR-001–006's deterministic fact and equivalence contract: GLM annotations are separate, versioned, evidence-linked records and cannot erase execution variability or change the packet. FR-011's size claim remains separate from provider cached-input savings.

The immediate [P01 model study](../008-featherless-trace-semantics/minimal-test.md) uses sanitized S01 fixtures across 18 attempts; the separate S09 status study retains its own 18-attempt boundary. It does not expand the original A1/S01 experiment or establish integrated fidelity. Applicable intermediate fidelity gates remain required before real encoder output is promoted to model consumption. Acceptance evidence belongs to feature 008 SC-001–005; no model benefit follows from this specification alone.
