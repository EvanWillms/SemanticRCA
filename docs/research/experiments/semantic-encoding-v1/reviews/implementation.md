# S01 implementation review (pre-execution)

Reviewed `experiments/semantic_encoding_v1/codec.py`,
`run_s01.py`, the frozen fixtures, and README on 2026-09-17. Added
`experiments/semantic_encoding_v1/test_s01.py`. No unit test, experiment,
model call, telemetry read, or repository-wide test command was run during this
review.

## Findings and fixes

1. The runner had a syntax error in the T2 delta calculation:
   `added_nodes = sorted([[...] for n in added)` was missing a closing list
   bracket. Fixed in `run_s01.py`.
2. The runner already used `out.mkdir(parents=True, exist_ok=False)`, which is
   correct for a first run when `data/experiments/semantic-encoding-v1/S01`
   is absent. Extracted that operation into `create_run_dir()` for direct unit
   coverage; reuse still raises `FileExistsError` and cannot replace an earlier
   attempt.
3. `codec.encode()` indexed all nine record fields before validating shape, so
   a missing binding produced an uncontrolled `KeyError`. Added required-field
   validation with a bounded `ValueError`; unresolved parent references remain
   rejected.
4. `provenance_audit()` raised on missing/malformed sidecar pointers or invalid
   indices instead of producing an auditable difference. It now records source,
   pointer, and index differences and continues safely. The runner reloads the
   persisted sidecar before auditing and checks that the packet's declared
   `provenance_sidecar` matches the saved filename.
5. Fixture processing exceptions previously escaped after creating a partial run
   directory, leaving no fact-diff or result report. The runner now records the
   fixture error, writes an honest partial result, marks the decision
   `inconclusive`, and avoids evaluating dependent contrasts when a fixture did
   not complete. Contract mismatches remain `falsified`.
6. The runner previously checked unknowns but did not check quality or root/
   resolved-parent markers. Added `quality_checks()` and included its results in
   fact differences and failure selection. The result narrative now reports
   observed counts and pair counts from actual decoded facts rather than fixed
   claims. README and retained review artifacts are included in manifest source
   hashes where present.

## Test coverage added

`test_s01.py` contains ten focused unittest cases covering:

- exact frozen structural recovery and provenance for T0/T1/T2;
- T0/T1 identifier/order invariance;
- the T2 added node and edge;
- missing occurrence detection against frozen T2 expectations;
- entity-binding mutation detection with counts and edges held equal;
- parent-edge mutation detection with counts and entity relations held equal;
- missing binding and unresolved parent rejection at encode;
- provenance digest and malformed-index corruption without an exception;
- quality, root-marker, and resolved-parent checks;
- creation of missing run parents and rejection of reused run IDs.

The different-entity pair expectation remains the complement of the authored
same-entity pairs over all unordered span pairs, as implemented by
`run_s01.compare()`; it is not an independently invented label.

## Pre-execution disposition

The S01 code is ready for authorized test execution after the retained review
document required by `run_s01.py` exists. Execution must remain limited to S01's
frozen synthetic fixtures, with zero model calls and no real telemetry. Any
failed test or fixture boundary should be reported before considering S02.
