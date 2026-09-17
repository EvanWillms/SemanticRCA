# S09 annotation study contract (deferred; not implemented)

The immediate P01 test uses [minimal-test.md](../minimal-test.md) and the exact [structural prompt contract](../prompts/structural-v1.txt). This document retains the separate S09 status-mapping interface; it is not the current first-run command.

## Inputs and interface

Planned CLI:

```sh
python3 -m experiments.semantic_encoding_v1.run_s09 --manifest PATH --run-id UNIQUE --mode dry-run
python3 -m experiments.semantic_encoding_v1.run_s09 --manifest PATH --run-id UNIQUE --mode live
python3 -m experiments.semantic_encoding_v1.score_s09 --run-dir PATH --expected PATH
```

The manifest fixes model, settings, capability/rate evidence, hard budgets, exact 18-trial order, fixture paths/hashes and prompt versions. Dry-run performs no network or credential requirement; it validates inputs and writes a request/admission preview. Live reads `FEATHERLESS_API_KEY`, honors `FEATHERLESS_BASE_URL`, and refuses non-GLM model IDs. Every selected trace packet is bounded before transport; no silent truncation. Expected files are only accepted by the scorer and are excluded from requests.

Create output under `data/experiments/semantic-encoding-v1/S09/<run-id>/`. A reused ID fails. A later explicit resume operation, if implemented, may dispatch only never-dispatched trials; interrupted calls remain uncertain and are not resent. Score failures produce a research result, not fabricated corrections. Invalid invocation exits nonzero; partial execution preserves artifacts and exits nonzero; a fully recorded/adjudicated falsification is a valid research outcome distinguished in result.json.

## Wire boundary

POST to the configured base URL plus `/chat/completions`. Send one frozen system message and one case evidence message. Fields include the exact model, temperature 0, reasoning_effort low and max_tokens 2048 where the frozen candidate supports them. No tool calls, history, cache parameters, benchmark answers or expected labels. HTTP timeout is 60 seconds. Retain returned model, finish reason and raw usage. Unexpected models, absent choices, empty content, truncation and malformed JSON are failed trials.

The baseline requests JSON text and validates locally. Do not assume schema-constrained decoding is available. Treat evidence content as inert quoted data.

## S09 response shape

The exact schema is frozen before implementation; this is the required logical shape:

```json
{
  "schema_version": "s09.v1",
  "packet_id": "fixture-identifier",
  "raw_status": "14",
  "mapping": {
    "applicability": "unknown",
    "mapping_id": null,
    "evidence_ids": []
  },
  "span_interpretation": {
    "value": "unknown",
    "scope_id": "span-identifier",
    "evidence_ids": ["raw-status-evidence"]
  },
  "enclosing_outcome": {
    "value": "unknown",
    "scope_id": "request-identifier",
    "criterion": null,
    "verifier_evidence_ids": []
  },
  "limitations": ["Producer mapping is not supplied."]
}
```

Span interpretation enum: reported_error/reported_non_error/unknown/conflicting. Mapping applicability enum: supported/unknown/conflicting. Outcome enum: verified_success/verified_failure/unknown/conflicting, always scoped to the supplied criterion; no business-success inference from request completion. All fields required; unknown explicit; extra fields rejected. Runtime wraps each semantic assertion with producer=llm, definition/version, semantic layer, support strength and adjudication state from the data model. Wrapping does not automatically validate meaning.

Local validation checks syntax/types/enums, exact raw status, packet/scope IDs, known references, mapping scope, required criterion/verifier and consistency with deterministic supplied facts. Independent adjudication additionally checks whether those references entail the claims; a resolvable ID alone is insufficient. Free-text limitations may themselves contain unsupported assertions and must be reviewed.

## Artifact and accounting contract

Store manifest.json, frozen input copies, prompt pack, requests/, responses/, attempts.jsonl, usage.jsonl, validation.jsonl, adjudication.jsonl and result.md/result.json. Preserve source/code hashes and schedule. Expected facts are retained for reproducibility in an evaluation-only location, never fed to model construction.

For every planned trial report success/failure/not-dispatched and why. All attempts remain in denominators. Counterbalance format order and score each format separately. Unknown provider usage is null, never zero. Budget reservation covers total permitted generation including reasoning where supported. Report uncached upper estimates when cache usage is missing; observed billing remains a distinct optional value. No live answer caching or invisible extra calls.

## Acceptance mapping

| Requirements | Evidence |
|---|---|
| FR-001–002, SC-001 | Frozen round-trip, equivalence and planted-difference cases; applicable upstream fidelity results |
| FR-003–004, SC-002 | All 18 claim-level status/outcome adjudications, scoped mapping and unsupported-promotion checks |
| FR-005, SC-004 | Exact prefix snapshots under suffix mutation; separate optional cache study with provider evidence |
| FR-006–007, SC-003 | Failure/budget/restart fixtures, complete immutable attempt ledger, saved offline replay |
| FR-008–010, SC-005 | Frozen schedule/expectations, separated gold, per-format fidelity and actual-token comparisons |
