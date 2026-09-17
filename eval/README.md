# Harness fixtures

`fixtures/query.csv` is a synthetic input for the empty-output harness. It
contains two non-contiguous row IDs and multiline instructions so the shipped
CSV and artifact association paths can be exercised offline.

The fixture contains no benchmark telemetry, labels, expected diagnoses, or
accuracy results. It is an I/O demonstration only. A successful run or
validation with it does not measure diagnostic performance and is not official
benchmark validation.

From the repository root, run the runner into a fresh empty directory and then
validate its artifacts:

```bash
HARNESS_OUT="$(mktemp -d)"
python3.12 run.py --dataset eval/fixtures --queries eval/fixtures/query.csv --out "$HARNESS_OUT" --agent agents.submission
python3.12 scripts/validate_harness.py --queries eval/fixtures/query.csv --out "$HARNESS_OUT"
```

The validator requires blank predictions, four explicitly unimplemented
evidence sections per ID, measured non-negative case timing, and zero model
usage. It does not call a model or access a network service.
