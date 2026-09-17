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
