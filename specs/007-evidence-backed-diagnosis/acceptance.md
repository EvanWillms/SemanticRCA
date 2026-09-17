# Acceptance matrix: evidence-backed diagnosis

These are planned checks, not executed tests. Use independently authored expectations; source/adaptor behavior must not generate its own expected answers.

| Case | Fixture/action | Required outcome | Requirements |
|---|---|---|---|
| H1 | Two competing causes, downstream symptom, large unrelated deviation | Preserve support/contradiction and distinguishing question; no heuristic promoted to proof | FR-001/002/007 |
| H2 | Normal service aggregate, disturbed pod, ambiguous placement | Keep pod explanation and qualified linkage without invented exact join | FR-001/002/005 |
| H3 | Delayed symptoms, sparse sampling, provisional units | Distinct observed/inferred onset and precision qualifications | FR-004/007 |
| H4 | Weak evidence, correlated observations and requested count exceeding supported explanations | Legal best guesses explicitly marked; no invented support or independent incidents | FR-002/006/007/008 |
| H5 | Renamed deployment and missing/unresolvable legal choices | Discover current identities; legal vocabulary validated; impossible answer is failed with blank prediction | FR-005/008 |
| O1 | Valid targeted metric/trace/log follow-up plus invalid field/resource/scope | Bounded source-linked outcomes; invalid inputs rejected and audited; valid empty distinguished | FR-003/013 |
| O2 | Malformed model output, provider timeout, unknown usage, exhausted operation budget | Bounded repair/fallback, finalization reserve, honest usage and stop status; next case proceeds | FR-003/008/009 |
| A1 | Seven projections with known full hypotheses | Exact requested fields, count, key order, UTC+8 and original identity | FR-006/011/014 |
| A2 | Two incidents sharing a component; tied onset; reorder IDs 42 and 9 | No component deduplication or field mixing; stable ordering; correct row association | FR-006/012 |
| A3 | Unsupported scope, partial discovery, persistence interruption, empty input | No access after unsupported scope; partial provenance retained; truthful exit/status; earlier checkpoints survive | FR-001/008/014 |
| E1 | Exact/mismatched component/reason; +/-59,60,61 seconds; too few/many incidents | Independently expected partial/strict scores; count mismatch awards no points under inspected reference | FR-011/012 |
| E2 | Permuted incident tuples, shuffled field order, malformed JSON and blank answer | Raw scorer behavior preserved; separate semantic validation; no silent rewrite of reference | FR-011 |
| E3 | Missing/duplicate/reordered IDs, missing answer, scorer exception | Explicit identity/score failure and full expected-case coverage; no positional guess or dropped denominator | FR-012 |
| E4 | Label and archived-answer files adjacent to telemetry; sealed outputs scored separately | Zero forbidden reads; inference cannot use scoring context; seal predates label access | FR-010/013 |
| E5 | Replay saved results; change scorer/policy/source identity | Identical saved metrics or explicit mismatch/invalidation; no live model calls for recomputation | FR-011/013 |
| R1 | Cold 20-case development rehearsal under prescribed machine limits | Under all time/cost/memory caps including preparation; complete outcome/usage accounting | FR-009/013 |
| R2 | Explicit stub, discovery and diagnosis validation paths | Stub/discovery regressions retained; default diagnosis switch gated on controlled acceptance | FR-014 |

## Constitution review

Completion-loop integration also requires
[feature 011 cases L01–L18](../011-completion-aware-investigation/acceptance.md).
They refine FR-003/008/009/013 and SC-003 here, including zero-tool completion,
rejected sufficiency, useful continuation, inability, non-progress, bounded
provider/assessment repair and unassessed final observations. Passing that
controlled matrix does not replace H1–H5 diagnosis checks or R1 runtime acceptance.

Evidence-first diagnosis: H1–H5. Bounded data access: O1–O2. Provider/routing restrictions and measured usage: O2/R1. Blind reproducibility and independent scoring: E1–E5. Submission compatibility: A1–A3/R2. The feature does not replace the constitution's repeated routed-versus-single-model held-out evaluation or certify diagnostic accuracy. Feature 002 and the project maintainer retain those delivery obligations.
