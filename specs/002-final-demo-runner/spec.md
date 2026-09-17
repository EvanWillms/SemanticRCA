# Feature Specification: Final demo and submission runner

## Active milestone — empty-output harness (2026-09-17)

The user's task-generation request narrows the next implementation to the demo runner harness with empty outputs. This milestone takes precedence over the complete-runner requirements below for the current tasks only; those requirements remain the final submission target.

- **H-001 / US1**: Run the official three-flag CLI unattended using a stub agent, preserving original query IDs. For every valid query write a blank prediction string, a four-section evidence file explicitly stating diagnosis is not implemented, and a usage record with no model calls. A header-only query CSV produces header-only predictions.csv, empty usage.jsonl, and an empty evidence/ directory.
- **H-002 / US2**: Perform no telemetry analysis, network access, or model calls; require no key for this stub. Validate CSV/paths/IDs, restrict writes to --out, and atomically checkpoint completed rows. A clean run exits zero with an explicit harness-only notice; invalid invocation or write failure exits nonzero.
- **H-003 / US3**: Demonstrate and validate only CLI execution and output scaffolding. Provide REPORT.md and eval/ documentation with diagnosis, accuracy, routing comparison, and evidence quality marked not implemented/not measured.
- **H-004 / US4**: Supply a root Dockerfile and truthful README/AI disclosure for a local reproducible demo. Publication, merge/push, form submission, paid evaluations, and final-release certification are deferred.

Independent milestone checks: US1 checks row/file coverage and blank values; US2 checks empty input, preflight failure, no network/key, and checkpoint preservation; US3 checks that the demo/validator recognize placeholders without claiming benchmark validity; US4 checks the exact container command from an isolated build context without secrets or neighboring-repo dependencies. These are narrowed slices of the corresponding stories below, not completion of their full judging goals. All seven task types may flow through the stub without parsing incident scope.


**Feature Branch**: `002-final-demo-runner`
**Created**: 2026-09-17
**Status**: Specified; implementation and validation pending
**Input**: Prepare the final Track 1 demo runner for unattended judging, required artifacts, AI disclosure, secret checks, and default-branch submission before 3:00 p.m.

## User Scenarios & Testing

### User Story 1 — Run the submitted agent unattended (Priority: P1)

A judge builds the public repository and runs the official command on an unseen bundle, without editing files, downloading runtime dependencies, or selecting an agent manually.

**Independent test**: Build a fresh checkout, run the official command on a small fixture with a controlled model endpoint, and inspect outputs.

**Acceptance scenarios**:

1. Given a root Dockerfile and a mounted bundle, the official command runs the intended routed agent with no extra flags or prompts.
2. Given non-contiguous query row IDs and multiple failures, each query produces its own prediction, evidence file, and usage record; failure count, incident associations, requested fields, and ordering are preserved.
3. Given an overridden endpoint and runtime key, all model traffic uses that endpoint and no credential appears in output, logs, or the image.
4. Given valid inputs and an unavailable model, the run falls back within the GLM family and continues; exhausted models yield a best guess with explicit uncertainty, never fabricated evidence.

### User Story 2 — Finish under judging limits (Priority: P1)

A judge receives usable results for all 20 cases within the resource, time, and cost envelope, including when provider latency increases.

**Independent test**: Run fault-injected fixtures under the machine limits and measure a full 20-case rehearsal separately.

**Acceptance scenarios**:

1. Case and run budgets include retrieval, retries, model calls, formatting, and output persistence; new calls stop before they can consume reserved completion capacity.
2. A case error does not discard earlier results or prevent later cases from running. Output is checkpointed after each case.
3. HTTP 200 error bodies, timeouts, malformed responses, and missing modalities do not cause unbounded retries. Evidence describes what could and could not be established.
4. If externally killed, completed prediction checkpoints remain readable; unfinished work is never reported as complete.

### User Story 3 — Demonstrate and evaluate the actual submission (Priority: P1)

The team runs a case live, opens the evidence just produced, and presents a reproducible comparison of routing against the same agent on one model.

**Independent test**: Follow the demo script and reproduce saved metrics from committed evaluation artifacts without model calls.

**Acceptance scenarios**:

1. The approximately four-minute presentation includes a real case, its four-section evidence file, and measured comparison results.
2. Evaluation uses a frozen set separated from development/tuning exposure, identical retrieval and reasoning logic across configurations, repeated runs, and records accuracy, evidence review, dollars, seconds, and variation.
3. REPORT.md documents sample sizes, failures, uncertainty, fallbacks, and limitations. Missing or unsuccessful runs remain visible rather than being excluded from averages.

### User Story 4 — Submit the intended public revision (Priority: P1)

The team can verify that judges will clone the tested work and that the public repository meets disclosure and security requirements.

**Independent test**: Audit a fresh clone of the remote default branch against the release checklist.

**Acceptance scenarios**:

1. The root has one Dockerfile, README.md, REPORT.md, and eval/; the README identifies every AI model, coding assistant, and framework actually used and distinguishes generated work from team-written work.
2. A secret scan covers tracked content, publishable Git history, and the image/build context; unresolved credentials block publication and require rotation/removal.
3. The verified default-branch revision is merged and pushed before September 17, 2026, 3:00 p.m. PDT; the submission form and repository link are checked separately.

### Edge Cases

- CSV instructions contain newlines; row IDs are non-contiguous or reordered. Duplicate or invalid IDs are rejected before paid work.
- Tasks request different projections of time/component/reason; multiple failures may share a component. Do not deduplicate incidents by component.
- Metrics/logs use seconds, traces milliseconds, and answers UTC+8 regardless of host timezone.
- A component appears only in the unseen deployment; component names must come from the mounted data, not development lookup tables.
- Missing telemetry, empty candidate sets, invalid model choices, capacity-error bodies without choices, and uncertain token usage require explicit degradation.
- An empty query file writes valid empty output; invalid paths, missing credentials, or an unwritable output directory fail with a sanitized actionable error before calls.
- A new run must not silently inherit stale outputs. Resume is optional and requires compatible input/configuration identity if supported.

## Requirements

### Functional Requirements

- **FR-001**: Preserve `python run.py --dataset /data --queries /data/query.csv --out /out` and make it select the submission agent by default. Provide exactly one Dockerfile at repository root.
- **FR-002**: Read runtime credentials only from `FEATHERLESS_API_KEY`; honor `FEATHERLESS_BASE_URL`, defaulting to `https://api.featherless.ai/v1`. Use only GLM-family models at that endpoint.
- **FR-003**: Read case data only from the supplied dataset and query input; write runtime artifacts only under the output directory. No runtime installs, downloads, answer-file access, or other network services.
- **FR-004**: Write `predictions.csv` with `row_id,prediction`, one row per valid input query. Number incident objects from 1, emit exactly the specified failure count, sort incidents by estimated occurrence time, and preserve datetime/component/reason key order while omitting unrequested fields. Use exact benchmark component/reason strings and UTC+8 times.
- **FR-005**: Write `evidence/<row_id>.md` with Answer, Confidence, Evidence, and Ruled out sections. Every claimed observation or exclusion must have a source locator and a defensible interpretation; guesses and unavailable evidence must be explicit.
- **FR-006**: Write per-case `usage.jsonl` with wall time and per-model calls/input/output tokens, including fallback calls. Unknown usage must not be represented as a measured zero.
- **FR-007**: Bound retries and disable persistently unavailable models. On recoverable failures return a best guess and evidence describing limitations, then proceed to the next case.
- **FR-008**: Operate within 2 CPUs, 8 GB RAM, no GPU; remain below 600 seconds/$3 per case and 1,200 seconds/$25 per 20-case run. Preserve completed outputs under interruption.
- **FR-009**: Include REPORT.md and eval/ with a reproducible routed/single-model comparison, strict and partial accuracy, per-task results, evidence review, per-case cost/time, repeat variation, configurations, pricing, and failure analysis. Recompute saved metrics without paid calls.
- **FR-010**: Include the README AI disclosure, exact build/run instructions, environment variables, and a demo walkthrough using the same shipped runner.
- **FR-011**: Require secret audit and fresh-clone validation before public release; verify remote default-branch content, push deadline, and submission form completion. Record release evidence without credentials.
- **FR-012**: Keep development labels and exposed cases out of blind inference and held-out evaluation. Record dataset, configuration, code, split, and result identities.

### Key Entities

- **Case scope**: Original row ID, instruction, deployment, time window, failure count, requested fields.
- **Incident hypothesis**: Associated onset, exact component, legal reason, uncertainty, supporting and contradicting observations.
- **Case result**: Prediction, evidence, usage, timing, and completion/degradation status.
- **Run budget**: Remaining case/run time and estimated spend with reserves for pending calls and output.
- **Evaluation record**: Configuration, case split, repeat, source revision, outputs, metrics, and limitations.
- **Release record**: Tested revision, remote default branch, security checks, disclosure review, and submission status.

## Success Criteria

- **SC-001**: A fresh checkout completes the prescribed build and run without source edits or interactive setup beyond the judge-provided key and mounts.
- **SC-002**: All valid fixture queries receive correctly associated, parseable predictions and four-section evidence; all seven requested-field combinations and a multi-failure case pass the official format/scoring checks.
- **SC-003**: A measured 20-case rehearsal finishes below every official cap; injected recoverable faults preserve completed work and produce explicit degraded results.
- **SC-004**: Saved routed and single-model results reproduce reported metrics without model calls; every reported evidence claim sampled in review resolves to raw telemetry or is marked unsupported and corrected.
- **SC-005**: A reviewer completes the live-case/evidence/comparison walkthrough in approximately four minutes, and release checks identify the exact public default-branch revision and completed disclosures.

## Assumptions

Track 1 governs: its specific Dockerfile requirement supersedes the generic Dockerfile-or-compose notice. Official local challenge materials at revision `314cca0bba49e1bb137aa9094d1dac4cdf7e4490` supply the contract; see research.md. Deadline is September 17, 2026, 3:00 p.m. PDT. This feature plans a headless runner and demo, not a dashboard. No accuracy improvement is promised before measurement. Experiment 001 establishes neither a working diagnoser nor a prerequisite for shipping this runner; integrate its evidence only after validation. Implementation, paid evaluation, publication, merge/push, and form submission are subsequent work, not actions completed by this specification.

## Featherless semantic-consumer integration

When integrating [feature 008](../008-featherless-trace-semantics/spec.md), follow [ADR 0015](../../docs/adr/0015-featherless-trace-semantics-and-prefix-caching.md). FR-006/FR-008/FR-009 require cache-aware accounting that preserves unknown usage, distinguishes cost estimates from observed charges, and admits calls against conservative uncached costs with completion reserves. Provider discounts cannot be assumed to meet the official caps. Stable prompt packs are reusable computation inputs, not cached answers.

Integration acceptance must exercise missing cached-token counters, cold/evicted cache, invalid responses and fallback calls; all attempts remain accounted for and saved metrics reproduce offline. Model annotations retain their evidence, uncertainty and version boundaries in FR-005 evidence output. The isolated S09 one-model/no-retry policy applies only to that experiment; it does not remove FR-007's production recovery obligations. This extension does not enlarge the H-001/H-002 zero-call stub milestone or assert production readiness.
