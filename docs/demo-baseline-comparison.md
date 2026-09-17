# Fixture-based baseline and comparison demo

Run from the repository root with Python 3.12:

```sh
python3.12 scripts/demo_baseline_comparison.py
```

No credentials, network access or private telemetry are required. The command reads the checked-in [authored CSV fixture](../tests/fixtures/qualified_baselines/README.md), runs the actual baseline/comparison library, prints all eight query outcomes, checks the independently authored expected values and reports its output directory. Exit 0 means the fixture check passed.

To choose a fresh output directory:

```sh
python3.12 scripts/demo_baseline_comparison.py --output-dir /tmp/my-baseline-demo
```

Existing nonempty output directories are rejected. The demo creates `demo.md` (presentation table), `demo.json` (complete source-linked result), `fixture-check.json` (expected-value check) and prepared source artifacts. It never modifies the fixture.

## What to demonstrate

| Request | Reference median | Query | Signed excess | Meaning |
| --- | ---: | ---: | ---: | --- |
| query-0 | 10 ms | 12 ms | +2 ms | Above this reference median |
| query-1 | 10 ms | 8 ms | −2 ms | Negative differences are retained |
| query-2 | 10 ms | 10 ms | 0 ms | Equal values are retained |
| query-zero | 0 ms | 12 ms | +12 ms | A zero reference still supports signed excess |
| query-new | unavailable | 5 ms | unavailable | A new context does not trigger a guessed fallback |

Each supported context has 20 reference requests across three occupied minutes, distributed 8/6/6. The same five-minute reference is used over six query slices. Requests query-3 through query-5 each retain +2 ms excess. The new context appears in the final slice.

Open `demo.json` to inspect source identities, locators, baseline IDs, support/stability and qualifications. The table is in slice/request order; it is not a trusted ranking. The library also exposes zero-denominator diagnostics as undefined rather than infinity.

## Core validation evidence

```sh
python3.12 -m unittest tests.integration.test_demo_baseline_comparison -v
```

This public CLI test was observed failing before the presentation script existed, then passing after implementation. It runs from outside the repository directory and checks saved outcomes for positive, negative, zero and unavailable comparisons. The displayed fixture command also completed with `Fixture check: PASS (8 query outcomes)` on 2026-09-17.

The thin [presentation script](../scripts/demo_baseline_comparison.py) calls `rca.baselining.demo.run_demo`; it does not replace the baseline or descriptor algorithms. The library owner maintains its separate focused tests and [current handoff](../coordination/baseline-comparison/status.md).

## Limits

This is an authored, deterministic library demonstration. Reference health and workload/replica equivalence are unverified, and source duration units are provisionally interpreted as microseconds. Full semantic evidence validation, trusted review rankings, formal versioned artifact CLIs, large-data performance and the full feature acceptance matrices remain deferred. No anomaly-detection accuracy, diagnosis or production-readiness claim follows from this fixture.
