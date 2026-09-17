# Feature Specification: Completion-aware investigation

**Feature Directory**: `specs/011-completion-aware-investigation`

**Created**: 2026-09-17

**Status**: Specified; planning, implementation and acceptance execution pending

**Input**: Translate the minimal completion-aware agent loop into an ADR and specifications.

## Scope and authority

An unattended investigator must assess whether the requested answer is supported,
whether another operation can close a material evidence gap, or why investigation
must stop. Users must distinguish those outcomes even when each yields an answer.

[ADR 0016](../../docs/adr/0016-completion-aware-investigation.md) governs this
loop. This feature refines investigation within
[feature 007](../007-evidence-backed-diagnosis/spec.md), which retains diagnosis,
incident assembly and scoring requirements. Features 003–004 own evidence and
bounded operations. Feature 002 retains provider restrictions, case/run budgets,
comparative evaluation and release authority. Completion means assessed
sufficiency for the requested diagnosis, not benchmark correctness or project completion.

The first scope is one investigation at a time, one follow-up per decision, and
controlled evidence fixtures. New adapters, delegated researchers, interactive
clarification during judged runs, online monitoring, arbitrary code execution
and additional release claims are excluded.

## User Scenarios & Testing

### User Story 1 — Assess the answer before returning (Priority: P1)

As an investigator, I need to know whether evidence supports the requested
conclusion, so a plausible draft is not mistaken for a completed diagnosis.

**Why this priority**: Completion is the central decision the loop must make.

**Independent Test**: Supply authored evidence and controlled assessments with
independently specified requested fields, supports and material gaps.

**Acceptance Scenarios**:

1. **Given** sufficient initial evidence, **when** completion checks pass, **then** return without follow-up and record evidence sufficiency.
2. **Given** proposed completion with invented references, illegal output, an unaddressed contradiction or material gap, **when** assessed, **then** reject completion and retain the failed check.
3. **Given** uncertainty irrelevant to the requested projection, **when** the requested conclusion is supported, **then** completion may retain the qualification without indefinitely investigating unrequested details.

### User Story 2 — Investigate a useful next question (Priority: P1)

As an investigator, I need each follow-up to address a gap and its result to
inform the next assessment.

**Why this priority**: The loop must improve an answer rather than repeat activity.

**Independent Test**: Use a synthetic replica-pressure versus shared-dependency
case with scripted results, coverage changes and repeated observations.

**Acceptance Scenarios**:

1. **Given** two plausible explanations, **when** a legal comparison could distinguish them, **then** perform one operation, preserve its result, and reassess before another action or supported return.
2. **Given** a missing source and another available operation that could close the gap, **when** inability is proposed, **then** reject the unsupported blocker and retain the available path.
3. **Given** repeated unchanged evidence or invalid operations, **when** the non-progress bound is reached, **then** stop with a progress-related reason and preserve unresolved questions.

### User Story 3 — Receive an honest result when work must stop (Priority: P1)

As an evaluator, I need bounded unattended termination and usable output when
evidence is insufficient or a provider stops responding.

**Why this priority**: A limit or failure must not become a false completion claim.

**Independent Test**: Inject missing capabilities, malformed assessments, provider
failures and exhausted budgets with a controllable clock and no paid service.

**Acceptance Scenarios**:

1. **Given** no useful feasible action, **when** investigation stops, **then** identify the blocker, relevant attempts and unresolved gap.
2. **Given** insufficient remaining capacity, **when** more work is considered, **then** dispatch none and finalize with the applicable limit, evidence and best available legal answer.
3. **Given** legal choices but insufficient evidence, **when** finalizing, **then** emit the required best guess without promoting adequacy; unsupported scope or impossible legal assembly instead yields a failed case.
4. **Given** a final result that cannot be reassessed because of hard failure, **when** finalizing, **then** retain the observation and mark it unassessed rather than claiming sufficiency.

### Edge Cases

Empty or initially sufficient evidence; partial projections; more requested
incidents than supported explanations; correlated observations; valid empty
selections; newly established missing coverage; missing source with alternatives;
all useful actions exhausted; false completion/blocker proposals; absent next
action; invalid references; transient versus permanent failure; malformed
assessment; repairs consuming budget; final result at deadline; late contradiction
of a previous draft; unavailable finalizer provider; unsupported scope; no legal output.

## Requirements

### Functional Requirements

- **FR-001 — State integrity**: Preserve scope, case identity, source/policy identities, evidence and coverage, hypotheses, supports/contradictions, material gaps, attempted work and remaining limits. Repeated views of one observation are not independent evidence.
- **FR-002 — Assessment boundary**: Assess initial evidence and each follow-up result before further investigation or declaring sufficiency. Retain the proposed decision, current answer, support, unresolved gaps and rationale. If assessment cannot run, record the hard stop and unassessed observations.
- **FR-003 — Completion gate**: Accept sufficiency only when requested fields/count are legally assemblable, each selected incident has a source-backed explanation, material contradictions and plausible alternatives are addressed, and no gap prevents the requested conclusion. Reference existence alone, confidence, empty action output and formatting are insufficient. Retain non-material uncertainty.
- **FR-004 — Useful continuation**: Require a named material gap and one available declared operation whose possible results could change the answer or adequacy. Validate scope, policies, arguments and remaining capacity before execution. Investigation focus cannot alter comparison policy.
- **FR-005 — Supported inability**: Record a concrete reason when no useful feasible continuation remains. Distinguish missing source, missing capability, exhausted useful actions and stalled progress; explain why available operations cannot resolve the material gap. Do not claim global impossibility or stop merely because one source is absent.
- **FR-006 — Progress and repetition**: Track new evidence, coverage knowledge and evidence-backed gap resolution. Reject identical unchanged operations except bounded transient retries. Stop at the declared consecutive non-progress bound. Confidence changes or rewording do not reset progress; valid empty results may do so when they add coverage knowledge.
- **FR-007 — Work limits**: Enforce declared assessment, operation, repair/retry, time and cost limits within existing case/run budgets. Charge all attempts, including failures/rejections. Admit work only with reserved reassessment and finalization capacity; hard resource stops override further work.
- **FR-008 — Invalid decisions and failures**: Reject unsupported completion/blocker proposals, missing required actions and malformed assessments. Record feedback, preserve valid state and permit bounded repair only. Distinguish invalid assessment, provider failure and budget exhaustion; none establishes sufficiency.
- **FR-009 — Independent outcomes**: Retain terminal reason independently of execution status, evidence adequacy and output validity. Preserve valid judged-case best guesses and explicit failures per feature 007. Forced guessing cannot upgrade adequacy, and budget exhaustion cannot erase already supported evidence.
- **FR-010 — Finalization from retained state**: Assemble and validate without requiring another live assessment/generation call. Preserve unresolved alternatives, unassessed observations and unsupported selections. Late contradictions prevent reuse of stale sufficiency claims. Preserve earlier checkpoints under existing persistence rules.
- **FR-011 — Audit and replay**: Record ordered assessments, gate results, operations, progress changes, budgets and the first accepted terminal decision. Replay fixed observations/assessments with fixed limits to the same outcome; live variability remains measurable. Unknown usage is not zero.
- **FR-012 — Integration boundary**: Consume declared feature 003–004 evidence/operations through feature 007's diagnosis path. Preserve stub/discovery behavior and label isolation. Controlled loop acceptance does not enable diagnosis by default or waive compatibility, performance or release gates.

### Key Entities

- **Investigation state**: Evidence, hypotheses, scope, attempt history and limits for one case.
- **Assessment**: Current answer, support, material gaps and proposed completion, continuation or inability.
- **Gate result**: Accepted/rejected proposal with concrete validation findings.
- **Progress record**: New evidence/coverage or supported resolution of a named gap.
- **Terminal outcome**: Stop reason and remaining gaps, independent of case status and adequacy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All controlled completion cases meet independently authored sufficiency expectations; zero unsupported proposals are accepted, and initially sufficient cases use zero follow-ups.
- **SC-002**: Every accepted follow-up identifies a gap and is assessed before another follow-up or sufficiency claim, except recorded hard stops; every attempted operation has an audit record.
- **SC-003**: All injected non-progress, unavailable-evidence, invalid-assessment and provider/budget cases terminate within declared limits with the expected reason and no hidden retries.
- **SC-004**: Every terminal fixture preserves evidence, material gaps and the applicable best guess or explicit failure. Zero forced guesses or unassessed results are mislabeled as supported completion.
- **SC-005**: Fixed-input replays reproduce reasons and decision histories; stub/discovery, answer-contract and label-isolation regression gates remain applicable and pass before integration acceptance.

The [acceptance matrix](acceptance.md) maps every requirement and outcome. The
[loop contract](contracts/investigation.md) defines records, transitions and toy
limits. All acceptance execution is pending implementation.

## Assumptions

- Controlled fixtures and scripted assessments validate the loop independently of unfinished evidence suppliers or paid providers.
- Initial defaults are three attempted follow-ups, four assessment-provider attempts and two consecutive non-progress operations; these are not demonstrated optimal settings.
- Sufficiency is fallible. Independent expectations test behavior; feature 002's held-out study measures diagnostic effectiveness.
- Feature 007 owns incident assembly and legal vocabulary; this feature does not invent a second answer policy.
- Planning must define concrete schemas, prompt/provider configuration, reservations and timeout handling before implementation. This specification establishes no implementation or release acceptance.
