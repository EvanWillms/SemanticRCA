# Review scope and evidence

Review baseline: repository HEAD
`fd49fbc98fc96b89552e2e7df95e74fac024a220`, plus the existing uncommitted
checkout captured before work. Review includes every code file created in
`libraries/trace_semantics` and this feature's documents. Other agents' changes
are outside this task's review; existing experimental encoders were inspected
as design inputs and are not modified or certified by this feature.

Standards sources: `CONTEXT.md`, `.specify/memory/constitution.md`, ADRs 0002,
0010, 0011, 0012 and 0015. Requirements source: `spec.md` and the user's request.

## Baseline

- `python3 -m pytest tests -q`: 41 passed, 12 subtests passed.
- `python3 -m pytest experiments/semantic_encoding_v1/test_s01.py experiments/semantic_encoding_v1/test_s02_s09.py -q`:
  14 passed, 3 subtests passed.

## Demo checkpoint review

Reviewed all source modules (`partition.py`, `description.py`, `__init__.py`,
`demo.py`), both test files and packaging. Luna extra-high agents implemented
partitioning and description slices; an independent Luna reviewer checked
standards and exercised the authored happy path. The owner reviewed the public
contract, full source, integration, packaging and scope reconciliation.

Demo blockers repaired: CSV numeric strings rejected as timing, malformed parent
values crashing processing, mismatched trace rows contributing accepted facts,
missing fields treated as complete records, conflict records choosing a winner,
input aliasing/coercion, missing policy in description and duplicate-envelope raw
loss. Description tests were moved from an accidentally written repository test
path into the isolated package before committing.

Validation at the demo checkpoint:

- `python3 -m pytest libraries/trace_semantics -q`: **19 passed**.
- `PYTHONPATH=libraries/trace_semantics/src python3 -m trace_semantics.demo`:
  **PASS**, 2 selected traces, 3 occurrences, early operation/status deferrals,
  exact raw recovery and deterministic two-stage/composed encoding.
- `python3 -m ruff check libraries/trace_semantics/src libraries/trace_semantics/tests`:
  **passed**.
- `python3 -m pytest tests -q`: **43 passed, 12 subtests passed** on the shared
  checkout (other owners' tests can change independently).
- Package copied outside the repository, built and installed with no runtime
  dependencies; isolated Python 3.12 import verified. Final installed demo is
  checked again against the committed source candidate.

## Remaining findings, outside the user-prioritized demo path

- Root handling currently accepts `None` like the documented blank-string marker;
  use exact `""` for the demo. Numeric identifiers are also accepted and need a
  stricter type-sensitive identity contract before broad ingestion.
- Evidence IDs include enclosing trace/deployment/raw/locator with a truncated
  digest and per-envelope duplicate suffixes. Repeated malformed envelopes need
  globally collision-safe evidence addressing. Complete valid demo envelopes
  have scoped, resolvable references.
- Context survives exactly in `trace["raw"]` (and `raw_envelopes` for merged
  inputs); the final description does not yet expose it as a separate structured
  field. Full ADR 0010 claim metadata is also a follow-up.
- Equivalent unit aliases can be treated as contradictory. Use consistent
  canonical units in the demo. No endpoint conversion or causal timing is claimed.
- Conflict groups repeat evidence membership in each deferral, so large conflict
  groups can consume quadratic space. Adversarial nesting and forged partitions
  need broader boundary validation.

These findings limit full robustness acceptance. None blocks the reviewed,
complete authored happy path. Per the user's latest instruction, stop at this
available interface and passing demo; do not claim production readiness,
compression gains, diagnosis accuracy or complete original-spec acceptance.

## Isolated follow-up verification

The user resumed remaining library work, then limited completion to three
material steps: partition fixes, description validation/context, and verified
commit/handoff. This follow-up is on `fix/trace-semantics-robustness`; it does not
rewrite the historical demo findings above.

The recorded root/typed identity, malformed evidence addressing, duplicate
envelope recovery, context/unit-alias, conflict-memory and parent-candidate
issues are repaired. Descriptions now expose context and shared trace-scoped
qualifications, and validate evidence/coverage/resolved-edge consistency.
Canonical JSON safely escapes strings and rejects recursive/non-finite input.

Independent Luna specification review reports no functional blockers and
confirms all parent candidates, typed composed encoding and malformed evidence
retention. Parent review covered all changed source/tests and caught a new
quadratic cycle-validation walk and raw-Python identity-key regression; both
were fixed before final verification. See [identity TDD notes](tdd-identity.md)
and [description TDD notes](tdd-description.md), including the recorded test
cadence deviation.

Final checks: **34 package tests passed**; Ruff passed on **source and tests**;
`git diff --check` passed. A fresh copy built and installed outside the repository
with no runtime dependencies; `python -I -m trace_semantics.demo` passed using
that installed package. The copied wheel was
`symbolicrca_trace_semantics-0.1.0-py3-none-any.whl`.

Limitations: structural validation does not authenticate telemetry or prove a
self-consistent supplied partition is genuine. Source operation mappings remain
caller supplied. No model, compression, diagnostic, causal, or production-readiness
claim is made. Further capabilities and hardening beyond these three steps are
deferred. Integration into the shared checkout is owned by the integration task.
