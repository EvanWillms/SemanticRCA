# Validation quickstart: Qualified baselines

This guide describes commands the implementation must make runnable. The new package, tests and synthetic fixtures do not exist yet; do not interpret these commands as executed acceptance evidence. Existing research scripts are not substitutes for these checks.

## Prerequisites

- Python 3.12 and the repository checkout; no third-party Python package or model credential.
- Implemented producer/API from [producer.md](contracts/producer.md).
- Authored synthetic fixture tree at `tests/fixtures/qualified_baselines/`, checked into source during implementation. Its `dataset/` follows the declared Track 1 trace CSV layout; `scope.json` supplies a deployment and offset-aware anchor. No private telemetry or fault labels are required.

The fixture inventory must cover B01–B12: interleaved adjacent partitions, all three allowlisted replicas, an out-of-scope replica, identical duplicates/conflicts, unknown/empty structure, exact time boundaries, sparse/concentrated cohorts, constant/zero/unstable centers and source mutation. Expected membership/values must be authored independently of producer helpers.

## Run focused acceptance

From the repository root after implementation:

```sh
python3.12 -m unittest discover -s tests/unit -p 'test_baseline_*.py' -v
python3.12 -m unittest discover -s tests/integration -p 'test_baseline_pipeline.py' -v
```

Expected: all [B01–B12](acceptance.md) checks pass. The test report identifies each case; an empty test discovery is a failure. Independent expectations verify 19/20 count, 2/3 occupied minutes, 10/11-of-20 concentration, 189/190 usable resamples and exactly/above 40% width. Zero median/MAD and supported instability must retain the prescribed distinct states.

Golden resampling fixtures include independently recorded block draws/quantile results. A same-function-twice equality check is insufficient. Validate a non-minute-aligned anchor as well as the minute-aligned research shape.

## Build and validate from raw synthetic sources

```sh
BASELINE_RUN_ROOT=$(mktemp -d)
python3.12 -m rca.baselining build \
  --dataset-dir tests/fixtures/qualified_baselines/dataset \
  --scope-file tests/fixtures/qualified_baselines/scope.json \
  --output-dir "$BASELINE_RUN_ROOT/baselines" \
  --policy-id short-window-c1-pooled-v1
python3.12 -m rca.baselining validate \
  --dataset-dir tests/fixtures/qualified_baselines/dataset \
  --bundle-dir "$BASELINE_RUN_ROOT/baselines"
```

Expected: exit 0 and a complete validated manifest. Every resolved query has an assignment; unsupported classes remain in coverage. The manifest references all artifacts listed in the producer contract. No source data is modified. Low support alone does not cause a process failure.

The fixture's positive constant cohort should contain 20 distinct roots spread over three absolute minutes with counts 8/6/6 and a 10 ms median. A query of 12 ms receives a qualified median reference with zero MAD; feature 010 will yield +2 ms and an undefined requested MAD score. Separate fixture cases cover a zero median, a missing C1 cohort and a supported unstable center.

## Reuse, corruption and boundary checks

The integration test must exercise the public Python API to reuse one prepared snapshot and baseline set across all six slices. Assert counters for one bootstrap per baseline and no repeated full CSV parsing, as well as unchanged set/catalog/member IDs. Introduce a new C1 shape and an entirely new C0 operation in the last slice: both produce typed missing-context assignments without modifying the reference-only catalog; the consumer retains complete unavailable outcomes. Reopening a moved dataset with identical relative paths/content validates the same snapshot; changing a source value, extraction rule or policy rejects reuse.

Run interruption tests at deterministic index-build/recovery/publication boundaries. A partial build has no valid complete marker; an affected incomplete reference population cannot produce a supported baseline. Validate that existing completed generations remain readable after a failed new generation.

Source and malformed-schema failures return nonzero with explicit reasons; they are not ordinary support abstentions. Compare indexed selection/recovery against the independent scan reference, including query executions that finish after their start slice and reference endpoints exactly at T.

## Joint consumer and container gate

Continue with [feature 010's quickstart](../010-comparative-descriptors/quickstart.md) using the generated baseline directory. After focused tests pass, run existing harness regressions affected by integration and rehearse the same two CLIs inside the existing Python 3.12 image with read-only synthetic dataset and writable output mounts. The official runner's required flags stay unchanged.

Record preparation, warm reuse, memory, source scans and index size; do not set a universal runtime claim from one machine. Preserve acceptance results under generated output, not source fixture expectations. A full study replay is an optional separately requested exposed-data regression, not a prerequisite for these authored checks.
