# Tasks: P01 controlled live experiment

Scope: implement and execute only minimal-test.md's P01 and conditionally eligible cache smoke. S09 and production integration remain deferred. Checkpoint b83e97c preserves the design.

## Setup and foundations

- [X] T001 Create bounded standard-library transport and environment loading in experiments/semantic_encoding_v1/featherless_p01.py; preserve secrets outside artifacts.
- [X] T002 Create immutable admission, request/attempt ledger and preflight capability capture in experiments/semantic_encoding_v1/run_p01.py.

## US1 — Preserve execution evidence

Independent test: authored source facts and changed-entity/edge/missing-record controls.

- [X] T003 [US1] Write source-grounded scorer corruption tests in experiments/semantic_encoding_v1/test_p01.py before implementing the scorer.
- [X] T004 [US1] Implement raw-field, dictionary, evidence and structural validation in experiments/semantic_encoding_v1/score_p01.py.

## US2 — Produce faithful semantic symbols

Independent test: all six frozen requests contain only the frozen prompt and selected input; all 18 slots accounted for.

- [X] T005 [US2] Implement frozen-request construction, exact token preflight and bounded 18-attempt execution in experiments/semantic_encoding_v1/run_p01.py.
- [X] T006 [US2] Execute P01 under data/experiments/semantic-encoding-v1/P01/ and score immutable raw responses offline.

## US3 — Account for cache and cost

Independent test: missing/invalid usage, timeout and exhausted-budget controls; cache eligibility checked before further inference.

- [X] T007 [US3] Implement honest token/cost parsing and conditional six-call cache-smoke gating in experiments/semantic_encoding_v1/run_p01.py; test in test_p01.py.
- [X] T008 [US3] Execute the separately frozen cache smoke only if P01 fidelity, natural static-prefix length and cache observability gates pass; otherwise persist the concrete skip reason in the P01 result.

## Completion

- [X] T009 Record results and limitations in docs/research/experiments/semantic-encoding-v1/P01-result.md and update specs/008-featherless-trace-semantics/quickstart.md.
- [X] T010 Check spec/plan/tasks consistency and remaining work; preserve any failed or incomplete live study as such.

Dependencies: T001 → T002; T003 → T004; T002/T004 → T005 → T006; T007 before live admission; T006/T007 → T008 → T009 → T010. Scorer work and transport design can be developed independently, but this implementation proceeds sequentially. Tests must pass before live inference. The user subsequently requested semantic commits at meaningful checkpoints; commit only P01-owned files. Broader experiments remain separately scoped.

Execution preflight: 11 offline checks pass. The static prefix measures 626 provider tokens, so T008 must record an ineligible cache probe without executing its six calls. The first preflight used the documented token-array parser; its count-only response is preserved in run 001. Run 002 freezes the corrected adapter before inference.

Live outcome: run 20260917-p01-002 completed 18/18 inference attempts and passed all fidelity checks. Token-cost estimate $0.00614413; four observed full-request cache hits. T008 completed by the declared skip branch (626-token natural prefix), not by executing cache calls. The top-level cached_tokens adapter was corrected offline after the live run; original raw responses/ledger and first report are preserved. No model rerun. The user subsequently requested a semantic checkpoint for this completed slice.

## Phase 7: Convergence — deferred beyond the completed P01 run

Checked 10 functional requirements, 5 success criteria and 5 constitutional principles against the bounded implementation. The executed P01 task is complete; feature-wide convergence is not claimed. These remaining capabilities require a subsequent scoped implementation/execution request, not more calls in the completed study.

- [ ] T011 [US3] Implement a separately frozen six-attempt cache-probe sender in experiments/semantic_encoding_v1/run_p01.py with matched target suffixes, distinct early tags, counted seeds and explicit eligibility/quality gates per FR-005/FR-009 and minimal-test.md (missing, MEDIUM). The current 626-token prompt correctly skips this branch; do not add padding or dispatch new calls to close this task.
- [ ] T012 [US2] Implement and validate the deferred S09 scoped-annotation runner/sidecars in experiments/semantic_encoding_v1/run_s09.py and its independent status/outcome adjudication per FR-003/FR-004 and contracts/annotation-study.md (partial, HIGH for that later capability). P01 does not validate status mappings, arbitrary incomplete graphs or real-trace model integration; preserve those prerequisite distinctions and use a separately frozen study.

Outcome: tasks_appended. Current-slice checks and offline replay passed; no additional live study is authorized by this convergence assessment. Optional commit hooks skipped.
