# External runner contract

## Current milestone override: empty-output stub

For the tasks currently requested, keep the build/CLI contract below but run a stub by default. Do not require FEATHERLESS_API_KEY or connect to FEATHERLESS_BASE_URL; provided values must not be printed or persisted. For N valid queries emit N CSV rows with original row_id and an empty prediction field (not `{}`, `null`, or fake incident objects). Write evidence/<row_id>.md with the required four headings and explicit unimplemented/no-evidence/no-alternatives-assessed text. Each usage.jsonl row contains row_id, measured wall_s, models={}, and zero prompt_tokens/completion_tokens/calls. Empty input with valid headers emits only `row_id,prediction` headers, an empty usage.jsonl and evidence/ directory.

Require dataset directory, query CSV with row_id/instruction headers, unique integer IDs, and an empty or absent writable --out. Validate all input rows before publishing outputs. Reject duplicate/malformed IDs, malformed CSV, nonexistent inputs, overlapping output/input paths and nonempty output; do not erase old runs. No resume support is required; if the flag is retained it must fail explicitly rather than silently overwrite. Honor --limit/--agent if retained from the starter, documenting supported options. Successful placeholders exit zero with a harness-only notice; preflight/write errors exit nonzero. Preserve completed checkpoints on failure.

The final-output requirements below are deferred. The scaffold validator must not present its pass as official benchmark validation.


## Build and invocation

The root Dockerfile must build from a clean public checkout:

```bash
docker build -t your-team .
docker run --rm \
  -e FEATHERLESS_API_KEY=<our key> \
  -v <a bundle>:/data:ro \
  -v <an empty folder>:/out \
  your-team \
  python run.py --dataset /data --queries /data/query.csv --out /out
```

This is the official command template, with judge-supplied placeholders. The three flags are required and must suffice; no `--agent` or preparation script is required. The image working directory contains run.py. Keep optional starter flags compatible where retained. `FEATHERLESS_BASE_URL` overrides the default `https://api.featherless.ai/v1`; derive the allowed model host from that value. Credentials come only from `FEATHERLESS_API_KEY` and are never serialized. All dependencies install at build time. Runtime data reads are restricted to dataset/query inputs; no label files. All runtime writes, including caches and temporary files, stay beneath --out.

## Prediction and evidence

Read query CSV with proper quoting/newline support. Use original unique integer row_id. The seven projections are: task_1 time; task_2 reason; task_3 component; task_4 time/reason; task_5 time/component; task_6 component/reason; task_7 all three. Instruction governs scope; reject ambiguous invalid scope before model work rather than silently changing it.

`predictions.csv` includes `row_id,prediction`; extra official-compatible columns are allowed. Each prediction contains one numbered JSON object per failure, numbered from `1`, in occurrence order. Within each object use only requested keys in this relative order:

1. `root cause occurrence datetime` — `YYYY-MM-DD HH:MM:SS`, UTC+8, estimated onset (official tolerance 60 seconds).
2. `root cause component` — exact deployment component name.
3. `root cause reason` — exact official reason label.

No newlines in values. Keep incident tuples associated, including repeated components. Use the official format helper or demonstrably equivalent serialization accepted by its unchanged evaluator. Markdown fences from the starter helper are permitted.

`evidence/<row_id>.md` contains exactly the four required top-level sections: `## Answer`, `## Confidence`, `## Evidence`, `## Ruled out`. Cite dataset-relative files, times, components, measurements and units for observed claims. If no alternative was actually excluded, say so. Best guesses remain required; missing observations are never manufactured.

`usage.jsonl` contains per-case row_id, wall_s, and models mapping model IDs to prompt_tokens, completion_tokens, calls. Preserve compatibility with the starter cost reader. Record unknown usage and conservative budget reservations in an auxiliary ledger under --out instead of inventing measured counts.

## Resilience and limits

Only GLM models, no network outside the configured endpoint. Inspect error bodies even on HTTP 200. Retry and fallback are bounded, repeatedly failed models suppressed across cases. No successful blank answer on provider failure. All limits include retrieval and retries: <600 seconds/$3 per case; <1,200 seconds/$25 per 20-case run; 2 CPUs, 8 GB, no GPU. Internal reserves cover in-flight calls and output finalization. Atomic predictions replacement preserves completed cases under termination. Missing credentials/invalid paths/duplicate IDs fail fast and sanitize errors; recoverable case failures produce degraded results and continue.
