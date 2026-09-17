#!/usr/bin/env python3
"""Generate and run the small, offline happy-path discovery demonstration."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Iterable


REPOSITORY = Path(__file__).resolve().parents[1]
PARTITION = "2025_06_15"
DEPLOYMENT = "cloudbed-8"
ANCHOR = "2025-06-15T09:00:00+08:00"
START = int(
    datetime(2025, 6, 15, 9, 0, tzinfo=timezone(timedelta(hours=8))).timestamp()
)
INSTRUCTION = (
    "The system cloudbed-8 experienced one failure on June 15, 2025, "
    "from 09:00 to 09:30. Please identify the root cause component."
)


def _write_csv(path: Path, columns: Iterable[str], rows: Iterable[Iterable[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


def _source(bundle: Path, family: str, columns: Iterable[str], rows: Iterable[Iterable[object]]) -> None:
    modality = family.split("_", 1)[0]
    _write_csv(
        bundle / "telemetry" / PARTITION / modality / f"{family}.csv",
        columns,
        rows,
    )


def _write_bundle(bundle: Path) -> Path:
    query = bundle / "query.csv"
    _write_csv(query, ("row_id", "instruction"), ((1, INSTRUCTION),))

    trace_columns = (
        "timestamp",
        "cmdb_id",
        "span_id",
        "trace_id",
        "duration",
        "type",
        "status_code",
        "operation_name",
        "parent_span",
    )
    reference_starts = (
        *(START - 180 + index for index in range(8)),
        *(START - 120 + index for index in range(6)),
        *(START - 60 + index for index in range(6)),
    )
    trace_rows = [
        (start * 1000, "frontend-0", "root", f"ref-{index:02d}", 100,
         "rpc", "0", "GET /", "")
        for index, start in enumerate(reference_starts)
    ]
    trace_rows.append(((START + 10) * 1000, "frontend-0", "root", "query", 300,
                       "rpc", "0", "GET /", ""))
    _source(bundle, "trace_span", trace_columns, trace_rows)

    metric_columns = ("timestamp", "cmdb_id", "kpi_name", "value")
    metric_rows = [
        (START - 100 + index, "worker-2", "cpu", 10)
        for index in range(20)
    ]
    metric_rows.append((START + 10, "worker-2", "cpu", 35))
    for family in ("metric_container", "metric_mesh", "metric_node", "metric_runtime"):
        _source(bundle, family, metric_columns, metric_rows)

    service_columns = ("service", "timestamp", "rr", "sr", "mrt", "count")
    service_rows = [
        ("worker", START - 100 + index, 1, 1, 10, 5)
        for index in range(20)
    ]
    service_rows.append(("worker", START + 10, 1, 1, 10, 5))
    _source(bundle, "metric_service", service_columns, service_rows)

    log_columns = ("log_id", "timestamp", "cmdb_id", "log_name", "value")
    _source(bundle, "log_service", log_columns,
            (("service-log", START + 10, "worker-2", "app", "resource busy"),))
    _source(bundle, "log_proxy", log_columns,
            (("proxy-log", START + 10, "worker-2", "proxy", "resource busy"),))
    return query


def _run(repo: Path, bundle: Path, query: Path, results: Path) -> None:
    command = [
        sys.executable,
        str(repo / "run.py"),
        "--dataset",
        str(bundle),
        "--queries",
        str(query),
        "--out",
        str(results),
        "--agent",
        "agents.discovery",
    ]
    run = subprocess.run(command, cwd=repo, capture_output=True, text=True)
    if run.returncode != 0:
        detail = (run.stderr or run.stdout).strip()
        raise RuntimeError(f"discovery CLI failed ({run.returncode}): {detail}")

    validation = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "validate_discovery.py"),
            "--queries",
            str(query),
            "--out",
            str(results),
            "--capability",
            "discovery",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if validation.returncode != 0:
        detail = (validation.stderr or validation.stdout).strip()
        raise RuntimeError(f"discovery validation failed ({validation.returncode}): {detail}")


def _write_baseline_scope(root: Path) -> Path:
    scope = root / "baseline-scope.json"
    scope.write_text(json.dumps({
        "schema_version": "baseline-scope-v1",
        "deployment": DEPLOYMENT,
        "anchor": ANCHOR,
    }, indent=2) + "\n", encoding="utf-8")
    return scope


def _run_baseline(repo: Path, bundle: Path, scope: Path, output: Path) -> None:
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "rca.baselining.demo",
            "--dataset-dir",
            str(bundle),
            "--scope-file",
            str(scope),
            "--output-dir",
            str(output),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if run.returncode != 0:
        detail = (run.stderr or run.stdout).strip()
        raise RuntimeError(f"baseline/comparison CLI failed ({run.returncode}): {detail}")


def _run_investigation(repo: Path, findings: Path, scope: Path, output: Path) -> None:
    run = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "demo_investigation.py"),
            "--findings",
            str(findings),
            "--scope",
            str(scope),
            "--out",
            str(output),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if run.returncode != 0:
        detail = (run.stderr or run.stdout).strip()
        raise RuntimeError(f"investigation CLI failed ({run.returncode}): {detail}")


def _write_summary(root: Path, results: Path) -> None:
    findings = json.loads((results / "cases" / "1" / "findings.json").read_text(encoding="utf-8"))
    baseline = json.loads((root / "baselines" / "demo.json").read_text(encoding="utf-8"))
    investigation = json.loads((root / "investigation.json").read_text(encoding="utf-8"))
    selected = []
    for finding in findings["candidates"]:
        if finding["channel"] == "trace_duration" and not any(
            item["channel"] == "trace_duration" for item in selected
        ):
            selected.append(finding)
        elif finding["channel"] == "metric" and finding.get("resource") == "worker-2" and not any(
            item["channel"] == "metric" for item in selected
        ):
            selected.append(finding)
    lines = [
        "# SymbolicRCA discovery demo",
        "",
        "Status: **Synthetic fixture; Discovery only**.",
        "",
        "This one-command run reads a generated eight-family telemetry bundle, "
        "persists descriptive findings, and makes zero model calls or network requests.",
        "",
        "| Channel | Resource | Observed | Reference | Change | Source |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for finding in selected:
        if finding["channel"] == "trace_duration":
            locator = finding["locator"]
            observed = finding["value"]
            reference = finding["reference_median"]
            change = finding["difference"]
            source = locator["path"]
        else:
            observation = finding["observation"]
            locator = observation["locator"]
            observed = finding["value"]
            reference = finding["reference_median"]
            change = finding["signed_difference"]
            source = locator["path"]
        lines.append(
            f"| `{finding['channel']}` | `{finding['resource']}` | {observed:g} | "
            f"{reference:g} | +{change:g} | [{Path(source).name}](bundle/{source}) |"
        )
    lines.extend([
        "",
        f"The run produced {len(findings['candidates'])} positive candidates. "
        "The observations are descriptive and do not establish a root cause.",
        f"The trace domain described {len(findings['semantic_description']['traces'])} selected trace(s), "
        f"retaining {len(findings['semantic_deferred'])} explicitly deferred semantic item(s).",
        f"Baseline/comparison: [report](baselines/demo.json) with {len(baseline['baselines'])} baseline(s), "
        f"{len(baseline['descriptors'])} descriptor(s), and {baseline['assignment_count']} assignment(s) "
        f"from {baseline['observation_count']} observation(s).",
        f"Investigation: [report](investigation.json), stopped at `{investigation['investigation_stop_reason']}` "
        f"after {investigation['usage']['assessment_attempts']} assessment attempt(s) and "
        f"{investigation['usage']['operation_attempts']} operation attempt(s); the scripted answer is not an "
        "accuracy claim.",
        "",
        "Artifacts: [predictions](results/predictions.csv), "
        "[scope](results/cases/1/scope.json), "
        "[findings](results/cases/1/findings.json), and "
        "[evidence](results/evidence/1.md).",
        "",
        "The complete generated bundle is under [bundle](bundle/).",
        "",
    ])
    (root / "demo.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path,
                        help="empty directory in which bundle, results, and demo.md are created")
    args = parser.parse_args(argv)
    root = args.out.expanduser().resolve()
    try:
        if root.exists() and (not root.is_dir() or next(root.iterdir(), None) is not None):
            raise ValueError("--out must be a new or empty directory")
        root.mkdir(parents=True, exist_ok=True)
        bundle = root / "bundle"
        results = root / "results"
        query = _write_bundle(bundle)
        _run(REPOSITORY, bundle, query, results)
        baseline_scope = _write_baseline_scope(root)
        _run_baseline(REPOSITORY, bundle, baseline_scope, root / "baselines")
        _run_investigation(
            REPOSITORY,
            results / "cases" / "1" / "findings.json",
            results / "cases" / "1" / "scope.json",
            root / "investigation.json",
        )
        _write_summary(root, results)
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(f"demo failed: {exc}", file=sys.stderr)
        return 2
    print(f"Discovery demo complete: {root / 'demo.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
