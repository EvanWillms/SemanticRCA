# RCA domain library review

Status: **pass for the minimal demo scope**, 2026-09-17. Broader feature acceptance
remains deferred under [demo scope](demo-scope.md).

The owning task reviewed all delivered ingestion, investigation, demo, test and
packaging files. [The inventory](reviewed-code-inventory.json) records their exact
SHA-256 hashes. Concurrent work outside this inventory is not claimed as reviewed.

Luna extra-high workers implemented independent ingestion and loop TDD slices,
then a producer-to-loop demo. See [ingestion](ingestion-tdd.md),
[loop](loop-tdd.md) and [demo](demo-tdd.md) red/green records.
Independent parallel reviews covered standards/core integrity (demo_tdd) and
specification/demo acceptance (rca_contract_audit); the latter reported no critical
blockers. The owner reviewed final repairs and reran the core checks.

## Findings resolved

- Preserve explanation and fill missing legal fields in degraded draft answers.
- Reject unsupported completion and blocked assessments claiming sufficiency.
- Check observation key/identity and deployment consistency.
- Preserve both original and incoming conflicting observations; conflicted support
  cannot establish completion. Match optional scope-window presence and values.
- Resolve producer aliases in retained definitions.
- Remove placeholder/dead code and implementation-mirroring identity assertions.
- Ground the scripted demo explanation in authored queue saturation observations.

## Verification

`PYTHONPATH=libraries/rca_domain/src:libraries/trace_semantics/src python3 -m pytest libraries/rca_domain/tests -q`

Result: **9 passed**. Core coverage includes preserved evidence/unknowns, invalid
input, follow-up and reassessment, rejected unsupported completion, budget/provider
fallback and conflict preservation.

`PYTHONPATH=libraries/rca_domain/src:libraries/trace_semantics/src python3 -m rca_domain.demo`

Result: worker-1 / resource saturation, evidence_sufficient, completed, supported;
2 assessments and 1 operation. This uses the actual semantic producer with an
explicitly synthetic scripted assessor, not a real diagnosis accuracy evaluation.

## Remaining limits

Operation callbacks are trusted injected code expected to return packets created
by from_semantic_traces; exhaustive adversarial packet/definition validation is
not established. Attempts are bounded, but callbacks cannot be forcibly stopped.
Hard time/cost limits, advanced retries, S01 compatibility, exhaustive projections,
full L01–L18 coverage, independent package installation and runner persistence
are deferred. These do not block the qualified demo handoff.

Earlier pre-implementation baselines were 41 repository tests / 12 subtests and
28 producer experiment tests / 3 subtests. They are not current full-regression
claims. Only the task-owned core suite was rerun for this isolated demo delivery.
