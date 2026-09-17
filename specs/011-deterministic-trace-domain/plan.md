# Implementation plan

Place a separately installable package under `libraries/trace_semantics` with
its own `pyproject.toml`, README and tests. Keep the restricted S01 experiment
and runtime integration untouched so concurrent agents can continue their work.
The library carries forward the fidelity boundaries of ADRs 0002, 0011, 0012
and 0015, without importing experimental runners or their fixture mappings.

Use a narrow JSON-compatible input boundary adapted to recovered Track-1
traces (`trace_id`, `deployment`, `spans` containing `raw` and `locator`). Retain
the whole input trace, including optional context, coverage and other extensions.
The collection policy declares units; explicit contradictory source context
must remain an unresolved timing qualification. The domain representation separates
raw evidence, accepted facts and deferred facets. Description construction is
pure and deterministic. No implicit unit or status conventions are installed.

Use Luna (`gpt-5.6-luna`, `xhigh`) agents for vertical TDD slices after public
seam confirmation. Pin review to the files created in this task, with starting
repository HEAD `fd49fbc98fc96b89552e2e7df95e74fac024a220`. Existing uncommitted
files predate this work and are outside the change review. Run independent
standards and specification reviews, repair findings, and validate standalone
installation plus the repository regression suite.

## Constitution compliance and workflow exception

Evidence remains authoritative and uncertainty explicit; the caller owns bounded
selection. There is no inference cost, output-contract change or diagnosis claim.
Synthetic controls validate representation only, without claiming deployment
accuracy or compression gains.

The user explicitly requested working ahead of other agents in the shared
repository. This feature records specification, plan and tasks locally rather
than invoking branch-changing or automatic-commit Spec Kit workflows against
their shared checkout. This is a documented workflow exception under Governance;
the implementation and review still validate requirements and remaining tasks.
The user subsequently requested semantic commits at meaningful checkpoints;
stage and commit only this feature's explicitly owned paths.
Follow-up owner: repository maintainer, for future runtime integration and its
normal Spec Kit workflow. Do not switch the shared branch or alter existing
artifacts.
