# Investigation loop TDD record

The confirmed public seam for this demo slice is:

```python
investigate(evidence, assessor, operations, answer_policy, work_policy=None) -> dict
```

The assessor and operation callbacks receive detached state copies. Operation
results are complete `rca-evidence-v1` packets and are merged only after scope,
observation identity and collection-shape checks. The demo uses three operation
attempts, four assessment attempts and two consecutive non-progress attempts by
default, with no automatic retries.

## Red and green evidence

- Initial red collection attempt:
  `PYTHONPATH=libraries/rca_domain/src pytest -q libraries/rca_domain/tests/test_investigation.py -k useful_followup`
  stopped at collection because the concurrently developed package initializer
  imported sibling `ingestion.py` before that file existed. No task-owned file was
  changed to work around the sibling setup.
- Green first slice:
  `PYTHONPATH=libraries/rca_domain/src pytest -q libraries/rca_domain/tests/test_investigation.py -k useful_followup`
  passed after the sibling module became available.
- Green focused suite:
  `PYTHONPATH=libraries/rca_domain/src pytest -q libraries/rca_domain/tests/test_investigation.py`
  passed 5 tests.
- Green syntax/whitespace checks:
  `PYTHONPATH=libraries/rca_domain/src python -m py_compile libraries/rca_domain/src/rca_domain/investigation.py`
  and `git diff --check` passed.

The cases cover useful follow-up and reassessment, rejected completion with an
unknown support reference, bounded best-guess finalization, assessor/provider
failure with an explicit terminal reason, and preservation of both sides of a
conflicting observation update.

This is the intentionally small demo controller. Hard wall-clock cancellation,
cost accounting, spawned callback isolation, persistence and the remaining L01–L18
edge trajectories remain deferred to the full implementation slice.
