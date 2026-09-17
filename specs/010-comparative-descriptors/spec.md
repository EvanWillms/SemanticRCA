# Feature Specification: Reference-relative comparative descriptors

**Feature Branch**: Not created; the repository hook was attempted and Git metadata was read-only. Specification identity is independent of the checkout.

**Created**: 2026-09-17

**Status**: Specified for implementation planning; production compliance not established

**Input**: Translate the short-window report into comparative-descriptor-specific ADRs and specifications.

## Scope and authority

Produce inspectable comparisons of frontend root duration and recorded direct-child structure. [ADR 0014](../../docs/adr/0014-reference-relative-comparative-descriptors.md) defines the decision. [Feature 009](../009-qualified-short-baselines/spec.md) owns reference selection and qualification; this feature consumes those results without changing membership. Feature 003 retains authority over broader contextual comparisons and retrieval.

The primary duration product is the reference median and signed excess. A parallel C0 structural comparison preserves information lost by C1 conditioning. Anomaly classification, severity, diagnosis, onset estimation, service-level objectives, tail estimates, resource metrics, and service-operation baselines are outside scope. The [evidence ledger](../009-qualified-short-baselines/evidence.md) connects research findings to requirements.

## User Scenarios & Testing

### User Story 1 — Inspect a measured duration difference (Priority: P1)

As an investigator, I need the observation, reference and difference together so I can understand what the comparison actually establishes.

**Why this priority**: A bare rank or score hides magnitude and reference meaning.

**Independent Test**: Use fixed references and independently calculated positive, negative and zero differences.

**Acceptance Scenarios**:

1. **Given** a 100 ms reference median, **when** a 120 ms observation is compared, **then** the descriptor reports 120 ms, 100 ms and +20 ms with the baseline identity and qualifications.
2. **Given** the same reference and an 80 ms observation, **when** comparison runs, **then** −20 ms remains in the complete result population.
3. **Given** an observation above a supported but unstable median, **when** the descriptor is rendered, **then** it states the arithmetic difference and instability without implying statistical significance or a fault.

### User Story 2 — Retain partial and unavailable outcomes (Priority: P1)

As a consumer, I need unavailable fields and comparisons distinguished from zero-valued results.

**Why this priority**: Degenerate references and support failures must not create false certainty or erase usable measurements.

**Independent Test**: Exercise constant, zero, sparse and incompatible-unit references.

**Acceptance Scenarios**:

1. A supported constant 10 ms reference and 12 ms observation yield +2 ms; an optional MAD-derived score is unavailable because MAD is zero.
2. A supported zero reference and 12 ms observation yield +12 ms; ratio and MAD-derived score are unavailable.
3. Unsupported references or incompatible units retain raw observations and available structural evidence, with an explained unavailable numerical comparison.
4. Supported references that fail the stability screen retain qualified numerical differences and the failed screen state.

### User Story 3 — See structural differences (Priority: P1)

As an investigator, I need recorded operation presence and multiplicity compared independently of duration eligibility.

**Why this priority**: Conditioning on an exact observed shape can hide requests whose shape has changed.

**Independent Test**: Author added/removed operations, count changes, unknown retrieval, and recovered empty structures.

**Acceptance Scenarios**:

1. A request with no matching C1 cohort remains visible against the eligible C0 reference population, including reference pattern frequencies and denominators.
2. A count change with unchanged operation presence retains the same C1 context and a separate multiplicity difference.
3. Unknown structure cannot become an empty set or an assertion that an operation disappeared.
4. Multiple reference patterns remain identifiable; no pattern is silently designated the expected business route.

### User Story 4 — Review and reproduce comparisons (Priority: P2)

As a reviewer, I need compact views to resolve to complete evidence and reproducible definitions.

**Independent Test**: Build a complete comparison population, generate review views, change a baseline version and challenge source references.

**Acceptance Scenarios**:

1. A top-five positive-excess view preserves deterministic ordering and qualifications while all negative, zero and unavailable outcomes remain accessible.
2. A changed baseline creates a new descriptor version without rewriting the observation or old comparison.
3. Compact labels resolve to the exact observation, reference evidence and calculation; stale, wrong-entity or wrong-statistic references are rejected.
4. Repeated requests across windows remain identifiable as shared observations rather than independent incidents.

### Edge Cases

Zero median/MAD; negative or nonfinite duration; provisional versus incompatible units; unsupported or unstable reference; tiny median and large ratio; signed negative excess; rounding near zero; tied ranks; unseen versus unknown structure; multiple reference patterns; zero structural denominator; count changes within C1; repeated window occurrences; changed source snapshots; missing or misleading evidence pointers.

## Requirements

### Functional Requirements

- **FR-001 — Input authority**: Consume versioned observations and baseline outcomes from the declared policy. Descriptor generation MUST NOT alter membership, lookback, replica pooling, context or support rules to obtain a comparison.
- **FR-002 — Duration semantics**: Preserve observed duration, reference median and signed excess `observation − median` in compatible declared units at working precision. Sign states arithmetic ordering only; display rounding cannot change it.
- **FR-003 — Field availability**: Represent availability per field, distinguishing not requested from undefined or unsupported. Optional ratio requires a positive median; an optional standardized departure requires positive MAD and a named definition. No epsilon, infinity, substituted zero or inferred probability is permitted.
- **FR-004 — Qualifications**: Propagate support, center stability, units, source coverage, pooling, reference health and other applicable qualifications. Supported unstable centers remain qualified descriptive comparisons. Unsupported references cannot become supported through rendering or ranking.
- **FR-005 — Semantic labels**: Define and version every compact label. Above/below/equal-to-median labels express arithmetic relations only and resolve to the full descriptor. No normal, anomalous, healthy, faulty, significant or probability claim follows from the comparison alone.
- **FR-006 — Complete outcomes**: Retain an outcome for every selected request, including negative/zero differences and unavailable comparisons with reasons. Preserve raw measurements and structural evidence when numerical comparison is unavailable; unavailable is not zero.
- **FR-007 — Structural comparison**: Compare recorded sets and multiplicities against identified eligible C0 reference patterns before C1 matching. Preserve pattern frequencies, known-structure denominators and unknown counts. Finite reference absence is not system novelty; unknown structure is not an empty set or an inferred missing operation.
- **FR-008 — Review views**: Provide a reproducible top-five view of positive signed excess in duration units, descending with scoped identity as the tie-break. Retain qualifications and complete outcomes. This view does not establish severity, operational importance, incident count or a common score across descriptor families.
- **FR-009 — Provenance and revision**: Resolve descriptors to exact observation/measurement evidence, reference membership, baseline statistics, qualification evidence and calculation versions. Reject incompatible or misdirected references. New baselines produce new descriptors while prior observations and comparisons remain intact.
- **FR-010 — Aggregation**: Preserve observation, occurrence, descriptor-field and cohort denominators separately. Report availability and structural unknowns, reconcile complete populations and identify overlapping windows. Multiple descriptors do not establish multiple faults.
- **FR-011 — Independent validation**: Validate arithmetic, structure, availability, preservation and evidence resolution against independently authored controls. A codebook, encoder, anomaly library, language model, diagnoser or fault labels are not prerequisites for these acceptance checks.

### Key Entities

ComparativeDescriptor; DurationComparison; StructuralComparison; FieldAvailability; DescriptorQualification; ReviewView; EvidenceReference. The [descriptor contract](contracts/descriptors.md) defines their meanings without prescribing storage or transport.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All D01–D04 cases retain exact expected arithmetic, field availability and reference qualifications, with zero unsupported anomaly or stable-center claims.
- **SC-002**: All D05–D07 cases preserve the planted structural differences and frequencies, with zero conversions of unknown structure into known absence.
- **SC-003**: All D08–D10 cases preserve complete populations, deterministic views, reconciled denominators and immutable earlier comparisons.
- **SC-004**: Every accepted descriptor in D11 resolves to the correct observation, statistic and governing evidence; every planted invalid reference is rejected.
- **SC-005**: D12 validates descriptor semantics independently of diagnosis and records control coverage without claiming operational detection accuracy.

The [acceptance matrix](acceptance.md) maps every requirement. Existing research controls are prior evidence, not completion of this feature's acceptance criteria.

## Assumptions

- The initial profile covers frontend root duration and recorded direct-child structure only. Other measurement families require their own semantics and validation.
- Median and signed excess are primary; ratio and MAD-derived departure are optional diagnostics. This specification does not select an anomaly library.
- Feature 009 supplies qualified baselines; this feature supplies comparisons for later investigation. Missing diagnosis is expected at this boundary.
- Planning, tasks, implementation and integration remain later Spec Kit stages. The branch hook failed because Git metadata was read-only; no branch or commit was created. Follow-up owner: project maintainer during implementation planning.
