# Short-window baselining v1 runner

This package implements the standalone exploratory study defined in
`docs/research/experiments/short-window-baselining.md`. It is deliberately
separate from `frontend_blind_v1` and does not modify a production path or
select a default for the unattended agent.

The runner first builds a complete, source-hashed index of both supplied trace
files. It then freezes the explicit frontend component allowlist, reconstructs
blank-parent root observations by composite `(trace_id, span_id)` identity,
and evaluates the 5/10/15/30/60 minute × C0/C1/C2 × same-replica/pooled
matrix at all twelve UTC+8 anchors. Reference membership, boundary
exclusions, unknown identity/structure, six frozen aging slices, full
comparisons, structural frequencies, uncertainty summaries, and costs are
written under `data/experiments/short-window-baselining-v1/`.

`runner.evaluate_policy` is the selector/comparator seam used by the fixture
checks. The separate controlled-check module owns copied-observation
interventions. Staged replay of the 57 distinct supplied query windows is a
separate post-selection command and is intentionally not run by the matrix
command.

After independent review freezes `selection.json` with
`selection_status: "selected"`, run the staged command with
`python -m experiments.short_window_baselining_v1.replay --selection <path>`.
It groups duplicate prompt rows, freezes each window's reference at its start,
and emits all six five-minute slices for the primary policy and optional
qualified fallback. It refuses preliminary or inconclusive matrix decisions;
the replay is descriptive confirmation over overlapping supplied telemetry,
not held-out validation or a new policy search.

The code preserves the provisional raw-duration interpretation (microseconds
converted to milliseconds) and never reads benchmark labels, `scoring_points`,
or status semantics. Passing exploratory gates does not establish healthy
references, context equivalence, tail reliability, or RCA accuracy.

This standalone experiment was implemented and executed under the user's
explicit research instruction. It is a governance exception for retrospective
research only: no production integration is implied, the Spec Kit feature
sequence and runtime/model-routing integration are deferred, and the
maintainer owns any later production feature work.
