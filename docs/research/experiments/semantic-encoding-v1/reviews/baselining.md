# S01 pre-execution review: `short_window_baselining_v1`

Review scope: read-only inspection of every non-cache source, fixture, and test
under `experiments/short_window_baselining_v1/`, plus the S01 handoff
(`docs/research/reliability-taxonomy-review.v1/07-incremental-experiments-handoff.v1.md`),
the active A1 plan (`specs/001-candidate-recall-experiment/plan.md`), the A1
specification, and the semantic evidence contract. No experiments, tests, or
entrypoints were executed, and no repository files were edited.

## Coverage inventory

Reviewed implementation modules:

- `contracts.py` (227 lines): C0/C1/C2 direct-child signatures, support gates, duration comparisons, block bootstrap, membership hashing.
- `index.py` (378): source discovery, CSV validation/hashing, SQLite index, root/trace retrieval.
- `observations.py` (165): root observation construction, direct-child extraction, identity/parent/cycle/coverage flags.
- `runner.py` (604): 12 anchors, 90-minute collection, 360-cell matrix, cohort matching, comparisons, aging, pilot/matrix writers.
- `controlled_checks.py` (638): copied interventions, selector seam, expected-fact-backed control matrix.
- `real_controls.py` (280): real-trace selection and control execution writer.
- `analysis.py` (738): artifact reconciliation, exposure inventory, sensitivity summaries.
- `reporting.py` (794): decision-table/report generation and final-selection state application.
- `replay.py` (223): 57-window replay and artifact streaming.
- `replay_reconciliation.py` (382): replay artifact reconciliation and source-pointer sampling.
- `__init__.py` and `README.md`.

Reviewed tests/fixtures:

- `tests/test_contracts.py` (190), `test_controlled_checks.py` (146),
  `test_index_contract.py` (135), `test_observations_contract.py` (122),
  `test_runner_contract.py` (83), `test_index_cache_contract.py` (76),
  `test_analysis_contract.py` (83), and `tests/expected_facts.json` (130).

## Findings and S01 relevance

### P0 — This package is the wrong experiment and must not be dispatched for S01

`README.md:1-41` and `__init__.py:1-9` define a short-window real-telemetry
baselining study. The executable paths are `runner.py:479-556` (all 360
real-data policy/anchor cells), `runner.py:559-584` (real-data pilot),
`real_controls.py:222-276`, `replay.py:134-206`, and `analysis.py:697-718`.
They index supplied daily CSVs, write under
`data/experiments/short-window-baselining-v1/`, and evaluate real observations.

S01 explicitly requires only A1's synthetic T0/T1/T2, a deterministic
encoder/decoder, frozen authored facts, zero model calls, no real telemetry,
and output under `data/experiments/semantic-encoding-v1/<slice>/<run-id>/`.
The handoff also says the semantic implementation belongs in
`experiments/semantic_encoding_v1/` and that earlier outputs/original telemetry
must not be modified. This directory has no S01 runner, graph decoder, or S01
result contract. Running any of its entrypoints would execute a different
study and risk overwriting historical short-window artifacts. Treat this as a
hard blocker and do not reuse it as the S01 execution command.

### P1 — Its representation cannot satisfy the A1 structural fidelity contract

`contracts.py:27-68` emits only root operation/type plus a direct-child set or
multiset. `observations.py:66-83` indexes parent/child relations by bare
`span_id` and retains only direct children. It does not encode the complete
descendant graph, per-occurrence parent references, recording-entity bindings,
or entity equality/distinctness required by S01. C2's direct-child count is not
the A1 exact occurrence graph. `06-selected-trace-semantic-encoding-experiment.v1.md:41`
already classifies these baseline helpers as reusable input infrastructure and
states that they do not preserve the required full graph/timing/identity
relationships.

### P1 — Duplicate/composite identity handling can produce false graph facts if reused

In `observations.py:66-73`, `by_span` and `parent_by_id` are keyed only by
`span_id`; `parent_by_id[span_id]` silently takes `rows[0]` for duplicate
identities. `observations.py:74-83` also selects direct children by bare
`parent_span`. A parent ID from another trace or one of multiple conflicting
rows can therefore be treated as the authoritative parent/edge even though the
contract requires composite `(trace_id, span_id)` identity and lossless conflict
retention. The function later marks some cases unresolved, but it still emits
the potentially wrong edge/flags before that qualification. This matches the
documented hazard in `06-selected-trace-semantic-encoding-experiment.v1:46`.
If these helpers are consulted while building an S01 decoder, this is a fidelity
blocker; use a separate composite-key graph implementation.

### P2 — Timing semantics are incompatible with S01's declared synthetic units

`observations.py:15-20,127-143` unconditionally parses `duration_us`/`duration`
as integer microseconds and derives milliseconds/endpoints. The package README
and `index.py:314` label that conversion provisional for real telemetry. S01
requires declared synthetic timing units but tests structural facts only; using
this adapter would import the provisional real-data interpretation into the
synthetic gate. Keep it out of the S01 input path.

### P2 — End-to-end execution glue is not covered by this test suite

The tests exercise pure helpers and copied fixtures. There is no test invoking
the primary writers and validating their complete artifact contract for
`runner.run_matrix` (`runner.py:479-556`), `run_pilot` (`runner.py:559-584`),
`real_controls.run_real_controls` (`real_controls.py:222-276`),
`replay.run_replay` (`replay.py:134-206`),
`analysis.analyze` (`analysis.py:697-718`),
`reporting.generate_report` (`reporting.py:689-780`), or
`replay_reconciliation.reconcile_replay` (`replay_reconciliation.py:127-364`).
This does not affect the S01 decision once the package is excluded, but it is a
material risk if a maintainer later executes the short-window study again.

### P2 — Provenance test assertion is too weak for a fidelity gate

`tests/test_controlled_checks.py:81-103` names inverse source-link preservation
but only asserts that the set of source-pointer values is non-empty at line 90;
it does not check each transformed identity maps to the correct original row or
that parent/child links are restored. The test would pass with a wrong
permutation of source links. This is insufficient evidence for S01's separate
provenance requirement and should not be treated as validation of an encoder.

## Decision for isolated S01

Do not execute this directory for S01. It is useful only as background/input
infrastructure after explicit qualification, and its direct-child signatures
cannot stand in for the A1 graph packet. The isolated run should use the
dedicated `experiments/semantic_encoding_v1/` fixtures/codec and keep its
results in the semantic-encoding artifact namespace. The only execution
qualification from this review is therefore **blocked for reuse**, with no
short-window code change requested.
