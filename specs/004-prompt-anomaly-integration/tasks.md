---
description: "Incremental task list for the Track 1 prompt and anomaly integration"
---

# Tasks: Track 1 prompt interpretation and anomaly identification

**Input**: Design documents in `specs/004-prompt-anomaly-integration/`.

**Scope**: Feature 004 owns deterministic scope interpretation, bounded Track 1
inventory/retrieval, qualified anomaly findings, corroboration, audit records and
the blank-prediction discovery handoff. Feature 002 owns the existing runner and
release contract; feature 007 owns diagnosis and model/provider behavior.

**Tests**: TDD is required. Each test task below writes one behavior at the
confirmed public seam, observes red, then the immediately following green task
implements only that behavior. Test seams are the plan-defined boundaries in T001. Subsequent user direction prioritizes parallel happy-path implementation with reduced defensive design. No test or implementation work is
performed by generating this file.

**Execution**: Work in R0–R6 order as small runnable vertical slices. Delegated
implementation may use Luna at extra-high reasoning effort. The shared dirty
checkout must not be switched, committed, reset, or cleaned. All code changes
are reviewed in the parent task after the slice gate; do not commit unrelated
work.

## Phase 1: Setup

**Purpose**: Confirm the public seams and prepare independent fixture locations
without changing runtime behavior.

- [X] T001 Use the plan-defined public test seams under the subsequent happy-path execution instruction in `specs/004-prompt-anomaly-integration/reviews/execution-log.md`: `interpret(QueryRow)`, typed discovery operations/receipts, and CLI writer/checkpoint behavior; see the recorded user steering and execution evidence.
- [ ] T002 [P] Define the independent fixture layout and label-free expectation ownership in `tests/fixtures/discovery/`, `tests/unit/`, `tests/contract/`, and `tests/integration/`; do not derive expected scopes from parser output, row IDs, labels, or answer files.

## Phase 2: Foundational — R0 baseline and shared seams

**Purpose**: Preserve the accepted empty-output baseline and establish the typed
interfaces required by every later slice. The happy-path execution instruction allows independent implementation work while foundation integration proceeds; acceptance gates remain tracked.

- [X] T003 Run `python3.12 -m unittest discover -s tests -q` and retain the 26 passing-test evidence in `specs/004-prompt-anomaly-integration/reviews/execution-log.md`.
- [X] T004 Run the explicit `--agent agents.submission` CLI smoke and strict `scripts/validate_harness.py` validator against `eval/fixtures/query.csv`; retain the exit-0 evidence in `specs/004-prompt-anomaly-integration/reviews/execution-log.md`.
- [X] T005 Confirm the dirty-checkout boundary, runtime snapshot and no-default-promotion/no-commit rule in `specs/004-prompt-anomaly-integration/reviews/execution-log.md`; preserve all existing files and unrelated work.
- [ ] T006 Write one failing contract test for backward-compatible query metadata, covering the data-model constraint `Original unique integer row_id, exact instruction, optional task_index`, in `tests/contract/test_discovery_contract.py` after T001 confirmation.
- [ ] T007 Implement only the T006 contract in `rca/contracts.py`: extend `QueryRow` with optional `task_index` and add an optional structured discovery result to `Solution` while preserving existing stub callers.
- [ ] T008 [P] Write one failing persistence contract for finite structured sidecars and blank predictions in `tests/integration/test_discovery_output.py`, using `rca/outputs.py` as the public writer seam after T001 confirmation.
- [ ] T009 Implement only the T008 behavior in `rca/outputs.py`: keep `OutputWriter` responsible for persistence, validate finite JSON values and stable row associations, and preserve the existing evidence/usage/predictions artifacts for stub solutions.
- [ ] T010 [P] Write one failing operation contract for typed requests, receipts and rejection outcomes in `tests/unit/test_discovery_operations.py`, covering the declared operation names from `specs/004-prompt-anomaly-integration/contracts/executor.md` after T001 confirmation.
- [ ] T011 Implement only the T010 behavior in `rca/discovery/context.py` and `rca/discovery/operations.py`: define the shared run context and typed operation envelope without accepting shell, SQL, Python, arbitrary paths, or untrusted policy values.
- [ ] T012 Review R0/foundation changes in the parent task against `specs/004-prompt-anomaly-integration/contracts/executor.md` and `specs/004-prompt-anomaly-integration/data-model.md`; run the changed seam tests plus the explicit stub CLI/validator regression and record results in `specs/004-prompt-anomaly-integration/reviews/r0-foundation.md`.

## Phase 3: User Story 1 — R1 scope interpretation (Priority: P1; MVP)

**Goal**: Interpret each Track 1 instruction into a typed, source-supported
scope before telemetry access, retaining original row identity and truthful
scope-only status.

**Independent Test**: Use independently authored expectations for all seven
projections, equivalent whitespace, renamed deployment/date, midnight rollover,
metadata conflict, and an invalid row followed by a valid row; assert no
telemetry access for unsupported scope.

### TDD implementation loop for US1

- [ ] T013 [US1] Write one failing parser test for deployment identity, lowercase canonicalization, original spelling support and UTF-8 instruction hash in `tests/unit/test_scope.py`.
- [ ] T014 [US1] Implement only T013 in `rca/scope.py`, anchoring identifiers to the supported system/event-subject grammar and rejecting conflicting canonical deployments.
- [ ] T015 [US1] Write one failing parser test for the supported date/time forms, fixed `UTC+08:00`, timezone-aware half-open 30-minute bounds, and Unicode source offsets in `tests/unit/test_scope.py`.
- [ ] T016 [US1] Implement only T015 in `rca/scope.py` with the locale-independent English month map, real calendar validation, and zero-based half-open Unicode extraction support.
- [ ] T017 [US1] Write one failing parser test for the narrowly permitted 23:30→00:00 next-day convention plus invalid, non-30-minute, conflicting, and ambiguous-date windows in `tests/unit/test_scope.py`.
- [ ] T018 [US1] Implement only T017 in `rca/scope.py`, recording date inheritance/rollover as convention-derived support and never repairing arbitrary overnight or conflicting dates.
- [ ] T019 [US1] Write one failing parser test for occurrence-count assertions, single/two/positive-decimal forms, repeated count corroboration, missing counts, and contradictory counts in `tests/unit/test_scope.py`.
- [ ] T020 [US1] Implement only T019 in `rca/scope.py`, ignoring descriptive “this failure” references and rejecting zero, unsupported number words, missing, or distinct asserted counts.
- [ ] T021 [US1] Write one failing parser test for explicit request-clause isolation, observed datetime/component/reason aliases, duplicate requests, canonical `datetime, component, reason` ordering, and conflicting projections in `tests/unit/test_scope.py`.
- [ ] T022 [US1] Implement only T021 in `rca/scope.py`, using an allowlisted request grammar and excluding background “unknown” prose from requested fields.
- [ ] T023 [US1] Write one failing parser test for optional `task_index` cross-checks, all seven mapping values, missing metadata, invalid metadata, and mismatch without repair in `tests/unit/test_scope.py`.
- [ ] T024 [US1] Implement only T023 in `rca/scope.py` and `rca/contracts.py`, preserving parsed scope as the authority and returning stable issue codes for metadata failures.
- [ ] T025 [US1] Write one failing parser test for empty, unsupported, impossible, and materially conflicting scope results with null scope and stable issue codes in `tests/unit/test_scope.py`.
- [ ] T026 [US1] Implement only T025 in `rca/scope.py`, returning typed `interpreted`/`unsupported` results and never reading files, environment, network, clock, labels, or expected-answer data.
- [ ] T027 [P] [US1] Author independently reviewed, label-free expectations for all 70 public instructions and synthetic renamed/date/whitespace/midnight variants in `tests/fixtures/discovery/scope_expectations.json`; document that the fixture is not generated by `rca/scope.py`.
- [ ] T028 [US1] Write one failing CLI contract for an invalid scope followed by a valid scope, proving no telemetry read for the invalid case and continued processing in `tests/contract/test_scope_cli.py`.
- [ ] T029 [US1] Implement only T028 in `agents/discovery.py`, exposing `solve(instruction, dataset_dir, ctx)` through the explicit `--agent agents.discovery` mode with scope-only findings `not_run` and `capability_not_implemented`.
- [ ] T030 [US1] Write one failing writer contract for `scope.json`, `findings.json`, `operations.jsonl`, truthful four-section evidence, zero model usage, and blank prediction checkpoint ordering in `tests/integration/test_scope_artifacts.py`.
- [ ] T031 [US1] Implement only T030 in `rca/outputs.py` and `agents/discovery.py`, writing sidecars/evidence/usage before publishing each prediction checkpoint and leaving the operation journal empty when telemetry is not attempted.
- [ ] T032 [US1] Write one failing capability-scope validator test for row association, instruction hash, Unicode offsets, scope invariants, status/nullability, truthful evidence, and zero usage in `tests/contract/test_validate_discovery.py`.
- [ ] T033 [US1] Implement only T032 in `scripts/validate_discovery.py`, keeping it independent from parser-generated expectations and separate from the strict placeholder validator.
- [ ] T034 [US1] Write one failing runner compatibility test for explicit discovery/stub agent selection, scope-only exit code 1 for nonempty input, header-only exit 0, and unsupported `--resume` in `tests/integration/test_discovery_runner.py`.
- [ ] T035 [US1] Implement only T034 in `run.py`, `rca/inputs.py`, and `rca/outputs.py`; preserve the official three-flag command, input preflight, original order, later valid rows, and explicit `agents.submission` regression mode.
- [ ] T036 [US1] Review every R1 change in the parent task against `specs/004-prompt-anomaly-integration/contracts/prompt-input.md` and `specs/004-prompt-anomaly-integration/contracts/integration.md`; run each changed test, the 70-row scope check, scope validator, CLI smoke, and stub regression, recording evidence in `specs/004-prompt-anomaly-integration/reviews/r1-scope.md`.

## Phase 4: User Story 2 — R2 inventory (Priority: P1)

**Goal**: Discover and validate the mounted Track 1 source inventory for an
interpreted scope, preserving raw values, identities, units and source receipt.

**Independent Test**: Run renamed deployments, changed replica counts, missing
sources, unsupported schemas, mixed timestamp units and forbidden answer-file
access traps against an authored inventory fixture.

- [ ] T037 [US2] Write one failing inventory test for supported source-family discovery, variable deployment identities, resource identities and KPI names in `tests/unit/test_inventory.py`.
- [ ] T038 [US2] Implement only T037 in `rca/telemetry/inventory.py`, discovering files/columns/resources from the mounted dataset without fixed development paths, component allowlists, replica counts, labels, or answers.
- [ ] T039 [US2] Write one failing inventory test for schema-family validation, missing/unsupported fields, raw-value preservation, and seconds/milliseconds timestamp qualification in `tests/unit/test_inventory.py`.
- [ ] T040 [US2] Implement only T039 in `rca/telemetry/inventory.py` and `rca/telemetry/schema.py`, reporting unsupported/missing fields explicitly while retaining source conversion identity and raw values.
- [ ] T041 [US2] Write one failing source-snapshot test for content digests, extraction/schema versions, complete/incomplete markers, output-local prepared storage, and answer-file/network access traps in `tests/integration/test_source_snapshot.py`.
- [ ] T042 [US2] Implement only T041 in `rca/telemetry/snapshot.py`, rebuilding or rejecting incomplete/incompatible prepared views beneath `--out/prepared` and charging cold work once.
- [ ] T043 [US2] Write one failing inventory-operation test for valid empty selection, invalid argument, unavailable source, failed execution, truncation and budget exhaustion receipts in `tests/unit/test_inventory_operation.py`.
- [ ] T044 [US2] Implement only T043 in `rca/discovery/operations.py`, validating inventory arguments before reads and emitting provenance, coverage, timing and stop reason for every attempt.
- [ ] T045 [US2] Review R2 in the parent task against `specs/004-prompt-anomaly-integration/contracts/executor.md`, `specs/004-prompt-anomaly-integration/contracts/integration.md`, and `specs/004-prompt-anomaly-integration/contracts/discovery-policy.md`; run inventory tests, answer-file/network traps, R1 CLI regression, and record `specs/004-prompt-anomaly-integration/reviews/r2-inventory.md`.

## Phase 5: User Story 2 — R3 recorded traces (Priority: P1)

**Goal**: Select scoped trace roots and recover available recorded spans with
identity, provenance, duplicate/conflict visibility, boundary coverage and
duration qualifications.

**Independent Test**: Use unsorted, cross-partition and boundary-crossing trace
fixtures with duplicate IDs, unresolved parents, unknown roots, variable
frontend identities and independently enumerated expected observations.

- [ ] T046 [US2] Write one failing trace-selection test for deployment and the half-open `[start, end)` query/reference windows in `tests/unit/test_trace_selection.py`.
- [ ] T047 [US2] Implement only T046 in `rca/telemetry/traces.py`, selecting roots by current snapshot identity and declared policy without stopping early on out-of-window rows.
- [ ] T048 [US2] Write one failing trace-recovery test for unsorted/cross-partition inputs, selected trace expansion, boundary completion, continuation cursors and explicit incomplete coverage in `tests/unit/test_trace_recovery.py`.
- [ ] T049 [US2] Implement only T048 in `rca/telemetry/traces.py`, recovering all available selected records within bounded pages and preserving withheld/stop information.
- [ ] T050 [US2] Write one failing trace-integrity test for duplicate/conflicting span IDs, unresolved ancestry, source locators, deployment-qualified identity and raw duration/unit flags in `tests/unit/test_trace_integrity.py`.
- [ ] T051 [US2] Implement only T050 in `rca/telemetry/traces.py`, retaining every duplicate/conflict and recording logical CSV record provenance rather than silently overwriting observations.
- [ ] T052 [US2] Write one failing frontend-role test for discovered compatible identities, unknown/ambiguous roots, multiplicity preservation and provisional duration-unit qualification in `tests/unit/test_trace_roles.py`.
- [ ] T053 [US2] Implement only T052 in `rca/telemetry/traces.py` and `rca/discovery/trace_facts.py`, binding only the configured current-deployment role and leaving unknown structure generic/qualified.
- [ ] T054 [US2] Write one failing operation integration test for `select_spans` and `recover_traces` receipts, source/policy identity, limits, coverage and stop reasons in `tests/integration/test_trace_operations.py`.
- [ ] T055 [US2] Implement only T054 in `agents/discovery.py` and `rca/discovery/operations.py`, routing typed trace operations through the shared context and retaining R1 status behavior for incomplete capability.
- [ ] T056 [US2] Review R3 in the parent task against `specs/004-prompt-anomaly-integration/contracts/discovery-policy.md` and feature 003 provenance rules; run trace tests, locator resolution, R1 stub/discovery CLI regressions, and record `specs/004-prompt-anomaly-integration/reviews/r3-traces.md`.

## Phase 6: User Story 2 — R4 resource series (Priority: P1)

**Goal**: Independently retrieve bounded container/node/service/mesh/runtime
metric observations, including useful findings when frontend traces are normal
or missing.

**Independent Test**: Use long-format and wide service fixtures with planted
resource changes, missing frontend traces, invalid KPI names, empty series,
unknown units and isolated spikes.

- [ ] T057 [US2] Write one failing metric-inventory test for long-format source families, wide service fields `rr`, `sr`, `mrt`, `count`, exact resource identity and KPI enumeration in `tests/unit/test_metric_inventory.py`.
- [ ] T058 [US2] Implement only T057 in `rca/telemetry/metrics.py`, treating each service field as a separate raw KPI and never inferring unit or success/error semantics from abbreviations.
- [ ] T059 [US2] Write one failing metric-series test for independent deployment/resource/KPI/unit/time selection, frontend absence tolerance, valid empty series and bounded sample retrieval in `tests/unit/test_metric_series.py`.
- [ ] T060 [US2] Implement only T059 in `rca/telemetry/metrics.py` and `rca/discovery/operations.py`, preserving exact context and distinguishing an empty result from an invalid or unavailable request.
- [ ] T061 [US2] Write one failing metric-qualification test for unknown units, counter semantics, duplicate/conflicting samples, missing fields, gaps and nonfinite values in `tests/unit/test_metric_qualifications.py`.
- [ ] T062 [US2] Implement only T061 in `rca/telemetry/metrics.py`, retaining raw values and explicit qualifications while refusing cross-unit pooling, interpolation, cumulative-counter rates, or fabricated values.
- [ ] T063 [US2] Write one failing packet-limit test proving comparison sees all inspected samples while display sampling retains an isolated spike and exact locator in `tests/unit/test_metric_packets.py`.
- [ ] T064 [US2] Implement only T063 in `rca/discovery/packets.py`, applying the declared 120-value display rule after comparison and recording returned/withheld counts and continuation state.
- [ ] T065 [US2] Review R4 in the parent task against `specs/004-prompt-anomaly-integration/contracts/discovery-policy.md`; run metric tests with and without frontend traces, invalid-KPI/empty-series cases, packet checks, and record `specs/004-prompt-anomaly-integration/reviews/r4-metrics.md`.

## Phase 7: User Stories 2 and 3 — R5 comparison and evidence packet (Priority: P1)

**Goal**: Turn independently retrieved observations into qualified, auditable,
channel-separated candidates and a structured case handoff without asserting a
failure or diagnosis.

**Independent Test**: Compare authored trace-duration, structural, metric,
sparse/zero/constant/missing-reference and candidate-ordering fixtures against
an independent fact inventory; validate finite values, provenance and coverage.

- [ ] T066 [US2] Write one failing duration-comparison test for frozen five-minute references, C1 context, at least 20 eligible occurrences, median, signed absolute excess, support and unavailable qualifications in `tests/unit/test_trace_comparisons.py`.
- [ ] T067 [US2] Implement only T066 in `rca/discovery/comparisons.py`, versioning the policy and retaining nonpositive qualified findings without calling historical typicality healthy.
- [ ] T068 [US2] Write one failing structural-comparison test for direct-child multisets, multiplicity-only changes, added/removed pairs, unmatched shapes, frequencies and no-reference unavailable status in `tests/unit/test_structure_comparisons.py`.
- [ ] T069 [US2] Implement only T068 in `rca/discovery/comparisons.py`, keeping unknown structure unknown and separate from duration scoring.
- [ ] T070 [US2] Write one failing metric-comparison test for per-sample median differences, both directions, sparse/constant/zero/contaminated references, insufficient support and no NaN/Infinity in `tests/unit/test_metric_comparisons.py`.
- [ ] T071 [US2] Implement only T070 in `rca/discovery/comparisons.py`, retaining qualified raw absolute differences and returning unavailable rather than ratios, percentiles, standardized scores or fault probabilities.
- [ ] T072 [US2] Write one failing candidate test for source-linked identity, observed interval, direction/magnitude, channel separation, deterministic tie order, truncation, repeated observations and failure-count-independent count in `tests/unit/test_candidates.py`.
- [ ] T073 [US2] Implement only T072 in `rca/discovery/candidates.py`, retaining candidate rationale and uncertainty without grouping by prompt failure count or treating reused evidence as independent corroboration.
- [ ] T074 [US3] Write one failing case-result test for `CaseDiscoveryResult`, scope/candidate/finding/relationship references, source-family coverage, stage status, timings and stop reason in `tests/contract/test_case_result.py`.
- [ ] T075 [US3] Implement only T074 in `rca/discovery/result.py`, preserving observed onset separately from inferred fault onset and keeping blank predictions for this milestone.
- [ ] T076 [US3] Write one failing discovery-validator test for status/nullability, row associations, provenance locators, policy/source versions, coverage, finite values, truthful non-diagnostic evidence and retained unavailable findings in `tests/contract/test_validate_discovery.py`.
- [ ] T077 [US3] Implement only T076 in `scripts/validate_discovery.py`, supporting `--capability discovery` independently from the official answer scorer and strict stub validator.
- [ ] T078 [US2] Review R5 in the parent task against `specs/004-prompt-anomaly-integration/contracts/discovery-policy.md`, `specs/004-prompt-anomaly-integration/contracts/integration.md`, and feature 003 qualifications; run all comparison/packet tests, validator checks, CLI regression, and record `specs/004-prompt-anomaly-integration/reviews/r5-comparison.md`.

## Phase 8: User Stories 3 and 4 — R6 corroboration, recovery and acceptance (Priority: P1)

**Goal**: Complete bounded relationship/log corroboration, operation audit,
budgets, replay/invalidation and the integrated discovery runner; promote the
default only after the full R6 gate.

**Independent Test**: Exercise exact and ambiguous relationships, targeted logs,
every receipt outcome, forced limits, interrupted preparation, cache changes,
mixed case statuses, checkpoint failure, and a cold 20-case Docker rehearsal.

- [ ] T079 [US2] Write one failing relationship test for exact evidence-linked joins, supported time intervals, ancestry/dependency/placement distinctions, and ambiguous service/replica/host targets in `tests/unit/test_relationships.py`.
- [ ] T080 [US2] Implement only T079 in `rca/discovery/relationships.py`, preserving unresolved relationships and never converting recording identity or naming resemblance into an exact request target.
- [ ] T081 [US2] Write one failing targeted-log test for a declared question, motivating observations, bounded source/resource scope, source locators, ambiguity and 200-record response limits in `tests/unit/test_targeted_logs.py`.
- [ ] T082 [US2] Implement only T081 in `rca/telemetry/logs.py`, allowing log reads only for a concrete supported follow-up and recording inspected/uninspected family reasons.
- [ ] T083 [US4] Write one failing operation-journal test for every accepted, rejected, empty, unavailable, failed, truncated and exhausted operation with question, bounded args, policy/source IDs, coverage, timing and stop reason in `tests/integration/test_operation_journal.py`.
- [ ] T084 [US4] Implement only T083 in `rca/discovery/journal.py`, persisting `cases/<row_id>/operations.jsonl` under `--out` and charging shared prepared work once.
- [ ] T085 [US4] Write one failing budget test for monotonic run/case limits, finalization reserves, shared preparation charge, bounded page/byte/record work, partial stop reasons and a later case retaining its allocation in `tests/unit/test_budgets.py`.
- [ ] T086 [US4] Implement only T085 in `rca/discovery/budget.py` and `rca/discovery/context.py`, enforcing the plan's initial ceilings/reserves and never treating exhaustion as no anomalies.
- [ ] T087 [US4] Write one failing replay/cache test for completed-result identity, source/instruction/deployment/policy invalidation, incomplete-build rejection, overlap reuse with separate row scopes, and controlled partial replay in `tests/integration/test_replay_cache.py`.
- [ ] T088 [US4] Implement only T087 in `rca/discovery/cache.py`, recording deterministic work boundaries/continuations and excluding elapsed time/run IDs from substantive result identity.
- [ ] T089 [US3] Write one failing integration test for shared preparation and repeated windows: reuse compatible evidence while retaining each row's instruction, projection, failure count and case artifact in `tests/integration/test_shared_preparation.py`.
- [ ] T090 [US3] Implement only T089 in `agents/discovery.py` and `rca/discovery/result.py`, producing `discovery-run.json` with shared preparation identity/time, associations, budgets and per-case status inventory.
- [ ] T091 [US3] Write one failing end-to-end artifact test for the official three-flag command, all required case sidecars, four evidence headings, blank predictions, zero model usage and explicit stub-mode regression in `tests/integration/test_discovery_end_to_end.py`.
- [ ] T092 [US3] Implement only T091 in `run.py`, `rca/outputs.py`, and `agents/discovery.py`, retaining the three-flag default on the last accepted stub until R6 acceptance and exposing discovery through the optional agent selector.
- [ ] T093 [US4] Write one failing failure-progress test for unsupported scope, partial/unavailable discovery, valid empty findings, recoverable later cases, fatal output failure, preserved prior CSV checkpoint and exit codes 1/2/3 in `tests/integration/test_discovery_failures.py`.
- [ ] T094 [US4] Implement only T093 in `run.py` and `rca/outputs.py`, persisting sidecars before prediction checkpoints, continuing after recoverable case failures, and aborting visibly on global/persistence failure.
- [ ] T095 [US4] Write one failing cold-runtime rehearsal test/spec for 20 development cases, no prebuilt index, 2 CPUs, 8 GB, no GPU/network, preparation included in wall time, and peak-memory/coverage/status reporting in `tests/integration/test_cold_rehearsal.py`.
- [ ] T096 [US4] Implement only T095 in `Dockerfile` and `docs/demo-harness.md`, keeping runtime data under mounted input/`--out`, requiring no key/model for discovery, and documenting measured limits without claiming final diagnosis readiness.
- [ ] T097 [US4] Review all R6 code in the parent task against `specs/004-prompt-anomaly-integration/acceptance.md`, the four contracts, the constitution and feature 002 compatibility; run the full discovery acceptance corpus, stub regression, validator, forbidden-data/network traps, replay/invalidation checks, and cold 20-case rehearsal, recording evidence in `specs/004-prompt-anomaly-integration/reviews/r6-acceptance.md`.

## Phase 9: Polish and cross-cutting verification

**Purpose**: Reconcile documentation and preserve an auditable handoff after all
accepted R0–R6 slices. This phase does not broaden Feature 004 into diagnosis or
submission model work.

- [ ] T098 [P] Run the changed unit/contract/integration suites plus the 26-test stub regression and reconcile actual commands/results in `specs/004-prompt-anomaly-integration/reviews/execution-log.md`.
- [ ] T099 [P] Update `specs/004-prompt-anomaly-integration/quickstart.md`, `specs/004-prompt-anomaly-integration/acceptance.md`, and `docs/demo-harness.md` with only measured discovery behavior, pending gates, and truthful blank-prediction status.
- [ ] T100 Review every changed file in the parent task against the constitution, plan, contracts, acceptance matrix and runtime snapshot; record findings and unresolved risks in `specs/004-prompt-anomaly-integration/reviews/code-review.md` without committing or modifying unrelated dirty work.

## Dependencies and execution order

```text
T001 → T006/T008/T010 (seam confirmation) → T007/T009/T011 → T012 (R0 foundation)
T012 → T013–T036 (R1 / US1) → T037–T045 (R2 / US2)
R2 → T046–T056 (R3 / US2) → T057–T065 (R4 / US2)
R4 → T066–T078 (R5 / US2+US3) → T079–T097 (R6 / US2+US3+US4)
R6 → T098–T100
```

Shared runtime files (`run.py`, `rca/contracts.py`, `rca/outputs.py`,
`agents/discovery.py`, and `rca/discovery/operations.py`) are edited only in
sequence. Within a red/green pair, the red test must fail for the intended
reason before its green task starts. Review and CLI regression tasks are gates;
the next slice does not start from an unreviewed or failing prior slice.

### User story dependencies

- **US1 (P1)**: Starts after R0 foundation; independent scope parser and scope-only CLI slice. It must not read telemetry.
- **US2 (P1)**: Starts after US1/R1; R2 inventory, R3 traces, R4 metrics, R5 comparisons and R6 corroboration are ordered dependencies within this story.
- **US3 (P1)**: Its R5 structured packet depends on US2 findings; its R6 runner handoff depends on the accepted packet and writer seam. It retains blank predictions and the explicit stub.
- **US4 (P1)**: R2 inventory receipts are prerequisites for R6 audit/budget/replay behavior; cold rehearsal depends on all R6 capabilities and feature 002 packaging.

### Parallel opportunities

- After T001, T002 and the independent R0 seam tests T006, T008 and T010 may be authored in parallel, but all remain blocked until seam confirmation.
- After each prior green task, independent fixture/test files for the next behavior may be prepared in parallel; implementation of shared files remains sequential.
- R3 trace work and R4 metric work are separate files but are intentionally run as ordered slices so each CLI gate observes the preceding accepted capability.
- R6 relationship/log tests may be authored in parallel; journal, budget, cache and runner integration tasks follow their red/green pairs.
- Documentation and final verification T098–T100 can run in parallel after the R6 review gate.

## Downstream dependencies (R7–R9; informational, out of Feature 004 scope)

Feature 004 must leave these seams compatible without implementing them:

| Slice | Owner | Consumes or verifies |
|---|---|---|
| R7 first diagnostic executor | Feature 007 | Consumes `CaseDiscoveryResult`/evidence packet; adds associated hypotheses, legal requested projection and GLM-family provider behavior. Feature 004 keeps blank predictions and does not add diagnosis code. |
| R8 investigatory loop | Feature 007 | Uses the declared operation registry for distinguishing questions and bounded finalize; no arbitrary Python or unrestricted executor is added to Feature 004. |
| R9 submission gate | Features 002/007 | Owns clean-image official submission, nonblank best guesses, exact answer vocabulary, cost/model routing, scorer parity, held-out evaluation and release evidence. Feature 004's no-call discovery rehearsal is not this gate. |

R7–R9 may begin only after the corresponding R6 handoff/review evidence is
available. Do not add provider calls, diagnosis entities, final answer assembly,
scoring, model routing or publication tasks to this file.

## Implementation strategy

1. Preserve the checked R0 baseline and confirm seams before any test task.
2. Deliver R1 as the MVP: pure scope interpretation, truthful sidecars and an explicit scope-only agent with stub regression.
3. Within each slice, complete the valid Track 1 path first, then add only the specified hardening cases; add R2 inventory, R3 trace facts, R4 independent metrics, R5 qualified comparison/packet, and R6 corroboration/audit/budget/replay in order, stopping at each review and CLI gate.
4. Promote the three-flag default only after T097 passes the full Feature 004 acceptance matrix and cold rehearsal. A scope-only or partial discovery run remains visibly incomplete.
5. Keep all TDD tests independent of implementation-derived expectations, use only supplied data at runtime, and report measured evidence. Parent-thread review is required after every slice; no task author commits or cleans the shared checkout.

## Task-generation validation

100 tasks total: setup 2, foundational/R0 10 (3 already evidenced), US1/R1 24,
US2/R2 9, US2/R3 11, US2/R4 9, US2+US3/R5 13, US2+US3+US4/R6 19, and polish 3.
Story-phase tasks carry `[US1]`–`[US4]`; every task has a checkbox, sequential
ID, and at least one concrete repository path. R0 checked tasks are supported by
`specs/004-prompt-anomaly-integration/reviews/execution-log.md`; no tests/code
were written by task generation. Optional `git` before/after task-generation
hooks were inspected and skipped because the shared checkout is dirty and the
user prohibited commits.
