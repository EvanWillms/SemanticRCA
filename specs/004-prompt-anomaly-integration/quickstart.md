# Validation quickstart: always-running executor

Status: planning guide. Only the baseline commands below run today. Discovery modules/validator/fixtures are planned, and their names below define implementation targets, not installed capabilities.

## Baseline available now

Prerequisites: Python 3.12, repository root as working directory; Docker for later image rehearsal. No key/network required for preparation.

```bash
PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s tests -v
BUNDLE=$(mktemp -d)
OUT=$(mktemp -d)
cp eval/fixtures/query.csv "$BUNDLE/query.csv"
python3.12 run.py --dataset "$BUNDLE" --queries "$BUNDLE/query.csv" --out "$OUT" --agent agents.submission
python3.12 scripts/validate_harness.py --queries "$BUNDLE/query.csv" --out "$OUT"
```

Expected: zero exit, original IDs, blank predictions, honest placeholder evidence and zero model usage. The current synthetic harness instructions are not scope-parser acceptance fixtures. Planning-time baseline: all 26 tests pass.

## First ten-minute implementation demonstration (R1)

Generate tasks from this plan, then implement only the scope vertical slice first. Use an independently authored Track 1 query fixture with all seven projections, renamed deployment, midnight rollover and a conflicting query followed by a valid query. No telemetry is required or accessed in this slice.

Planned invocation after the module exists:

```bash
OUT=$(mktemp -d)
python3.12 run.py --dataset tests/fixtures/discovery --queries tests/fixtures/discovery/query.csv --out "$OUT" --agent agents.discovery
python3.12 scripts/validate_discovery.py --queries tests/fixtures/discovery/query.csv --out "$OUT" --capability scope
```

The run's full-discovery status remains not_run/nonzero for this intermediate capability. The capability-specific validator can pass scope correctness without asserting full discovery readiness. Inspect scope.json for source-supported values and findings.json for explicit not_run; evidence says diagnosis and remaining preparation are pending. Confirm later valid rows are persisted after an invalid scope. Preserve the stub tests. If time expires before checks pass, demonstrate only the last accepted baseline.

## Trace, metric and comparison slices (R2–R6)

Add authored telemetry records with independently enumerated expected facts: unsorted and cross-partition traces, duplicate/conflicting span IDs, unresolved parents, boundary completion, invalid durations, metric change without a frontend anomaly, sparse/zero/constant references and ambiguous relationships. Run scoped extraction against an independent scan oracle before accepting SQLite reuse. Verify every evidence locator and every rejected/empty/truncated operation receipt.

Repeat completed runs with unchanged sources/policy/work limits for equal substantive results. For deadline-truncated runs, replay recorded batch boundaries or a controlled clock schedule; different live timing may change coverage and findings. Change source bytes and policy to verify invalidation; interrupt a build to prove an incomplete view is rejected. Test repeated same-window queries with different projection/count and distinct row IDs. Trap forbidden label paths and any network call. Forced clock/volume exhaustion must preserve earlier checkpoints and reserve finalization capacity.

After R6 acceptance, the three-flag default runs discovery and the planned validator with `--capability discovery` requires completed discovery rather than merely scope artifacts. Missing required sources or partial work must fail this readiness check; qualified comparisons and adequately inspected empty findings can pass. Blank predictions remain expected for this feature.

## Cold submission rehearsal

Use the Docker command/resource envelope in [the demo guide](../../docs/demo-harness.md), with an approved mounted telemetry bundle and fresh output directory. Run the declared 20-case development corpus with no prebuilt index. Record build identity, cold/warm preparation, wall time, peak memory, coverage and case outcomes. Scope-only fixture success does not satisfy this gate.

After feature 007, repeat the unchanged official command for actual nonblank legal predictions, pinned evaluator compatibility, model usage/cost, bounded provider failures and isolated labels. Final release additionally requires feature 002's evidence review and held-out routed/single-model comparison. Do not score discovery placeholders as a completed diagnostic executor.
