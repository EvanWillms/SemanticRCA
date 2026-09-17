# S01 pre-execution review: harness and repository-authored code

Reviewed 2026-09-17 from `/Users/nonadmin/Development/SymbolicRCA`.
This review was read-only: no experiment, test suite, model call, telemetry
read, or repository file modification was performed.

## Authority and scope

Read the complete handoff at
`docs/research/reliability-taxonomy-review.v1/07-incremental-experiments-handoff.v1.md`.
For S01 it requires only the A1 synthetic T0/T1/T2 fixtures, an independently
frozen fact sheet, a minimal deterministic structural encoder/decoder, exact
operation/edge/count/entity recovery, graph equivalence under declared aliases,
the one-node/one-edge T2 delta, separate provenance auditing, zero model calls,
and a stop after S01. The active A1 plan and semantic-evidence contract were
also read at the relevant fixture and fidelity sections.

The requested repository-code review covered every authored code candidate
outside `.git/`, `data/`, `experiments/`, and `docs/research/` found by
`rg --files --hidden`:

- Runtime and container: `run.py`; `rca/contracts.py`, `rca/inputs.py`,
  `rca/outputs.py`; `agents/__init__.py`, `agents/heuristic.py`,
  `agents/submission.py`; `scripts/validate_harness.py`; `Dockerfile`.
- Tests: `tests/contract/test_empty_outputs.py`,
  `tests/contract/test_validate_harness.py`,
  `tests/integration/test_checkpointing.py`,
  `tests/integration/test_harness_failures.py`, and package initializers.
- Core hidden Spec Kit Bash: `.specify/scripts/bash/check-prerequisites.sh`,
  `common.sh`, `create-new-feature.sh`, `resolve-template.sh`,
  `setup-plan.sh`, `setup-tasks.sh`.
- Hidden Git extension Bash: `.specify/extensions/git/scripts/bash/`'s
  `auto-commit.sh`, `create-new-feature-branch.sh`, `git-common.sh`, and
  `initialize-repo.sh`.
- Hidden Git extension Python: `.specify/extensions/git/scripts/python/`'s
  `auto_commit.py`, `create_new_feature_branch.py`, `git_common.py`, and
  `initialize_repo.py`.
- Hidden Git extension PowerShell: `.specify/extensions/git/scripts/powershell/`'s
  `auto-commit.ps1`, `create-new-feature-branch.ps1`, `git-common.ps1`, and
  `initialize-repo.ps1`.

Non-code project metadata, templates, specs, ADRs, and README material were
not treated as runtime code. The relevant A1 plan, contract, ADR, and handoff
were consulted for constraints.

## Findings and S01 relevance

### 1. The existing runtime is not an S01 implementation

`run.py:1-100` is explicitly the official three-flag empty-output entrypoint.
It preflights a dataset directory and query CSV, dynamically imports an agent,
and writes the harness artifact shape. The default seam is
`agents/submission.py:1-37`; `solve()` deletes the instruction, dataset path,
and context and returns `Solution(prediction="", ... usage={})`. The heuristic
agent only delegates to that stub (`agents/heuristic.py:1-7`).

`scripts/validate_harness.py:1-5,202-227` validates I/O shape only and says so
in its output. The tests likewise cover blank predictions, evidence
placeholders, preflight failures, credential-free behavior, and checkpoint
rollback; no test asserts a semantic packet, decoder, graph, or expected S01
fact.

**Boundary/blocker:** do not route S01 through `run.py`, the default agent, or
the harness validator. They cannot read or encode the three span fixtures and
would produce a false blank-output result. S01 must remain an isolated
implementation/run under the handoff's experiment location, leaving the final
runner and prior artifacts unchanged. This is a routing limitation, not a
failure of the current harness contract.

### 2. The runner's I/O contract is otherwise safe but irrelevant to S01

`rca/inputs.py:1-130` resolves paths, requires an existing dataset directory
and UTF-8 CSV, rejects duplicate IDs and malformed rows, and rejects output
paths overlapping either input. `rca/outputs.py:1-162` creates predictions,
usage, and evidence artifacts, publishes predictions atomically, and rolls back
usage/evidence on a failed case. Those behaviors are coherent for the
empty-output milestone, but the output contract is incompatible with S01's
manifest/fixture/expected-facts/packet/fact-diff/result artifact contract.

The only minor robustness caveat found is `run.py:44-49`: agent import errors
are caught only for `ImportError` and `AttributeError`; an arbitrary
import-time exception from a selected custom agent can escape with a traceback.
That does not affect the default stub or an isolated S01 run.

### 3. No current runtime path introduces model or telemetry execution

The reviewed runner and agents contain no model client, network retrieval, raw
trace parser, or causal classifier. This is positive for S01's zero-model,
synthetic-only boundary. The stub intentionally ignores credentials and the
integration tests check that supplied Featherless values do not enter output
artifacts (`tests/integration/test_checkpointing.py:81-124`). Do not add or
reuse a real-data path to fill this gap during S01.

### 4. Hidden Spec Kit scripts are stateful workflow tooling, not S01 code

The core scripts resolve/persist feature state and templates. For example,
`common.sh:131-231` can write `.specify/feature.json`, and
`setup-plan.sh:30-64` / `setup-tasks.sh:25-60` create or replace planning
artifacts. They do not implement trace encoding. `check-prerequisites.sh:95-135`
uses the quoted assignments emitted by `get_feature_paths`, so its `eval` is
bounded by `%q` output, but running these scripts would still mutate project
state outside S01. They are therefore out of the execution path.

### 5. Hidden Git extension scripts can mutate branches, commits, and remotes

The Git scripts are fully separate from the harness. They initialize and commit
the repository (`initialize-repo.*`), auto-commit all changes
(`auto-commit.*`), create/switch branches, and may query/fetch remotes
(`create-new-feature-branch.sh:165-205,566-604`, Python counterpart
`:243-277,560-618`, PowerShell counterpart `:127-174,511-565`). They are not
needed for S01 and should not be invoked as part of experiment execution.
No reviewed S01 dependency requires network, Git mutation, or PowerShell.

### 6. No reviewed code supplies the A1 fixture or independent answer key

The A1 graph and expected constraints are specified in
`specs/001-candidate-recall-experiment/plan.md:43-73`: seven spans rooted at
`frontend#1 request.handle`, a checkout/cart/db chain, two catalog occurrences
on `catalog#1`, one on `catalog#2`; T1 is a bijective rename/shuffle; T2 adds a
fourth catalog child on `catalog#1`. The reviewed runtime has no representation
of those fixtures or their expected facts. The implementation must author and
freeze those inputs and expectations independently before encoder output is
seen. A generated answer key, constant labeler, or raw-record decoder would
invalidate the S01 gate.

## Decision for isolated S01

`supported_on_fixture`/`falsified`/`inconclusive` cannot be assigned by this
harness review: no S01 encoder was executed here. The harness review outcome is
**clear for isolated execution with one explicit routing blocker**:

1. Keep `run.py`, `rca/`, `agents/`, `scripts/`, Dockerfile, prior outputs,
   original telemetry, and hidden workflow tooling untouched.
2. Execute only the isolated S01 implementation against frozen T0/T1/T2.
3. Decode without raw-record access; audit provenance separately.
4. Require exact structural recovery, T0/T1 equivalence, and T0/T2's one-node/
   one-edge and count delta before reporting S01.
5. Stop after S01; do not launch S02-S09, any 18/126-call model matrix, or
   real-telemetry work.

No code-level defect in the reviewed harness blocks that isolated workflow.
The material blocker is that the existing final harness is intentionally not
the S01 encoder and must not be mistaken for one.
