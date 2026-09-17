# Feature Specification: Contextual telemetry retrieval and comparison

**Feature Branch**: `003-contextual-telemetry-evidence`

**Created**: 2026-09-17

**Status**: Specified; implementation compliance and acceptance results not established

**Input**: Record the agreed ADRs and resulting specifications for collecting comparable traces, reusable retrieval, qualified baselines, and resource relationships outside recorded traces.

## Scope and authority

An investigator needs to discover relevant unusual behavior within a supplied incident window without first knowing the fault's component or onset. This feature specifies reproducible evidence access, contextual comparison, and bounded expansion to related resources. It does not prescribe a universal anomaly threshold or establish a complete RCA system.

[ADR 0003](../../docs/adr/0003-indexed-telemetry-retrieval.md) governs reusable retrieval, [ADR 0004](../../docs/adr/0004-qualified-contextual-baselines.md) governs comparison, and [ADR 0005](../../docs/adr/0005-evidence-backed-resource-relationships.md) governs resource linkage. The [descriptive evidence specification](../001-candidate-recall-experiment/spec.md) retains its separate first experiment. The [runner specification](../002-final-demo-runner/spec.md) governs integration, runtime budgets, and submission. Existing scripts are starting points; this document does not certify their compliance.

## User Scenarios & Testing

### User Story 1 — Retrieve requests and their earlier context (Priority: P1)

As an investigator, I need requests from the supplied window and an explicitly chosen earlier interval, plus the available recorded spans for selected requests, without knowing the fault answer.

**Why this priority**: A truncated or answer-selected evidence set invalidates subsequent comparison.

**Independent Test**: Retrieve an authored corpus with interleaved records, cross-boundary traces, missing records, and deliberate identity collisions; compare against its independently authored inventory.

**Acceptance Scenarios**:

1. **Given** unsorted records and a request beginning before a partition boundary, **when** its execution is selected, **then** retrieval returns every available recorded span for it across declared partitions, including spans outside the selection interval.
2. **Given** candidate and reference time windows, **when** requests are collected, **then** candidate membership uses only scope and declared selection policy, and every selected or excluded observation has a reproducible basis.
3. **Given** an incomplete, stale, or incompatible prepared data view, **when** it is queried, **then** the investigator receives an explicit coverage limitation or a rebuilt compatible view, never a false completeness claim.
4. **Given** missing ancestry, conflicting duplicate identities, or incomplete source availability, **when** evidence is returned, **then** conflicts and limitations remain visible without guessed parents or targets.

### User Story 2 — Find departures against qualified references (Priority: P1)

As an investigator, I need a comparison that states what differs, which observations support the reference, and whether the contexts are comparable.

**Why this priority**: The prompt identifies an investigation window but leaves relevant abnormal behavior to be discovered.

**Independent Test**: Compare authored observations against independently specified reference groups, including constant, contaminated, sparse, and incompatible groups. No encoder or fault labels are required.

**Acceptance Scenarios**:

1. **Given** compatible contexts and sufficient support for the selected comparison, **when** an observation is compared, **then** the finding records the reference, absolute difference, applicable relative measures, direction, and uncertainty.
2. **Given** insufficient support, zero variation, unknown units, or context mismatch, **when** comparison is attempted, **then** it is qualified or unavailable as prescribed; no invented finite score, probability, or healthy verdict is produced.
3. **Given** an extra operation or unmatched execution shape, **when** latency cohorts are formed, **then** the observation remains available for structural comparison rather than disappearing from investigation.
4. **Given** historical and peer references that disagree, **when** candidates are prioritized, **then** the disagreement is retained and the reference is not chosen solely to maximize a desired anomaly.
5. **Given** a new baseline version, **when** comparisons are recomputed, **then** descriptive observations and earlier reference-relative results remain recoverable.

### User Story 3 — Investigate resources beyond a recorded trace (Priority: P2)

As an investigator, I need to follow supported service, endpoint, and host relationships while knowing whether each link describes an exact request or broader context.

**Why this priority**: Database and infrastructure effects can matter even when their targets have no receiver spans in the trace.

**Independent Test**: Use authored spans, service-traffic evidence, resource placement, and endpoint observations with known ambiguity and identity changes.

**Acceptance Scenarios**:

1. **Given** a database client operation with an unnamed target, **when** service-traffic evidence identifies a related resource, **then** that resource becomes an investigation candidate while the individual operation's exact target remains unresolved.
2. **Given** exact recorded span ancestry, a service dependency, placement evidence, and nearby measurements, **when** relationships are shown or traversed, **then** their kinds, temporal support, and evidentiary strength remain distinguishable.
3. **Given** endpoint reuse or multiple possible replicas, **when** resource evidence is joined, **then** the result preserves time scope and ambiguity rather than assigning one permanent identity.
4. **Given** unavailable evidence or an exhausted expansion budget, **when** exploration stops, **then** the frontier and reason remain explicit; an unvisited resource is not declared irrelevant.

### User Story 4 — Audit and reuse an investigation (Priority: P2)

As a reviewer, I need to reproduce why evidence was retrieved, compared, and expanded, and to distinguish a development example from validation.

**Independent Test**: Replay a fixed selection/comparison policy against an unchanged source snapshot, then change a source or policy and verify the resulting identities and qualifications.

**Acceptance Scenarios**:

1. Every returned observation, reference membership, comparison finding, and resource link resolves to source evidence and its governing policy.
2. Repeated queries against unchanged prepared data reuse it without reparsing full source files; results match the declared scan-based reference.
3. Reference observations are selected without expected answers. Known-label case illustrations are marked development-only and do not count as held-out detector validation.

### Edge Cases

Unsorted files; cross-midnight or long-running traces; unavailable adjacent partitions; duplicate/conflicting span IDs; shared span IDs in different deployments/traces; missing or multiple roots; partial instrumentation; unknown duration units; mixed timestamp units; late observations; start-selected references that cross the cutoff; unknown request type; changed call counts; zero median or spread; sparse tails; contaminated history; peer-wide faults; workload shifts; collection loss; ambiguous service-to-replica mappings; endpoint reuse; repeated correlated evidence; interrupted builds; changed source snapshots; multiple incidents and overlapping symptoms.

## Requirements

### Functional Requirements

- **FR-001 — Scope**: Accept deployment, query interval, requested fields, and supplied failure count independently of diagnostic answers. Gold onset/component/reason and derived answer hints MUST NOT enter collection, reference selection, comparison, or relationship derivation.
- **FR-002 — Selection and expansion**: Distinguish time-bounded request selection from retrieval of all available recorded spans for selected executions. An arbitrary time margin MUST NOT be claimed to guarantee a complete trace.
- **FR-003 — Identity and fidelity**: Preserve deployment, trace/span identity, recording component, raw values, source provenance, and measurement uncertainty. Conflicting duplicates and missing ancestry MUST remain explicit.
- **FR-004 — Coverage and reuse**: Declare prepared-source coverage, source identity, extraction version, and completion state. Reuse MUST reject incompatible or incomplete views; bounded partial coverage MUST be reported.
- **FR-005 — References**: Declare the comparison question, conditioning context, membership, time policy, permitted expansion/fallback, and estimator-specific support. Freeze them for each investigation and preserve historical, peer, and verified-success views separately.
- **FR-006 — Qualification**: Each comparison MUST report eligible, qualified, or unavailable with reasons. Typicality MUST NOT imply independently verified health/success. Constant, sparse, contaminated, and incompatible references MUST follow explicit policies.
- **FR-007 — Differences**: Preserve observation-relative and reference-relative products separately. Support relevant structural, frequency, attribute, contextual, novel-event, and missing-event findings with units, exposure, and coverage appropriate to each question.
- **FR-008 — Candidate retention**: Changed/unmatched execution shapes, isolated spikes, and unavailable comparisons MUST remain auditable. Conditional matching MUST NOT erase the behavior being investigated. Priority policy MUST retain absolute magnitude, temporal behavior, scope, quality, and conflicting evidence without treating uncalibrated scores as fault probabilities.
- **FR-009 — Relationships**: Distinguish recorded ancestry, service dependency, placement, endpoint association, and temporal association. Every derived link MUST retain evidence, rule version, observed time support, unresolved fields, and ambiguity.
- **FR-010 — Linkage limits**: A resource name, nearby timestamp, or similar identifier MUST NOT establish an exact request join without validated linkage. Unresolved targets, multiple possible replicas, endpoint reuse, and unknown placement MUST remain explicit.
- **FR-011 — Bounded exploration**: Related-resource expansion MUST use declared entity/time/volume budgets and report truncation and unvisited candidates. Additional resource telemetry MUST remain associated with the relationship that justified retrieval.
- **FR-012 — Reproducibility**: Preserve source, selection, reference, comparison, derivation, and priority versions sufficient to reproduce findings. Changes to a baseline MUST NOT rewrite descriptive evidence. Behavior onset and fault onset MUST remain separate.
- **FR-013 — Operational fit**: Measure preparation, repeated retrieval, storage, and memory separately. Runtime integration MUST comply with the runner's input/output restrictions and resource/time limits; it MUST NOT depend on a developer's prebuilt data artifacts.

### Key Entities

InvestigationScope; SourceSnapshot; RetrievalPolicy; RetrievalResult; CoverageStatement; ExecutionIdentity; Observation; ReferencePolicy; ReferenceCohort; Baseline; ComparisonFinding; PriorityPolicy; ResourceEntity; ResourceRelationship; ExpansionResult. Their planned content and invariants are in [data-model.md](data-model.md).

## Success Criteria

### Measurable Outcomes

- **SC-001 — Retrieval fidelity**: All authored retrieval cases R1–R5 return exactly the available records specified by the reference inventory, with zero invented joins and every planted conflict/coverage limitation surfaced.
- **SC-002 — Comparison validity**: All authored comparison cases B1–B6 retain the planted differences and produce the declared eligibility outcome; no deliberately unsupported comparison receives an unqualified result.
- **SC-003 — Relationship fidelity**: All authored linkage cases L1–L5 preserve relationship kind, identity, time support, and uncertainty, with zero unsupported request-level links.
- **SC-004 — Auditability**: Every observation, finding, and relationship in these acceptance cases resolves to its source and rule versions; replay preserves the same content for unchanged inputs and policies.
- **SC-005 — Reuse correctness**: Repeated retrieval against unchanged prepared data yields the same records as the scan reference without another full-source parse. Preparation and reuse costs are reported separately; no speedup is claimed without measurement.
- **SC-006 — Scope integrity**: Collection, comparison, and linkage cases pass independently of fault labels or a working diagnoser. Integration retains the existing when/where/why contract and runner limits; it does not relabel these local checks as RCA accuracy evidence.

The [acceptance matrix](acceptance.md) maps each requirement to its verification cases. These are planned acceptance criteria, not completed results.

## Assumptions

The short-window frontend specialization in [feature 009](../009-qualified-short-baselines/spec.md) and [feature 010](../010-comparative-descriptors/spec.md) refines FR-005–FR-008 and FR-012 with a selected reference profile, separate support/stability states and descriptor semantics. It does not replace this feature's broader retrieval, reference-view or resource-relationship scope.

- The supplied dataset is a recorded snapshot. Complete retrieval is relative to its declared source inventory and says nothing about unrecorded activity.
- The earlier 30-minute window, 20-reference cutoff, operation-count grouping, and robust-departure formula are exploratory choices, not universal constants. Concrete policies must be declared before evaluation.
- Current telemetry may lack route, workload, configuration, endpoint history, or success metadata. Missing context yields qualifications or unavailable comparisons.
- Static recordings do not establish when each record became available online. Retrospective, start-selected references and strict pre-cutoff comparisons require distinct claims.
- Source ingestion, reference building, comparison, and relationship derivation are independent validation targets. Implementing every modality or a new detector is not authorized by this documentation task.
- The first representation experiment and final runner retain their separate specifications. This feature is ready for implementation planning; no implementation, paid run, submission, commit, or publication is claimed here.
