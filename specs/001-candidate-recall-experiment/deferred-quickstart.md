> **Deferred historical artifact.** This describes the previous candidate-recall integration study, not the active first experiment. Use [the revised assertion plan](plan.md). No CLI, loader, fusion pipeline, or full benchmark run described below is required for the first test.

# Validation guide for experiment 001

Status: planning artifact. The new package and commands below must be implemented through the tasks phase first.

## Prerequisites

A complete organizer-provided `Market-cloudbed-1` bundle; enough disk for its documented roughly 12 GB extraction; a Python environment with locked starter-compatible dependencies; the pinned official starter checkout. Do not use upstream hidden-evaluation answers.

1. Use the extracted `data/track-1` bundle and inspect its manifest; validate archive integrity if extracting again. Confirm `query.csv`, `dev/query_dev.csv`, container/node metric files, and trace files. Record data hashes.
2. Complete development clock/ID/duration audit and group inventory. Freeze the seed and manifest. Review actual sample count against the plan's six-block decision guard.
3. Run the unchanged starter in its own checkout for a reproducibility smoke test. This is existing syntax, and the query input should be a development-only CSV with the original schema:

```bash
python run.py --dataset /path/to/Market-cloudbed-1 --queries /path/to/development_queries.csv --out /path/to/baseline-out --agent agents.heuristic
python score.py --predictions /path/to/baseline-out/predictions.csv --queries /path/to/development_queries.csv
```

The official score is ancillary. Obtain full B0 component rankings from `analyse(...).ranked` in the planned adapter.

4. After implementation, run the planned `prepare`, `rank --split development`, and `evaluate` commands defined in [the CLI contract](contracts/experiment-cli.md). Development rankings must have zero access to gold.
5. Validate synthetic fixtures: duplicate query variants stay in one block; partial labels remain partial; UTC+8 and ms/s conversions agree; midnight windows load both dates; same-component links do not become network edges; a trace split across distant source records reconstructs correctly; mixed status strings and blank type survive parsing; zero durations are not reclassified as failed work; sub-millisecond overlaps do not establish concurrency; orphan spans are flagged; absent traces reproduce S1; ambiguous IDs do not get exact-match credit; a missing result lowers recall.
6. Inspect development evidence and coverage, freeze config, then run holdout ranking once and score it. Preserve exact config/data/split/source hashes and all arms' outputs. Repeat only to verify deterministic reproduction; do not tune against that report.
7. Check `report.md` contains every method, denominators, paired deltas/intervals, network breakdown, wins/losses, onset availability, runtime and evidence size, zero model spend, and the decision from the predeclared gate.

Completion means a valid, reproducible decision—including stop or inconclusive—not necessarily a positive hypothesis. This experiment does not complete the final-agent routing, container, or submission requirements.

The [trace audit](../../docs/research/track-1-trace-audit.md) supplies concrete schema observations and reproducible audit scripts. Use synthetic equivalents for parser regressions rather than committing raw telemetry fixtures.
