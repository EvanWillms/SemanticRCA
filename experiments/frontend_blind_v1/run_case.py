"""Prepare deterministic, label-free case artifacts for frontend-blind-v1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .build_index import ARTIFACT_ROOT, DEFAULT_DB, TraceIndex, build_index
from .detectors import attach_signatures, detect
from .trace_evidence import build_evidence


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / "experiments" / "frontend_blind_v1"
SCOPE_PATH = ROOT / "docs" / "research" / "experiments" / "frontend-blind-v1" / "scope.csv"
CONFIG_PATH = EXPERIMENT_ROOT / "config.json"
CASE_ROOT = ARTIFACT_ROOT / "cases"


def _epoch_ms(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp() * 1000)


def read_scope(path: Path = SCOPE_PATH) -> dict[int, dict]:
    with path.open(newline="") as stream:
        rows = {}
        for row in csv.DictReader(stream):
            item = dict(row)
            item["row_id"] = int(item["row_id"])
            item["query_start_ms"] = _epoch_ms(item["query_start"])
            item["query_end_ms"] = _epoch_ms(item["query_end"])
            item["reference_start_ms"] = _epoch_ms(item["reference_start"])
            item["reference_end_ms"] = item["query_start_ms"]
            item["failure_count"] = int(item["failure_count"])
            item["exposure_flags"] = [flag for flag in item.get("exposure_flag", "").split(";") if flag]
            rows[item["row_id"]] = item
    return rows


def _jsonable(value):
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, set)):
        return [_jsonable(item) for item in value]
    return value


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True) + "\n")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _ranking_payload(result) -> dict:
    leaders = {}
    for arm, ranked in result.leaders.items():
        leaders[arm] = {
            str(limit): ranked[:limit] for limit in (1, 3, 5, 10)
        }
    rows = []
    for row in result.rows:
        item = dict(row)
        item.pop("signature", None)
        rows.append(item)
    return {
        "reference_roots": result.reference_count,
        "query_roots": result.query_count,
        "cohorts": result.cohort_count,
        "eligible": result.eligible_count,
        "excluded": result.excluded_count,
        "coverage": result.coverage,
        "leaders": leaders,
        "rows": rows,
        "inspection_prefixes": [1, 3, 5, 10],
    }


def _selected_rows(result) -> list[dict]:
    selected: list[dict] = []
    seen = set()
    for arm in ("duration", "mad", "iforest"):
        for row in result.leaders[arm][:10]:
            key = (str(row["trace_id"]), str(row["span_id"]))
            if key in seen:
                continue
            seen.add(key)
            selected.append(dict(row, selected_arms=[arm]))
    if len({row["trace_id"] for row in selected}) > 30:
        allowed = []
        for row in selected:
            if row["trace_id"] not in allowed and len(allowed) < 30:
                allowed.append(row["trace_id"])
        selected = [row for row in selected if row["trace_id"] in allowed]
    return selected


def prepare_case(row_id: int, *, index: TraceIndex | None = None, case_root: Path = CASE_ROOT) -> Path:
    """Prepare one public scope row and return its private case directory."""
    scope = read_scope()
    if row_id not in scope:
        raise KeyError(f"Unknown scope row {row_id}")
    item = scope[row_id]
    index = index or TraceIndex(DEFAULT_DB)
    config = json.loads(CONFIG_PATH.read_text())
    started = time.perf_counter()
    margin = int(config["initial_margin_ms"])
    fetched = index.get_frontend(item["reference_start_ms"] - margin, item["query_end_ms"] + margin)
    reference = [row for row in fetched if item["reference_start_ms"] <= int(row["timestamp"]) < item["reference_end_ms"] and not row.get("parent_span")]
    query = [row for row in fetched if item["query_start_ms"] <= int(row["timestamp"]) < item["query_end_ms"] and not row.get("parent_span")]
    reference = sorted(attach_signatures(reference, fetched), key=lambda row: (str(row.get("source_file", "")), int(row.get("source_record", 0))))
    query = sorted(attach_signatures(query, fetched), key=lambda row: (str(row.get("source_file", "")), int(row.get("source_record", 0))))
    result = detect(reference, query)
    selected = _selected_rows(result)
    trace_ids = list(dict.fromkeys(str(row["trace_id"]) for row in selected))
    traces = index.get_traces(trace_ids)
    roots_by_key = {(str(row["trace_id"]), str(row["span_id"])): row for row in query}
    evidence_roots = []
    for row in selected:
        root = dict(roots_by_key.get((str(row["trace_id"]), str(row["span_id"])), row))
        root["ranking"] = {key: row.get(key) for key in ("duration_ms", "mad_score", "iforest_score", "b_score", "c_score", "rank_range")}
        evidence_roots.append(root)
    evidence = build_evidence(evidence_roots, traces, max_depth=int(config["max_trace_depth"]))
    evidence["selected_trace_ids"] = trace_ids
    evidence["selected_count"] = len(trace_ids)
    evidence["selection_policy"] = "union of each arm top-10, capped at 30 distinct traces"
    target = Path(case_root) / str(row_id)
    target.mkdir(parents=True, exist_ok=True)
    scope_out = dict(item)
    scope_out["source_identities"] = {
        "scope": str(SCOPE_PATH.relative_to(ROOT)),
        "trace_index": str(index.db_path.relative_to(ROOT)) if index.db_path.is_relative_to(ROOT) else str(index.db_path),
        "trace_dates": sorted({row["source_file"].split("/")[3] for row in fetched if row.get("source_file") and len(row["source_file"].split("/")) > 3}),
    }
    scope_out["source_policy"] = "label-free public scope and trace telemetry only"
    _write(target / "scope.json", scope_out)
    _write(target / "rankings.json", _ranking_payload(result))
    # Keep detector-arm evidence explicitly separated. The union is only a
    # retrieval optimization; no arm receives another arm's shortlist.
    by_root = {(record["trace_id"], str(record["root"]["span_id"])): record
               for record in evidence["traces"]}
    evidence["arm_evidence"] = {}
    for arm, ranked in result.leaders.items():
        arm_ids = [str(row["trace_id"]) for row in ranked[:10]]
        arm_keys = [(str(row["trace_id"]), str(row["span_id"])) for row in ranked[:10]]
        arm_records = [by_root[key] for key in arm_keys if key in by_root]
        components = []
        for record in arm_records:
            for component in record["dependency_reachability"]["components"]:
                if component not in components:
                    components.append(component)
        evidence["arm_evidence"][arm] = {
            "trace_ids": arm_ids,
            "traces": arm_records,
            "component_shortlist": components,
        }
    _write(target / "trace_evidence.json", evidence)
    _write(target / "run_inputs.json", {
        "config": config,
        "query_fetch_bounds_ms": [item["reference_start_ms"] - margin, item["query_end_ms"] + margin],
        "reference_root_count": len(reference),
        "query_root_count": len(query),
        "root_operation_counts": dict(Counter(str(row.get("operation_name", "")) for row in query)),
        "root_type_counts": dict(Counter(str(row.get("type", "")) for row in query)),
        "reference_root_operation_counts": dict(Counter(str(row.get("operation_name", "")) for row in reference)),
        "reference_root_type_counts": dict(Counter(str(row.get("type", "")) for row in reference)),
        "selected_trace_ids": trace_ids,
        "source_files": sorted({str(row.get("source_file")) for row in fetched if row.get("source_file")}),
        "generated_at_utc": datetime.now().astimezone().isoformat(),
    })
    _write(target / "index.json", {"index": str(index.db_path)})
    _write(target / "run.json", {
        "row_id": row_id,
        "status": "prepared",
        "elapsed_seconds": time.perf_counter() - started,
        "index": str(index.db_path),
        "config_sha256": _hash_file(CONFIG_PATH),
        "code_sha256": {name: _hash_file(EXPERIMENT_ROOT / name) for name in ("detectors.py", "trace_evidence.py", "run_case.py", "build_index.py")},
        "labels_read": False,
    })
    return target


def inspect_case(case_dir: str | Path) -> dict:
    """Return a compact investigator-facing summary without loading raw spans."""
    case_dir = Path(case_dir)
    scope = json.loads((case_dir / "scope.json").read_text())
    rankings = json.loads((case_dir / "rankings.json").read_text())
    evidence = json.loads((case_dir / "trace_evidence.json").read_text())
    compact = {
        "row_id": scope["row_id"],
        "instruction": scope.get("instruction", ""),
        "task_index": scope.get("task_index"),
        "query": [scope.get("query_start"), scope.get("query_end")],
        "reference": [scope.get("reference_start"), scope.get("query_start")],
        "failure_count": scope.get("failure_count"),
        "coverage": rankings.get("coverage", {}),
        "rankings": {arm: {limit: rows for limit, rows in limits.items()} for arm, limits in rankings.get("leaders", {}).items()},
        "selected_trace_ids": evidence.get("selected_trace_ids", []),
        "trace_summaries": [
            {
                "trace_id": trace["trace_id"],
                "root": {key: trace["root"].get(key) for key in ("span_id", "timestamp", "duration", "cmdb_id", "operation_name", "ranking")},
                "flags": trace["flags"],
                "intervals": trace["intervals"],
                "immediate_attribution": {
                    "largest_direct_child": trace["immediate_attribution"].get("largest_direct_child"),
                    "linked_receivers": trace["immediate_attribution"].get("linked_receivers", []),
                },
                "dependency_reachability": trace["dependency_reachability"],
            }
            for trace in evidence.get("traces", [])
        ],
    }
    return compact


def prepare_all() -> list[Path]:
    built = build_index(DEFAULT_DB)
    index = TraceIndex(Path(built["index"]) if isinstance(built, dict) else built)
    return [prepare_case(row_id, index=index) for row_id in sorted(read_scope())]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("row_id", type=int, nargs="?")
    parser.add_argument("--prepare-all", action="store_true")
    parser.add_argument("--inspect", type=Path)
    args = parser.parse_args(argv)
    if args.prepare_all:
        paths = prepare_all()
        print(json.dumps({"prepared": len(paths), "case_root": str(CASE_ROOT)}))
        return 0
    if args.inspect:
        print(json.dumps(inspect_case(args.inspect), indent=2))
        return 0
    if args.row_id is None:
        parser.error("provide row_id, --prepare-all, or --inspect")
    print(str(prepare_case(args.row_id)))
    return 0


if __name__ == "__main__":
    if __package__ in (None, ""):
        sys.path.insert(0, str(ROOT))
        from experiments.frontend_blind_v1.run_case import main as _main
        raise SystemExit(_main())
    raise SystemExit(main())
