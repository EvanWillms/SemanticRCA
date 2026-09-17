#!/usr/bin/env python3
"""Build a bounded post-run RESULTS.md from sealed evaluator artifacts.

The collector is label-free. It consumes evaluator outputs after the seal gate
and case execution metadata, but never opens query labels, scoring points,
answer keys, evidence narratives, or predictions. Missing metrics are reported
as unavailable rather than converted into success claims.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import itertools
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

REQUIRED_ROWS = tuple(row for row in range(70) if row != 25)
ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SCOPE = ROOT / "docs/research/experiments/frontend-blind-v1/scope.csv"
DEFAULT_CASE_ROOT = ROOT / "data/experiments/frontend-blind-v1/cases"
DEFAULT_METRICS = ROOT / "data/experiments/frontend-blind-v1/results/metrics.json"
DEFAULT_RESULTS = ROOT / "data/experiments/frontend-blind-v1/results/results.csv"
DEFAULT_COMPARISONS = ROOT / "data/experiments/frontend-blind-v1/results/comparisons.csv"


class CollectionError(RuntimeError):
    pass


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectionError(f"cannot read JSON {path}: {exc}") from exc


def _rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError as exc:
        raise CollectionError(f"cannot read CSV {path}: {exc}") from exc


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return "Unavailable"
    return f"{value:.{digits}f}" if isinstance(value, float) else str(value)


def _pct(value: Any) -> str:
    number = _number(value)
    return "Unavailable" if number is None else f"{number:.1%}"


def _md_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    body = ["| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |"]
    body.extend("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |"
                for row in rows)
    return "\n".join(body)


def _gate(case_root: Path, scope_path: Path) -> dict[str, Any]:
    """Run the existing label-free seal gate before reading report inputs."""
    from experiments.frontend_blind_v1.seal import SealError, validate_all
    try:
        return validate_all(case_root, scope_csv=scope_path, require_final=True)
    except (SealError, OSError, ValueError) as exc:
        raise CollectionError(f"report refused before reading metrics: {exc}") from exc


def _scope(path: Path) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    for row in _rows(path):
        try:
            result[int(row["row_id"])] = row
        except (KeyError, ValueError) as exc:
            raise CollectionError(f"scope row has invalid row_id: {row}") from exc
    if set(result) != set(range(70)):
        raise CollectionError("scope must contain the public 70 rows, including control 25")
    return result


def _safe_case_facts(case_root: Path, row_id: int, output_dir: Path) -> dict[str, Any]:
    """Read execution metadata only; never read case predictions or narratives."""
    case = case_root / str(row_id)
    facts: dict[str, Any] = {"row_id": row_id, "status": "Unavailable",
                             "elapsed_seconds": None, "retrieval_calls": 0,
                             "coverage": "Unavailable", "eligible": "Unavailable",
                             "span_flags": 0}
    run_path = case / "run.json"
    if run_path.exists():
        run = _load_json(run_path)
        facts["status"] = run.get("status", "Unavailable")
        facts["preparation_elapsed_seconds"] = run.get("elapsed_seconds")
        # Preparation also writes elapsed_seconds; never call that investigator runtime.
        facts["elapsed_seconds"] = run.get("investigation_elapsed_seconds")
        for start_key, end_key in (("investigation_start_utc", "investigation_end_utc"),
                                   ("started_at_utc", "finished_at_utc"),
                                   ("investigation_started_at_utc", "investigation_finished_at_utc")):
            if run.get(start_key) and run.get(end_key):
                try:
                    facts["elapsed_seconds"] = (datetime.fromisoformat(run[end_key].replace("Z", "+00:00")) - datetime.fromisoformat(run[start_key].replace("Z", "+00:00"))).total_seconds()
                except (ValueError, TypeError):
                    pass
                break
        facts["labels_read"] = run.get("labels_read", "Unavailable")
    retrieval = case / "retrieval.jsonl"
    if retrieval.exists():
        try:
            facts["retrieval_calls"] = sum(1 for line in retrieval.read_text().splitlines() if line.strip())
        except OSError:
            facts["retrieval_calls"] = "Unavailable"
    rankings = case / "rankings.json"
    if rankings.exists():
        value = _load_json(rankings)
        coverage = value.get("coverage", {})
        facts["coverage"] = json.dumps(coverage, sort_keys=True) if coverage else "Unavailable"
        facts["eligible"] = value.get("eligible", "Unavailable")
    trace = case / "trace_evidence.json"
    if trace.exists():
        value = _load_json(trace)
        facts["span_flags"] = sum(
            1 for record in value.get("traces", [])
            for state in record.get("flags", {}).values()
            if state not in (False, None, [], {})
        )
    for name in ("evidence.md", "investigate.py"):
        path = case / name
        facts[f"{name}_link"] = os.path.relpath(path, output_dir) if path.exists() else "Unavailable"
    for name, key in (("trace_only.seal.json", "trace_seal_link"),
                      ("final.seal.json", "final_seal_link")):
        path = case / name
        facts[key] = os.path.relpath(path, output_dir) if path.exists() else "Unavailable"
    # Prefer machine-recorded orchestration times over agent-written timestamps.
    ledger = case_root.parent / "orchestration/dispatch.jsonl"
    final_seal = case / "final.seal.json"
    if ledger.exists() and final_seal.exists():
        dispatches = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
        dispatched = next((row for row in dispatches if row.get("event") == "dispatch" and row.get("row_id") == row_id), None)
        if dispatched:
            sealed = _load_json(final_seal)
            facts["elapsed_seconds"] = (datetime.fromisoformat(sealed["created_at"]) - datetime.fromisoformat(dispatched["timestamp"])).total_seconds()
            facts["runtime_source"] = "machine dispatch to final seal"
    return facts


def _read_report_inputs(metrics_path: Path, results_path: Path,
                        comparisons_path: Path) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:
    metrics = _load_json(metrics_path)
    results = _rows(results_path)
    comparisons = _rows(comparisons_path)
    if not isinstance(metrics, dict):
        raise CollectionError("metrics.json must contain an object")
    return metrics, results, comparisons


def _stage_summary(metrics: Mapping[str, Any], stage: str) -> list[Any]:
    summary = metrics.get("stages", {}).get(stage, {})
    groups = summary.get("by_task", {})
    denominator = sum(int(group.get("rows", 0)) for group in groups.values()
                      if isinstance(group, Mapping))
    weighted = sum(float(group["mean_official_score"]) * int(group["rows"])
                   for group in groups.values()
                   if isinstance(group, Mapping) and group.get("mean_official_score") is not None)
    solved = sum(int(group.get("fully_solved", 0)) for group in groups.values()
                 if isinstance(group, Mapping))
    return [stage, denominator, _fmt(weighted / denominator if denominator else None), solved]


def _requested_field_summary(metrics: Mapping[str, Any]) -> list[list[Any]]:
    rows = []
    for stage, summary in metrics.get("stages", {}).items():
        for field, values in summary.get("field_metrics", {}).items():
            rows.append([stage, field, values.get("hits", "Unavailable"),
                         values.get("denominator", "Unavailable"), _pct(values.get("accuracy"))])
    return rows


def _discovery_tables(discovery: Mapping[str, Any]) -> list[str]:
    arms = discovery.get("arms", {})
    if not isinstance(arms, Mapping) or not arms:
        return ["Discovery metrics unavailable."]
    rows = []
    for arm, values in arms.items():
        if not isinstance(values, Mapping):
            continue
        for key, metric in values.items():
            if isinstance(metric, Mapping) and ("recall" in metric or "any_incident_recall" in metric):
                rows.append([arm, key, metric.get("windows", metric.get("denominator", "Unavailable")),
                             _pct(metric.get("any_incident_recall", metric.get("recall"))),
                             _pct(metric.get("all_labelled_components_recall")),
                             metric.get("component_hits", metric.get("hits", "Unavailable"))])
    blocks = [_md_table(["Arm", "Metric", "Denominator", "Any-incident / component recall", "All-labelled-components recall", "Component hits"], rows)]
    conflicts = discovery.get("component_conflicts", [])
    blocks.append("Component-label conflicts: " +
                  str(len(conflicts) if isinstance(conflicts, list) else "Unavailable"))
    pairs = discovery.get("per_window", [])
    if isinstance(pairs, list) and pairs:
        pair_rows = []
        for first, second in itertools.combinations(sorted(arms), 2):
            for kind in ("immediate", "reachable"):
                for budget in (1, 3, 5, 10):
                    key = f"{kind}_budget_{budget}"
                    wins = losses = ties = 0
                    for window in pairs:
                        labels = set(window["labelled_components"])
                        a = len(labels & set(window["arms"][first][key]))
                        b = len(labels & set(window["arms"][second][key]))
                        wins += a > b
                        losses += a < b
                        ties += a == b
                    pair_rows.append([f"{first} vs {second}: {key}", wins, losses, ties, len(pairs)])
        if pair_rows:
            blocks.append(_md_table(["Paired comparison", "Wins", "Losses", "Ties", "Denominator"], pair_rows))
    return blocks


def _comparison_summary(rows: list[dict[str, str]]) -> list[Any]:
    wins = losses = ties = 0
    for row in rows:
        trace, final = _number(row.get("trace_score")), _number(row.get("final_score"))
        if trace is None or final is None:
            continue
        if final > trace:
            wins += 1
        elif final < trace:
            losses += 1
        else:
            ties += 1
    return [wins, losses, ties, wins + losses + ties]


def _case_table(scope: Mapping[int, Mapping[str, str]], result_rows: list[dict[str, str]],
                case_facts: Mapping[int, Mapping[str, Any]]) -> str:
    by_key = {(row.get("stage", ""), int(row["row_id"])): row for row in result_rows
              if row.get("row_id", "").isdigit()}
    rows = []
    for row_id in REQUIRED_ROWS:
        final = by_key.get(("final", row_id), {})
        facts = case_facts[row_id]
        evidence = facts.get("evidence.md_link", "Unavailable")
        code = facts.get("investigate.py_link", "Unavailable")
        rows.append([row_id, scope[row_id].get("task_index", ""), scope[row_id].get("window_id", ""),
                     facts.get("status", "Unavailable"), final.get("official_score", "Unavailable"),
                     final.get("field_accuracy", "Unavailable"),
                     f"[evidence]({evidence})" if evidence != "Unavailable" else evidence,
                     f"[code]({code})" if code != "Unavailable" else code,
                     facts.get("retrieval_calls", "Unavailable")])
    return _md_table(["Row", "Task", "Window", "Run status", "Final official score",
                      "Final field accuracy", "Evidence", "Code", "Retrieval calls"], rows)


def _request_distributions(case_root: Path, scope: Mapping[int, Mapping[str, str]]) -> str:
    canonical = {}
    for rid in REQUIRED_ROWS:
        canonical.setdefault(scope[rid]["window_id"], rid)
    distributions = {arm: [] for arm in ("duration", "mad", "iforest")}
    excesses = {arm: [] for arm in distributions}
    for rid in canonical.values():
        value = _load_json(case_root / str(rid) / "rankings.json")
        for arm in distributions:
            top = value.get("leaders", {}).get(arm, {}).get("1", [])
            if top:
                duration = _number(top[0].get("duration_ms"))
                if duration is not None:
                    distributions[arm].append(duration)
                excess = _number(top[0].get("excess_ms"))
                if excess is not None:
                    excesses[arm].append(excess)
    rows = []
    for arm, values in distributions.items():
        rows.append([arm, len(values), _fmt(min(values) if values else None),
                     _fmt(statistics.median(values) if values else None),
                     _fmt(max(values) if values else None), sum(v < 1 for v in values),
                     _fmt(statistics.median(excesses[arm]) if excesses[arm] else None)])
    return _md_table(["Arm top-1", "Unique windows", "Minimum duration ms", "Median duration ms", "Maximum duration ms", "Duration <1 ms (descriptive)", "Median excess ms"], rows)


def collect(*, metrics_path: Path, results_path: Path, comparisons_path: Path,
            scope_path: Path, case_root: Path, output_path: Path) -> Path:
    gate = _gate(case_root, scope_path)
    # No evaluator input is read before the all-case gate succeeds.
    metrics, result_rows, comparison_rows = _read_report_inputs(metrics_path, results_path, comparisons_path)
    scope = _scope(scope_path)
    facts = {row_id: _safe_case_facts(case_root, row_id, output_path.parent)
             for row_id in REQUIRED_ROWS}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    curated = output_path.with_name("case-results.csv")
    fields = ("row_id", "task_index", "window_id", "run_status", "trace_score",
              "final_score", "final_field_accuracy", "retrieval_calls",
              "evidence", "code", "trace_seal", "final_seal")
    by_key = {(row.get("stage", ""), int(row["row_id"])): row for row in result_rows
              if row.get("row_id", "").isdigit()}
    with curated.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row_id in REQUIRED_ROWS:
            trace, final = by_key.get(("trace_only", row_id), {}), by_key.get(("final", row_id), {})
            item = facts[row_id]
            writer.writerow({"row_id": row_id, "task_index": scope[row_id].get("task_index", ""),
                             "window_id": scope[row_id].get("window_id", ""),
                             "run_status": item.get("status", "Unavailable"),
                             "trace_score": trace.get("official_score", "Unavailable"),
                             "final_score": final.get("official_score", "Unavailable"),
                             "final_field_accuracy": final.get("field_accuracy", "Unavailable"),
                             "retrieval_calls": item.get("retrieval_calls", "Unavailable"),
                             "evidence": item.get("evidence.md_link", "Unavailable"),
                             "code": item.get("investigate.py_link", "Unavailable"),
                             "trace_seal": item.get("trace_seal_link", "Unavailable"),
                             "final_seal": item.get("final_seal_link", "Unavailable")})
    stage_rows = [_stage_summary(metrics, stage) for stage in ("trace_only", "final")
                  if stage in metrics.get("stages", {})]
    runtime = [_number(facts[row_id].get("elapsed_seconds")) for row_id in REQUIRED_ROWS]
    runtime = [value for value in runtime if value is not None]
    calls = [_number(facts[row_id].get("retrieval_calls")) for row_id in REQUIRED_ROWS]
    calls = [value for value in calls if value is not None]
    day_rows = []
    task_rows = []
    abstention_rows = []
    time_rows = []
    for stage, summary in metrics.get("stages", {}).items():
        for task, values in summary.get("by_task", {}).items():
            task_rows.append([stage, task, values["rows"], _fmt(values["mean_official_score"]), values["fully_solved"]])
        for field, value in summary.get("abstention_by_field", {}).items():
            abstention_rows.append([stage, field, value.get("count", "Unavailable")])
        errors = summary.get("time_error_seconds", [])
        time_rows.append([stage, len(errors), _fmt(statistics.median(errors) if errors else None), _fmt(max(errors) if errors else None)])
        for day, values in summary.get("by_day", {}).items():
            day_rows.append([stage, day, values.get("rows", "Unavailable"),
                             _fmt(values.get("mean_official_score")),
                             values.get("fully_solved", "Unavailable")])
    canonical_rows = []
    for stage, summary in metrics.get("stages", {}).items():
        canonical = summary.get("canonical_56", {})
        sensitivity = summary.get("sensitivity_excluding_24_26", {})
        canonical_rows.append([stage, "canonical_56", canonical.get("denominator", "Unavailable"),
                               _fmt(canonical.get("mean_official_score")),
                               "sensitivity -24/-26", sensitivity.get("denominator", "Unavailable"),
                               _fmt(sensitivity.get("mean_official_score"))])
    report = [
        "# Frontend blind v1 results", "",
        "This report was generated only after the all-69 seal gate passed. It aggregates evaluator outputs and execution metadata and does not revise sealed predictions.",
        "",
        f"- Seal gate: {gate.get('expected_rows', 'Unavailable')} scheduled attempts; failed attempts preserved: {len(gate.get('failed_rows', []))}.",
        f"- Official scorer provenance: {metrics.get('official_provenance', 'Unavailable')}.",
        "- Model cost: unavailable from supplied run metadata; no USD estimate is invented.", "",
        "## Official scores", "",
        _md_table(["Stage", "Rows", "Mean score", "Fully solved"], stage_rows) if stage_rows else "Unavailable.", "",
        "Trace-only versus final paired rows:", "", _md_table(["Final wins", "Final losses", "Ties", "Denominator"], [_comparison_summary(comparison_rows)]), "",
        "## Task and day summaries", "",
        _md_table(["Stage", "Task", "Rows", "Mean score", "Fully solved"], task_rows), "",
        _md_table(["Stage", "Day", "Rows", "Mean score", "Fully solved"], day_rows) if day_rows else "Unavailable.", "",
        _md_table(["Stage", "Population", "Denominator", "Mean score", "Sensitivity", "Denominator", "Mean score"], canonical_rows) if canonical_rows else "Unavailable.", "",
        "## Requested fields, abstention, and time error", "",
        _md_table(["Stage", "Field", "Hits", "Denominator", "Accuracy"], _requested_field_summary(metrics)) if _requested_field_summary(metrics) else "Unavailable.", "",
        "Blank abstentions remain separate from malformed output and count errors. Time errors are reported only where an eligible occurrence-time label and parseable prediction were present.", "",
        _md_table(["Stage", "Field", "Blank internal incident slots (all prompts)"], abstention_rows), "",
        _md_table(["Stage", "Scored time predictions", "Median absolute error (s)", "Maximum absolute error (s)"], time_rows), "",
        "## Discovery", "",
        *_discovery_tables(metrics.get("discovery", {})), "",
        _request_distributions(case_root, scope), "",
        "The <1 ms count describes the selected requests; it is not an alert threshold or a healthy/unhealthy classification.", "",
        "Discovery recall is reported only for windows with available, non-conflicting component labels. Immediate attribution and dependency reachability remain separate; component shortlist recall uses fixed K=1/3/5 prefixes.", "",
        "## Coverage, flags, and execution", "",
        _md_table(["Row", "Status", "Coverage", "Eligible", "Span flags"], [
            [row_id, facts[row_id].get("status", "Unavailable"), facts[row_id].get("coverage", "Unavailable"),
             facts[row_id].get("eligible", "Unavailable"), facts[row_id].get("span_flags", "Unavailable")]
            for row_id in REQUIRED_ROWS]), "",
        f"Runtime records available: {len(runtime)}/{len(REQUIRED_ROWS)}; retrieval-call records available: {len(calls)}/{len(REQUIRED_ROWS)}.",
        f"Runtime mean (seconds, machine-recorded dispatch to final seal where available): {_fmt(sum(runtime) / len(runtime) if runtime else None)}; retrieval calls total: {sum(calls) if calls else 'Unavailable'}.", "",
        "## Curated per-case inventory", "",
        f"Machine-readable table: {curated.name}.", "",
        _case_table(scope, result_rows, facts), "",
        "## Interpretation limits", "",
        "These development trials cover 56 canonical windows across two days, with adjacent and overlapping reference windows. Duplicate prompts remain in row-level reporting but are not independent evidence for canonical summaries. Case 25 is an exposed engineering control; cases 24 and 26 remain in coverage and are excluded only in the declared sensitivity summary. Discovery is candidate recall, while official scores measure only each requested projection. No production false-positive or out-of-system generalization claim follows from this report.", "",
        "## Private artifact inventory and reproduction", "",
        f"- Scope: {scope_path}",
        f"- Sealed cases: {case_root} (69 included rows; control 25 excluded from the gate).",
        f"- Evaluator metrics: {metrics_path}",
        f"- Per-case evaluator rows: {results_path}",
        f"- Stage comparisons: {comparisons_path}",
        f"- Report command: python {Path(__file__)} --metrics {metrics_path} --results {results_path} --comparisons {comparisons_path} --scope {scope_path} --case-root {case_root} --out {output_path}",
        "",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(report))
    return output_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--comparisons", type=Path, default=DEFAULT_COMPARISONS)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--case-root", type=Path, default=DEFAULT_CASE_ROOT)
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("RESULTS.md"))
    args = parser.parse_args(argv)
    try:
        print(collect(metrics_path=args.metrics, results_path=args.results,
                      comparisons_path=args.comparisons, scope_path=args.scope,
                      case_root=args.case_root, output_path=args.out))
    except (CollectionError, OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
