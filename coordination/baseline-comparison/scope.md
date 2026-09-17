# Baseline and comparison ownership

Owner task: `01a0b13b-d809-7c80-a199-c868d40b8781` (Implement baseline descriptor plans).

Owned paths: `rca/baselining/`, `rca/comparisons/`, new `rca/telemetry/trace_index.py` (unless the trace-domain owner claims this prerequisite), `tests/unit/test_baseline_*.py`, `tests/unit/test_descriptor_*.py`, `tests/integration/test_baseline_pipeline.py`, `tests/integration/test_comparison_pipeline.py`, and this coordination folder.

Public interface: declared trace inventory and source snapshot + deployment + anchor in epoch milliseconds → prepared observations → immutable five-minute C1 baseline set and C0 structural populations → six-slice query assignments → complete comparative descriptors and separate top-five review views. Public modules: `rca.baselining` and `rca.comparisons`.

Dependencies: existing telemetry inventory/path containment; feature 009/010 contracts. Temporary Luna extra-high workers report through this owner.

Exclusions: legacy discovery policy, runner flags, final diagnosis, model calls, GLM semantics, investigation loop and experiments. No other task's files are staged in our commits. Integration explicitly opts into the profile.
