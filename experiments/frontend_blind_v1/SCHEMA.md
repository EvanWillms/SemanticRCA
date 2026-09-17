# Frontend blind v1 artifact schema

The investigator writes `trace_only.json` before requesting metrics or logs and
writes `final.json` after the bounded corroboration stage. Both files are JSON
objects with the following required fields:

```json
{
  "row_id": 0,
  "stage": "trace_only",
  "incidents": [
    {
      "occurrence_time": "",
      "component": "frontend-api",
      "reason": "",
      "observed_symptom_time": "2022-03-20 09:04:10",
      "confidence": 0.55,
      "evidence_refs": ["trace_evidence.json#/traces/t1"]
    }
  ],
  "candidates": ["frontend-api", "orders-db"]
}
```

`incidents` must contain exactly the `failure_count` entries in the case's
`scope.json`. Each entry must contain the six fields shown above. Unknown or
unsupported values are the empty string (`""`); an investigator must not use
`null`, a guessed label, or a missing key to express abstention. `confidence`
is a number in `[0, 1]` or the empty string when no confidence was recorded.
`evidence_refs` is an array of stable local references and may be empty.
Additional fields are preserved by the seal and evaluator. The evaluator never
uses additional fields to repair a prediction.

`candidates` is an ordered list of component strings, from most to least
plausible. It is a discovery artifact and is independent of the incident
projection. Unknown candidates are represented by an empty list.

The official projection reads only `occurrence_time`, `component`, and
`reason`, in that order, and retains one output object per incident. The
official datetime format is `%Y-%m-%d %H:%M:%S`; other strings remain unchanged
and receive no time credit. The structured schema deliberately keeps observed
symptom time separate from inferred occurrence time.

## Discovery evidence

For discovery recall, `trace_evidence.json` may contain an `arms` mapping. Each
arm (`duration`, `mad`, or `isolation_forest`) may contain `top_requests` keyed
by request budget (`1`, `3`, `5`, `10`), whose entries are objects with an
ordered `immediate_components` list and an ordered `reachable_components`
list. Components are de-duplicated within each list. Equivalent explicit
`request_prefixes`/`components` records are accepted by the evaluator, but
the canonical form above should be used for new cases. The shared harness also
emits `arm_evidence` with ranked `traces`; the evaluator derives the same fixed
prefixes from those records without consulting labels.

## Seals and failed attempts

`trace_only.seal.json` and `final.seal.json` are write-once manifests. A trace
seal covers the stage output, scope, rankings, trace evidence, run inputs, and
other deterministic data references. A final seal additionally covers the
current `investigate.py`, `evidence.md`, `run.json`, retrieval log, and every
code/data reference declared by `run.json`. Each seal contains its stage,
creation timestamp, SHA-256 hashes of the stage output and all declared inputs,
and the current source/config hash snapshot. A completed attempt
has `run.json` with `status: "completed"`; an infrastructure failure has
`status: "failed"` and a non-empty `failure` object. A failure is an explicit
experimental outcome and does not make an unsealed prediction valid.

The investigator seals from the repository root with:

```sh
python -m experiments.frontend_blind_v1.seal seal --case-dir data/experiments/frontend-blind-v1/cases/<rowid> --stage trace_only
# perform only the bounded Stage M work, then write final.json/evidence.md
python -m experiments.frontend_blind_v1.seal seal --case-dir data/experiments/frontend-blind-v1/cases/<rowid> --stage final
```

The first command must succeed before retrieval begins. Sealing is write-once;
repair the artifact in a new declared attempt rather than deleting or replacing
a seal. The coordinator's all-case gate is:

```sh
python -m experiments.frontend_blind_v1.seal validate-all
```
