"""Independent artifact reconciliation and paired sensitivity summaries.

This module intentionally uses only the Python standard library and reads the
label-free matrix artifacts after the runner has completed.  It does not read
``dev/query_dev.csv``, ``record.csv``, ``scoring_points``, or any answer key.
The runner remains responsible for producing the primary tables; this module
checks their cardinalities and derives paired descriptive summaries without
changing selection decisions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Mapping


EXPECTED_LOOKBACKS = (5, 10, 15, 30, 60)
EXPECTED_MODES = ("C0", "C1", "C2")
EXPECTED_REPLICAS = ("same_replica", "pooled")
EXPECTED_ANCHOR_HOURS = (1, 5, 9, 13, 17, 21)
EXPECTED_ANCHORS = tuple(
    f"2022-03-{day:02d}T{hour:02d}:00:00+08:00"
    for day in (20, 21)
    for hour in EXPECTED_ANCHOR_HOURS
)


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(value)
    return rows


def _identity(row: Mapping) -> tuple[str, str]:
    return (str(row.get("trace_id", row.get("root_key", [""])[0] if isinstance(row.get("root_key"), list) else "")),
            str(row.get("span_id", row.get("root_key", ["", ""])[1] if isinstance(row.get("root_key"), list) else "")))


def _cell_key(row: Mapping) -> tuple[str, int, str, str]:
    return (str(row.get("anchor_id", "")), int(row.get("lookback_minutes", -1)),
            str(row.get("mode", "")), str(row.get("replica_policy", "")))


def _hash_json(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _hash_file_streaming(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_timestamp(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


def _interval_overlap(left: tuple[datetime, datetime], right: tuple[datetime, datetime]) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def _query_inventory(repo_root: Path) -> tuple[list[dict], list[dict]]:
    """Read the public label-free query rows and attach exact time bounds.

    ``query.csv`` is the authoritative row inventory and has no answer fields.
    The existing public scope register supplies parsed bounds.  If an older
    scope register is missing a row, parse only the date/time phrase from that
    prompt and retain the missing-scope qualification in the result.
    """
    query_path = repo_root / "data/track-1/query.csv"
    with query_path.open(newline="", encoding="utf-8") as handle:
        query_rows = list(csv.DictReader(handle))
    scope_path = repo_root / "docs/research/experiments/frontend-blind-v1/scope.csv"
    scope_by_id: dict[str, dict] = {}
    if scope_path.is_file():
        with scope_path.open(newline="", encoding="utf-8") as handle:
            scope_by_id = {str(row["row_id"]): row for row in csv.DictReader(handle)}
    supplied: list[dict] = []
    missing_scope_rows: list[dict] = []
    parse_failures: list[dict] = []
    for row in query_rows:
        row_id = str(row["row_id"])
        scope = scope_by_id.get(row_id)
        if scope and scope.get("query_start") and scope.get("query_end"):
            start, end = str(scope["query_start"]), str(scope["query_end"])
        else:
            # This fallback is deliberately narrow and records that the
            # public parsed scope was absent.  It never opens query_dev.csv.
            import re
            match = re.search(
                r"March\s+(20|21),\s+2022.*?(?:from|between)\s+(\d{1,2}):(\d{2})\s*(?:to|and)\s+(?:(?:March\s+\d{1,2},\s+2022,?\s*(?:at|from)\s+))?(\d{1,2}):(\d{2})",
                str(row.get("instruction", "")),
                flags=re.IGNORECASE | re.DOTALL,
            )
            if not match:
                parse_failures.append({"row_id": row_id, "reason": "missing_time_bounds"})
                continue
            day, sh, sm, eh, em = (int(value) for value in match.groups())
            start = f"2022-03-{day:02d}T{sh:02d}:{sm:02d}:00+08:00"
            end_day = day + 1 if eh == 0 and sh != 0 else day
            end = f"2022-03-{end_day:02d}T{eh:02d}:{em:02d}:00+08:00"
            missing_scope_rows.append({"row_id": row_id, "reason": "parsed_from_public_instruction"})
        supplied.append({
            "row_id": row_id,
            "query_start": start,
            "query_end": end,
            "task_index": str(row.get("task_index", "")),
        })
    if parse_failures:
        raise ValueError(f"unable to derive public query time bounds: {parse_failures}")
    return supplied, missing_scope_rows


def _exposure_inventory(repo_root: Path, manifest: Mapping) -> dict:
    """Build a label-free 57-window and telemetry-overlap inventory."""
    supplied_rows, missing_scope_rows = _query_inventory(repo_root)
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in supplied_rows:
        grouped[(row["query_start"], row["query_end"])].append(str(row["row_id"]))
    supplied = []
    for (start, end), row_ids in sorted(grouped.items()):
        supplied.append({
            "kind": "supplied_query_window",
            "window_start": start,
            "window_end": end,
            "row_ids": sorted(row_ids, key=lambda value: int(value)),
            "duplicate_row": len(row_ids) > 1,
            "study_exposure": "planned_label_free_descriptive_replay",
        })

    prior_path = repo_root / "specs/001-candidate-recall-experiment/development-exposures.json"
    prior = _read_json(prior_path)
    prior_intervals = []
    for item in prior.get("exposures", []):
        prior_intervals.append({
            "kind": "prior_development_exposure",
            "row_id": str(item.get("row_id", "")),
            "window_start": str(item.get("window_start", "")),
            "window_end": str(item.get("window_end", "")),
            "reason": str(item.get("reason", "")),
            "selected_example": bool(item.get("selected_example", False)),
            "source": str(prior_path),
        })

    # The public scope register also records telemetry exposure around the
    # known control and adjacent rows.  Keep these flags explicit even if the
    # minimum historical ledger predates them.
    scope_path = repo_root / "docs/research/experiments/frontend-blind-v1/scope.csv"
    if scope_path.is_file():
        with scope_path.open(newline="", encoding="utf-8") as handle:
            for item in csv.DictReader(handle):
                if not item.get("exposure_flag"):
                    continue
                prior_intervals.append({
                    "kind": "scope_register_exposure",
                    "row_id": str(item.get("row_id", "")),
                    "window_start": str(item.get("query_start", "")),
                    "window_end": str(item.get("query_end", "")),
                    "reason": str(item.get("exposure_flag", "")),
                    "selected_example": str(item.get("role", "")) == "exposed_control",
                    "source": str(scope_path),
                })

    anchors = []
    for raw in manifest.get("anchors", []):
        anchor_id = str(raw.get("anchor_id", ""))
        start = _parse_timestamp(str(raw.get("local", anchor_id)))
        support_start = start.replace()  # preserve timezone from the anchor
        # Anchor support is the full 90-minute collection horizon, not a
        # claim that every event in it was used by every policy.
        anchors.append({
            "kind": "core_anchor_support",
            "anchor_id": anchor_id,
            "window_start": (support_start - timedelta(minutes=60)).isoformat(),
            "window_end": (support_start + timedelta(minutes=30)).isoformat(),
            "study_exposure": "label_free_matrix_support_completed",
        })

    # A supplied-window replay consumes the frozen reference plus every six
    # five-minute query slice.  Before a policy is selected, use the declared
    # maximum 60-minute reference to make shared telemetry exposure explicit.
    replay_support = []
    for item in supplied:
        start = _parse_timestamp(item["window_start"])
        end = _parse_timestamp(item["window_end"])
        replay_support.append({
            "kind": "current_replay_support",
            "row_ids": item["row_ids"],
            "window_start": (start - timedelta(minutes=60)).isoformat(),
            "window_end": end.isoformat(),
            "lookback_used_for_overlap": 60,
            "study_exposure": "planned_not_executed_label_free_descriptive_replay",
        })

    intervals = replay_support + prior_intervals + anchors
    parsed = []
    for index, item in enumerate(intervals):
        try:
            bounds = (_parse_timestamp(item["window_start"]), _parse_timestamp(item["window_end"]))
        except (KeyError, TypeError, ValueError):
            continue
        parsed.append((index, bounds))
    adjacency: dict[int, set[int]] = {index: set() for index, _ in parsed}
    for pos, (left_index, left) in enumerate(parsed):
        for right_index, right in parsed[pos + 1:]:
            if _interval_overlap(left, right):
                adjacency[left_index].add(right_index)
                adjacency[right_index].add(left_index)
    groups = []
    seen: set[int] = set()
    interval_by_index = {index: item for index, item in enumerate(intervals)}
    for index in adjacency:
        if index in seen:
            continue
        stack = [index]
        component = []
        seen.add(index)
        while stack:
            current = stack.pop()
            component.append(interval_by_index[current])
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        groups.append(component)

    return {
        "source": str(scope_path),
        "row_count": len(supplied_rows),
        "distinct_query_windows": len(supplied),
        "query_row_count_expected": 70,
        "query_row_count_ok": len(supplied_rows) == 70,
        "distinct_query_windows_expected": 57,
        "distinct_query_windows_ok": len(supplied) == 57,
        "missing_scope_rows": missing_scope_rows,
        "duplicate_query_windows": [item for item in supplied if item["duplicate_row"]],
        "supplied_windows": supplied,
        "prior_exposures": prior_intervals,
        "core_anchor_support_intervals": anchors,
        "current_replay_support_intervals": replay_support,
        "overlap_group_count": len(groups),
        "overlap_groups": groups,
        "policy": "overlap groups are descriptive telemetry exposure accounting; no independent split is claimed",
    }


def _top_ids(row: Mapping) -> set[tuple[str, str]]:
    values = row.get("top5_positive_absolute_excess", [])
    return {_identity(value) for value in values if isinstance(value, Mapping)}


def _comparison_ids(rows: Iterable[Mapping]) -> dict[tuple[str, int, str, str], set[tuple[str, str]]]:
    values: dict[tuple[str, int, str, str], set[tuple[str, str]]] = defaultdict(set)
    for row in rows:
        values[_cell_key(row)].add(_identity(row))
    return values


def _comparison_maps(rows: Iterable[Mapping]) -> dict[tuple[str, int, str, str], dict[tuple[str, str], dict]]:
    values: dict[tuple[str, int, str, str], dict[tuple[str, str], dict]] = defaultdict(dict)
    for row in rows:
        values[_cell_key(row)][_identity(row)] = dict(row)
    return values


def _membership_hash(rows: Iterable[Mapping]) -> str:
    identities = []
    for row in rows:
        root_key = row.get("root_key", [row.get("trace_id", ""), row.get("span_id", "")])
        if not isinstance(root_key, (list, tuple)) or len(root_key) != 2:
            continue
        # Match contracts.stable_membership_hash exactly: provenance is
        # checked separately below and is intentionally not part of this
        # membership identity hash.
        identities.append((str(root_key[0]), str(root_key[1])))
    payload = json.dumps(sorted(set(identities)), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _membership_ids(rows: Iterable[Mapping]) -> dict[tuple[str, int, str, str], set[tuple[str, str]]]:
    values: dict[tuple[str, int, str, str], set[tuple[str, str]]] = defaultdict(set)
    for row in rows:
        if str(row.get("role", "")) == "query":
            values[_cell_key(row)].add(_identity(row))
    return values


def _artifact_reconciliation(repo_root: Path, artifact_dir: Path, manifest: Mapping, observations: list[dict], coverage: list[dict], comparisons: list[dict], uncertainty: list[dict], memberships: list[dict]) -> dict:
    expected_keys = {
        (anchor, lookback, mode, replica)
        for anchor in EXPECTED_ANCHORS
        for lookback in EXPECTED_LOOKBACKS
        for mode in EXPECTED_MODES
        for replica in EXPECTED_REPLICAS
    }
    actual_keys = [_cell_key(row) for row in coverage]
    actual_set = set(actual_keys)
    duplicates = [key for key, count in Counter(actual_keys).items() if count > 1]
    missing = sorted(expected_keys - actual_set)
    unexpected = sorted(actual_set - expected_keys)
    aging_counts = Counter()
    malformed_aging = []
    for row in coverage:
        aging = row.get("aging", [])
        aging_counts[_cell_key(row)] = len(aging)
        if len(aging) != 6:
            malformed_aging.append({"cell": _cell_key(row), "count": len(aging)})
    uncertainty_cells = {_cell_key(row) for row in uncertainty}
    membership_cells = {_cell_key(row) for row in memberships}
    comparison_cells = {_cell_key(row) for row in comparisons}
    observation_ids = {_identity(row) for row in observations}
    duplicate_observation_ids = len(observation_ids) != len(observations)
    source_pointer_missing = 0
    unresolved_membership_sources = 0
    for row in memberships:
        root_key = row.get("root_key")
        if not isinstance(root_key, (list, tuple)) or len(root_key) != 2:
            source_pointer_missing += 1
        elif tuple(str(value) for value in root_key) not in observation_ids:
            unresolved_membership_sources += 1
        source = row.get("source")
        if not isinstance(source, Mapping) or not source.get("source_file") or not source.get("source_record"):
            source_pointer_missing += 1
    comparison_source_missing = sum(
        1 for row in comparisons
        if not isinstance(row.get("source"), Mapping) or not row.get("source", {}).get("source_file")
    )
    comparison_counts = Counter(_cell_key(item) for item in comparisons)
    cell_comparison_count_mismatches = []
    for row in coverage:
        key = _cell_key(row)
        count = comparison_counts.get(key, 0)
        if count != int(row.get("supported_query_count", 0) or 0):
            cell_comparison_count_mismatches.append({
                "cell": list(key),
                "coverage_supported_query_count": int(row.get("supported_query_count", 0) or 0),
                "comparison_rows": count,
            })
    invalid_coverage_values = [
        {"cell": list(_cell_key(row)), "request_coverage": row.get("request_coverage")}
        for row in coverage
        if not isinstance(row.get("request_coverage"), (int, float)) or not 0 <= float(row.get("request_coverage")) <= 1
    ]
    invalid_aging_values = []
    for row in coverage:
        for aging in row.get("aging", []):
            value = aging.get("request_coverage")
            if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
                invalid_aging_values.append({"cell": list(_cell_key(row)), "offset_minutes": aging.get("offset_minutes"), "request_coverage": value})
    uncertainty_hash_missing = sum(
        1 for row in uncertainty
        if not isinstance(row.get("membership_hashes"), Mapping)
        or not row.get("membership_hashes", {}).get("reference_membership_hash")
        or not row.get("membership_hashes", {}).get("query_membership_hash")
    )
    membership_hash_mismatches = []
    memberships_by_cell_cohort_role: dict[tuple, list[dict]] = defaultdict(list)
    for row in memberships:
        memberships_by_cell_cohort_role[(_cell_key(row), str(row.get("cohort_key")), str(row.get("role", "")))].append(row)
    for row in uncertainty:
        cell = _cell_key(row)
        cohort = str(row.get("cohort_key"))
        expected_hashes = row.get("membership_hashes", {})
        ref_rows = [item for item in memberships_by_cell_cohort_role.get((cell, cohort, "reference"), []) if item.get("status") == "included"]
        query_rows = [item for item in memberships_by_cell_cohort_role.get((cell, cohort, "query"), []) if item.get("identity_resolved") and item.get("status") in {"candidate", "included"}]
        actual_ref_hash = _membership_hash(ref_rows)
        actual_query_hash = _membership_hash(query_rows)
        if actual_ref_hash != expected_hashes.get("reference_membership_hash") or actual_query_hash != expected_hashes.get("query_membership_hash"):
            membership_hash_mismatches.append({
                "cell": list(cell),
                "cohort_key": cohort,
                "expected": expected_hashes,
                "actual": {"reference_membership_hash": actual_ref_hash, "query_membership_hash": actual_query_hash},
            })

    distinct_membership_rows = {}
    for row in memberships:
        root_key = row.get("root_key")
        source = row.get("source")
        if isinstance(root_key, (list, tuple)) and len(root_key) == 2 and isinstance(source, Mapping):
            distinct_membership_rows.setdefault((str(root_key[0]), str(root_key[1])), row)
    source_pointer_sample_rows = [distinct_membership_rows[key] for key in sorted(distinct_membership_rows)[:200]]
    source_pointer_sample_size = len(source_pointer_sample_rows)
    source_pointer_sample_mismatches = []
    source_pointer_check_error = None
    index_raw = manifest.get("index", {}).get("index") if isinstance(manifest.get("index"), Mapping) else None
    index_path = Path(str(index_raw)) if index_raw else artifact_dir / "trace.sqlite3"
    if not index_path.is_absolute():
        index_path = repo_root / index_path
    try:
        with sqlite3.connect(str(index_path)) as conn:
            conn.execute("PRAGMA query_only=ON")
            for row in source_pointer_sample_rows:
                root_key = row.get("root_key")
                source = row.get("source")
                if not isinstance(root_key, (list, tuple)) or len(root_key) != 2 or not isinstance(source, Mapping):
                    continue
                found = conn.execute(
                    "SELECT 1 FROM spans WHERE trace_id=? AND span_id=? AND source_file=? AND source_record=?",
                    (str(root_key[0]), str(root_key[1]), str(source.get("source_file", "")), int(source.get("source_record", 0) or 0)),
                ).fetchone()
                if found is None:
                    source_pointer_sample_mismatches.append({"root_key": list(root_key), "source": dict(source)})
    except (OSError, sqlite3.Error) as exc:
        source_pointer_check_error = f"{type(exc).__name__}: {exc}"
    return {
        "manifest_version": manifest.get("version"),
        "expected_policy_anchor_cells": len(expected_keys),
        "coverage_rows": len(coverage),
        "coverage_duplicate_cells": [list(key) for key in sorted(duplicates)],
        "coverage_missing_cells": [list(key) for key in missing],
        "coverage_unexpected_cells": [list(key) for key in unexpected],
        "all_coverage_cells_present_once": len(coverage) == 360 and not duplicates and not missing and not unexpected,
        "aging_slices_per_cell": dict(sorted(("|".join(map(str, key)), count) for key, count in aging_counts.items())),
        "malformed_aging_cells": malformed_aging,
        "uncertainty_cell_count": len(uncertainty_cells),
        "membership_cell_count": len(membership_cells),
        "comparison_cell_count": len(comparison_cells),
        "observation_count": len(observations),
        "duplicate_observation_id": duplicate_observation_ids,
        "membership_source_pointer_missing": source_pointer_missing,
        "membership_observation_unresolved": unresolved_membership_sources,
        "comparison_source_pointer_missing": comparison_source_missing,
        "cell_comparison_count_mismatches": cell_comparison_count_mismatches,
        "invalid_coverage_values": invalid_coverage_values,
        "invalid_aging_values": invalid_aging_values,
        "uncertainty_membership_hash_missing": uncertainty_hash_missing,
        "membership_hash_mismatches": membership_hash_mismatches,
        "source_pointer_sample_size": source_pointer_sample_size,
        "source_pointer_sample_mismatches": source_pointer_sample_mismatches,
        "source_pointer_check_error": source_pointer_check_error,
        "source_linked_results_valid": not duplicate_observation_ids and source_pointer_missing == 0 and unresolved_membership_sources == 0 and comparison_source_missing == 0 and not cell_comparison_count_mismatches and not invalid_coverage_values and not invalid_aging_values and uncertainty_hash_missing == 0 and not membership_hash_mismatches and not source_pointer_sample_mismatches and source_pointer_check_error is None,
        "coverage_file": str(artifact_dir / "coverage.jsonl"),
    }


def _paired_sensitivities(coverage: list[dict], comparisons: list[dict], uncertainty: list[dict], memberships: list[dict], observations: list[dict]) -> dict:
    by_key = {_cell_key(row): row for row in coverage}
    comparison_ids = _comparison_ids(comparisons)
    comparison_maps = _comparison_maps(comparisons)
    membership_ids = _membership_ids(memberships)
    pairing = []
    for anchor in EXPECTED_ANCHORS:
        for lookback in EXPECTED_LOOKBACKS:
            for mode in EXPECTED_MODES:
                same_key = (anchor, lookback, mode, "same_replica")
                pooled_key = (anchor, lookback, mode, "pooled")
                if same_key not in by_key or pooled_key not in by_key:
                    continue
                same_supported = comparison_ids.get(same_key, set())
                pooled_supported = comparison_ids.get(pooled_key, set())
                common_supported = same_supported & pooled_supported
                query_population = membership_ids.get(same_key, set()) | membership_ids.get(pooled_key, set())
                same_top_full = _top_ids(by_key[same_key])
                pooled_top_full = _top_ids(by_key[pooled_key])
                top_intersection = same_top_full & pooled_top_full
                same_common_rows = [row for identity, row in comparison_maps.get(same_key, {}).items() if identity in common_supported and (row.get("absolute_excess_ms") or 0) > 0]
                pooled_common_rows = [row for identity, row in comparison_maps.get(pooled_key, {}).items() if identity in common_supported and (row.get("absolute_excess_ms") or 0) > 0]
                order = lambda row: (-float(row.get("absolute_excess_ms", 0.0)), str(row.get("trace_id", "")), str(row.get("span_id", "")))
                same_top_common = {_identity(row) for row in sorted(same_common_rows, key=order)[:5]}
                pooled_top_common = {_identity(row) for row in sorted(pooled_common_rows, key=order)[:5]}
                common_top_intersection = same_top_common & pooled_top_common
                query_changes = []
                for identity in sorted(common_supported):
                    same_row = comparison_maps.get(same_key, {}).get(identity, {})
                    pooled_row = comparison_maps.get(pooled_key, {}).get(identity, {})
                    same_center = same_row.get("median_ms")
                    pooled_center = pooled_row.get("median_ms")
                    same_excess = same_row.get("absolute_excess_ms")
                    pooled_excess = pooled_row.get("absolute_excess_ms")
                    query_changes.append({
                        "trace_id": identity[0],
                        "span_id": identity[1],
                        "signed_center_change_ms": pooled_center - same_center if same_center is not None and pooled_center is not None else None,
                        "signed_excess_change_ms": pooled_excess - same_excess if pooled_excess is not None and same_excess is not None else None,
                    })
                center_changes = [row["signed_center_change_ms"] for row in query_changes if row["signed_center_change_ms"] is not None]
                excess_changes = [row["signed_excess_change_ms"] for row in query_changes if row["signed_excess_change_ms"] is not None]
                full_union = same_top_full | pooled_top_full
                common_top_union = same_top_common | pooled_top_common
                pairing.append({
                    "anchor_id": anchor,
                    "lookback_minutes": lookback,
                    "mode": mode,
                    "same_supported_count": len(same_supported),
                    "pooled_supported_count": len(pooled_supported),
                    "common_supported_count": len(common_supported),
                    "query_population_count": len(query_population),
                    "same_vs_pooled_full_population_overlap": len(top_intersection) / len(query_population) if query_population else None,
                    "same_vs_pooled_full_top5_jaccard": len(top_intersection) / len(full_union) if full_union else None,
                    "same_vs_pooled_common_supported_overlap": len(common_top_intersection) / min(5, len(common_supported)) if common_supported else None,
                    "same_vs_pooled_common_supported_top5_jaccard": len(common_top_intersection) / len(common_top_union) if common_top_union else None,
                    "full_top5_intersection_count": len(top_intersection),
                    "common_supported_top5_intersection_count": len(common_top_intersection),
                    "same_top5_full_population": sorted(same_top_full),
                    "pooled_top5_full_population": sorted(pooled_top_full),
                    "same_top5_reranked_common_supported": sorted(same_top_common),
                    "pooled_top5_reranked_common_supported": sorted(pooled_top_common),
                    "per_query_center_changes": query_changes,
                    "median_signed_center_change_ms": statistics.median(center_changes) if center_changes else None,
                    "median_signed_excess_change_ms": statistics.median(excess_changes) if excess_changes else None,
                })

    centers: dict[tuple[str, str, str, str], dict[int, float | None]] = defaultdict(dict)
    for row in uncertainty:
        key = (str(row.get("anchor_id", "")), str(row.get("mode", "")), str(row.get("replica_policy", "")), str(row.get("cohort_key", "")))
        summary = row.get("summary", {})
        stats = summary.get("reference_statistics", {}) if isinstance(summary, Mapping) else {}
        try:
            lookback = int(row.get("lookback_minutes"))
        except (TypeError, ValueError):
            continue
        centers[key][lookback] = stats.get("median_ms")
    adjacent = []
    for key, values in sorted(centers.items()):
        for left, right in zip(EXPECTED_LOOKBACKS, EXPECTED_LOOKBACKS[1:]):
            if left not in values or right not in values:
                continue
            left_center, right_center = values[left], values[right]
            adjacent.append({
                "anchor_id": key[0],
                "mode": key[1],
                "replica_policy": key[2],
                "cohort_key": key[3],
                "left_lookback_minutes": left,
                "right_lookback_minutes": right,
                "left_median_ms": left_center,
                "right_median_ms": right_center,
                "signed_center_change_ms": (right_center - left_center) if left_center is not None and right_center is not None else None,
            })

    scopes: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in coverage:
        scope_key = (str(row.get("mode", "")), str(row.get("replica_policy", "")), str(row.get("lookback_minutes", "")))
        scopes[scope_key].append(row)
    scope_rows = []
    for key, rows in sorted(scopes.items()):
        resolved = sum(int(row.get("query_resolved_count", 0) or 0) for row in rows)
        supported = sum(int(row.get("supported_query_count", 0) or 0) for row in rows)
        scope_rows.append({
            "mode": key[0],
            "replica_policy": key[1],
            "lookback_minutes": int(key[2]),
            "anchor_count": len(rows),
            "resolved_query_count": resolved,
            "supported_query_count": supported,
            "request_coverage": supported / resolved if resolved else 0.0,
            "anchors_at_least_80pct": sum(1 for row in rows if row.get("query_resolved_count", 0) and float(row.get("request_coverage", 0.0)) >= 0.8),
            "zero_median_cohort_count": sum(int(row.get("zero_median_cohort_count", 0) or 0) for row in rows),
        })

    # Compute coverage by the observed C0/C2 shape and recording replica.  The
    # strata are built from query memberships and source observations, so the
    # denominator remains the full observed query population for each cell.
    observation_by_id = {_identity(row): row for row in observations}
    stratum_queries: dict[tuple, set[tuple[str, str]]] = defaultdict(set)
    stratum_resolved: dict[tuple, set[tuple[str, str]]] = defaultdict(set)
    stratum_supported: dict[tuple, set[tuple[str, str]]] = defaultdict(set)
    for row in memberships:
        if str(row.get("role", "")) != "query":
            continue
        cell = _cell_key(row)
        identity = _identity(row)
        observation = observation_by_id.get(identity)
        if observation is None:
            continue
        signatures = observation.get("signature", {})
        strata = {
            "C0": signatures.get("C0"),
            "C2": signatures.get("C2"),
            "replica": observation.get("cmdb_id"),
        }
        for kind, value in strata.items():
            if isinstance(value, Mapping):
                value = json.dumps(value, sort_keys=True, separators=(",", ":"))
            stratum_key = (cell, kind, str(value))
            stratum_queries[stratum_key].add(identity)
            if bool(row.get("identity_resolved")):
                stratum_resolved[stratum_key].add(identity)
    for cell, rows in comparison_maps.items():
        for identity in rows:
            observation = observation_by_id.get(identity)
            if observation is None:
                continue
            signatures = observation.get("signature", {})
            strata = {
                "C0": signatures.get("C0"),
                "C2": signatures.get("C2"),
                "replica": observation.get("cmdb_id"),
            }
            for kind, value in strata.items():
                if isinstance(value, Mapping):
                    value = json.dumps(value, sort_keys=True, separators=(",", ":"))
                stratum_supported[(cell, kind, str(value))].add(identity)
    stratum_rows = []
    for (cell, kind, stratum_key), query_set in sorted(stratum_queries.items(), key=lambda item: (item[0][0], item[0][1], item[0][2])):
        supported_set = stratum_supported.get((cell, kind, stratum_key), set())
        resolved_set = stratum_resolved.get((cell, kind, stratum_key), set())
        stratum_rows.append({
            "anchor_id": cell[0],
            "lookback_minutes": cell[1],
            "mode": cell[2],
            "replica_policy": cell[3],
            "stratum_kind": kind,
            "stratum_key": stratum_key,
            "query_count": len(query_set),
            "resolved_query_count": len(resolved_set),
            "unresolved_query_count": len(query_set - resolved_set),
            "supported_query_count": len(supported_set),
            "request_coverage": len(supported_set) / len(resolved_set) if resolved_set else 0.0,
            "all_observed_request_coverage": len(supported_set) / len(query_set) if query_set else 0.0,
        })

    # Pair every available policy within an anchor.  This keeps context,
    # lookback, and replica comparisons descriptive even when no policy passes
    # the screening gates.
    policy_pairs = []
    by_anchor: dict[str, list[tuple[str, int, str, str]]] = defaultdict(list)
    for key in by_key:
        by_anchor[key[0]].append(key)
    for anchor, keys in sorted(by_anchor.items()):
        keys = sorted(keys)
        for left_index, left_key in enumerate(keys):
            for right_key in keys[left_index + 1:]:
                left_ids = comparison_ids.get(left_key, set())
                right_ids = comparison_ids.get(right_key, set())
                common = left_ids & right_ids
                population = membership_ids.get(left_key, set()) | membership_ids.get(right_key, set())
                left_map = comparison_maps.get(left_key, {})
                right_map = comparison_maps.get(right_key, {})
                delta = [right_map[item].get("absolute_excess_ms") - left_map[item].get("absolute_excess_ms") for item in common if right_map[item].get("absolute_excess_ms") is not None and left_map[item].get("absolute_excess_ms") is not None]
                rank = lambda row: (-float(row.get("absolute_excess_ms", 0.0)), str(row.get("trace_id", "")), str(row.get("span_id", "")))
                left_top_full = {_identity(row) for row in sorted([row for row in left_map.values() if (row.get("absolute_excess_ms") or 0) > 0], key=rank)[:5]}
                right_top_full = {_identity(row) for row in sorted([row for row in right_map.values() if (row.get("absolute_excess_ms") or 0) > 0], key=rank)[:5]}
                left_top_common = {_identity(row) for row in sorted([row for identity, row in left_map.items() if identity in common and (row.get("absolute_excess_ms") or 0) > 0], key=rank)[:5]}
                right_top_common = {_identity(row) for row in sorted([row for identity, row in right_map.items() if identity in common and (row.get("absolute_excess_ms") or 0) > 0], key=rank)[:5]}
                full_top_intersection = left_top_full & right_top_full
                full_top_union = left_top_full | right_top_full
                common_top_intersection = left_top_common & right_top_common
                common_top_union = left_top_common | right_top_common
                policy_pairs.append({
                    "anchor_id": anchor,
                    "left_policy": list(left_key[1:]),
                    "right_policy": list(right_key[1:]),
                    "left_supported_count": len(left_ids),
                    "right_supported_count": len(right_ids),
                    "common_supported_count": len(common),
                    "query_population_count": len(population),
                    "left_request_coverage": by_key[left_key].get("request_coverage"),
                    "right_request_coverage": by_key[right_key].get("request_coverage"),
                    "median_signed_excess_change_ms": statistics.median(delta) if delta else None,
                    "full_top5_intersection_count": len(full_top_intersection),
                    "full_top5_jaccard": len(full_top_intersection) / len(full_top_union) if full_top_union else None,
                    "full_top5_population_overlap": len(full_top_intersection) / len(population) if population else None,
                    "common_supported_top5_intersection_count": len(common_top_intersection),
                    "common_supported_top5_overlap": len(common_top_intersection) / min(5, len(common)) if common else None,
                    "common_supported_top5_jaccard": len(common_top_intersection) / len(common_top_union) if common_top_union else None,
                    "left_top5_full_population": sorted(left_top_full),
                    "right_top5_full_population": sorted(right_top_full),
                    "left_top5_reranked_common_supported": sorted(left_top_common),
                    "right_top5_reranked_common_supported": sorted(right_top_common),
                })
    return {
        "same_vs_pooled_per_query": pairing,
        "adjacent_lookback_centers": adjacent,
        "policy_scopes": scope_rows,
        "stratum_coverage_by_C0_C2_replica": stratum_rows,
        "policy_pairwise_sensitivity": policy_pairs,
    }


def analyze(artifact_dir: Path, repo_root: Path, output_path: Path | None = None) -> dict:
    artifact_dir = Path(artifact_dir)
    manifest = _read_json(artifact_dir / "manifest.json")
    observations = _read_jsonl(artifact_dir / "observations.jsonl")
    coverage = _read_jsonl(artifact_dir / "coverage.jsonl")
    comparisons = _read_jsonl(artifact_dir / "comparisons.jsonl")
    uncertainty = _read_jsonl(artifact_dir / "uncertainty.jsonl")
    memberships = _read_jsonl(artifact_dir / "memberships.jsonl")
    result = {
        "analysis_version": "short-window-baselining-v1/independent-analysis-1",
        "artifact_dir": str(artifact_dir),
        "artifact_hashes": {path.name: _hash_file_streaming(path) for path in sorted(artifact_dir.glob("*.jsonl"))},
        "artifact_reconciliation": _artifact_reconciliation(repo_root, artifact_dir, manifest, observations, coverage, comparisons, uncertainty, memberships),
        "paired_sensitivities": _paired_sensitivities(coverage, comparisons, uncertainty, memberships, observations),
        "exposure_inventory": _exposure_inventory(repo_root, manifest),
    }
    if output_path is None:
        output_path = artifact_dir / "independent-analysis.json"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = analyze(args.artifact_dir, args.repo_root, args.output)
    print(json.dumps({
        "analysis_version": result["analysis_version"],
        "all_coverage_cells_present_once": result["artifact_reconciliation"]["all_coverage_cells_present_once"],
        "distinct_query_windows": result["exposure_inventory"]["distinct_query_windows"],
        "output": str(args.output or args.artifact_dir / "independent-analysis.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
