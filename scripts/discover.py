#!/usr/bin/env python3
"""Run deterministic discovery and render its persisted findings."""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
import subprocess
import sys
from typing import Any


REPOSITORY = Path(__file__).resolve().parents[1]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="mounted dataset directory")
    parser.add_argument("--queries", required=True, help="query CSV path")
    parser.add_argument("--out", required=True, help="discovery output directory")
    return parser


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _display(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "unavailable"
    if number == int(number):
        return str(int(number))
    return format(number, ".12g")


def _case_key(path: Path) -> tuple[int, str]:
    try:
        return (0, f"{int(path.parent.name):020d}")
    except ValueError:
        return (1, path.parent.name)


def _locator(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    direct = candidate.get("locator")
    if isinstance(direct, Mapping):
        return direct
    observation = candidate.get("observation")
    if isinstance(observation, Mapping):
        nested = observation.get("locator")
        if isinstance(nested, Mapping):
            return nested
    provenance = candidate.get("provenance")
    if isinstance(provenance, Sequence) and not isinstance(provenance, (str, bytes)):
        first = next((item for item in provenance if isinstance(item, Mapping)), None)
        if first is not None:
            return first
    return {}


def _source_path(dataset: Path, locator: Mapping[str, Any]) -> str | None:
    raw_path = locator.get("path")
    if not raw_path:
        return None
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = dataset / path
    return str(path.expanduser().resolve(strict=False))


def _source(locator: Mapping[str, Any], dataset: Path) -> str:
    path = _source_path(dataset, locator)
    record = locator.get("record")
    if path is None:
        return "source unavailable"
    if record is None:
        return f"source={path}"
    return f"source={path} record={record}"


def _trace_positive(candidates: Sequence[Any]) -> Mapping[str, Any] | None:
    found: list[Mapping[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping) or candidate.get("channel") != "trace_duration":
            continue
        difference = _number(candidate.get("difference"))
        if difference is not None and difference > 0:
            found.append(candidate)
    found.sort(key=lambda item: (
        -(_number(item.get("difference")) or 0.0),
        _number(item.get("timestamp")) or 0.0,
        str(item.get("resource", "")),
        str(_locator(item).get("path", "")),
        int(_number(_locator(item).get("record")) or 0),
        str(item.get("id", "")),
    ))
    return found[0] if found else None


def _metric_departure(candidates: Sequence[Any]) -> Mapping[str, Any] | None:
    found: list[tuple[float, Mapping[str, Any]]] = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping) or candidate.get("channel") != "metric":
            continue
        signed = _number(candidate.get("signed_difference"))
        if signed is None:
            signed = _number(candidate.get("difference"))
        if signed is None or signed == 0:
            continue
        found.append((abs(signed), candidate))
    found.sort(key=lambda item: (
        -item[0],
        _number(item[1].get("timestamp")) or 0.0,
        str(item[1].get("resource", "")),
        str(item[1].get("kpi", "")),
        str(item[1].get("family", "")),
        str(_locator(item[1]).get("path", "")),
        int(_number(_locator(item[1]).get("record")) or 0),
        str(item[1].get("id", "")),
    ))
    return found[0][1] if found else None


def _trace_line(candidate: Mapping[str, Any], dataset: Path) -> str:
    difference = _display(candidate.get("difference"))
    return (
        f"trace positive {candidate.get('resource', 'unavailable')} "
        f"raw observed={_display(candidate.get('value'))} "
        f"reference={_display(candidate.get('reference_median'))} "
        f"raw change {difference} {_source(_locator(candidate), dataset)}"
    )


def _metric_line(candidate: Mapping[str, Any], dataset: Path) -> str:
    signed = _number(candidate.get("signed_difference"))
    if signed is None:
        signed = _number(candidate.get("difference"))
    observation = candidate.get("observation")
    raw_observed = candidate.get("raw_value")
    if isinstance(observation, Mapping) and observation.get("raw_value") is not None:
        raw_observed = observation.get("raw_value")
    return (
        f"metric departure {candidate.get('resource', 'unavailable')} "
        f"{candidate.get('kpi', 'unavailable')} raw observed={_display(raw_observed)} "
        f"reference={_display(candidate.get('reference_median'))} "
        f"change {_display(signed)} {_source(_locator(candidate), dataset)}"
    )


def _case_line(case: Mapping[str, Any], dataset: Path) -> str:
    status = str(case.get("status") or "unavailable")
    stop_reason = case.get("stop_reason")
    candidates = case.get("candidates")
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        candidates = []
    trace = _trace_positive(candidates)
    metric = _metric_departure(candidates)
    details: list[str] = []
    if trace is not None:
        details.append(_trace_line(trace, dataset))
    if metric is not None:
        details.append(_metric_line(metric, dataset))
    if not details:
        if status in {"partial", "unavailable", "not_run"}:
            reason = f"; stop reason={stop_reason}" if stop_reason else ""
            details.append(f"no supported departure can be reported{reason}")
        else:
            details.append("no supported departure; no health conclusion")
    reason = f" stop_reason={stop_reason}" if stop_reason else ""
    return f"case {case.get('row_id', 'unknown')} status={status}{reason}: " + "; ".join(details)


def _markdown_case(case: Mapping[str, Any], dataset: Path) -> list[str]:
    status = str(case.get("status") or "unavailable")
    lines = [f"## Case {case.get('row_id', 'unknown')} — {status}", ""]
    if case.get("stop_reason"):
        lines.append(f"Stop reason: `{case['stop_reason']}`.")
        lines.append("")
    candidates = case.get("candidates")
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        candidates = []
    trace = _trace_positive(candidates)
    metric = _metric_departure(candidates)
    if trace is not None:
        locator = _locator(trace)
        source = _source_path(dataset, locator)
        link = f"[{source}]({source})" if source else "source unavailable"
        lines.append(
            f"- Trace positive departure on `{trace.get('resource', 'unavailable')}`: "
            f"raw observed `{_display(trace.get('value'))}`, reference "
            f"`{_display(trace.get('reference_median'))}`, raw change "
            f"`{_display(trace.get('difference'))}`; {link} (record "
            f"`{locator.get('record', 'unavailable')}`)."
        )
    if metric is not None:
        locator = _locator(metric)
        source = _source_path(dataset, locator)
        link = f"[{source}]({source})" if source else "source unavailable"
        observation = metric.get("observation")
        raw_observed = metric.get("raw_value")
        if isinstance(observation, Mapping) and observation.get("raw_value") is not None:
            raw_observed = observation.get("raw_value")
        signed = _number(metric.get("signed_difference"))
        if signed is None:
            signed = _number(metric.get("difference"))
        lines.append(
            f"- Metric departure on `{metric.get('resource', 'unavailable')}` "
            f"(`{metric.get('kpi', 'unavailable')}`): raw observed "
            f"`{_display(raw_observed)}`, reference "
            f"`{_display(metric.get('reference_median'))}`, signed change "
            f"`{_display(signed)}`; {link} (record "
            f"`{locator.get('record', 'unavailable')}`)."
        )
    if trace is None and metric is None:
        if status in {"partial", "unavailable", "not_run"}:
            lines.append("- No supported departure can be reported from this persisted case.")
        else:
            lines.append("- No supported departure; no health conclusion is established.")
    lines.append("")
    return lines


def _load_cases(output: Path) -> list[dict[str, Any]]:
    cases_dir = output / "cases"
    if not cases_dir.is_dir():
        return []
    cases: list[dict[str, Any]] = []
    for path in sorted(cases_dir.glob("*/findings.json"), key=_case_key):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(value, Mapping):
            cases.append(dict(value))
    return cases


def _write_findings(output: Path, dataset: Path, cases: Sequence[Mapping[str, Any]]) -> None:
    lines = [
        "# Findings",
        "",
        "These are persisted descriptive departures. They do not establish a root cause or system health.",
        "",
    ]
    for case in cases:
        lines.extend(_markdown_case(case, dataset))
    if not cases:
        lines.append("No persisted case findings were available.")
        lines.append("")
    (output / "findings.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    dataset = Path(args.dataset).expanduser().resolve(strict=False)
    queries = Path(args.queries).expanduser().resolve(strict=False)
    output = Path(args.out).expanduser().resolve(strict=False)
    command = [
        sys.executable,
        str(REPOSITORY / "run.py"),
        "--dataset",
        str(dataset),
        "--queries",
        str(queries),
        "--out",
        str(output),
        "--agent",
        "agents.discovery",
    ]
    run = subprocess.run(command, cwd=REPOSITORY, capture_output=True, text=True)
    if run.returncode >= 2:
        if run.stdout:
            print(run.stdout, end="")
        if run.stderr:
            print(run.stderr, end="", file=sys.stderr)
        return run.returncode

    cases = _load_cases(output)
    try:
        _write_findings(output, dataset, cases)
    except OSError as exc:
        print(f"error: findings report could not be written: {exc}", file=sys.stderr)
        return run.returncode

    for case in cases:
        print(_case_line(case, dataset))
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
