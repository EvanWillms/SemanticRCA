"""Bounded reconciliation checks for a completed descriptive replay.

The replay writer is intentionally streaming, so this validator reads JSONL
rows into compact identity maps and counters rather than loading observations
or full comparison payloads.  It checks every window and policy cell, six
fixed-reference aging slices, primary/offset-zero equality, duplicate root
identities, source pointers, and membership hashes.  It does not select a
policy and never reads labels.

Importing this module does not read artifacts.  Call ``reconcile_replay``
after a replay has been reviewed and executed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_OFFSETS = (0, 5, 10, 15, 20, 25)


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            yield value


def _identity(row: Mapping) -> tuple[str, str]:
    root_key = row.get("root_key")
    if isinstance(root_key, (list, tuple)) and len(root_key) == 2:
        return str(root_key[0]), str(root_key[1])
    return str(row.get("trace_id", "")), str(row.get("span_id", ""))


def _cell(row: Mapping) -> tuple[str, str]:
    return str(row.get("window_id", "")), str(row.get("policy_role", ""))


def _hash_identities(identities: Iterable[tuple[str, str]]) -> str:
    payload = json.dumps(sorted(set(identities)), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sample_source_pointers(replay_dir: Path, manifest: Mapping, sample_size: int) -> dict:
    # Keep the lexicographically earliest deterministic sample without
    # retaining every observation pointer in memory.
    sample_by_key: dict[tuple[str, tuple[str, str]], dict] = {}
    candidate_count = 0
    path = replay_dir / "observations.jsonl"
    for row in _iter_jsonl(path):
        observation = row.get("observation")
        if not isinstance(observation, Mapping):
            continue
        candidate_count += 1
        identity = _identity(observation)
        source = observation.get("source")
        if not isinstance(source, Mapping):
            candidate = {"window_id": row.get("window_id"), "identity": list(identity), "source": None}
        else:
            candidate = {
                "window_id": str(row.get("window_id", "")),
                "identity": list(identity),
                "source": {
                    "source_file": str(source.get("source_file", "")),
                    "source_record": int(source.get("source_record", 0) or 0),
                    "source_header": int(source.get("source_header", 1) or 1),
                },
            }
        limit = max(0, int(sample_size))
        if limit:
            key = (str(candidate["window_id"]), (str(candidate["identity"][0]), str(candidate["identity"][1])))
            sample_by_key[key] = candidate
            if len(sample_by_key) > limit:
                del sample_by_key[max(sample_by_key)]
    sample = [sample_by_key[key] for key in sorted(sample_by_key)]
    index_value = manifest.get("index", {}).get("index") if isinstance(manifest.get("index"), Mapping) else None
    index_path = Path(str(index_value)) if index_value else replay_dir / "trace.sqlite3"
    if not index_path.is_absolute():
        index_path = ROOT / index_path
    missing: list[dict] = []
    check_error = None
    try:
        with sqlite3.connect(str(index_path)) as conn:
            conn.execute("PRAGMA query_only=ON")
            for item in sample:
                source = item.get("source")
                if not isinstance(source, Mapping):
                    missing.append(item)
                    continue
                found = conn.execute(
                    "SELECT 1 FROM spans WHERE trace_id=? AND span_id=? AND source_file=? AND source_record=?",
                    (item["identity"][0], item["identity"][1], source["source_file"], source["source_record"]),
                ).fetchone()
                if found is None:
                    missing.append(item)
    except (OSError, sqlite3.Error) as exc:
        check_error = f"{type(exc).__name__}: {exc}"
    return {
        "candidate_count": candidate_count,
        "sample_size": len(sample),
        "sample": sample,
        "missing": missing,
        "check_error": check_error,
        "valid": not missing and check_error is None,
    }


def reconcile_replay(*, replay_dir: Path, source_sample_size: int = 200) -> dict:
    """Reconcile every replay window, policy, slice, and source sample."""
    replay_dir = Path(replay_dir)
    manifest = _read_json(replay_dir / "manifest.json")
    summary = _read_json(replay_dir / "run_summary.json")
    coverage = list(_iter_jsonl(replay_dir / "coverage.jsonl"))

    coverage_keys = [_cell(row) for row in coverage]
    coverage_counts = Counter(coverage_keys)
    duplicate_cells = [list(key) for key, count in sorted(coverage_counts.items()) if count > 1]
    cell_set = set(coverage_keys)
    policy_roles = sorted(str(item.get("role", "")) for item in manifest.get("selection_policies", []) if isinstance(item, Mapping))
    windows = sorted({key[0] for key in cell_set})
    exposure_windows = list(_iter_jsonl(replay_dir / "exposure_windows.jsonl"))
    expected_windows = {str(row.get("window_id", "")) for row in exposure_windows}
    missing_windows = sorted(expected_windows - set(windows))
    unexpected_windows = sorted(set(windows) - expected_windows)
    expected_cells = {(window, role) for window in expected_windows for role in policy_roles}
    missing_cells = sorted(expected_cells - cell_set)
    unexpected_cells = sorted(cell_set - expected_cells)
    expected_cell_count = len(expected_cells)
    exposure = _read_json(replay_dir / "exposure_inventory.json")
    exposure_row_ids = [str(row_id) for window in exposure.get("supplied_windows", []) if isinstance(window, Mapping) for row_id in window.get("row_ids", [])]
    exposure_row_id_set = set(exposure_row_ids)
    query_inventory_check = {
        "row_count": exposure.get("row_count"),
        "row_count_expected": exposure.get("query_row_count_expected"),
        "distinct_window_count": exposure.get("distinct_query_windows"),
        "distinct_window_count_expected": exposure.get("distinct_query_windows_expected"),
        "unique_row_id_count": len(exposure_row_id_set),
        "unique_row_id_count_expected": 70,
        "valid": exposure.get("row_count") == exposure.get("query_row_count_expected") == 70 and exposure.get("distinct_query_windows") == exposure.get("distinct_query_windows_expected") == 57 and len(exposure_row_id_set) == 70,
    }

    comparable_fields = ("observed_ms", "median_ms", "mad_ms", "absolute_excess_ms", "ratio", "standardized_departure")
    primary: dict[tuple[str, str], dict[tuple[str, str], tuple]] = defaultdict(dict)
    primary_duplicates: Counter[tuple[str, str, tuple[str, str]]] = Counter()
    for row in _iter_jsonl(replay_dir / "comparisons.jsonl"):
        key = _cell(row)
        identity = _identity(row)
        primary_duplicates[(key[0], key[1], identity)] += 1
        primary[key][identity] = tuple(row.get(field) for field in comparable_fields)
    duplicate_primary_ids = [list(key) for key, count in sorted(primary_duplicates.items()) if count > 1]

    aging: dict[tuple[str, str, int], dict[tuple[str, str], tuple]] = defaultdict(dict)
    aging_duplicates: Counter[tuple[str, str, int, tuple[str, str]]] = Counter()
    aging_offsets: Counter[tuple[str, str, int]] = Counter()
    for row in _iter_jsonl(replay_dir / "aging_comparisons.jsonl"):
        cell = _cell(row)
        offset = int(row.get("offset_minutes", -1))
        identity = _identity(row)
        aging_duplicates[(cell[0], cell[1], offset, identity)] += 1
        aging_offsets[(cell[0], cell[1], offset)] += 1
        aging[(cell[0], cell[1], offset)][identity] = tuple(row.get(field) for field in comparable_fields)
    duplicate_aging_ids = [list(key[:3]) + [list(key[3])] for key, count in sorted(aging_duplicates.items()) if count > 1]

    offset0_mismatches = []
    malformed_aging_cells = []
    for row in coverage:
        cell = _cell(row)
        aging_rows = row.get("aging") if isinstance(row.get("aging"), list) else []
        observed_offsets = sorted(int(item.get("offset_minutes", -1)) for item in aging_rows if isinstance(item, Mapping))
        if observed_offsets != list(EXPECTED_OFFSETS):
            malformed_aging_cells.append({"cell": list(cell), "offsets": observed_offsets})
        primary_ids = set(primary.get(cell, {}))
        offset0_ids = set(aging.get((cell[0], cell[1], 0), {}))
        if primary_ids != offset0_ids:
            offset0_mismatches.append({"cell": list(cell), "primary_count": len(primary_ids), "offset0_count": len(offset0_ids), "missing_from_offset0": [list(value) for value in sorted(primary_ids - offset0_ids)], "missing_from_primary": [list(value) for value in sorted(offset0_ids - primary_ids)]})
            continue
        for identity in sorted(primary_ids):
            left = primary[cell][identity]
            right = aging[(cell[0], cell[1], 0)][identity]
            if left != right:
                offset0_mismatches.append({"cell": list(cell), "identity": list(identity), "reason": "value_mismatch"})

    coverage_comparison_count_mismatches = []
    aging_comparison_count_mismatches = []
    coverage_range_errors = []
    aging_range_errors = []
    for row in coverage:
        cell = _cell(row)
        expected_primary = int(row.get("supported_query_count", 0) or 0)
        actual_primary = len(primary.get(cell, {}))
        if expected_primary != actual_primary:
            coverage_comparison_count_mismatches.append({"cell": list(cell), "coverage": expected_primary, "comparisons": actual_primary})
        resolved = int(row.get("query_resolved_count", 0) or 0)
        raw = int(row.get("query_raw_count", 0) or 0)
        coverage_value = row.get("request_coverage")
        if raw < 0 or resolved < 0 or expected_primary < 0 or resolved > raw or expected_primary > resolved or not isinstance(coverage_value, (int, float)) or not 0 <= float(coverage_value) <= 1 or abs(float(coverage_value) - (expected_primary / resolved if resolved else 0.0)) > 1e-9:
            coverage_range_errors.append({"cell": list(cell), "query_raw_count": raw, "query_resolved_count": resolved, "supported_query_count": expected_primary, "request_coverage": coverage_value})
        for aging_row in row.get("aging", []) if isinstance(row.get("aging"), list) else []:
            offset = int(aging_row.get("offset_minutes", -1))
            expected = int(aging_row.get("supported_query_count", 0) or 0)
            actual = len(aging.get((cell[0], cell[1], offset), {}))
            if expected != actual:
                aging_comparison_count_mismatches.append({"cell": list(cell), "offset_minutes": offset, "coverage": expected, "comparisons": actual})
            aging_resolved = int(aging_row.get("resolved_query_count", 0) or 0)
            aging_raw = int(aging_row.get("query_count", 0) or 0)
            aging_coverage = aging_row.get("request_coverage")
            if aging_raw < 0 or aging_resolved < 0 or expected < 0 or aging_resolved > aging_raw or expected > aging_resolved or not isinstance(aging_coverage, (int, float)) or not 0 <= float(aging_coverage) <= 1 or abs(float(aging_coverage) - (expected / aging_resolved if aging_resolved else 0.0)) > 1e-9:
                aging_range_errors.append({"cell": list(cell), "offset_minutes": offset, "query_count": aging_raw, "resolved_query_count": aging_resolved, "supported_query_count": expected, "request_coverage": aging_coverage})

    observation_ids: Counter[tuple[str, tuple[str, str]]] = Counter()
    observation_missing_source = 0
    for row in _iter_jsonl(replay_dir / "observations.jsonl"):
        observation = row.get("observation")
        if not isinstance(observation, Mapping):
            observation_missing_source += 1
            continue
        observation_ids[(str(row.get("window_id", "")), _identity(observation))] += 1
        source = observation.get("source")
        if not isinstance(source, Mapping) or not source.get("source_file") or not source.get("source_record"):
            observation_missing_source += 1
    duplicate_observation_ids = [list(key[0:1]) + [list(key[1])] for key, count in sorted(observation_ids.items()) if count > 1]

    membership_sets: dict[tuple[tuple[str, str], str, str], set[tuple[str, str]]] = defaultdict(set)
    membership_duplicates: Counter[tuple[tuple[str, str], str, str, tuple[str, str]]] = Counter()
    membership_cell_role_duplicates: Counter[tuple[tuple[str, str], str, tuple[str, str]]] = Counter()
    membership_missing_source = 0
    for row in _iter_jsonl(replay_dir / "memberships.jsonl"):
        cell = _cell(row)
        cohort = str(row.get("cohort_key"))
        role = str(row.get("role", ""))
        identity = _identity(row)
        membership_duplicates[(cell, cohort, role, identity)] += 1
        membership_cell_role_duplicates[(cell, role, identity)] += 1
        status = str(row.get("status", ""))
        include = (role == "reference" and status == "included") or (role == "query" and bool(row.get("identity_resolved")) and status in {"candidate", "included"})
        if include:
            membership_sets[(cell, cohort, role)].add(identity)
        source = row.get("source")
        if not isinstance(source, Mapping) or not source.get("source_file") or not source.get("source_record"):
            membership_missing_source += 1
    duplicate_membership_ids = [list(key[0]) + [key[1], key[2], list(key[3])] for key, count in sorted(membership_duplicates.items()) if count > 1]
    duplicate_membership_cell_role_ids = [list(key[0]) + [key[1], list(key[2])] for key, count in sorted(membership_cell_role_duplicates.items()) if count > 1]

    uncertainty_hash_missing = 0
    membership_hash_mismatches = []
    uncertainty_duplicates: Counter[tuple[tuple[str, str], str]] = Counter()
    uncertainty_cells: set[tuple[str, str]] = set()
    for row in _iter_jsonl(replay_dir / "uncertainty.jsonl"):
        cell = _cell(row)
        cohort = str(row.get("cohort_key"))
        uncertainty_cells.add(cell)
        uncertainty_duplicates[(cell, cohort)] += 1
        hashes = row.get("membership_hashes")
        if not isinstance(hashes, Mapping) or not hashes.get("reference_membership_hash") or not hashes.get("query_membership_hash"):
            uncertainty_hash_missing += 1
            continue
        actual = {
            "reference_membership_hash": _hash_identities(membership_sets.get((cell, cohort, "reference"), set())),
            "query_membership_hash": _hash_identities(membership_sets.get((cell, cohort, "query"), set())),
        }
        if actual != {"reference_membership_hash": hashes.get("reference_membership_hash"), "query_membership_hash": hashes.get("query_membership_hash")}:
            membership_hash_mismatches.append({"cell": list(cell), "cohort_key": cohort, "expected": dict(hashes), "actual": actual})
    duplicate_uncertainty_cells = [list(key[0]) + [key[1]] for key, count in sorted(uncertainty_duplicates.items()) if count > 1]
    uncertainty_missing_cells = sorted(expected_cells - uncertainty_cells)
    uncertainty_unexpected_cells = sorted(uncertainty_cells - expected_cells)

    cost_rows = list(_iter_jsonl(replay_dir / "cost.jsonl"))
    cost_keys = [_cell(row) for row in cost_rows]
    cost_duplicates = [list(key) for key, count in Counter(cost_keys).items() if count > 1]
    cost_scope_values = sorted({str(row.get("cost_scope", "")) for row in cost_rows})
    cost_denominator_mismatches = []
    cost_by_window: dict[str, list[dict]] = defaultdict(list)
    for row in cost_rows:
        cost_by_window[str(row.get("window_id", ""))].append(row)
    for window_id, group in sorted(cost_by_window.items()):
        comparable = ("raw_root_rows", "distinct_root_identities", "trace_rows_retrieved", "trace_ids")
        if any(tuple(row.get(field) for field in comparable) != tuple(group[0].get(field) for field in comparable) for row in group[1:]):
            cost_denominator_mismatches.append(window_id)
    cost_cell_set = set(cost_keys)
    cost_missing_cells = sorted(expected_cells - cost_cell_set)
    cost_unexpected_cells = sorted(cost_cell_set - expected_cells)
    cost_scope_valid = cost_scope_values == ["shared_window_collection"]
    run_summary_valid = summary.get("window_count") == len(expected_windows) and summary.get("policy_count") == len(policy_roles)

    source_sample = _sample_source_pointers(replay_dir, manifest, source_sample_size)
    reconciliation = {
        "version": "short-window-baselining-v1/replay-reconciliation-1",
        "manifest_window_count": manifest.get("window_count"),
        "expected_window_count": manifest.get("expected_window_count"),
        "coverage_window_count": len(windows),
        "policy_roles": policy_roles,
        "coverage_cell_count": len(coverage),
        "expected_cell_count": expected_cell_count,
        "coverage_duplicate_cells": duplicate_cells,
        "coverage_missing_cells": [list(key) for key in missing_cells],
        "coverage_unexpected_cells": [list(key) for key in unexpected_cells],
        "coverage_missing_windows": missing_windows,
        "coverage_unexpected_windows": unexpected_windows,
        "primary_comparison_duplicate_ids": duplicate_primary_ids,
        "aging_comparison_duplicate_ids": duplicate_aging_ids,
        "observation_duplicate_ids": duplicate_observation_ids,
        "membership_duplicate_ids": duplicate_membership_ids,
        "membership_cell_role_duplicate_ids": duplicate_membership_cell_role_ids,
        "uncertainty_duplicate_cells": duplicate_uncertainty_cells,
        "uncertainty_missing_cells": [list(key) for key in uncertainty_missing_cells],
        "uncertainty_unexpected_cells": [list(key) for key in uncertainty_unexpected_cells],
        "aging_offsets": list(EXPECTED_OFFSETS),
        "malformed_aging_cells": malformed_aging_cells,
        "offset0_mismatches": offset0_mismatches,
        "coverage_comparison_count_mismatches": coverage_comparison_count_mismatches,
        "aging_comparison_count_mismatches": aging_comparison_count_mismatches,
        "coverage_range_errors": coverage_range_errors,
        "aging_range_errors": aging_range_errors,
        "query_inventory_check": query_inventory_check,
        "observation_missing_source": observation_missing_source,
        "membership_missing_source": membership_missing_source,
        "uncertainty_cell_count": len(uncertainty_cells),
        "uncertainty_membership_hash_missing": uncertainty_hash_missing,
        "membership_hash_mismatches": membership_hash_mismatches,
        "cost_row_count": len(cost_rows),
        "cost_duplicate_cells": cost_duplicates,
        "cost_scope_values": cost_scope_values,
        "cost_missing_cells": [list(key) for key in cost_missing_cells],
        "cost_unexpected_cells": [list(key) for key in cost_unexpected_cells],
        "cost_scope_valid": cost_scope_valid,
        "cost_denominator_mismatches": cost_denominator_mismatches,
        "run_summary_valid": run_summary_valid,
        "source_sample": source_sample,
        "run_summary": summary,
    }
    reconciliation["valid"] = not any((
        reconciliation["manifest_window_count"] != reconciliation["expected_window_count"],
        reconciliation["coverage_window_count"] != reconciliation["expected_window_count"],
        reconciliation["coverage_cell_count"] != expected_cell_count,
        duplicate_cells, missing_windows, unexpected_windows, missing_cells, unexpected_cells,
        duplicate_primary_ids, duplicate_aging_ids, duplicate_observation_ids,
        duplicate_membership_ids, duplicate_membership_cell_role_ids, duplicate_uncertainty_cells, uncertainty_missing_cells, uncertainty_unexpected_cells, malformed_aging_cells,
        offset0_mismatches, coverage_comparison_count_mismatches,
        aging_comparison_count_mismatches, coverage_range_errors, aging_range_errors, observation_missing_source,
        membership_missing_source, uncertainty_hash_missing,
        membership_hash_mismatches, not query_inventory_check["valid"], cost_duplicates, cost_missing_cells,
        cost_unexpected_cells, not cost_scope_valid, cost_denominator_mismatches, not run_summary_valid,
        not source_sample["valid"],
    ))
    return reconciliation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-sample-size", type=int, default=200)
    args = parser.parse_args(argv)
    result = reconcile_replay(replay_dir=args.replay_dir, source_sample_size=args.source_sample_size)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": result["valid"], "coverage_cell_count": result["coverage_cell_count"], "offset0_mismatch_count": len(result["offset0_mismatches"])}, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
