# Demo handoff

Implementation checkpoint: `7539556`. Python 3.12, standard library only.

Run the authored CSV fixture from the repository root with a fresh output path:

```sh
python3.12 -m rca.baselining.demo \
  --dataset-dir tests/fixtures/qualified_baselines/dataset \
  --scope-file tests/fixtures/qualified_baselines/scope.json \
  --output-dir /tmp/baseline-comparison-demo
```

The output is a demo receipt (`demo.json`), not a validated artifact bundle.
It contains two supported baseline contexts and eight complete query
descriptors. The six constant-context excesses are `[2, -2, 0, 2, 2, 2]` ms.
The zero-center query has +12 ms excess and undefined ratio/MAD diagnostics.
The new context remains unavailable. Health and replica equivalence are
unverified qualifications, not diagnoses.

The reusable composition is implemented in `rca.baselining.demo.run_demo`:

```python
from rca.baselining import (
    BaselinePolicy, prepare_sources, collect_requests,
    freeze_baselines, assign_queries,
)
from rca.comparisons import ComparisonDefinition, describe

policy = BaselinePolicy(normalization_id="provisional-us-to-ms-v1")
view = prepare_sources(dataset_dir, source_inventory, output_dir)
batch = collect_requests(view, deployment, anchor_ms, policy)
baseline_set = freeze_baselines(batch, view.snapshot, anchor_ms, policy)
assignments = assign_queries(batch, baseline_set)
descriptors = [
    describe(item.observation, item, item.baseline,
             item.structural_population, ComparisonDefinition())
    for item in assignments.assignments
]
```

`source_inventory` comes from `rca.telemetry.inventory.inventory` and timestamps
are epoch milliseconds. The source adapter returns the shared typed
`ObservationBatch`; the pure kernels perform no source access. CSV raw duration
is provisionally interpreted as microseconds and normalized to milliseconds;
the explicit normalization policy must match the observation measurements.

Core validation:

```sh
python3.12 -m unittest tests.unit.test_baseline_core \
  tests.unit.test_baseline_sources tests.unit.test_descriptor_core \
  tests.integration.test_baseline_pipeline -v
```

Eight tests passed at the implementation checkpoint; the final suite also includes five comparison-core checks (13 total). This demonstrates the
public seam; it does not establish all planned B01–B12 / D01–D12 gates.

Deferred to keep the demo small: formal immutable bundle build/load/validation
CLIs, complete source/member/statistic evidence-graph validation, trusted
rankings, complete acceptance matrices and large-source performance work.
`validate_descriptor` can check arithmetic and local pointers but returns
`unchecked` on success while semantic validation is deferred. `review_view`
rejects constructed/unchecked descriptors. Do not promote their status merely
to enable ranking. Integration explicitly chooses this new profile; the legacy
runner/discovery policy was not changed by this task.

Presentation wrapper: `python3.12 scripts/demo_baseline_comparison.py`, owned and committed separately in `90e1011`. It prints the authored expected/actual outcomes and saves a readable Markdown walkthrough plus JSON.
