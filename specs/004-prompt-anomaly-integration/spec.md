# Feature Specification: Track 1 prompt interpretation and anomaly identification

**Feature Branch**: `004-prompt-anomaly-integration`
**Created**: 2026-09-17
**Status**: Specified; planning, implementation and acceptance execution pending
**Input**: “spec integration of the prompt interpretation and anomaly identifiction”; clarification: “scope tightly to the track-1 requirements and dataset”.

## Scope and authority

Advance the empty-output demo runner into an unattended Track 1 investigation: interpret each public query, retrieve relevant supplied telemetry, identify unusual observations against declared references, and return auditable candidates for later diagnosis. An anomaly candidate is an observed departure or structural difference worth investigating; it is not a labelled failure, calibrated fault probability, or root-cause answer.

Scope is the Track 1 Market microservice bundle and its seven task types, including another deployment of the same system with different component identities. Interpret the provided English prompt forms, deployment, 30-minute window, requested fields and positive failure count. General chat, arbitrary natural-language instructions, live monitoring, new data providers, upstream answer downloads, dashboards, and a general-purpose anomaly framework are outside this feature.

Use the supplied trace, metric and log schemas only. Require a bounded trace comparison path and a bounded metric candidate path; use logs for targeted corroboration when those observations make a concrete question possible. Do not require scanning every modality or log line for every case. No standalone log-learning system, provider/model integration or final diagnosis is required here.

[Feature 002](../002-final-demo-runner/spec.md) owns the runner and final submission contract. [Feature 003](../003-contextual-telemetry-evidence/spec.md) and ADRs [0003](../../docs/adr/0003-indexed-telemetry-retrieval.md), [0004](../../docs/adr/0004-qualified-contextual-baselines.md), and [0005](../../docs/adr/0005-evidence-backed-resource-relationships.md) govern retrieval, qualified references and resource linkage. This feature specifies their operational connection; it does not certify existing experiment scripts as production-ready.

## User Scenarios & Testing

The OpenRCA adoption amendment is governed by [ADR 0006](../../docs/adr/0006-bounded-investigation-operations.md). It strengthens portable schema validation and operation auditability below without adding models or diagnosis. [Feature 007](../007-evidence-backed-diagnosis/spec.md) owns the later diagnostic handoff and scorer compatibility; its best-guess contract does not change this milestone's blank predictions.

### User Story 1 — Interpret a Track 1 query into investigation scope (Priority: P1)

As an evaluator, I need the runner to understand what the query asks before it reads telemetry, retaining the exact original case identity.

**Why this priority**: Wrong time bounds, failure count or requested fields invalidate every later stage.

**Independent Test**: Interpret the public query inventory against an independently reviewed, label-free scope fixture; add equivalent wording, a renamed deployment, another date and a cross-midnight case.

**Acceptance Scenarios**:

1. A supported prompt produces its deployment, start/end in UTC+8, positive failure count and ordered requested-field subset, with the source text supporting each extracted value.
2. All seven field combinations are recognized from the actual instruction. Optional task_index metadata is cross-checked; a contradiction is surfaced instead of silently changing the request.
3. “A failure”, “one failure”, “a single failure” and the supplied multiple-failure wording resolve correctly. Whitespace, line breaks and CSV quoting do not change meaning.
4. Interpretation uses the current instruction rather than a development row-ID lookup, fixed March date, previously authored scope table or expected-answer fields.
5. A missing, conflicting, impossible or unsupported scope produces an explicit per-case interpretation failure; no telemetry is retrieved for that case, and later valid cases can proceed unattended.

### User Story 2 — Find supported unusual behavior within the scope (Priority: P1)

As an investigator, I need trace and resource observations that differ from a declared reference, without having to supply the faulty component or onset.

**Why this priority**: This is the first useful output beyond the runner scaffold and must work without a root-cause answer.

**Independent Test**: Feed authored Track 1-shaped telemetry with known duration, structural and resource-metric changes, sparse references and missing sources; compare findings to an independent fact inventory.

**Acceptance Scenarios**:

1. Requests are selected by deployment/window and the frozen policy; selected trace expansion retrieves the available recorded spans, including relevant boundary-crossing spans, or explicitly reports incomplete retrieval.
2. Eligible trace comparisons retain observed duration, reference median, signed absolute excess, support, identity and evidence. Changed or unmatched child-operation sets/counts remain in a separate structural channel instead of being discarded or assigned a zero score.
3. A planted pod/node/service metric change yields a candidate with exact recording/resource identity, metric, unit or unit qualification, time interval, observed value and reference comparison. Discovery does not depend exclusively on frontend latency being unusual.
4. A targeted metric/log follow-up is justified by an observation or time-supported resource relationship. The resulting record preserves the link and ambiguity; a nearby log or service-level association cannot silently establish an exact request target.
5. Constant, zero, sparse, missing, incompatible or provisionally interpreted references receive the required qualification or unavailable status. Unsupported comparisons produce no fabricated ratio, infinite score, percentile or fault probability.
6. Candidate count is independent of the supplied failure count. Two independent changes are retained even if they share a component or the prompt requests one failure; one shared observation is not counted as independent corroboration multiple times.

### User Story 3 — Inspect the integrated case result (Priority: P1)

As a demonstrator or downstream diagnostic stage, I need one case result joining the interpreted scope, anomaly candidates, raw-evidence locators and limitations.

**Why this priority**: Separate successful experiment scripts are not an integrated unattended runner.

**Independent Test**: Run the official three-flag command on a small fixture and inspect the produced scope, findings, evidence and usage for each original row ID.

**Acceptance Scenarios**:

1. The default runnable path performs interpretation and discovery without a prebuilt local index, scope register, manual policy selection or required additional flag. Each input row gets its own result and evidence, including non-contiguous IDs.
2. Identical deployment/window queries may share retrieval/reference work, but different requested fields/failure counts and their source instructions remain attached to their own cases. Reuse across distinct deployments, source snapshots or policies is prohibited.
3. The evidence file explains actual observed departures and limitations. It states that causal diagnosis remains pending and makes no unsupported ruled-out claim.
4. Prediction cells remain blank for this discovery-only milestone. Scope, observation onset and candidate ranking are not serialized as fabricated incident answers. The existing four evidence headings and usage file remain present.
5. The existing empty-output scaffold remains explicitly runnable for regression; its placeholder-only validator is not weakened to mislabel discovery artifacts as valid placeholders or official predictions.

### User Story 4 — Bound, recover and audit the investigation (Priority: P1)

As an evaluator, I need the run to respect Track 1 restrictions and show what actually completed when time, sources or reference support run out.

**Why this priority**: Cold preparation and incomplete cases consume the same judging budget as useful analysis.

**Independent Test**: Run source/cache changes, missing modalities and forced budget exhaustion through the integration, then rehearse from a cold container on supplied development data.

**Acceptance Scenarios**:

1. All case-data reads come from the supplied input; all indexes, journals, temporary files and result writes are under --out. Prepared views are rebuilt or rejected when incomplete or incompatible. No developer-local data artifact is required.
2. Preparation, interpretation, retrieval, comparison, corroboration and finalization consume declared shared budgets. A stage stops with an explicit reason and coverage statement before using reserved output time; later cases retain their allocated opportunity.
3. Completed case outputs survive an interrupted or failed later case. Failed interpretation, partial retrieval, unavailable comparison and no candidates are distinguishable outcomes.
4. Completed runs with unchanged inputs, policies and deterministic work limits preserve scope and substantive findings apart from timing/run identifiers. Deadline-truncated runs retain work boundaries and stop decisions for controlled partial replay; live reruns may inspect different amounts of data. Changing instruction or policy cannot reuse an incompatible cached scope/result.
5. Accuracy claims, if later evaluated, are separate from scope correctness and anomaly-discovery checks. Exposed/overlapping development windows are not counted as independent held-out evidence.

### Edge Cases

Missing/duplicate CSV IDs; optional metadata omitted or inconsistent; an instruction containing newlines or repeated requested-field phrases; malformed dates, conflicting dates and cross-midnight bounds; host timezone changes; trace timestamps in milliseconds versus metric/log seconds; separately uncertain duration units; unsorted/cross-partition traces; no recorded frontend root; missing trace modality with valid resource metrics; no metric samples; unknown target or replica; shared timestamps across deployments; source replacement and interrupted index builds; insufficient lookback at the beginning of the bundle; constant/zero/contaminated references; unmatched structure and missing ancestry; overlapping symptoms from multiple incidents; tied priorities; empty candidate lists; partial output persistence; repeated queries with different projection requests.

## Requirements

### Functional Requirements

- **FR-001 — Input authority**: Use each supplied row_id and instruction as scope inputs; recognize the Track 1 English prompt forms and seven requested-field projections. Do not use labels, scoring_points, private answer files or precomputed development row-ID maps. Preserve optional task metadata for consistency checks only.
- **FR-002 — Scope semantics**: Record deployment, original instruction identity, timezone-aware 30-minute bounds, positive failure count and ordered requested fields. Normalize UTC+8 independently of host timezone. Each extracted value must have a supporting text location or an explicit documented Track 1 convention. Reject contradictory or unsupported scope without silently inventing values.
- **FR-003 — Interpretation isolation**: Scope interpretation must be independently verifiable before telemetry retrieval. Invalid scope is a case-level failure, not permission to read the whole dataset or to ask an interactive question during the run.
- **FR-004 — Bounded collection**: Select observations from the scoped deployment/window plus the declared reference interval; bound and document trace expansion separately from initial time selection. Preserve identity, raw source values, conversion assumptions, duplicate conflicts and coverage under feature 003.
- **FR-005 — Source/policy portability**: Build required prepared views automatically from the mounted bundle and retain them beneath --out. Validate source/extraction/policy identity before reuse. Do not ship development source indexes, component allowlists or per-case findings as answers.
- **FR-006 — Trace discovery**: Support the existing qualified duration-comparison and structural-difference paths as separate findings. Record explicit eligibility, support and unit limitations; retain unmatched/unknown structure. A configured frontend policy must discover/bind compatible components from the current deployment, never assume the three development replicas exist unchanged.
- **FR-007 — Metric discovery and corroboration**: Include bounded resource-metric candidate discovery using the provided container/node/service/mesh/runtime schema families as supported by declared policies. Each family is reported as inspected, unavailable or not inspected with a reason. Candidate-directed log inspection must record its question, scope, source observations and any unresolved relationship; no generic all-log scan is required.
- **FR-008 — Reference qualification**: Freeze reference selection and comparison policy for the investigation. Preserve eligible, qualified and unavailable outcomes; do not equate historical typicality with health, unknown structure with novelty, missing samples with a missing event, or an unvisited resource with an exclusion. No undeclared lookback expansion, fallback or threshold tuning from desired results.
- **FR-009 — Candidate integrity**: Every candidate links its observation, source records, comparison/reference policy and qualification. Preserve observed time/interval, exact resource identities, absolute magnitude, direction, support and priority rationale. Keep incomparable channels separate; report ties and truncation. Neither candidate count nor grouping may be forced to the prompt's failure count.
- **FR-010 — Discovery handoff**: Emit a per-case scope and discovery result with status, ordered candidates, retained qualifications/unavailable findings, coverage, timings and stop reasons. Preserve observed behavior onset separately from inferred fault onset. No root-cause conclusion is required or implied by these artifacts.
- **FR-011 — Runner compatibility**: Keep the root Dockerfile and `python run.py --dataset /data --queries /data/query.csv --out /out` usable without manual preprocessing. Preserve one prediction row, four-section evidence file and usage record per input case when persistence succeeds. This milestone keeps prediction values blank, updates evidence to actual discovery findings, and provides distinct validation for the retained empty stub and the integrated path.
- **FR-012 — Failure and progress**: Process valid cases after an invalid-scope or recoverably degraded case. Publish a readable case status and preserve previous prediction checkpoints on later failure. Global invocation/output failure must return nonzero; mixed successful/failed discovery must be visible in both run status and exit behavior. No-findings with sufficient coverage is a valid discovery result, not proof of no fault.
- **FR-013 — Runtime constraints**: Fit 2 CPUs/8 GB/no GPU, less than 600 seconds per case and 1,200 seconds per 20-case run including cold preparation. Declare and enforce stage/run budgets with finalization reserve. This integration performs no model calls and requires no key; record zero model usage and measured local work, without implying the future GLM routing requirement is fulfilled.
- **FR-014 — Reproducible verification**: Preserve input/source/policy identities and verify interpretation, retrieval/comparison fidelity and integration independently using authored fixtures and label-free public queries. Reconcile development exposure before any later accuracy evaluation. Record cold preparation separately from reused work without double-counting shared windows.

The following adoption requirements extend the discovery boundary:

- **FR-015 — Validated inventory**: Discover supported files, columns, resource identities and KPI names from the mounted bundle before referencing them. Validate the Track 1 schema family and timestamp-unit convention, preserve raw values, and report unsupported/missing fields. Do not assume OpenRCA's hardcoded deployment paths, component lists or replica count. Duration units retain feature 003 qualifications.
- **FR-016 — Operation audit**: Record each declared discovery operation's question, bounded scope, policy/source identities, outcome, coverage, elapsed time and stop reason, including rejected, failed and truncated operations. Distinguish a valid empty selection from invalid resource/KPI references, unavailable sources and exhausted limits. Discovery uses deterministic operations; no unrestricted generated-code executor is introduced.

### Key Entities

- **Interpreted scope**: Original row/instruction identity, deployment, UTC+8 window, failure count, ordered projection, extraction support and status.
- **Discovery policy**: Supported source families, reference/context selection, numerical/structural comparison rules, qualification, priority, bounded corroboration and version.
- **Observation/reference finding**: Exact source/resource identity, raw and normalized measurement, time support, reference membership, difference, eligibility and limitations; governed by feature 003.
- **Anomaly candidate**: A prioritized observation or candidate episode with source-linked findings, rationale and uncertainty; distinct from a failure or causal hypothesis.
- **Case discovery result**: Scope, candidates, retained unavailable/unselected evidence, coverage, stage status, timing and stop reason, linked to runner outputs.
- **Run discovery record**: Shared preparation identity/cost, per-case completion outcomes and total budget usage.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 70 supplied public instructions match independently reviewed scope expectations, including every task type, failure-count wording and window; no answer-label access occurs. Supported synthetic date/deployment substitutions and equivalent whitespace forms preserve interpretation.
- **SC-002**: Every authored ambiguous/unsupported scope fails explicitly before telemetry access, with no invented default; a later valid case still completes.
- **SC-003**: Controlled trace-duration, structural and resource-metric changes produce the expected source-linked findings; every authored unsupported comparison retains its limitation. The checked cases contain zero invented observations, causal claims or lost unmatched structures.
- **SC-004**: Every completed fixture case produces correctly associated discovery artifacts, evidence, blank prediction and usage; every deliberately interrupted/degraded case has an explicit status and preserves earlier completed outputs.
- **SC-005**: The unchanged official command works from a cold isolated image under Track 1 resource limits on a declared 20-case development rehearsal, including preparation, with completion/partial rates, time and memory measured. A successful two-row fixture alone cannot satisfy this gate.
- **SC-006**: Completed runs reproduce substantive findings and provenance for identical sources, frozen policy and deterministic work limits. Deadline-truncated runs reproduce their partial findings only when replaying the same recorded work boundaries or controlled clock schedule; live elapsed-time variation may change coverage and must remain explicit. Every cached result invalidation test distinguishes changes to deployment, instruction, source and policy; overlapping-window reuse preserves separate row scopes.
- **SC-007**: Every authored renamed-inventory, unsupported-schema, mixed-timestamp-unit and empty-operation fixture produces the expected identity/validation outcome, and every attempted operation in the controlled corpus has a complete audit record with no invented resource or measurement.

Acceptance mapping and expected artifacts are in [acceptance.md](acceptance.md) and the [integration contract](contracts/integration.md). These are planned checks, not executed results.

## Assumptions

- This request integrates interpretation and anomaly identification, not final causal diagnosis. The previous empty-answer exception continues only for this intermediate milestone; the final Track 1 answer/evaluation/release obligations remain unsatisfied.
- Initial support follows the supplied Track 1 schemas and English prompt styles. Dates, component IDs and deployment identities may vary; the implementation must not hard-code 70 rows, 57 windows or March 20–21 as runtime constraints.
- No model is needed to interpret this bounded prompt family or run the empirical discovery stage. Choosing a model-assisted interpreter later is a separate scoped change with the existing GLM/endpoint/budget requirements.
- The five-minute pooled C1 experiment is qualified development evidence for an empirical trace comparison, not a production detector calibration. Its applicable policy and limitations must be versioned in the shipped source; its ignored selection/index files are not runtime prerequisites.
- Metric comparison and priority policies must be fixed and tested during planning/implementation, rather than implied by trace research or label access. They need not be statistically identical to the trace policy. The planning gate must bind executable policies before implementation can be called complete.
- Existing experiment code is reusable only after its paths, component assumptions, units, retrieval coverage and runtime cost satisfy this specification and feature 003. No new experiments, runtime changes or public release occur while authoring this spec.
