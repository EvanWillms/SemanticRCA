# Tasks: Final demo runner — empty-output harness

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [contracts/runner.md](contracts/runner.md), [research.md](research.md), [quickstart.md](quickstart.md).
**Scope**: User-requested H-001–H-004 milestone. All tasks below are scaffold work. No diagnosis, retrieval, model integration, paid calls, accuracy evaluation, or publication.
**Tests**: Contract/integration checks are required by the feature specification, narrowed to this milestone. Use Python standard-library unittest.
**Organization**: Story labels retain US1–US4 from spec.md, but implement only their explicitly narrowed harness slices. Paths are relative to repository root.

## Phase 1: Setup

**Purpose**: Create only the runtime and test scaffolding needed for an offline harness.

- [X] T001 Create Python package markers at agents/__init__.py, rca/__init__.py, tests/__init__.py, tests/contract/__init__.py and tests/integration/__init__.py; use Python 3.12 standard library without adding model or telemetry dependencies.
- [X] T002 [P] Add .dockerignore excluding .git, .env files, credentials, data/, generated outputs, experiments/ and unrelated research; update .gitignore for harness output/cache paths without overwriting existing rules.

## Phase 2: Foundational

**Purpose**: Establish the input/result interface shared by the stories. Complete before story implementation.

- [X] T003 Define QueryRow and Solution in rca/contracts.py; retain `row_id (unique integer from input)` and `CSV-aware ingestion; no row-position substitution.` Solution holds prediction: str, evidence: str and per-model usage dict; support the public solve(instruction, dataset_dir, ctx) interface without incident/hypothesis entities.
- [X] T004 Implement CSV and path preflight in rca/inputs.py using a CSV reader with required row_id/instruction headers, multiline instruction support, all-row unique integer validation and deterministic input order; require existing dataset/query inputs and empty-or-absent writable output, reject output overlapping inputs and nonempty output before any result writes. Accept valid header-only input.

**Checkpoint**: A valid query list and output location can be resolved without telemetry access, credentials, or network.

## Phase 3: US1 — Run the harness unattended (P1; MVP)

**Goal**: Official CLI creates one empty result set per query through a replaceable agent seam.
**Independent test**: Two multiline queries with IDs 9 and 42 yield exactly two blank prediction rows, evidence/9.md and evidence/42.md, and two zero-call usage records without a key.

- [X] T005 [P] [US1] Write tests/contract/test_empty_outputs.py for original/non-contiguous IDs, multiline CSV, all seven task labels passing through unchanged, blank prediction strings, four evidence headings with unimplemented notices, and usage records with models={} and zero tokens/calls; tests must fail before output implementation.
- [X] T006 [P] [US1] Implement agents/submission.py stub solve() returning prediction="", explicit placeholder prose under Answer/Confidence/Evidence/Ruled out, and usage={}; create agents/heuristic.py as its compatibility shim. Never read telemetry, diagnose, call a model, or report invented evidence.
- [X] T007 [US1] Implement rca/outputs.py to initialize predictions.csv with row_id,prediction headers, empty usage.jsonl and evidence/; write per-case evidence and measured wall_s/zero-call usage before atomic same-directory replacement of the prediction CSV. Keep every temporary write under --out and preserve blank strings rather than serializing null or fake JSON.
- [X] T008 [US1] Implement root run.py with required --dataset/--queries/--out flags, default agents.heuristic, public Solution re-export, and sequential solve calls after complete preflight; print an explicit harness-only notice, exit zero for successfully written placeholders and nonzero on input/write errors. No credential check or network/client initialization; document any retained optional flags and explicitly reject unsupported resume.
- [X] T009 [US1] Run tests/contract/test_empty_outputs.py and record actual command/results in specs/002-final-demo-runner/checklists/harness-validation.md; verify invocation with no --agent override selects the stub.

**Checkpoint**: Local CLI MVP works. Blank predictions intentionally do not meet the final judged answer contract.

## Phase 4: US2 — Keep scaffold execution bounded and safe (P1)

**Goal**: No-call execution handles empty/malformed input and preserves completed outputs on failure.
**Independent test**: Header-only input creates empty artifacts; invalid inputs fail before rows are published; an injected persistence failure preserves the last complete CSV.

- [X] T010 [P] [US2] Add tests/integration/test_harness_failures.py covering header-only input, duplicate/noninteger IDs, missing required headers, malformed CSV, missing paths, nonempty output and output/input overlap; assert no successful partial run on preflight errors and no deletion of existing artifacts.
- [X] T011 [P] [US2] Add tests/integration/test_checkpointing.py injecting a failure before CSV replacement after one completed case; assert prior CSV remains parseable, later cases are not falsely reported complete and process fails visibly. Check no credentials appear in captured output or artifacts when fake sentinel environment values are supplied.
- [X] T012 [US2] Harden run.py and rca/outputs.py to satisfy T010/T011: disable bytecode writes before local imports, keep temporary files under --out, sanitize diagnostics, and terminate clearly on persistence failure while retaining prior checkpoints; do not add retry/model-budget machinery to the no-call stub.
- [X] T013 [US2] Run all tests/integration/ checks and update specs/002-final-demo-runner/checklists/harness-validation.md with measured scaffold timing and results; distinguish zero model cost by construction from unmeasured final-agent performance.

## Phase 5: US3 — Demonstrate output scaffolding honestly (P1)

**Goal**: Provide an offline output validator and a reproducible harness demonstration.
**Independent test**: Validator accepts expected placeholders, rejects missing/mismatched files and emits only a harness-shape success statement; documentation reports diagnosis and benchmark evaluation as unimplemented.

- [X] T014 [P] [US3] Add eval/fixtures/query.csv with synthetic multiline queries and non-contiguous IDs, plus eval/README.md explaining that fixtures validate I/O only and contain no benchmark telemetry, labels or accuracy results.
- [X] T015 [P] [US3] Create REPORT.md stating harness-only status, empty outputs, no model use, and diagnosis/routing/accuracy/evidence evaluation not implemented or not measured; list remaining final-runner gates without fabricated results.
- [X] T016 [US3] Implement scripts/validate_harness.py accepting query/output paths and checking complete ID coverage, truly blank predictions, four placeholder evidence sections and zero usage; reject missing/extra/duplicate IDs and print that successful scaffold validation is not official benchmark validation. Exercise it on T014 and deliberately damaged outputs, recording results in specs/002-final-demo-runner/checklists/harness-validation.md.
- [X] T017 [US3] Write docs/demo-harness.md with the exact local run and validator commands, fresh output setup, an example of inspecting generated files and an explicit unimplemented-diagnosis explanation; exclude routed/single-model result claims and API-key setup.

## Phase 6: US4 — Package the local demo (P1)

**Goal**: A standalone root image runs the same placeholder harness with the official command shape.
**Independent test**: Isolated source context builds and runs with read-only input, an empty output mount, --network=none, --cpus=2 and --memory=8g, without a key or host Python dependencies.

- [X] T018 [P] [US4] Add the single root Dockerfile using Python 3.12, WORKDIR /app, disabled bytecode and narrow COPY of run.py, agents/ and rca/; require no pip/runtime installs or custom ENTRYPOINT that conflicts with `python run.py`. Do not copy datasets, .git or secrets.
- [X] T019 [P] [US4] Write README.md with harness-only status, exact build/run command, supplied-mount prerequisites, no-key/no-network stub behavior, output definitions, demo/REPORT/eval links and accurate disclosure of actual AI assistants/models/frameworks and generated versus team-written work; do not invent unknown tool identities.
- [X] T020 [US4] Build from an isolated allowlisted source context and run the exact three-flag command in Docker with eval/fixtures/query.csv, read-only input, --network=none, --cpus=2 and --memory=8g; validate outputs with scripts/validate_harness.py, inspect image contents for excluded local data/secrets and record actual results or blockers in specs/002-final-demo-runner/checklists/harness-validation.md. Do not merge, push, publish or submit a form.

## Phase 7: Polish and cross-cutting checks

- [X] T021 Reconcile specs/002-final-demo-runner/quickstart.md and checklists/requirements.md with observed harness behavior; run the contract/integration tests and documented demo command, recording results in checklists/harness-validation.md and leaving checklists/release.md gates pending wherever the full diagnoser/evaluation/public release is required.

## Dependencies and execution order

```text
T001 + T002 → T003 → T004 → foundation complete
foundation → T005 + T006 → T007 → T008 → T009 (US1)
US1 → T010 + T011 → T012 → T013 (US2)
foundation → T014 + T015; US1 + T014 → T016 → T017 (US3)
foundation → T018 + T019; US1 + US2 + US3 + T018 + T019 → T020 (US4)
US1 + US2 + US3 + US4 → T021
```

Story verification is independent once prerequisites exist: US2 uses failure fixtures; US3 can validate fixture outputs; US4 checks the actual image. Shared runtime files must be edited sequentially. [P] denotes an independent file task at the stated prerequisite boundary, not permission to bypass its dependencies or launch agents automatically.

## Parallel examples by story

- **US1**: After foundations, T005 (contract tests) and T006 (stub/shim) use separate files; T007–T009 follow in order.
- **US2**: After US1, T010 (preflight failures) and T011 (checkpoint failures) may be authored together; T012 fixes the shared runtime afterward.
- **US3**: T014 (fixtures/eval documentation) and T015 (report skeleton) are independent; T016 waits for runnable outputs.
- **US4**: T018 (Dockerfile) and T019 (README) are independent once the foundation contract is stable; T020 waits for all integrated artifacts.

## Implementation strategy

Implement setup/foundation and US1 first for the local CLI MVP. Add US2 safety, US3 truthful validation/demo artifacts, then US4 packaging to complete the requested containerized harness. Tests precede relevant implementation and must demonstrate intended failure first; record actual outcomes, not assumed passes. No paid calls are needed. Keep every task unchecked until performed.

## Deferred final-runner coverage

Full FR-002 model access, FR-004 valid diagnoses, FR-005 evidence-grounded reasoning, FR-007 provider fallback, FR-008 production budgeting, FR-009 measured routing evaluation, FR-011 public release and FR-012 held-out evaluation remain future work. Current tasks cover the scaffold portions of FR-001/003/004/005/006/008/009/010 only. Finishing this file completes H-001–H-004, not the original full user stories or submission readiness. Do not run the official answer validator and relabel its expected rejection of blanks as a pass; do not weaken it to accept placeholders.

## Task-generation validation

21 tasks: setup 2, foundation 2, US1 5, US2 4, US3 4, US4 3, polish 1. Every task has a checkbox, sequential ID, concrete file paths and story labels in story phases. Optional before_tasks/after_tasks git-commit hooks are skipped because their auto_commit settings are disabled. No implementation or runtime tests were performed by task generation.

## Completion record

All 21 harness tasks completed and parent-reviewed on 2026-09-17. See [validation evidence](checklists/harness-validation.md) and [code review](reviews/code-review.md). This completion applies only to H-001–H-004. Full release gates remain pending.
