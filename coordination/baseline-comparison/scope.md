# Baseline and comparison ownership

Owner: [Implement baseline descriptor plans](codex://threads/01a0b13b-d809-7c80-a199-c868d40b8781) (implementation and this coordination folder).

Design origin: [Demonstrate best-in-class anomaly](codex://threads/01a0b0a2-ce71-78a0-9aea-64fd43294105), which produced ADRs 0013/0014 and the feature 009/010 specifications and implementation plans. Design handoff: `fd49fbc` (ADRs/specs), `c44acda` (reviewed plans). The implementation owner maintains executable work and reports subagent progress here.

Owned paths: `rca/baselining/`, `rca/comparisons/`, new `rca/telemetry/trace_index.py` (unless the trace-domain owner claims this prerequisite), `tests/unit/test_baseline_*.py`, `tests/unit/test_descriptor_*.py`, `tests/integration/test_baseline_pipeline.py`, `tests/integration/test_comparison_pipeline.py`, and this coordination folder.

Public interface: declared trace inventory and source snapshot + deployment + anchor in epoch milliseconds → prepared observations → immutable five-minute C1 baseline set and C0 structural populations → six-slice query assignments → complete comparative descriptors and separate top-five review views. Public modules: `rca.baselining` and `rca.comparisons`.

Dependencies: existing telemetry inventory/path containment; feature 009/010 contracts. Temporary Luna extra-high workers report through this owner.

Exclusions: legacy discovery policy, runner flags, final diagnosis, model calls, GLM semantics, investigation loop and experiments. No other task's files are staged in our commits. Integration explicitly opts into the profile.

Design inputs: [baseline producer contract](../../specs/009-qualified-short-baselines/contracts/producer.md), [descriptor consumer contract](../../specs/010-comparative-descriptors/contracts/consumer.md). These are planned interfaces; demo readiness requires an available implementation plus a passing happy-path check. In particular, late MissingContext outcomes must preserve frozen catalogs and trusted review views must require semantic evidence validation.
