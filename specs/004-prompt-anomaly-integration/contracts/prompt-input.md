# Prompt input and interpretation contract

## Authority and public seam

This contract defines the pure US1 interpretation seam. [integration.md](integration.md) and [executor.md](executor.md) govern runner modes, artifacts and exit behavior for every slice, including scope-only R1. Pure Python interface:

```text
interpret(query: QueryRow) -> InterpretationResult
```

The function reads no files, environment variables, network or clock; it performs no model call. It accepts only original row identity, instruction and optional task_index. The types and serialized schema are defined in ../data-model.md. Unsupported grammar returns a typed result; programmer errors are not relabeled as a valid scope.

## Input grammar and conventions

1. **System identity**: Recognize the supplied “cloud service system, <identifier>”, “system <identifier>”, and “<identifier> system” forms, including their comma/whitespace variations. The identifier token is a letters/digits/hyphens/underscores/dots token anchored to the system-identification phrase, not any occurrence elsewhere. Also recognize a deployment identifier used directly as the event subject (the supplied row 32 uses “Cloudbed-1”). Match identifiers case-insensitively and canonicalize the ASCII identifier to lowercase while retaining its original spelling in text support; reject distinct canonical values. Do not interpret filler words such as “cloud” or “service” as identifiers. Track 1 cloudbed identifiers have variable numeric suffixes; no cloudbed-1 constant or telemetry path inference.
2. **Window**: Support “time range/period of <Month> <day>, <year>, from <HH:MM> to <HH:MM>” and “On <Month> <day>, <year>, between <HH:MM> and <HH:MM>”. Window introducers also include within/during/between the time range, within the specified time range, within the timeframe, within the time period, and On <date> from <start> to <end>. End time may include an explicit English date and optional “at”. Use a locale-independent full English month map, real calendar validation and fixed UTC+08:00. Whitespace/case variations are tolerated; no fuzzy date repair. Multiple distinct explicit windows are unsupported.
3. **End-date rules**: Omitted end date inherits the start date if that yields a positive 30-minute interval. Only a start clock of 23:30 with end clock 00:00 and no explicit end date may roll to the next calendar day; record this convention. Explicit end dates always control and are never rolled/repaired. Invalid dates, 24:00, longer/shorter/negative intervals, ambiguous timezone statements or conflicting explicit dates are unsupported.
4. **Failure count**: Extract counts from the occurrence assertion and any explicit repeated count assertion. Support observed “experienced/encountered a failure”, “a single failure”, “one failure”, “two failures”, auxiliaries such as “has experienced” and “may have experienced”, and positive decimal counts in the same grammar. “There is one known failure” and “confirmed there was one failure” corroborate a count. References such as “reason for this failure” do not establish count. Zero, unsupported number words, missing or distinct asserted counts are unsupported; do not count mentions or default to one.
5. **Requested fields**: Isolate explicit imperative clauses, including Please identify/determine/pinpoint/investigate to determine; Your task is to identify; You are tasked with identifying/to identify/to determine; You are required to identify; You need to identify and determine; and standalone Identify. Parse the requested noun phrases within those clauses, including observed aliases: root cause occurrence datetime/time; affected component(s)/root cause component; root cause reason(s)/reason behind this issue/failure/reason for this failure. Background “unknown” descriptions do not supply requested fields. Repeated identical requests are allowed; distinct explicit request projections are unsupported. Negation or unsupported request syntax is not handled by substring inclusion.
6. **Canonical projection**: Emit datetime, component, reason in that order, omitting unrequested fields and deduplicating repeated identical phrases. task_index, if supplied, must match the derived projection: task_1=datetime, task_2=reason, task_3=component, task_4=datetime+reason, task_5=datetime+component, task_6=component+reason, task_7=all. Never use task_index to repair an unparseable instruction.
7. **Provenance**: Retain exact text and source spans for every interpreted field. Support offsets refer to Unicode characters in the original decoded instruction, not bytes, physical CSV lines or a normalized string. Convention-derived values identify their rule and supporting text.

The implementation must cover every observed supplied prompt form and validate it against independently reviewed fixtures. This is an allowlisted grammar, not permission to accept arbitrary prose containing a few matching words. Unrecognized materially conflicting scope text returns unsupported instead of selecting the first match. No hard-coded dates, row counts or per-row expected scopes belong in runtime code.

## Unsupported results

Use these stable issue codes as applicable:

| Code | Meaning |
|---|---|
| empty_instruction | Required instruction text has no non-whitespace content. |
| missing_deployment / conflicting_deployment | No supported system identity or multiple explicit identities. |
| missing_window / invalid_window / conflicting_window | Missing, impossible, non-30-minute or contradictory bounds. |
| missing_failure_count / invalid_failure_count / conflicting_failure_count | Missing, unsupported/nonpositive or inconsistent explicit occurrence count. |
| missing_requested_fields / unsupported_request / conflicting_requested_fields | No interpretable request, unsupported request grammar or inconsistent projections. |
| unsupported_task_index / task_index_mismatch | Nonempty metadata outside the seven values, or disagreement with the parsed projection. |
| unsupported_instruction | Other materially unsupported scope grammar/timezone that prevents safe interpretation. |

For unsupported results, scope is null and issues identify the reason; partial candidate field matches may appear only in issue/support provenance, never as a usable scope. Missing task_index is permitted.

## Runner and artifacts

R1 is the scope-only capability of `agents.discovery`, selected explicitly with
`--agent agents.discovery`. The official three-flag default remains the accepted
stub until the plan's R6 acceptance gate; then it selects full discovery. Keep
`--agent agents.submission` for explicit stub regression. No separate
`agents.prompt_input` mode or default promotion is required.

Dataset directory existence remains a preflight check. R1 reads no telemetry and
requires no key, model, additional mandatory flag or interactive repair. The
unsupported `--resume` behavior remains.

Use the artifact set in [integration.md](integration.md): predictions.csv,
evidence/<row_id>.md, usage.jsonl, cases/<row_id>/scope.json,
cases/<row_id>/findings.json, cases/<row_id>/operations.jsonl and the root
discovery-run.json. For R1, findings are `not_run` with
`capability_not_implemented` after valid interpretation, or the interpretation
failure reason otherwise. The operation journal is empty because no discovery
operation was attempted; do not invent completed telemetry operations. Persist
sidecars, evidence and usage before publishing the case's prediction checkpoint.

Evidence states diagnosis pending, distinguishes interpreted/unsupported scope,
shows source-text support or errors, and states telemetry was not inspected and
no causal alternatives were assessed. Usage records measured local work, empty
models and zero calls/tokens. Prediction values remain blank for this intermediate
milestone; this does not meet official final-answer requirements.

Header-only discovery input produces empty predictions/usage/evidence/cases plus
a discovery-run.json declaring zero cases and the selected capability. Explicit
stub mode retains its existing artifact set and strict placeholder validator.

`scripts/validate_discovery.py --capability scope` checks row associations,
schema/status/nullability, metadata, instruction hash, original-text offsets,
scope invariants, truthful evidence and zero usage. It may pass while the
scope-only executor exits nonzero for incomplete discovery. It must not run the
interpreter to manufacture expected answers; semantic accuracy uses independently
authored expectations.

## Exit behavior

Use these project-local codes consistently with the integration contract; the
official docs do not prescribe numeric exit codes:

- 0: all cases completed discovery, or a valid empty query inventory.
- 1: any unsupported scope or partial/unavailable/not_run discovery, including
  nonempty scope-only R1 runs. Continue subsequent structurally valid cases.
- 2: invalid CSV/IDs/paths/nonempty output or unsupported CLI flag, before analysis.
- 3: unexpected fatal runtime or persistence error; preserve prior checkpoints
  and avoid raw exception/credential output. Recoverable analysis failures use 1.

Original input order is preserved. Scope parsing runs independently per row;
full discovery may reuse compatible retrieval work without merging row scopes,
requested projections or failure counts.
