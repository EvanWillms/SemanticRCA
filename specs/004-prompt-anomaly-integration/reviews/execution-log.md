# Feature 004 incremental execution record

## Starting boundary — 2026-09-17

User goal: incrementally execute `plan.md` using Luna subagents at extra-high reasoning effort, with TDD and review of all changes in this task.

The checkout is already substantially dirty, including untracked runtime files. Preserve existing work. Starting HEAD: `cc252900b235501cde01337247cee12284e32d99`. A byte-for-byte snapshot of the 18 existing runtime/test/build files is retained at `/private/tmp/symbolicrca-004-start-01a0b11d`; its `manifest.json` records SHA-256 hashes. Review task changes against that snapshot rather than misattributing all untracked work to this task. No branch/default promotion or commit has occurred.

## R0 baseline

- `python3.12 -m unittest discover -s tests -q`: 26 tests pass.
- Same runner suite under the shell's Python 3.14.3: 26 tests pass.
- Explicit `--agent agents.submission` CLI smoke on `eval/fixtures/query.csv`: exit 0.
- Strict `scripts/validate_harness.py` on those smoke outputs: exit 0.
- Smoke bundle/artifacts: `/private/tmp/symbolicrca-004-r0-gt95s6wv`.
- Broad `python3 -m unittest discover -v`: 36 tests pass and one experiment import fails because `pyod` is not installed. This is pre-existing experimental dependency coverage, not a runner regression.

## Execution gates

The TDD skill requires confirmation of public test seams before writing tests. Proposed seams: `interpret(QueryRow)`, declared discovery operations, and CLI output/checkpoint behavior. The user subsequently directed parallel work and explicitly prioritized getting the full happy path working with reduced defensive design. Execution proceeds at these plan-defined seams under that instruction.

The feature requirements checklist has 17 checked items and no unchecked items. The constitution requires task generation before implementation; tasks are being generated from the existing plan. Optional git commit hooks are not selected in this dirty shared checkout.

R1 is scope-only and must remain behind `--agent agents.discovery`, with `not_run` findings and exit 1 for nonempty runs. R6 full acceptance and cold 20-case rehearsal are required before promoting the default. R7–R9 remain downstream feature 007/002 obligations.

## R1 contract audit (Luna xhigh, read-only)

The current runner drops optional task metadata and has no interpretation/result-sidecar seam. Extend QueryRow and Solution compatibly; keep output persistence owned by OutputWriter. Preserve exact stub artifact/validator behavior. Unsupported scope is a typed result, not a fatal exception; later rows continue and a nonempty scope-only run returns 1. Persist a discovery run record for header-only inventories, which return 0. Validate all sidecars before publishing a case prediction checkpoint.

Parser review priorities: isolate imperative request clauses from background descriptions; anchor deployment extraction to supported identification/event forms; cross-check explicit occurrence counts; retain original Unicode support offsets; enforce fixed UTC+08 and exactly 30 minutes; reject explicit contradictions rather than repairing them. Public corpus coverage is necessary but does not replace authored rejection/portability cases.

Docker daemon availability confirmed: version 25.0.3. No container build/rehearsal has been performed. At the end of baseline preparation no runtime code or new tests had been written. Happy-path TDD implementation subsequently began under the user’s explicit direction.

## Happy-path implementation begins

User steering: parallelize practical work, reduce defensive design, get the full happy path working. Use the previously stated plan public seams. Initial CLI test `python3.12 -m unittest tests.integration.test_discovery -v` fails as expected: discovery agent unavailable, exit 3 rather than expected scope-only exit 1. Parent implements runner/writer integration while Luna xhigh agents implement scope, inventory and metrics in disjoint files. Independent public expectations cover all 70 prompts and passed a second manual review.

## Runnable happy path

The initial scope-only CLI test reached green, then was advanced to exercise explicit unavailable-source behavior as the discovery pipeline was connected. The full authored CLI fixture reached green: source inventory, recorded trace recovery/comparison, all five metric families, metric comparison, exact-resource targeted logs, sidecars, operation journal and blank predictions. The fixture produces both a raw duration excess of 200 and a resource metric difference of 25, independently of its one-failure prompt. The separate public-query check matched all 70 reviewed scope expectations. At this checkpoint the Python 3.12 suite passed 40 tests.

This is happy-path execution evidence, not full feature004 acceptance. SQLite prepared views, safe cache reuse, complete pagination, recorded-boundary partial replay, detailed resource ceilings and the cold 20-case real-data rehearsal remain open. Default remains the accepted stub. Review and adapter simplification are in progress; no deployment/commit has occurred.

## Combined demo checkpoint

Later user steering explicitly reduced acceptance work to core TDD and a runnable demo. The saved 18-file prerequisite snapshot was committed separately as `5487b25`; integration edits remained in the working tree. Ready owner handoffs consumed: baseline/comparison `7539556`, trace semantics `fda066b` (subsequent owner demo updates retained), and RCA investigation `c05a60e`. Domain implementation remains in those owners' commits.

Core red/green additions: the discovery CLI initially lacked `semantic_description`; the same public CLI fixture then passed through `trace_semantics`. Its scripted investigation subprocess initially failed because the entrypoint did not exist, then passed with an evidence-supported component-shaped answer, two assessments and one operation. A Luna regression test exposed selection of unrelated traces before the trace cap; `frontend_only=True` now selects declared frontend roots before recovery. A Luna demo test initially lacked a baseline report, then passed with 20 supported references, one descriptor and the investigation result.

Validation: 44 explicit runner/discovery tests passed on Python 3.12; the additional combined-demo CLI test passed (45 total). No broad experimental suite rerun was needed. `scripts/demo_discovery.py` generates the eight-family authored bundle and calls the actual discovery CLI, independent artifact validator, baseline library CLI and scripted RCA adapter using the same source data.

The combined command passed in Docker image `sha256:5fc865c4c3c3120ee09582c6a758bf107b0f3f65cf8c79492b4ec1fc1ddda589`, with network disabled, 2 CPUs and 8 GB memory. Host artifacts: `/private/tmp/symbolicrca-combined-demo-20260917/demo.md`. The report includes raw trace excess +200, independent metric difference +25, a supported 20-member baseline with approximately +0.2 ms descriptor excess under the explicit provisional normalization, one semantic trace with three deferred items, and a scripted `frontend-0` answer after two assessments and one operation. The script explicitly makes no causal accuracy claim; discovery predictions remain blank and model calls remain zero.

Shared prepared sources are now demonstrated inside the separate baseline library. Adoption into the complete discovery scheduler, full receipt/run metadata, complete pagination and partial replay, semantic graph validation, hard callback cancellation, real-data cold-20 performance and default promotion remain deferred. These are not claimed by the synthetic demo checkpoint.
