# Feature Specification: Evidence-backed diagnosis and evaluator compatibility

**Feature Directory**: `specs/007-evidence-backed-diagnosis`

**Authoring branch**: `005-evidence-backed-diagnosis` (created by the required workflow; shared checkout subsequently changed by another task)

**Created**: 2026-09-17

**Status**: Specified; planning, implementation and acceptance execution pending

**Input**: Translate the OpenRCA adoption recommendations into ADRs and feature specifications.

## Scope and authority

Advance Track 1 discovery findings into auditable root-cause answers through bounded hypothesis investigation, associated incident selection and independent evaluator compatibility checks. Reuse the existing submission runner and the interpreted scopes, qualified findings and resource relationships owned by features [004](../004-prompt-anomaly-integration/spec.md) and [003](../003-contextual-telemetry-evidence/spec.md).

[ADR 0006](../../docs/adr/0006-bounded-investigation-operations.md) governs bounded operations, [ADR 0007](../../docs/adr/0007-evidence-backed-incident-diagnosis.md) governs diagnosis and uncertainty, and [ADR 0008](../../docs/adr/0008-isolated-evaluator-compatibility.md) governs isolated scoring. [Feature 002](../002-final-demo-runner/spec.md) retains authority over submission artifacts, GLM/Featherless restrictions, budgets, comparative evaluation and release. Its complete-runner requirements govern diagnosis mode; its historical empty-output milestone remains an explicit stub regression target.

Scope is the supplied Track 1 Market schemas and seven task projections, including renamed deployments and multiple incidents. A general agent framework, arbitrary code execution, online monitoring, new data sources, scorer redesign and automatic publication are excluded. This feature requires an unattended diagnostic path and truthful model accounting when models are used; the full routed-versus-single-model study remains a feature 002 delivery gate.

## User Scenarios & Testing

### User Story 1 — Compare explanations from evidence (Priority: P1)

As an investigator, I need to distinguish possible initiating faults from their observed effects and understand which observations favor each explanation.

**Why this priority**: Candidate anomaly evidence alone cannot answer the requested cause.

**Independent Test**: Supply authored discovery results and controlled follow-up observations with independently specified support, contradictions and unresolved relationships.

**Acceptance Scenarios**:

1. **Given** several anomalous resources and two plausible explanations, **when** diagnosis compares them, **then** it retains each explanation's supporting and contradicting evidence and identifies the question that could distinguish them.
2. **Given** a downstream latency symptom and an upstream resource disturbance, **when** localization runs, **then** neither downstream position nor largest deviation alone establishes the cause.
3. **Given** weak or conflicting support, **when** a legal answer is selected, **then** the result explicitly marks a best guess and preserves the unresolved alternatives without fabricated exclusions or calibrated probability.
4. **Given** sampled behavior onset later than a hypothesized initiating fault, **when** onset is estimated, **then** the two times remain distinct and the inference and precision limitations are recorded.

### User Story 2 — Investigate within the remaining budget (Priority: P1)

As an evaluator, I need unattended investigation to make progress through declared operations without escaping the query scope or losing completed cases.

**Why this priority**: Useful answers must fit the judging environment even when operations or providers fail.

**Independent Test**: Use controlled operation/model responses, a controllable clock and injected failures; no paid service is required.

**Acceptance Scenarios**:

1. **Given** a distinguishing question, **when** follow-up is requested, **then** the operation specifies its scope and policy, respects remaining limits, and returns source-linked observations with coverage.
2. **Given** an invalid operation, malformed model output or unavailable provider, **when** recovery runs, **then** retries are bounded and recorded, permitted fallbacks preserve the same evidence contract, and finalization capacity is reserved.
3. **Given** exhausted capacity, **when** the case stops, **then** it retains findings and a stop reason, emits a legal qualified best guess if possible, and permits later cases to proceed.

### User Story 3 — Receive the requested incident answers (Priority: P1)

As a judge, I need each original query to receive the requested fields for the specified number of incidents, with evidence explaining each selected tuple.

**Why this priority**: Mixing fields between incidents or misassociating rows invalidates otherwise useful reasoning.

**Independent Test**: Assemble answers from controlled hypotheses for all seven projections, reordered non-contiguous row IDs, repeated-component incidents and equal onset estimates.

**Acceptance Scenarios**:

1. **Given** a supported query and sufficient legal choices, **when** final answers are assembled, **then** they preserve incident association, requested count, chronological order and exact allowed component/reason strings, and omit unrequested fields.
2. **Given** separate incidents on the same component, **when** answers are selected, **then** they remain separate incidents rather than being deduplicated by component.
3. **Given** fewer supported explanations than requested incidents, **when** best guesses fill remaining selections, **then** the evidence identifies unsupported aspects and does not describe those selections as independently established incidents.
4. **Given** unsupported scope or no legal answer choices, **when** assembly fails, **then** a blank failed-case artifact and reason are emitted, later valid cases proceed, and overall exit is nonzero.

### User Story 4 — Verify compatibility without exposing answers (Priority: P1)

As a reviewer, I need to reproduce scoring of sealed predictions and distinguish format compatibility from diagnostic performance.

**Why this priority**: Labels must not affect inference and scorer quirks must not masquerade as agent regressions.

**Independent Test**: Run an authored answer/scoring corpus through the pinned reference and compatibility checks, with identity-reordered rows and label-access probes.

**Acceptance Scenarios**:

1. **Given** sealed predictions, **when** scoring begins, **then** labels are available only to the scoring context and results retain prediction, evaluator and corpus identities.
2. **Given** all seven projections, exact/mismatched labels, count mismatches and time errors of 59, 60 and 61 seconds, **when** the reference scorer runs, **then** scores match independently authored expectations and strict/partial results remain distinguishable.
3. **Given** reordered query/prediction rows, **when** scoring aligns them, **then** original identity determines association; missing and duplicate IDs are explicit failures rather than positional guesses.
4. **Given** blank, malformed or missing answers, **when** evaluation reports results, **then** failures remain in case coverage and aggregate denominators, with raw scores or exceptions retained and no false compatibility claim; official blank answers score zero.

### Edge Cases

No discovery candidates; contradictory modalities; normal service aggregates masking pod changes; unavailable references; unknown duration units; isolated spikes; repeated correlated observations; ambiguous placement or endpoints; multiple incidents sharing component/reason; tied or uncertain onsets; missing legal vocabulary; unsupported scope; unknown model usage; invalid operations; malformed responses; provider exhaustion; partial discovery; output interruption; empty input; duplicate/missing/reordered IDs; regex-accepted but invalid JSON; scoring source drift; labelled artifacts present near runtime input.

## Requirements

### Functional Requirements

- **FR-001 — Evidence handoff**: Consume original case identity, supported scope, source/policy identities, qualified discovery findings and coverage. Preserve all limitations when discovery is partial; unsupported scope prevents diagnostic telemetry access.
- **FR-002 — Hypothesis integrity**: Keep observed behavior, comparative departure, proposed cause and final selection separate. Each hypothesis retains associated onset/component/reason, supporting/contradicting observations, alternative explanations and unresolved questions; no anomaly or structural heuristic is sufficient proof by itself.
- **FR-003 — Bounded investigation**: Perform follow-up only through declared operations with validated resource/time scope, policies and volume/deadline limits. Record invalid, empty, failed and truncated operations. No unrestricted generated-code execution or answer-directed baseline tuning is permitted.
- **FR-004 — Temporal reasoning**: Preserve observed onset separately from inferred fault onset and explain any difference. Preserve sampling/coverage/unit uncertainty; do not infer sub-sample precision or use scorer tolerance to fabricate evidence.
- **FR-005 — Identity and reasons**: Obtain component identities and mappings from the supplied deployment; retain unresolved mappings. Use the governing Track 1 fault-reason vocabulary with recorded provenance and exact output spelling, distinguishing it from descriptive behavior labels. No development component allowlist or per-case answer table is permitted.
- **FR-006 — Incident assembly**: For supported scopes with legal answer choices, emit the supplied number of associated incidents in chronological order, using a declared stable tie rule, and only requested fields. Do not deduplicate separate incidents by component or treat candidate count as failure count. Mark unsupported parts of best guesses explicitly. Low confidence, no anomaly candidates and provider exhaustion never justify abstention on a valid judged case.
- **FR-007 — Honest evidence**: Preserve the runner's Answer, Confidence, Evidence and Ruled out sections. Link every claimed observation/exclusion to its source and interpretation; distinguish measured facts, causal inference and guesses. Unvisited resources are not exclusions and uncalibrated confidence is not a fault probability.
- **FR-008 — Failure outcomes**: Record completed/degraded/failed case status independently from evidence adequacy. Exhausted budgets/providers may yield a legal degraded best guess; unsupported scope or absence of legal choices yields blank failed output and nonzero final exit. Continue recoverable cases; preserve published checkpoints on later failure. Partial upstream discovery stays visible even if diagnosis produces an answer.
- **FR-009 — Runtime and usage**: Honor feature 002's endpoint/model restrictions and caps: 2 CPUs/8 GB/no GPU, under 600 seconds/$3 per case and 1,200 seconds/$25 per 20-case run. Include cold preparation, retries, follow-up, formatting and persistence, reserve finalization capacity, and count all model calls. Unknown usage is not measured zero.
- **FR-010 — Label isolation**: Keep labels, scoring points, archived predictions and derived answer hints inaccessible to inference and its operations. Freeze outputs before scoring. The compatibility environment must demonstrate the separation, including when forbidden files exist near supplied telemetry.
- **FR-011 — Scoring parity**: Record governing contract and pinned scorer identities; use the official Track 1 scorer pinned in the adoption notes and retain its documented differences from upstream. Validate all projections, key order, incident count, exact strings, temporal boundaries and tuple association against authored expected outcomes. Preserve raw reference behavior and distinguish semantic validation failures from scorer exceptions or scores.
- **FR-012 — Case accounting**: Associate predictions and queries by original identity before scoring. Retain missing, malformed, blank, duplicate and timed-out results visibly. Report strict/partial accuracy and per-task coverage with declared denominators; do not select a gold-best sample as a deployable inference result.
- **FR-013 — Reproducibility**: Retain source, code, operation, prompt/model/routing, vocabulary, budget and evaluator identities as applicable, plus exposed-versus-held-out case status. Recompute metrics from sealed outputs without model calls. Replay fixed operation/model observations reproducibly; live model variation is measured, not denied.
- **FR-014 — Mode compatibility**: Retain explicit stub and discovery regression paths and their distinct validators. Enable diagnosis as the default only after its controlled contract gates pass; this changes no feature 004 discovery-mode blank-output obligation. Diagnosis acceptance does not certify the final release or held-out accuracy study.

### Key Entities

- **Diagnostic hypothesis**: Associated incident explanation, evidence for/against it, alternatives, inferred onset and uncertainty.
- **Investigation operation**: A bounded request, its result, source/policy references, coverage, timing and stop reason.
- **Diagnostic case result**: Original scope, retained hypotheses, selected incidents, evidence adequacy, completion/degradation/failure and limitations.
- **Answer projection**: Requested fields of selected incident tuples, formatted for the external contract.
- **Compatibility record**: Frozen prediction/corpus/evaluator identities, validation outcome, raw scoring outcome and normalized failure accounting.
- **Run manifest**: Input/configuration identities, per-case status and measured/unknown usage, shared preparation accounting and total outcomes.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every controlled diagnosis fixture retains its authored supports, contradictions and qualifications, with zero invented observations or unsupported exclusions; onset inference remains distinguishable from observation.
- **SC-002**: All seven projection fixtures and multi-incident/reordered-ID fixtures produce exact expected count, association, ordering and field selection. Every legal best guess is visibly qualified; every impossible assembly is visibly failed.
- **SC-003**: Every injected invalid operation, malformed response and budget/provider failure terminates within declared limits, preserves earlier results and accounts for all attempted calls with unknown usage explicitly marked.
- **SC-004**: The independent compatibility matrix matches the pinned reference's expected scores or expected errors in every authored case. Every row identity or semantic-validation failure is reported separately, and saved metrics reproduce without model calls.
- **SC-005**: Isolation checks record zero forbidden label/answer reads by inference. All scored outputs have a pre-scoring seal and every missing/failed case remains in coverage accounting.
- **SC-006**: A cold isolated 20-case development rehearsal reports completion/degradation/failure counts, memory, time and cost and satisfies all feature 002 caps. Controlled fixture success alone does not meet this runtime gate or establish held-out accuracy.

The [acceptance matrix](acceptance.md) maps every requirement. Artifact and evaluator details are in the [contract](contracts/diagnosis.md). All acceptance remains pending implementation.

## Assumptions

- The supplied Track 1 contract governs; the inspected OpenRCA checkout is a versioned reference. The official scorer and 15-reason vocabulary source are pinned in [adoption notes](../../docs/openrca-adoption.md).
- Features 003–004 are specified dependencies, not certified implementations. Authored handoff fixtures permit independent diagnosis development; end-to-end completion requires their validated integration.
- Best-guess output follows feature 002. Explicit operational failure when no legal answer exists fails final diagnosis acceptance; it is not valid benchmark abstention.
- Provider integration and routing decisions must comply with feature 002 and be frozen during planning. Controlled model responses suffice for local correctness checks; this documentation task authorizes no paid run.
- No accuracy threshold is invented here. Final effectiveness, routed/single-model comparison, evidence review and release remain feature 002 requirements owned by the project maintainer.

## Consuming Featherless trace annotations

[ADR 0015](../../docs/adr/0015-featherless-trace-semantics-and-prefix-caching.md) and [feature 008](../008-featherless-trace-semantics/spec.md) define a possible descriptive evidence supplier. Consume validated annotations with their original packet references, definition versions, support strength, scope and limitations. A descriptive class, model agreement or prefix-cache hit is not causal evidence; retain supported facts and unresolved interpretations separately when evaluating an incident hypothesis.

SC-001 integration fixtures must include unmapped status, mapped child error with independently verified enclosing success, unsupported mechanism proposals and conflicting annotations. Each must retain uncertainty without promoting a label into fault reason or onset. SC-003 accounting must include every annotation and diagnostic call under feature 002 budgets. Failed/unknown annotations may reduce available evidence but do not waive the final best-guess or explicit operational-failure contract. S09 success alone does not satisfy SC-006 or establish diagnostic accuracy.
