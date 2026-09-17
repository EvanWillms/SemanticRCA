# Incremental executor contract

This supplements [integration.md](integration.md); that contract remains authoritative for discovery status, output and failure semantics.

## Public entrypoints

Preserve `python run.py --dataset DATA --queries QUERIES --out OUT`. Existing optional `--agent` selects a module exposing `solve(instruction, dataset_dir, ctx) -> Solution`. No new required flag or external preparation command. `--resume` remains explicitly unsupported.

Planned `agents.discovery` orchestrates deterministic preparation. `agents.submission` remains the explicit stub. During intermediate development the former may be selected with `--agent agents.discovery`; incomplete capabilities are visibly not_run/partial and do not satisfy full discovery acceptance. Promote the three-flag default only after the plan's R6 gate. No mode may infer a diagnosis from a discovery candidate.

ctx preserves row_id/dataset_dir/out_dir and adds optional task_index plus one shared run context (source handles, immutable policy, deadline and remaining-case budget). Tests may supply a fake clock or operation provider; production never takes policy from untrusted telemetry text. Keep old stub callers valid.

## Bounded operation interface

`execute(request, run_context) -> receipt` accepts only an enumerated operation and typed arguments:

- `inventory`: allowed Track 1 source families for an interpreted deployment.
- `select_spans`: half-open time interval, discovered recording identities and explicit selection policy.
- `recover_traces`: snapshot-scoped trace IDs, separate recovery limits and continuation.
- `metric_series`: discovered resource/KPI identities, time bounds, sample/series limits.
- `compare`: observation IDs and a frozen eligible reference policy/context.
- `expand_relationships`: evidence-linked entities, relation kind and supported time range.
- `inspect_logs`: concrete question, motivating observations, discovered source/resource, bounded interval/record count.

Validate arguments, policy identity, resource/KPI inventory, permitted scope and remaining budget before source reads. Do not accept shell commands, Python, SQL from the agent or arbitrary paths. Implementation owns parameterized SQL and allowed source paths. Reject path escapes and forbidden input families. Trace recovery may cross the initial selection window only within the declared source snapshot; reference/log windows must be separately declared.

Every receipt includes status, provenance, coverage, timing and stop reason. Valid empty is a successful empty selection; invalid identity, unavailable source and exhausted budget are different outcomes. Journal attempts even when rejected. The later agent can choose a permitted operation, not change comparison thresholds or invent source identity.

## Persistence

Retain predictions.csv, evidence/<row_id>.md, usage.jsonl. Add cases/<row_id>/scope.json, findings.json, operations.jsonl and discovery-run.json as specified by the integration contract. Scope-only returns findings status not_run with reason `capability_not_implemented`; it must not report completed discovery. Prepared storage lives beneath OUT/prepared with content/extraction identities and an explicit completion marker.

OutputWriter serializes structured Solution data; the solver returns results rather than writing final artifacts itself. Persist sidecars, evidence and usage before atomic prediction replacement. Validate JSON finite values and stable row associations. Account for partial artifacts on write failure, keep the last published CSV and exit nonzero. Do not broaden the strict stub validator to accept discovery artifacts; add a separate validator.

## Budget and deterministic replay

Use monotonic deadlines and the plan's initial frozen ceilings/reserves. Charge hashing, scans, building, retrieval, comparison and persistence, including empty/failed calls. Shared work is charged once. Byte/record/trace/series caps require explicit truncation and coverage; silence is not completeness. Completed runs with identical inputs, policies and deterministic work limits reproduce substantive results and tie order. Live deadline exhaustion may change coverage and findings under different machine load. Record the last completed batch, continuation cursor and stop decision; controlled replay uses the same recorded work boundaries or fake-clock schedule to reproduce that partial result. Measured timing/run IDs may vary; partial replay never certifies complete coverage.

Nonempty not_run discovery and full discovery partial/unavailable/unsupported outcomes return nonzero after recoverable later cases. R7+ diagnostic best-guess behavior belongs to feature 007 and does not change feature 004's intentionally blank predictions.
