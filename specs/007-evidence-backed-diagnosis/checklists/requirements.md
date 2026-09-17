# Specification Quality Checklist: Evidence-backed diagnosis

**Purpose**: Validate completeness and readiness for planning.
**Created**: 2026-09-17
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] Feature requirements describe observable outcomes; implementation details are reserved for the contract/planning. Externally required formats and limits remain explicit.
- [x] Stories focus on investigator, evaluator and reviewer needs in plain language.
- [x] All mandatory sections are present.

## Requirement Completeness

- [x] No unresolved clarification markers remain.
- [x] All requirements are testable and mapped to acceptance cases.
- [x] Success criteria are measurable without selecting a programming language or model architecture.
- [x] Acceptance covers primary flows and edge cases for inference, identity, time uncertainty, failures and scoring.
- [x] Scope, dependencies and assumptions are explicit; no general agent framework or publication is included.

## Feature Readiness

- [x] FR-001–FR-014 map to H1–H5, O1–O2, A1–A3, E1–E5 and R1–R2 in [acceptance.md](../acceptance.md).
- [x] All seven projections, multiple incidents and reordered original IDs have explicit acceptance.
- [x] Official scoring/submission documents govern; scorer revision/hash and reason vocabulary source are pinned.
- [x] Best guesses preserve honest evidence. Blank operational failures fail final acceptance; low confidence is not an abstention policy.
- [x] Scorer parity, semantic validity, case coverage and diagnosis accuracy remain separate claims.
- [x] No empirical success or implementation completion is implied by this checklist.

## Review findings resolved

- Reused and amended feature 004 for inventory/discovery with FR-015/016 and O1/O2.
- Preserved independent trace/metric discovery and qualified references instead of copying threshold relaxation and causal heuristics.
- Reconciled chronological submission order with permutation-insensitive scoring.
- Pinned official starter scoring rather than the upstream wrapper: ID joins, stringified predictions and zero-criteria handling differ. Coverage and duplicate checks remain necessary outside the scorer.
- Retained GLM/endpoint restrictions, runtime limits and honest unknown usage; judges meter independently.
- Recorded the labelled example exposure in the official data guide as development exposure.
- Preserved constitution 1.0.2's repeated routed/single-model evaluation and feature 002's release obligations, including the post-deadline prohibition on new features.

## Workflow and status

The mandatory branch hook computed `005-evidence-backed-diagnosis`; after a sandbox failure that branch was created successfully with a permitted Git operation. Another task then created `005-track1-trace-extraction` and changed the active branch and feature pointer. This specification moved to `007-evidence-backed-diagnosis` to avoid numbering collisions; the other task's branch and `.specify/feature.json` were preserved. Select this feature directory explicitly when planning it.

The active template resolved to `.specify/templates/spec-template.md`. Optional after-specify commit was skipped because auto_commit is disabled. No changes were committed. Documentation review passes; implementation acceptance remains pending. Ready for planning in the order recorded in the [adoption map](../../../docs/openrca-adoption.md).
