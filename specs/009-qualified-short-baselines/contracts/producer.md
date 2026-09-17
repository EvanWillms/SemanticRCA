# Planned baseline producer interface

**Version**: `qualified-baseline-bundle-v1` / `short-window-c1-pooled-v1`.

This implementation contract specializes [baseline.md](baseline.md) and [data-model.md](../data-model.md). The APIs and commands below are planned, not currently implemented.

## Python boundary

- `prepare_sources(dataset_dir, inventory, output_dir, work_budget) -> PreparedTraceView`: validate contained source paths, build or open a verified snapshot-bound view, and return preparation/validation receipts. Generic source semantics remain governed by features 003/005.
- `collect_requests(view, deployment, anchor_ms, policy, work_budget) -> ObservationBatch`: select root starts over the declared reference/query horizon, recover complete available executions independently of time range, and retain raw unresolved outcomes and continuations.
- `freeze_baselines(observation_batch, snapshot, anchor_ms, policy) -> BaselineSet`: pure selection/support/statistics using the batch's explicit selection/recovery receipts; no source reads, query-driven threshold choice or mutation of observations. Construct catalogs solely from reference candidates, not query contexts.
- `assign_queries(observations, baseline_set) -> AssignmentBatch`: produce one assignment per resolved query occurrence, plus unresolved raw outcomes. No refresh or fallback. A missing C1/C0 context returns a typed MissingContext outcome derived from the frozen set and lookup key; it never appends a catalog object or changes set identity.
- `write_bundle(baseline_set, observations, assignments, output_dir) -> BundleManifest` and `load_bundle(path, source_resolver) -> ValidatedBaselineBundle`: strict schema, hash, source identity and semantic consistency validation.

Pure kernels accept small authored data for testing. Production collection may spill to prepared SQLite storage; semantic results must agree with the scan oracle. Runtime APIs return receipts for the feature 004 executor to charge; they do not own final predictions or model reasoning.

## Bundle contents

| Artifact | Contents |
| --- | --- |
| `manifest.json` | schema/policy versions, snapshot and baseline-set IDs, anchor/horizon, artifact hashes/counts, completion/partial status, qualification and work-summary references |
| `observations.jsonl` | Source-linked normalized reference/query observations, raw measurements, contexts and extraction states; roles may overlap across sets |
| `baselines.jsonl` | Per-C1 frozen baseline outcomes, support/stability, statistics, member IDs, exclusions and estimator evidence |
| `structural-references.jsonl` | Per-C0 known/unknown populations and identified multiset patterns with members and denominators |
| `assignments.jsonl` | Resolved query occurrences and their baseline/structural references, eligibility and reasons |
| `exclusions.jsonl` | Raw unresolved records, conflicts, out-of-scope and invalid/completion exclusions with source locators |
| `coverage.json` | Per-slice/class/replica accounting, unique observations versus occurrences, unavailable ratios and partial inspection state |
| `timings.json` | Preparation, validation, selection/recovery, estimation and persistence costs; cache hits, work counters, runtime versions and stop decisions |

The manifest includes the complete source inventory or a hashed in-bundle inventory object. Rebuildable `prepared/` SQLite files are optional accelerators, not the sole copy of provenance or a required author cache. Member/statistic evidence is addressable by artifact ID and actual JSONL logical record plus semantic ID; indexes are verified against content, not treated as evidence themselves.

## Serialization and publication

Encode numeric values as finite JSON numbers. Nulls require explicit availability/reasons. Retain original numeric text separately. Canonical hashes use UTF-8 JSON with sorted object keys, sorted semantically unordered collections and no NaN/Infinity; observed order is preserved only where meaningful. Persist exact serialization/arithmetic versions. Baseline identity excludes timing, run IDs and absolute output/mount paths.

Write into a new output directory or a temporary generation; existing completed bundles are immutable. Publish the manifest last by atomic replacement after validating all artifact hashes/counts. Failure leaves an explicitly incomplete generation. A partial manifest may retain completed evidence with stop reason/continuation; consumers cannot mistake it for complete reference membership or complete query coverage.

Common rejection reasons include `unsupported_schema`, `policy_mismatch`, `source_changed`, `incomplete_preparation`, `invalid_identity`, `invalid_measurement`, `unknown_structure`, `unresolved_completion`, `minimum_count`, `occupied_minutes`, `minute_concentration`, `outside_horizon` and `budget_exhausted`. Use multiple reasons where applicable; these are machine outcomes, not health labels.

## Source and semantic validation

A relocated dataset with identical relative inventory and content can satisfy the same snapshot. A changed source digest, schema, extraction definition or policy cannot reuse the old baseline identity. Validate original field values and exact endpoint eligibility, deduplication, C1 membership, support counts, draw indexes/quantiles and C0 denominators. Hash consistency alone is insufficient.

Duplicate policy is `logical-span-dedup-v1`: byte-equivalent parsed source fields for one scoped span collapse with all locators; conflicting content remains unresolved. This is versioned and checked against prior research rather than assumed to reproduce its duplicate treatment.

## Developer CLI

Planned commands:

```sh
python -m rca.baselining build --dataset-dir DATA --scope-file SCOPE.json --output-dir OUT --policy-id short-window-c1-pooled-v1
python -m rca.baselining validate --dataset-dir DATA --bundle-dir OUT
```

`SCOPE.json` contains exactly `schema_version: "baseline-scope-v1"`, `deployment`, and `anchor` (an ISO-8601 timestamp with explicit offset). This CLI accepts one anchor per invocation; the reusable Python API supports multiple anchors against a shared verified snapshot handle. Query slices are derived from the frozen policy, not read from a failure label. Reject naive timestamps, unrecognized policy IDs and output paths inside the read-only dataset. Do not accept arbitrary policy code or load policy instructions from telemetry.

Exit 0 means a complete valid bundle, even when legitimate comparison support is low. Exit 2 means invalid arguments/schema/policy; exit 3 means source/integrity failure; exit 4 means partial work due to unavailable required sources or exhausted work budget. Emit structured reasons and preserve completed audit artifacts where possible. Validation returns nonzero for partial or corrupted bundles.

The CLI is for offline validation. The official `run.py --dataset --queries --out` contract gains no required preparation command. A future discovery integration selects this policy explicitly and persists bundles under permitted output paths with shared receipts.
