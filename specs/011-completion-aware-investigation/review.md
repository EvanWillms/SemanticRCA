# RCA domain library: review scope and evidence

Status: implementation pending public-boundary confirmation. This is a live
evidence record, not a completed code review or library-readiness claim.

## Owned scope

The task will own all files under `libraries/rca_domain`, its examples, packaging
and tests, and the implementation artifacts in this feature directory. That
library directory is absent at baseline. The trace encoder scaffold under
`libraries/trace_semantics` belongs to separate work and is not this library's
implementation or acceptance evidence.

Review baseline is repository HEAD
`fd49fbc98fc96b89552e2e7df95e74fac024a220` as inspected at initial continuation,
plus the explicit absence of the new library and existing uncommitted work.
Concurrent commits may advance HEAD; review task-owned current files directly
and record hashes rather than treating unrelated branch changes as this task.

Standards: `CONTEXT.md`, `.specify/memory/constitution.md`, ADRs 0002, 0006,
0007, 0010, 0011, 0015 and 0016. Requirements: this feature's specification,
contract, acceptance matrix and the user's full domain-library objective.

## Executed baseline checks — 2026-09-17

- `python3 -m pytest tests -q`: 41 passed, 12 subtests passed.
- `python3 -m pytest experiments/semantic_encoding_v1/test_s01.py experiments/semantic_encoding_v1/test_s02_s09.py experiments/semantic_encoding_v1/test_p01.py -q`: 28 passed, 3 subtests passed.
- Feature document relative links resolve.
- `git diff --check` for the task's documentation found no whitespace issues.
- Checkpoint `b888d82` contains only nine task-owned ADR/research/specification
  documents; other agents' staged files were excluded using explicit commit paths.

These results establish pre-implementation baselines only. They do not prove
that semantic traces can reach an investigation loop; that code does not yet exist.

## Pending review gates

- Public seam confirmation, followed by recorded Luna extra-high red/green slices.
- Independent standards and specification reviews covering every task code file.
- Current source/test/example/packaging inventory and hashes.
- Reproduction and repair of actionable findings.
- Requirement-by-requirement audit, standalone installation and complete trace-to-loop example.

## Parallel planning audits

Luna extra-high `rca_contract_audit` inspected actual S01, P01 and S02–S09 producers.
It recommends S01 plus provenance sidecar as the first compatibility input, an
explicit native envelope for general evidence, and rejection of unversioned
positional P01 payloads. No producer experiment is promoted to a causal contract.

Luna extra-high `loop_plan_review` identified eight implementation prerequisites:
callback timeout enforcement, legal-answer inputs, structural versus semantic
gate responsibilities, immutable revision semantics, runner/package ownership,
input schemas, retry/reserve accounting, and terminal-event precedence.
[The API design](contracts/domain-api.md) now records decisions for those areas.
These are planning dispositions, not verified code fixes. Exact serialized native
examples/value signatures remain in T04 and all implementation tests are pending.
