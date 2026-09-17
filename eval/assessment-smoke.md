# Assessment output verification — 2026-09-17

The official three-flag CLI was exercised on two queries (row IDs 0 and 1) from
the local 11 GB Track 1 bundle. Only query IDs, task indices, and instructions
were copied into the subset. No model API key was supplied for this check.

Before the fix, whole-bundle inventory exhausted the 30-second discovery
allocation and the first case emitted no candidate observations. The assessment
path now scans dated metric partitions with a 30-minute reference window,
requires 20 reference samples, caps retained samples, and preserves measurements
when a later scan is interrupted. Trace and log coverage remains uninspected and
is explicitly reported.

| Case | Elapsed seconds | Measured findings | Model calls |
| --- | ---: | ---: | ---: |
| 0 | 6.334 | 24 | 0 |
| 1 | 6.622 | 24 | 0 |

Both cases wrote `predictions.csv`, their `evidence/<row_id>.md` files, and
`usage.jsonl`. The requested prediction fields contain `I don't know`, following
the explicit unavailable-model fallback. Evidence retains observed values,
reference medians and sample counts, timestamps, and CSV record locators.
All 48 findings and their reference medians were checked against 1,460 distinct
CSV records across four raw source files.

The artifact validator passed. All 76 repository unittest checks passed,
including the two-case default-CLI test with minute-cadence synthetic telemetry,
sparse row IDs, and a datetime-only query. Additional tests cover retaining
completed findings on timeout, excluding conflicting samples, and respecting
the selected metric dates. `make validate` includes these assessment checks.

This verifies measured output and unattended execution, not root-cause
accuracy. Raw magnitudes across different KPIs are not directly comparable;
cumulative counters can dominate the shortlist. A peak sample is not a verified
fault onset, an empirical baseline is not verified healthy, and an unknown
prediction can score zero. Live GLM diagnosis and the full 20-case constrained
benchmark are not certified by this offline check.
