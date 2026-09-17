# S01 pre-execution review

Date: 2026-09-17. Scope: isolated S01, as required by the handoff's final assignment
and active A1 plan. S02–S09 are not part of this dispatch. Development/review work
uses Luna subagents requested at extra-high (`xhigh`) reasoning. Experiment model
calls remain zero.

## Existing repository coverage

The three subagents reviewed all 77 existing authored Python, Bash and PowerShell
files in [the hashed inventory](reviewed-code-inventory.json), with the Dockerfile
and relevant experiment documentation. Generated caches, telemetry, Git internals
and Markdown skill instructions are not executable project source.

- [Harness and workflow tooling review](reviews/harness.md)
- [Frontend experiment and trace-audit review](reviews/frontend.md)
- [Short-window baselining review](reviews/baselining.md)
- [Independent frozen-input review](reviews/fixtures.md)

Existing experiments and the final runner are not S01 implementations. The final
runner intentionally returns empty predictions; older experiment signatures do
not retain the complete graph. Some graph helpers collapse duplicate identities,
and timing helpers assume microseconds. These are limitations on reusing those
paths, not blockers for an isolated synthetic S01 run. No historical runner,
experiment, output, workflow script or telemetry is modified or invoked.

The new implementation imports only Python's standard library and its local
codec. It accepts one resolved synthetic rooted tree; missing/conflicting
observations are outside S01 and are rejected rather than repaired. There is no
raw data/model/benchmark access path.

## Frozen fixtures and comparison rules

Inputs, expected structural facts, codebook, and policy were authored and hashed
before encoder implementation. A separate agent checked every fixture and all
six freeze hashes without importing the encoder. T0 and T1 have seven spans;
T2 adds exactly one catalog#1 child. Timings are explicitly synthetic milliseconds.

The fixture review's ordering concern is resolved in `compare()` and documented
in the implementation README: node rows and edges are sorted; entity relations
are unordered span pairs with sorted endpoints; `distinct_pairs` counts spans
with different recording entities. These rules implement the frozen unordered
policy without changing any frozen fact. Cross-fixture equivalence uses an
operation/entity-colored rooted-tree signature; indistinguishable siblings need
not have a unique occurrence-level cross-fixture correspondence. Original IDs
and source positions remain separately resolvable.

No independent human annotation is available. Report fidelity as provisional
against authored expectations, with separate agent review—not independent human
validation or a deployment-accuracy estimate.

## New-code readiness

The [method review](reviews/method.md) caught an unmatched bracket and a gap in
checking the saved sidecar link before execution. The [implementation review](reviews/implementation.md)
records the corrections and ten focused contract tests. The [resolution review](reviews/method-resolution.md)
confirms the syntax correction, quality checks in decision aggregation, persisted
sidecar audit, and sidecar filename verification. The primary agent also read the
final codec, runner and test suite before execution. No remaining blocker was
found for the focused tests and one S01 attempt.

All 77 existing source hashes still matched the pre-review inventory immediately
before dispatch. None of the existing runtime code was changed. The run may now
proceed; failed checks must retain evidence and block progression to later slices.

## Test preflight correction

The first focused test invocation passed nine cases and failed one assertion in
`test_provenance_corruption_is_reported_without_raising`. That test retained a
`bad-index` mutation when starting its missing-digest case, so the auditor correctly
reported the invalid index before inspecting a digest. The primary agent reviewed
and corrected the test to deep-copy the original sidecar before deleting its digest.
No codec or acceptance expectation was changed. The original console log and source
snapshot are retained as `test-execution-attempt-001.txt` and
`test-attempt-001-code/`. S01 was not dispatched after that failed preflight.
