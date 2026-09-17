> **Deferred historical artifact.** This describes the previous candidate-recall integration study, not the active first experiment. Use [the revised assertion plan](../plan.md). No CLI, loader, fusion pipeline, or full benchmark run described below is required for the first test.

# Planned experiment CLI and artifact contract

These interfaces are specifications for implementation; the commands do not exist yet.

```text
python -m symbolic_rca.cli prepare --dataset PATH --queries PATH --out PATH --seed 20260917
python -m symbolic_rca.cli rank --dataset PATH --manifest PATH --config PATH --split development|holdout --out PATH
python -m symbolic_rca.cli evaluate --rankings PATH --gold PATH --manifest PATH --out PATH
```

- `prepare` validates CSVs, clock audit evidence, grouping, labels and coverage. Trace validation must preserve all nine raw columns, exact mixed status strings, blank types, zero durations and opaque identifiers; detect malformed records and duplicate composite IDs rather than silently coercing them. Writes `inventory.json`, `split.json`, evaluator-only `gold.jsonl`, and label-free `rank-input.jsonl`. An unresolved audit returns nonzero; never silently falls back to machine-local time.
- `rank` reads label-free inputs, telemetry, and frozen config only. Runs B0/B1/S1/S2/N2; records config and input hashes. It cannot open scoring-points or gold files. Holdout mode requires a configuration lock and frozen split, and emits rankings before evaluation.
- `evaluate` joins by stable IDs, checks complete method/unit coverage and unique candidates, computes plan metrics, and writes `metrics.json`, `comparison.csv`, and `report.md`. Missing or failed rankings are misses, not dropped rows. Schema failures return nonzero.
- Rank artifacts: `rankings.jsonl`, `runtime.jsonl`, and `evidence/<method>/<unit_id>.md`. Evidence includes inspected sources, top-three component contributions, transition provenance, ordering limitations, strongest alternative, and missing channels.
- Ranked candidates are independent of official `predictions.csv`; they do not masquerade as fully classified faults. A later submission adapter must preserve `solve(instruction, dataset_dir, ctx) -> Solution`, required failure count, exact component/reason strings, and datetime/component/reason key order via the starter formatter.
- No network calls, credentials, paid models, or interactive prompts during experiment execution. Dataset/output paths are arguments, never developer-specific constants. Raw telemetry and generated outputs remain untracked.
