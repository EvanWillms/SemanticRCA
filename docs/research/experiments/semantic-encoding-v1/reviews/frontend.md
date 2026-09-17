# S01 pre-execution review: frontend blind and trace-audit code

Scope reviewed read-only: the complete source/docs/test set under `experiments/frontend_blind_v1/`, `docs/research/experiments/frontend-blind-v1/`, and `docs/research/trace-audit/`, plus the S01 handoff and active A1/semantic-evidence contracts. No frontend experiment, test suite, telemetry scan, or source edit was run. The only execution was an independent stdlib hash/fact check over the S01 fixtures, recorded separately in `/tmp/s01-fixture-review.md`.

## Coverage inventory

- `experiments/frontend_blind_v1/`: `build_index.py`, `detectors.py`, `trace_evidence.py`, `retrieval.py`, `run_case.py`, `seal.py`, `evaluate.py`, `coordinator.py`, `config.json`, API/investigator/schema docs, requirements, and all four test modules (test files collectively cover detector cohorts, index cross-day retrieval, mapping/budgets/seal gating, evaluator assignment, and trace interval/graph edge cases).
- `docs/research/experiments/frontend-blind-v1/`: execution and planning docs, random-eight amendment, `scope.csv`, `collect_random8.py`, `review_random8.py`, `collect_results.py`, and `verify_control.py`.
- `docs/research/trace-audit/`: README, `audit_trace.py`, `audit_trace_semantics.py`, `audit_trace_span.py`, `analyze_case25_causality.py`, `discover_case25_latency.py`, `demo_pyod_latency.py`, and both requirements files.
- Handoff and active contracts reviewed: `docs/research/reliability-taxonomy-review.v1/07-incremental-experiments-handoff.v1.md`, `.../06-selected-trace-semantic-encoding-experiment.v1.md`, `specs/001-candidate-recall-experiment/plan.md`, and `specs/001-candidate-recall-experiment/contracts/semantic-evidence.md`.

## Findings and S01 relevance

1. **Do not reuse frontend timing semantics in S01 (qualification, no S01 blocker).** `experiments/frontend_blind_v1/trace_evidence.py:30-41` unconditionally interprets raw duration as microseconds and derives endpoints. The semantic contract requires unknown duration units to keep raw duration while withholding derived endpoints (`semantic-evidence.md:34-38`); the trace audit calls the microsecond interpretation provisional (`docs/research/trace-audit/README.md:12-16`). S01 declares synthetic milliseconds, so its new encoder may use that declared fixture context, but importing `_span` or copying this assumption would violate the S01 separation.

2. **Duplicate graph rows are flagged then collapsed by helpers (existing-code limitation, outside S01).** `trace_evidence.py:47-66` retains duplicate rows in `by_id` but builds `child_ids` and `parent_by_id` as single-row dictionaries. Later path enrichment (`:145-148`) therefore selects one duplicate for fields. This conflicts with the semantic contract's requirement to retain conflicting duplicate records and mark relations as conflicting. S01 has unique IDs and does not exercise this path; keep the new encoder independent.

3. **Frontend cohort signatures omit non-frontend direct children (existing-code correctness concern, outside S01).** `detectors.py:19-24` filters all signature rows to `cmdb_id.startswith("frontend-")`, although the documented cohort is the multiset of recorded direct-child operation names (`PLAN.md:75-81`). A direct child emitted by a downstream component can therefore disappear from the cohort and become an empty/changed signature. This is not an S01 input or dependency.

4. **Audit tree recursion has no cycle guard (existing-code robustness concern, outside S01).** `docs/research/trace-audit/audit_trace.py:142-145` recursively calls `tree` over `children` after separately detecting cycles. A cyclic fixture can recurse until failure instead of returning the promised cycle-qualified report. S01 fixtures are acyclic and the audit scripts must not be invoked for S01.

5. **Schema audit reports a header mismatch but still zips rows against the expected order (existing-code robustness concern, outside S01).** `docs/research/trace-audit/audit_trace_span.py:79-90,142-150` records `header_matches_expected` but maps row positions to `EXPECTED` regardless of the actual header. A reordered header can yield misleading lexical counts. No S01 fixture uses this code.

6. **The semantic audit is intentionally bounded and qualified, not an S01 oracle.** `docs/research/trace-audit/audit_trace_semantics.py:7-10,83-109` keeps a 100,000-row prefix plus the selected real trace and uses a provisional microsecond endpoint calculation; its own interpretation limits (`:137-142`) disallow full-dataset graph/coverage or fault conclusions. The S01 handoff explicitly requires synthetic-only, zero model calls, and no real telemetry, so these scripts are evidence boundaries only.

7. **Case-25 scripts are exposed development controls and must stay out of S01.** `analyze_case25_causality.py:14-19,39-56`, `discover_case25_latency.py:11-12,45-49`, and `demo_pyod_latency.py:67-70,121-127` contain fixed case timing/known-trace controls and optional post-ranking lookup. Their docstrings/README identify them as development diagnostics. S01 does not need them and must not read their outputs.

8. **The frontend trial is a separate, later/older experiment.** Its execution protocol requires private cases, Stage-T seals, retrieval budgets, and eventually labels (`experiments/frontend_blind_v1/INVESTIGATOR.md:21-70`; `DATA_API.md:15-76`). S01 requires a new local deterministic encoder/decoder, synthetic fixtures only, no model calls, and must stop after S01 (`07-incremental-experiments-handoff.v1.md:45-73`). There is no code dependency from S01 on this harness; executing or modifying frontend code would expand scope and is a blocker to scientific isolation, not a prerequisite.

## Readiness decision for isolated S01

The frontend/trace-audit code review reveals no dependency that needs to run or be modified for S01. Keep it out of the S01 execution path. The only S01-specific issue is the fixture fact-sheet ordering ambiguity documented in `/tmp/s01-fixture-review.md`; resolve it by comparing order-insensitive graph/pair relations or by declaring canonical ordering before implementing the gate. No real telemetry, frontend case, model, or label access is required.
