#!/usr/bin/env python3
"""Run the authored baseline/comparison fixture and print an inspectable table."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from rca.baselining.demo import run_demo

FIXTURE = REPO / "tests/fixtures/qualified_baselines"


def check_fixture(report: dict, expected: dict) -> list[str]:
    """Compare public results with the independently authored fixture oracle."""
    failures = []
    rows = {row["trace_id"]: row for row in report["descriptors"]}
    checks = {
        "completed collection": report["status"] == "completed" and report["unresolved_count"] == 0,
        "all query outcomes retained": report["assignment_count"] == expected["query_occurrences"] == len(report["descriptors"]),
        "reference populations": len(report["baselines"]) == 2 and all(
            row["member_count"] == expected["reference_count_per_context"] and row["support"] == "supported"
            for row in report["baselines"]),
        "reference medians": sorted(row["median_ms"] for row in report["baselines"]) ==
            sorted([expected["constant_median_ms"], expected["zero_median_ms"]]),
    }
    for index, excess in enumerate(expected["constant_excess_ms"]):
        row = rows.get(f"query-{index}", {})
        checks[f"query-{index} signed excess and slice"] = (
            row.get("duration", {}).get("signed_excess", {}).get("value") == excess
            and row.get("slice_index") == expected["slices"][index]
        )
    checks["zero reference excess"] = rows.get("query-zero", {}).get("duration", {}).get("signed_excess", {}).get("value") == expected["zero_excess_ms"]
    checks["new context stays unavailable"] = rows.get("query-new", {}).get("duration", {}).get("signed_excess", {}).get("status") == expected["new_context"]
    for label, passed in checks.items():
        if not passed:
            failures.append(label)
    return failures


def render(report: dict, failures: list[str]) -> str:
    baselines = {row["baseline_id"]: row for row in report["baselines"]}
    lines = [
        "# Fixture demo: contextual baselines and comparative descriptors", "",
        "Authored synthetic CSV · 5-minute reference · 6 query slices · no model calls", "",
        "| Request | Slice | Reference n | Median ms | Query ms | Excess ms | Outcome |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in sorted(report["descriptors"], key=lambda item: (item["slice_index"], item["trace_id"])):
        duration = row["duration"]
        baseline = baselines.get(duration["baseline_id"])
        observed = duration["observed"]["value"]
        median = duration["reference_median"]["value"]
        excess = duration["signed_excess"]["value"]
        outcome = "qualified" if duration["signed_excess"]["status"] == "available" else "unavailable"
        values = [row["trace_id"], str(row["slice_index"]), str(baseline["member_count"]) if baseline else "—",
                  f"{median:g}" if median is not None else "—", f"{observed:g}" if observed is not None else "—",
                  f"{excess:+g}" if excess is not None else "—", outcome]
        lines.append("| " + " | ".join(values) + " |")
    lines += ["", "Fixture check: " + ("FAIL — " + "; ".join(failures) if failures else "PASS (8 query outcomes)"), "",
              "The constant reference produces +2, −2 and 0 ms differences. The zero reference still supports +12 ms excess. "
              "The new context remains unavailable; no fallback is selected.", "",
              "These are qualified empirical comparisons. Reference health is unverified and raw duration units are provisionally microseconds. "
              "Full semantic evidence validation and trusted rankings are deferred; this is not a diagnosis or anomaly-accuracy demonstration.", "",
              "## Remaining gaps", ""]
    lines.extend(f"- {gap}" for gap in report["acceptance_gaps"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="Fresh output directory; defaults to a new temporary directory.")
    args = parser.parse_args(argv)
    output = args.output_dir.resolve() if args.output_dir else Path(tempfile.mkdtemp(prefix="baseline-comparison-demo-"))
    try:
        if output.exists() and any(output.iterdir()):
            raise ValueError("output directory must be empty; choose a fresh directory")
        output.mkdir(parents=True, exist_ok=True)
        scope = json.loads((FIXTURE / "scope.json").read_text())
        expected = json.loads((FIXTURE / "expected.json").read_text())
        anchor_ms = int(datetime.fromisoformat(scope["anchor"]).timestamp() * 1000)
        report = run_demo(FIXTURE / "dataset", scope["deployment"], anchor_ms, output)
        failures = check_fixture(report, expected)
        summary = render(report, failures)
        (output / "demo.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        (output / "fixture-check.json").write_text(json.dumps({"status": "failed" if failures else "passed", "failures": failures}, indent=2) + "\n")
        (output / "demo.md").write_text(summary)
        print(summary)
        print(f"Artifacts: {output}")
        return 1 if failures else 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
