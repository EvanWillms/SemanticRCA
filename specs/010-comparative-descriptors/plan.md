# Implementation Plan: Reference-relative comparative descriptors

**Feature context**: `010-comparative-descriptors` | **Date**: 2026-09-17 | **Spec**: [spec.md](spec.md)

**Git branch at planning**: `008-featherless-trace-semantics`. Explicit feature-directory setup selected this specification; no Git branch was created.

**Input**: `specs/010-comparative-descriptors/spec.md`

**Status**: Phase 0 research and Phase 1 design complete. Implementation and feature acceptance execution remain pending.

## Summary

Build a pure `rca.comparisons` consumer of feature 009's immutable baseline bundle. Each selected resolved query occurrence receives a descriptor containing duration and structural subresults, per-field availability, qualifications and evidence. Emit complete descriptors first; top-five positive-excess lists are separate review views. Validate source/entity/statistic references before presenting a comparison as usable.

This layer cannot choose references, change support, infer normality or diagnose faults. The [research decisions](research.md) identify useful prototype arithmetic and the missing availability, denominator and evidence semantics. [Feature 009's plan](../009-qualified-short-baselines/plan.md) is the producer dependency.

## Technical Context

**Language/Version**: Python 3.12.

**Primary Dependencies**: Standard-library dataclasses, collections, math, hashlib, json, pathlib and unittest; feature 009 typed values and verified evidence access. No detector library, LLM or network requirement.

**Storage**: Immutable JSONL descriptor records with an index, coverage and review-view sidecars; input baseline bundles remain read-only. Output paths are caller-supplied and contained under the runner's output when integrated.

**Testing**: Authored D01–D12 arithmetic/structural fixtures; all availability states; evidence corruption and wrong-entity/statistic cases; canonical serialization/revision checks; joint producer-consumer integration and container rehearsal after implementation.

**Target Platform**: Existing Linux Python 3.12 container and local Python 3.12.

**Project Type**: Internal comparison library plus offline developer CLI and a versioned future discovery adapter contract.

**Performance Goals**: One descriptor per query occurrence; validate/recompute each distinct baseline once per verified snapshot handle; stream full descriptors and keep only five rank entries per slice in memory. Structural work scales with observed reference patterns and operation counts, not an artificial fixed cap. Record descriptor count, source reads, distinct validations, elapsed time and memory before claiming performance.

**Constraints**: No reference reselection, complete nonpositive/unavailable outcomes, strict finite field encoding, mandatory qualification propagation, no cross-unit/cross-snapshot ranks, deterministic ties and exact source evidence. Partial results cannot appear complete.

**Scale/Scope**: Frontend root duration and C0 direct-child structural comparisons for the feature 009 five-minute/six-slice profile. Unsupported or unusual references remain expected outputs; no requested failure count enters the descriptor API.

## Constitution Check

Pre-research and post-design gates pass for this scope:

| Principle/gate | Design evidence and outcome |
| --- | --- |
| I: evidence-first | Exact measurement/statistic validation and immutable baseline links; differences do not become cause. PASS |
| II: bounded access | Pure comparison core; restricted evidence resolver and streamed artifacts with explicit partial coverage. PASS |
| III: cost-aware routing | Zero inference calls; source and comparison costs recorded separately. Later routing unchanged. PASS |
| IV: reproducible evaluation | Independent D01–D12 expectations, stable definitions and joint 009→010 checks. No exposed-data result relabeled as held-out accuracy. PASS |
| V: runtime/submission | Standard-library package fits current image; separate developer CLI; official runner flags/predictions remain unchanged. PASS |
| Workflow | ADR/spec→research/design completed; tasks and implementation remain next. PASS |

No amendment or principle exception is required. The constitution's existing ratification-date placeholder remains the project maintainer's governance item. Feature completion requires the integration gates below; a mock-only comparison demonstration is insufficient.

## Project Structure

### Documentation

```text
specs/010-comparative-descriptors/
├── spec.md, acceptance.md
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/
│   ├── descriptors.md       # existing semantic authority
│   └── consumer.md          # planned API, artifact, CLI and adapter boundary
└── checklists/
    ├── requirements.md
    └── design-review.md
```

`tasks.md` belongs to the subsequent `$speckit-tasks` command.

### Planned source layout

```text
rca/comparisons/
├── __init__.py               # describe, review, summarize, validate API
├── contracts.py              # immutable descriptor/field/view values
├── describe.py               # pure duration and structural calculations
├── evidence.py               # semantic evidence validation via resolver
├── views.py                  # non-destructive ranking and coverage
├── artifacts.py              # canonical serialization and bundle validation
└── __main__.py               # offline consumer/validator CLI
tests/unit/test_descriptor_*.py
tests/integration/test_comparison_pipeline.py
tests/fixtures/comparative_descriptors/
```

**Structure Decision**: One comparison package consumes the shared producer contract. Existing general `rca.contracts` runner types stay compatible. The chosen package name is `rca.comparisons`; documentation uses comparative descriptor as the domain term, not an additional competing runtime package.

## Delivery sequence and gates

1. **Typed outcomes and arithmetic (D01–D04)**: Implement per-field availability and immutable descriptor envelopes; consume authored feature 009 outcomes. Preserve support, instability, raw measurement evidence and optional diagnostic definitions. No production reference selector is called from the comparison core.
2. **C0 structural comparison (D05–D07)**: Use known denominators, per-pattern members and count maps from the producer. Preserve multiple patterns, unknown/empty distinction and no-match statements. Validate that duration abstention does not erase a structurally comparable query.
3. **Evidence and revision (D10–D11)**: Add the restricted resolver, source/entity/measurement checks, baseline-statistic verification and calculation validation. Reject incompatible bundles and preserve per-record failures without invented values. New versions cannot overwrite old comparisons.
4. **Views, serialization and coverage (D08–D09)**: Write complete descriptors, separate top-five references and occurrence summaries. Round-trip all four availability states, qualifications and negative/zero values. Record partial writes/work with a non-complete manifest.
5. **Joint acceptance (D12 and 009 B12)**: Execute a fresh-source feature 009→010 fixture, source relocation, corrupted-source/artifact checks and offline container rehearsal. Verify unchanged official harness behavior. The future discovery adapter may expose links to descriptors only under an explicit selected profile; default-policy promotion and diagnosis are outside these feature gates.

Pure consumer development can proceed after the producer contract is frozen; end-to-end acceptance waits for real feature 009 artifacts. A separately authored fixture is an oracle, not proof that producer integration works.

## Validation and evaluation impact

The [acceptance matrix](acceptance.md) maps all FRs to D01–D12; [quickstart.md](quickstart.md) defines the implementation-era validation commands. Expected values must not be generated by the same helper under test. Check both pointer resolution and claimed value/qualifications. A valid hash or parseable pointer alone is insufficient.

For each run retain a reconciliation of input assignments, descriptor envelopes, subfield availability, structural unknowns, repeated observations and review membership. Rank by unrounded signed excess; floating-point assertion tolerances are test tools and never ranking thresholds. Corruption or unresolved required evidence produces explained unavailable output or a rejected bundle, according to the interface contract.

This feature measures descriptor fidelity and source validity. It neither improves nor reduces a claimed diagnostic score because diagnosis is not evaluated here. A full development-prompt replay is optional subsequent regression, not a planning prerequisite.

## Complexity Tracking

No constitution violations require an exception. An explicit field-result type and a semantic evidence validator are required to avoid collapsing unavailable states or accepting a reference to the wrong measurement. The pure core has no storage dependency; artifact I/O and validation are separate boundaries.
