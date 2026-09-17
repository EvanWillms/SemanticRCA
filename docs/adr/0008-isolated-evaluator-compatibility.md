---
status: accepted
date: 2026-09-17
---

# Isolate scoring from inference and pin evaluator compatibility

OpenRCA provides an executable task/evaluation reference. Its runner loads labels and scoring points in the same process as inference, and its evaluator has observable parsing and alignment behavior beyond the conceptual when/where/why contract. Importing the runner wholesale would weaken SymbolicRCA's blind-inference boundary.

## Decision and trade-offs

- Keep inference and scoring in separate execution contexts. Inference receives only public instructions, allowed metadata, telemetry and approved policy/vocabulary. Labels, scoring points and archived answers are evaluation-only inputs and must be inaccessible to inference, including model operations.
- Freeze predictions and their input/configuration identities before scoring. Preserve failed, missing and timed-out cases in coverage and aggregate denominators; report scored-case counts separately where necessary. Do not select a best sample using gold scores as if that were a deployable single-run result.
- Pin the evaluator revision and content identity. The official Track 1 `starter/score.py` at revision `314cca0bba49e1bb137aa9094d1dac4cdf7e4490` is the compatibility target; its hash and the inspected differences from upstream are recorded in the adoption notes. The official scoring/submission documents govern; OpenRCA is a design reference.
- Test all seven field projections, exact component/reason strings, incident-count mismatch, multiple-incident association, ±60-second boundaries, malformed/blank outputs, and field ordering. Emit time/component/reason keys in that order, omitting unrequested fields, with UTC+8 datetimes and chronological incident ordering.
- The inspected evaluator uses a fixed-order regex and permutation matching. Preserve its raw behavior for parity testing rather than silently improving it. Keep semantic validation separate; passing the regex is not proof of a well-formed or supported diagnosis.
- Align each prediction to its original query identity explicitly before invoking a scorer. The official wrapper joins by ID but can omit missing cases and multiply duplicates; validate coverage and uniqueness outside the unchanged scorer. Do not use the upstream wrapper's prediction-only sort as alignment. Missing or duplicate identities are reported, never repaired by guessing row positions.
- Separate format compatibility, candidate discovery correctness, strict/partial diagnosis accuracy and evidence quality. Report each claim with its own fixtures or evaluation corpus and provenance.

The extra scoring boundary and parity tests reduce convenience, but prevent labels from affecting inference and make metric changes attributable to agent changes rather than scorer drift.

## Consequences and verification

[Feature 007](../../specs/007-evidence-backed-diagnosis/spec.md) adds the compatibility gate. [Feature 002](../../specs/002-final-demo-runner/spec.md) still owns repeated routed-versus-single-model evaluation, pricing, release and submission. An offline compatibility suite does not complete those obligations. See [adoption notes](../openrca-adoption.md) for the pinned local source and implementation sequence.
