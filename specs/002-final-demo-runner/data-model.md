# Runner data model

## Active harness subset

Only query row_id/instruction, Solution prediction/evidence/usage, case wall time and checkpoint rows are needed now. Reuse the constraint `row_id (unique integer from input)` and `CSV-aware ingestion; no row-position substitution.` Do not implement scope parsing, hypotheses, observations, model ledgers or evaluation records yet. The stub result is explicitly placeholder, outside the completed/degraded diagnosis states below. See contracts/runner.md for exact empty values and file behavior.


| Entity | Fields and validation |
|---|---|
| CaseScope | row_id (unique integer from input), instruction, deployment, start/end in UTC+8, positive failure_count, ordered requested_fields. CSV-aware ingestion; no row-position substitution. |
| Observation | source path relative to dataset, modality, timestamp units, window/filter, component binding, statistic/value/unit, count/coverage, extraction policy. Distinguish no observation from measured absence. |
| IncidentHypothesis | onset, component, reason, confidence, supporting/conflicting observation IDs, alternatives, guess explanation. Component names derive from data; reason from official label vocabulary. |
| CaseResult | scope ID, ordered incident list, prediction string, rendered evidence, status (completed/degraded), timing, model ledger. Incident count equals scope count, fields are projected after sorting. |
| CallLedger | case ID, model, purpose, attempt, outcome, input/output tokens, usage-known flag, reserved and settled estimated cost, elapsed time. No credentials or raw authenticated headers. |
| RunState | run/config/input identities, monotonic start/deadline, completed IDs, remaining budgets, suppressed models, output directory. Optional resume must validate identities. |
| EvalRecord | revision, dataset identity, split/exposure manifest, configuration, repeat, per-case result/score/cost/time, evidence review, pricing version, aggregate metrics. Labels accessed only by scoring. |
| ReleaseRecord | tested commit, remote/default branch and resolved revision, security/validation results, AI disclosure review, deadline, form completion status. |

Transitions: preflight → scoped → retrieving → diagnosing → validating → persisting → completed. Recoverable retrieval/provider/time/cost errors go to degraded validation and persistence. Invalid invocation fails preflight without paid calls. Whole-run exhaustion switches remaining valid cases to budget-free best guesses while time permits; an external kill preserves only completed checkpoints. No transition invents supporting evidence.

Persist evidence and a reconciled usage record before publishing a prediction checkpoint. A new run requires a clean output directory. Temporary writes and caches stay inside it; optional resume must reconcile all three artifacts, not merely trust a predictions row.
