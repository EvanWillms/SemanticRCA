"""Descriptive replay over the supplied 57 label-free query windows.

This command is intentionally downstream of selection.  It refuses a
preliminary matrix decision and accepts only a frozen selection manifest with
one primary policy and at most one explicitly qualified fallback.  It reads
the public query inventory and trace index only; no benchmark labels are
opened.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping

from .analysis import _exposure_inventory, _query_inventory
from .index import DEFAULT_ARTIFACT_ROOT, DEFAULT_INDEX, DEFAULT_TRACE_ROOT, discover_frontend_components, fetch_frontend_roots, fetch_traces, open_index, source_inventory, validate_index
from .observations import build_observation, group_root_rows
from .runner import evaluate_policy


ROOT = Path(__file__).resolve().parents[2]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Mapping]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
                handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True, default=str) + "\n")


def _hash_code_files() -> dict[str, str]:
    hashes = {}
    for path in sorted(Path(__file__).parent.glob("*.py")):
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _parse_ms(value: str) -> int:
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        raise ValueError(f"replay timestamp must include timezone: {value}")
    return int(parsed.timestamp() * 1000)


def _read_selection(path: Path) -> list[dict]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("selection manifest must be a JSON object")
    status = str(value.get("selection_status", value.get("status", ""))).lower()
    if status not in {"selected", "frozen", "approved_for_replay"}:
        raise ValueError("replay requires a frozen selected policy; preliminary or inconclusive decisions cannot trigger replay")
    policies = []
    primary = value.get("primary") or value.get("primary_policy")
    fallback = value.get("fallback") or value.get("fallback_policy")
    if not isinstance(primary, Mapping):
        raise ValueError("selection manifest must declare primary policy")
    policies.append({"role": "primary", **dict(primary)})
    if fallback is not None:
        if not isinstance(fallback, Mapping):
            raise ValueError("fallback policy must be an object or null")
        policies.append({"role": "fallback", **dict(fallback)})
    for policy in policies:
        required = {"mode", "replica_policy", "lookback_minutes"}
        missing = sorted(required - set(policy))
        if missing:
            raise ValueError(f"selection policy missing {missing}")
        if str(policy["mode"]) not in {"C0", "C1", "C2"}:
            raise ValueError(f"unsupported replay mode: {policy['mode']}")
        if str(policy["replica_policy"]) not in {"same_replica", "pooled"}:
            raise ValueError(f"unsupported replay replica policy: {policy['replica_policy']}")
        if int(policy["lookback_minutes"]) not in {5, 10, 15, 30, 60}:
            raise ValueError(f"unsupported replay lookback: {policy['lookback_minutes']}")
    return policies


def _window_rows(repo_root: Path) -> list[dict]:
    supplied, missing = _query_inventory(repo_root)
    fatal_missing = [item for item in missing if str(item.get("reason", "")) != "parsed_from_public_instruction"]
    if fatal_missing:
        raise ValueError(f"query inventory contains unparseable time bounds: {fatal_missing}")
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in supplied:
        grouped[(str(row["query_start"]), str(row["query_end"]))].append(str(row["row_id"]))
    rows = []
    for (start, end), row_ids in sorted(grouped.items()):
        if _parse_ms(end) - _parse_ms(start) != 30 * 60_000:
            raise ValueError(f"supplied query window is not exactly 30 minutes: {start} to {end}")
        rows.append({"window_id": f"{start}__{end}", "query_start": start, "query_end": end, "row_ids": sorted(row_ids, key=int), "duplicate_prompt_rows": len(row_ids) > 1})
    if len(rows) != 57:
        raise ValueError(f"expected 57 distinct supplied windows, found {len(rows)}")
    return rows


def _collect_window(index_path: Path, components: list[str], start_ms: int, end_ms: int) -> tuple[dict[tuple[str, str], dict], dict]:
    """Retrieve one 60-minute frozen-reference + 30-minute query support span."""
    conn = open_index(index_path)
    root_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    raw_roots = 0
    trace_rows = 0
    try:
        roots = fetch_frontend_roots(conn, start_ms - 60 * 60_000, end_ms, components)
        raw_roots = len(roots)
        for key, rows in group_root_rows(roots).items():
            root_groups[key].extend(rows)
        by_trace: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for key in root_groups:
            by_trace[key[0]].append(key)
        records = {}
        trace_ids = sorted(by_trace)
        for offset in range(0, len(trace_ids), 300):
            chunk = trace_ids[offset:offset + 300]
            traces = fetch_traces(conn, chunk)
            trace_rows += sum(len(rows) for rows in traces.values())
            for trace_id in chunk:
                for key in by_trace.get(trace_id, []):
                    records[key] = build_observation(root_groups[key], traces.get(trace_id, []))
    finally:
        conn.close()
    return records, {"raw_root_rows": raw_roots, "distinct_root_identities": len(records), "trace_rows_retrieved": trace_rows, "trace_ids": len(by_trace) if "by_trace" in locals() else 0}


def run_replay(*, selection_path: Path, output_dir: Path = DEFAULT_ARTIFACT_ROOT / "replay", repo_root: Path = ROOT, index_path: Path = DEFAULT_INDEX, trace_root: Path = DEFAULT_TRACE_ROOT) -> dict:
    started = time.perf_counter()
    policies = _read_selection(Path(selection_path))
    selection_content = json.loads(Path(selection_path).read_text(encoding="utf-8"))
    windows = _window_rows(Path(repo_root))
    validation = validate_index(index_path, trace_root)
    if not validation.get("valid"):
        raise RuntimeError(f"trace index failed validation: {validation}")
    conn = open_index(index_path)
    try:
        components = discover_frontend_components(conn)
    finally:
        conn.close()
    core_manifest_path = DEFAULT_ARTIFACT_ROOT / "manifest.json"
    if not core_manifest_path.is_file():
        raise RuntimeError(f"core matrix manifest is required before replay: {core_manifest_path}")
    core_manifest = json.loads(core_manifest_path.read_text(encoding="utf-8"))
    frozen_components = list(core_manifest.get("component_allowlist", []))
    if frozen_components != components:
        raise RuntimeError("replay frontend allowlist differs from the frozen core matrix allowlist")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frozen_manifest = {"version": "short-window-baselining-v1-replay", "created_at_utc": datetime.now(timezone.utc).isoformat(), "status": "frozen_before_replay", "selection_path": str(Path(selection_path).resolve()), "selection_sha256": hashlib.sha256(Path(selection_path).read_bytes()).hexdigest(), "selection": selection_content, "selection_policies": policies, "source_inventory": source_inventory(trace_root), "index": validation, "component_allowlist": components, "code_hashes": _hash_code_files(), "core_manifest_path": str(core_manifest_path.resolve()), "core_manifest_sha256": hashlib.sha256(core_manifest_path.read_bytes()).hexdigest(), "window_count": len(windows), "expected_window_count": 57, "duplicate_prompt_window_count": sum(1 for window in windows if window["duplicate_prompt_rows"]), "governance": "descriptive label-free confirmation; no held-out claim; overlapping support intervals stay grouped"}
    _write_json(output_dir / "manifest.json", frozen_manifest)
    coverage_handle = (output_dir / "coverage.jsonl").open("w", encoding="utf-8")
    comparison_handle = (output_dir / "comparisons.jsonl").open("w", encoding="utf-8")
    aging_handle = (output_dir / "aging_comparisons.jsonl").open("w", encoding="utf-8")
    membership_handle = (output_dir / "memberships.jsonl").open("w", encoding="utf-8")
    uncertainty_handle = (output_dir / "uncertainty.jsonl").open("w", encoding="utf-8")
    structure_handle = (output_dir / "structure.jsonl").open("w", encoding="utf-8")
    observation_handle = (output_dir / "observations.jsonl").open("w", encoding="utf-8")
    cost_rows = []
    exposure_rows = []
    try:
        for window in windows:
            start_ms = _parse_ms(window["query_start"])
            end_ms = _parse_ms(window["query_end"])
            records, cost = _collect_window(index_path, components, start_ms, end_ms)
            for record in records.values():
                observation_handle.write(json.dumps({"window_id": window["window_id"], "row_ids": window["row_ids"], "observation": record}, ensure_ascii=False, sort_keys=True, default=str) + "\n")
            for policy in policies:
                lookback = int(policy["lookback_minutes"])
                anchor = {"anchor_id": window["window_id"], "local": window["query_start"], "epoch_ms": start_ms, "reference_intervals": {str(lookback): [start_ms - lookback * 60_000, start_ms]}, "query_slices": [[start_ms + offset * 5 * 60_000, start_ms + (offset + 1) * 5 * 60_000] for offset in range(6)]}
                cell = evaluate_policy(records, anchor, lookback, str(policy["mode"]), str(policy["replica_policy"]), components)
                row = {"window_id": window["window_id"], "row_ids": window["row_ids"], "duplicate_prompt_rows": window["duplicate_prompt_rows"], "policy_role": policy["role"], "selection_policy": {key: policy[key] for key in ("mode", "replica_policy", "lookback_minutes")}, **cell["policy"]}
                coverage_handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")
                for membership in cell["memberships"]:
                    membership_handle.write(json.dumps({"window_id": window["window_id"], "row_ids": window["row_ids"], "policy_role": policy["role"], **membership}, ensure_ascii=False, sort_keys=True, default=str) + "\n")
                for comparison in cell["comparisons"]:
                    comparison_handle.write(json.dumps({"window_id": window["window_id"], "row_ids": window["row_ids"], "policy_role": policy["role"], **comparison}, ensure_ascii=False, sort_keys=True, default=str) + "\n")
                for comparison in cell.get("aging_comparisons", []):
                    aging_handle.write(json.dumps({"window_id": window["window_id"], "row_ids": window["row_ids"], "policy_role": policy["role"], **comparison}, ensure_ascii=False, sort_keys=True, default=str) + "\n")
                for uncertainty in cell["uncertainty"]:
                    uncertainty_handle.write(json.dumps({"window_id": window["window_id"], "row_ids": window["row_ids"], "policy_role": policy["role"], **uncertainty}, ensure_ascii=False, sort_keys=True, default=str) + "\n")
                structure_handle.write(json.dumps({"window_id": window["window_id"], "row_ids": window["row_ids"], "policy_role": policy["role"], **cell["structure"]}, ensure_ascii=False, sort_keys=True, default=str) + "\n")
                cost_rows.append({"window_id": window["window_id"], "row_ids": window["row_ids"], "policy_role": policy["role"], "cost_scope": "shared_window_collection", **cost})
            exposure_rows.append({"window_id": window["window_id"], "row_ids": window["row_ids"], "query_start": window["query_start"], "query_end": window["query_end"], "support_start": (datetime.fromisoformat(window["query_start"]) - timedelta(minutes=60)).isoformat(), "support_end": window["query_end"], "duplicate_prompt_rows": window["duplicate_prompt_rows"], "telemetry_reused_across_policies": True, "telemetry_reused_across_duplicate_rows": bool(window["duplicate_prompt_rows"])} )
    finally:
        coverage_handle.close()
        comparison_handle.close()
        aging_handle.close()
        membership_handle.close()
        uncertainty_handle.close()
        structure_handle.close()
        observation_handle.close()
    exposure = _exposure_inventory(Path(repo_root), core_manifest)
    exposure["actual_replay_support_intervals"] = exposure_rows
    exposure["actual_collected_window_count"] = len(exposure_rows)
    _write_json(output_dir / "exposure_inventory.json", exposure)
    _write_jsonl(output_dir / "cost.jsonl", cost_rows)
    _write_jsonl(output_dir / "exposure_windows.jsonl", exposure_rows)
    _write_json(output_dir / "run_summary.json", {"window_count": len(windows), "policy_count": len(policies), "elapsed_seconds": time.perf_counter() - started, "status": "completed_descriptive_replay"})
    return {"output_dir": str(output_dir), "windows": len(windows), "policies": len(policies), "elapsed_seconds": time.perf_counter() - started}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_ARTIFACT_ROOT / "replay")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--trace-root", type=Path, default=DEFAULT_TRACE_ROOT)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    result = run_replay(selection_path=args.selection, output_dir=args.output_dir, repo_root=args.repo_root, index_path=args.index, trace_root=args.trace_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
