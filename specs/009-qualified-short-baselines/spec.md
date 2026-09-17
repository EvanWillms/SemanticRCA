# Feature Specification: Qualified short-window frontend baselines

**Feature Branch**: Not created; the repository hook was attempted and Git metadata was read-only. Specification identity is independent of the checkout.

**Created**: 2026-09-17

**Status**: Specified for implementation planning; production compliance not established

**Input**: Translate the short-window report into baselining-specific ADRs and specifications.

## Scope and authority

Provide a reproducible, qualified historical reference for frontend root duration, using the selected five-minute C1 pooled policy and preserving its limitations. [ADR 0013](../../docs/adr/0013-qualified-short-window-frontend-baselines.md) specializes feature 003's general [baseline contract](../003-contextual-telemetry-evidence/contracts/baselining.md). [Feature 010](../010-comparative-descriptors/spec.md) consumes the resulting baseline; it owns comparison descriptors. Retrieval and scoped identities retain features 003/005's authority.

The deliverable is a baseline with membership, support, center stability, distributions, and coverage. Alerting, diagnosis, resource-metric baselining, online adaptation, and submission packaging are outside this feature. Research measurements are motivation and regression evidence, not production service-level targets.

## User Scenarios & Testing

### User Story 1 — Obtain a contextual reference (Priority: P1)

As an investigator, I need a reference for the recorded request shape so a lightweight request is not compared with an unrelated checkout-like flow.

**Why this priority**: The reference must answer a declared question before any score or descriptor is meaningful.

**Independent Test**: Use an independently authored corpus with different operation sets, call counts, replica identities, and reference/query boundaries.

**Acceptance Scenarios**:

1. **Given** compatible C1 requests across the explicit frontend allowlist, **when** a baseline is built at T, **then** membership uses only eligible starts in the preceding five minutes and all represented execution endpoints are strictly before T.
2. **Given** the same operation presence with different counts, **when** C1 groups are built, **then** those requests share a cohort and their multiplicities remain available for structural comparison.
3. **Given** an unknown structure and a recovered empty recorded child set, **when** references are selected, **then** these states remain distinct; unknown structure does not enter a shape-conditioned baseline.
4. **Given** a new replica outside the allowlist, **when** collection encounters it, **then** its out-of-scope status is reported without inferring service equivalence from its name.

### User Story 2 — Know when a reference is usable (Priority: P1)

As a comparison consumer, I need sample support and center stability reported separately so adequate counts cannot conceal a weak reference.

**Why this priority**: The confirmation study contains both support failures and supported but unstable centers.

**Independent Test**: Author cohorts at the count, temporal-concentration, and uncertainty boundaries, including constant and zero-valued references.

**Acceptance Scenarios**:

1. **Given** 20 valid references across three one-minute bins with a largest bin of 10, **when** support is assessed, **then** the cohort passes count/time support; 19 references, two occupied bins, or a largest bin of 11 each independently fail the corresponding rule.
2. **Given** supported data with an uncertainty interval wider than 40% of a positive median, **when** qualification is returned, **then** the empirical reference remains inspectable with a failed stable-center screen and is never presented as a stable reference.
3. **Given** fewer than 190 usable resampling replicates, **when** stability is assessed, **then** it is inconclusive rather than a pass.
4. **Given** a supported constant or zero reference, **when** qualification is returned, **then** median support remains separate from zero MAD and the zero-center relative-width limitation.

### User Story 3 — Preserve failures and reference meaning (Priority: P1)

As a reviewer, I need unsupported requests and frozen membership retained across the observation horizon, without a hidden change of baseline.

**Why this priority**: Automatic fallback or selective exclusion could manufacture coverage or absorb a disturbance.

**Independent Test**: Freeze a baseline, replay six slices with sparse/unmatched/changed requests, then introduce an explicit new policy version.

**Acceptance Scenarios**:

1. **Given** an unsupported five-minute cohort, **when** duration comparison is requested, **then** it is unavailable with reasons; history is not expanded and the replica/context policy is not changed automatically.
2. **Given** six query-start slices over 30 minutes, **when** a baseline is reused, **then** all use the same frozen membership and record their offset from T.
3. **Given** boundary exclusions or ambiguous identities, **when** coverage is reported, **then** raw records, resolved requests, unknown identities, and exclusions reconcile without duplicated requests or silent losses.
4. **Given** most requests are supported but one class/window fails, **when** aggregate coverage is published, **then** that failure remains visible by class, replica and slice.

### User Story 4 — Reproduce and challenge the scope (Priority: P2)

As a reviewer, I need to inspect membership, sensitivity, and the policy's empirical limits without assuming that typical traffic is healthy.

**Independent Test**: Replay unchanged sources and policies; compare explicitly separate same-replica and alternative-lookback assessments; apply authored contamination controls.

**Acceptance Scenarios**:

1. Reordering records preserves resolved membership and derived statistics; changing a source or policy creates a distinct baseline version.
2. A baseline whose median approaches 60 seconds remains a qualified empirical reference, with no healthy/acceptable label.
3. Pooling contributions, half-window sensitivity, and uncertainty evidence remain available even when aggregate support passes.

### Edge Cases

Cross-midnight references; unsorted partitions; duplicated/conflicting identities; missing ancestors or adjacent sources; reference endpoints equal to T; long query executions completing after their start slice; unknown versus empty recorded structure; invalid/negative/nonfinite durations; uncertain units; sparse cohorts; zero median/MAD; concentrated samples; failed bootstrap replicates; a shifted minority replica; contaminated history; changed source snapshots; empty windows; shared support across replay windows.

## Requirements

### Functional Requirements

- **FR-001 — Scope and identity**: Declare the deployment, source inventory, explicit frontend allowlist, observation identity, anchor and units. Resolve requests independently of row order; retain conflicts and excluded records without invented equivalence.
- **FR-002 — Context**: Use C1: root raw operation/type plus the set of recorded direct-child operation/type pairs. Preserve C0, counts, component bindings and structural quality separately. Unknown structure MUST NOT match a known empty set.
- **FR-003 — Time eligibility**: Use the half-open five-minute start interval before T and require recovered root/span endpoints strictly before T. Recover the available recorded trace across declared partitions and report unresolved completion and boundary exclusions, including duration distributions. Do not claim online availability from event time.
- **FR-004 — Frozen policy**: Version and freeze membership, replica/context policy, support and uncertainty rules before comparisons. Support six five-minute query-start slices through T+30 minutes without refresh or automatic fallback. Further horizons or alternatives require an explicit separate policy/version.
- **FR-005 — Support**: For this profile require at least 20 usable resolved references, at least three occupied absolute one-minute bins, and at most half in any bin. Record every failing condition. Invalid duration/unit compatibility or unresolved identity/structure cannot be repaired by a score.
- **FR-006 — Center stability**: Assess the declared one-minute block-resampling screen independently of support, preserving usable/failed replicates and interval endpoints. Positive-center width above 40% fails the screen; fewer than 190/200 usable replicates is inconclusive; zero-center relative width is inapplicable. Supported median comparisons remain qualified when this screen fails or is inconclusive.
- **FR-007 — Baseline evidence**: Preserve reference count, median, quartiles, MAD, start/end support, occupied bins, largest gap, minute/replica concentration, boundary/invalid exclusions, first/second-half and leave-one-minute-out sensitivity, and source membership with governing versions.
- **FR-008 — Qualification**: Preserve support, stability and field availability independently. Every supported reference in this initial scope retains health, workload/configuration, pooling-equivalence, instrumentation/unit and retrospective-availability qualifications as applicable. Zero MAD does not invalidate a supported median.
- **FR-009 — Coverage**: Report supported/resolved request counts, raw records and unresolved identities separately; expose cohort-incidence denominators and C0/C2 strata so grouping changes cannot improve apparent coverage silently. Report by anchor, query offset, class and replica, with empty denominators unavailable rather than 100%.
- **FR-010 — Provenance and changes**: Every membership and statistic MUST resolve to source evidence and policy/estimator versions. Reuse rejects changed sources or incompatible extraction. A new baseline does not overwrite prior baselines or observations.
- **FR-011 — Validation and claims**: Validate membership, boundary handling, support, uncertainty and preservation independently of an encoder, detector, model or fault labels. Preserve failure cells, exposure/overlap accounting and separate preparation/reuse costs. Coverage is not health, accuracy, collector uptime, or independent sample count.

### Key Entities

BaselinePolicy; ReferenceCohort; FrozenBaseline; SupportAssessment; CenterStabilityAssessment; BaselineQualification; MembershipEvidence; CoverageStatement. The [baseline contract](contracts/baseline.md) defines their semantic contents and state composition without prescribing storage or transport.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All independently authored membership and cutoff cases B01–B03 recover exactly the declared eligible references, with zero invented matches or silently lost requests.
- **SC-002**: All support, uncertainty and degenerate-reference cases B04–B06 return the prescribed separate outcomes, with zero unsupported stable-center claims.
- **SC-003**: Every replay result in B07–B10 resolves to unchanged frozen membership or an explicitly new version; every coverage numerator and denominator reconciles.
- **SC-004**: Every benchmark-shaped regression in B11 preserves its expected qualification or failure rather than meeting an invented universal coverage target.
- **SC-005**: All accepted baselines preserve resolvable provenance and the claim boundary in B12; validation does not require labels or a functioning diagnoser.

The [acceptance matrix](acceptance.md) covers every requirement. Passing the existing research tests is prior evidence, not completion of these feature acceptance criteria.

## Assumptions

- Scope is the supplied Track 1 frontend snapshot; the policy generalizes only after separate validation. The reference producer consumes validated extraction from features 003/005.
- The short-window study selected one primary descriptive policy with no fallback; class-specific alternatives remain separately inspectable evidence.
- Availability and uncertainty screens are adopted as versioned scope settings. Reported percentages are observations, not guaranteed acceptance targets for new traffic.
- This request authorizes ADRs and specifications. Planning, tasks, implementation, integration and routing/submission evaluation remain later Spec Kit stages. The branch hook failed because Git metadata was read-only; no branch, commit or implementation change is required to identify this specification. Follow-up owner: project maintainer during implementation planning.
