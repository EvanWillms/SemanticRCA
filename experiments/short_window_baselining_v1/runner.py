"""Core matrix runner for the short-window baselining study.

This module performs retrospective event-time replay only.  It does not read
benchmark labels, status semantics, or scoring fields, and it never changes a
reference while evaluating the six query-aging slices.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from collections import Counter, defaultdict
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping

from .contracts import (
    bootstrap_median,
    compare_duration,
    support_diagnostics,
    signature_key,
    stable_membership_hash,
)
from .index import (
    DEFAULT_ARTIFACT_ROOT,
    DEFAULT_INDEX,
    DEFAULT_TRACE_ROOT,
    build_index,
    discover_frontend_components,
    fetch_frontend_roots,
    fetch_traces,
    open_index,
    source_inventory,
    validate_index,
)
from .observations import build_observation, group_root_rows


ROOT = Path(__file__).resolve().parents[2]
UTC8 = timezone(timedelta(hours=8))
LOOKBACKS = (5, 10, 15, 30, 60)
MODES = ("C0", "C1", "C2")
REPLICA_POLICIES = ("same_replica", "pooled")
PRIMARY_QUERY_MINUTES = 5
AGING_OFFSETS = (0, 5, 10, 15, 20, 25)
BOOTSTRAP_SEED = 42
BOOTSTRAP_REPLICATES = 200


def _json_default(value):
    if isinstance(value, (Path, datetime, date)):
        return str(value)
    raise TypeError(type(value).__name__)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=_json_default, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Mapping]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True, default=_json_default) + "\n")
            count += 1
    return count


def _hash_files(paths: Iterable[Path]) -> dict[str, str]:
    output = {}
    for path in sorted({Path(p) for p in paths}):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        output[str(path)] = digest
    return output


def anchor_specs() -> list[dict]:
    anchors = []
    for day in (date(2022, 3, 20), date(2022, 3, 21)):
        for hour in (1, 5, 9, 13, 17, 21):
            local = datetime.combine(day, dt_time(hour=hour), tzinfo=UTC8)
            start_ms = int(local.timestamp() * 1000)
            anchors.append({
                "anchor_id": f"{day.isoformat()}T{hour:02d}:00:00+08:00",
                "local": local.isoformat(),
                "epoch_ms": start_ms,
                "reference_intervals": {str(minutes): [start_ms - minutes * 60_000, start_ms] for minutes in LOOKBACKS},
                "query_slices": [[start_ms + offset * 60_000, start_ms + (offset + 5) * 60_000] for offset in AGING_OFFSETS],
            })
    return anchors


def _root_intervals(anchors: Iterable[Mapping]) -> list[tuple[int, int]]:
    intervals = []
    for anchor in anchors:
        intervals.append((int(anchor["epoch_ms"]) - 60 * 60_000, int(anchor["epoch_ms"]) + 30 * 60_000))
    return intervals


def collect_observations(index_path: Path, components: list[str], anchors: list[dict]) -> tuple[dict[tuple[str, str], dict], dict]:
    """Collect each distinct root and its complete indexed trace once."""
    conn = open_index(index_path)
    root_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    raw_root_rows = 0
    try:
        for start_ms, end_ms in _root_intervals(anchors):
            roots = fetch_frontend_roots(conn, start_ms, end_ms, components)
            raw_root_rows += len(roots)
            for key, rows in group_root_rows(roots).items():
                seen = {(str(row.get("source_file", "")), int(row.get("source_record", 0) or 0)) for row in root_groups[key]}
                root_groups[key].extend(row for row in rows if (str(row.get("source_file", "")), int(row.get("source_record", 0) or 0)) not in seen)
        trace_ids = sorted({key[0] for key in root_groups})
        keys_by_trace: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for key in root_groups:
            keys_by_trace[key[0]].append(key)
        records = {}
        trace_rows = 0
        trace_ids_retrieved = 0
        for offset in range(0, len(trace_ids), 300):
            trace_chunk = trace_ids[offset:offset + 300]
            traces = fetch_traces(conn, trace_chunk)
            trace_ids_retrieved += len(traces)
            trace_rows += sum(len(rows) for rows in traces.values())
            for trace_id in trace_chunk:
                for key in keys_by_trace.get(trace_id, []):
                    if key in root_groups:
                        records[key] = build_observation(root_groups.pop(key), traces.get(trace_id, []))
            if not root_groups:
                break
        # A missing trace in a validated index remains an explicit unresolved
        # observation rather than disappearing from denominators.
        for key, rows in root_groups.items():
            records[key] = build_observation(rows, [])
    finally:
        conn.close()
    return records, {
        "raw_root_rows": raw_root_rows,
        "distinct_root_identities": len(records),
        "trace_ids_retrieved": trace_ids_retrieved,
        "trace_rows_retrieved": trace_rows,
        "trace_closure_failures": sum(1 for record in records.values() if record["structure_status"] == "unknown_structure"),
        "cross_file_boundary_count": sum(1 for record in records.values() if record.get("flags", {}).get("cross_file_boundary")),
        "identity_ambiguity_count": sum(1 for record in records.values() if not record.get("identity_resolved")),
    }


def _replica_matches(record: Mapping, replica_policy: str, anchor_component: str | None, allowlist: list[str]) -> bool:
    if replica_policy == "pooled":
        return str(record.get("cmdb_id", "")) in set(allowlist)
    if replica_policy == "same_replica":
        # The same-replica key is applied per query observation below.  All
        # explicit frontend components remain in the denominator and no
        # majority replica is silently selected.
        return str(record.get("cmdb_id", "")) in set(allowlist)
    raise ValueError(f"unknown replica policy {replica_policy}")


def _root_component_for_anchor(records: Iterable[Mapping], start_ms: int) -> str | None:
    counts = Counter(str(record.get("cmdb_id", "")) for record in records if int(record.get("timestamp_ms", -1)) >= start_ms and int(record.get("timestamp_ms", -1)) < start_ms + PRIMARY_QUERY_MINUTES * 60_000)
    return counts.most_common(1)[0][0] if counts else None


def _record_in_interval(record: Mapping, interval: tuple[int, int]) -> bool:
    timestamp = int(record.get("timestamp_ms", -1))
    return int(interval[0]) <= timestamp < int(interval[1])


def _reference_boundary_reason(record: Mapping, anchor_ms: int) -> str | None:
    endpoint = record.get("max_recorded_end_us")
    if endpoint is None:
        return "unresolved_endpoint"
    if int(endpoint) >= int(anchor_ms) * 1000:
        return "endpoint_reaches_anchor"
    return None


def _eligible_signature(record: Mapping, mode: str) -> tuple[str | None, str | None]:
    if mode in {"C1", "C2"} and record.get("structure_status") == "unknown_structure":
        return None, "unknown_structure"
    return signature_key(record["signature"][mode]), None


def _policy_key(record: Mapping, mode: str, replica_policy: str) -> tuple[str | None, str | None]:
    key, reason = _eligible_signature(record, mode)
    if key is not None and replica_policy == "same_replica":
        key = f"component={record.get('cmdb_id', '')}\x1f{key}"
    return key, reason


def _duration_rows(records: Iterable[Mapping]) -> list[dict]:
    return [dict(record) for record in records if record.get("duration_ms") is not None]


def _cached_reference_stats(values: list[float]) -> dict:
    ordered = sorted(values)
    if not ordered:
        return {"n": 0, "median_ms": None, "q1_ms": None, "q3_ms": None, "mad_ms": None}
    median = statistics.median(ordered)
    quartiles = statistics.quantiles(ordered, n=4, method="inclusive") if len(ordered) > 1 else [median, median, median]
    return {"n": len(ordered), "median_ms": median, "q1_ms": quartiles[0], "q3_ms": quartiles[2], "mad_ms": statistics.median([abs(value - median) for value in ordered])}


def _compare_cached(observed: object, stats: Mapping) -> dict:
    try:
        value = float(observed)
    except (TypeError, ValueError):
        value = math.nan
    median = stats.get("median_ms")
    mad = stats.get("mad_ms")
    if not math.isfinite(value) or median is None:
        return {"observed_ms": None if not math.isfinite(value) else value, "n": int(stats.get("n", 0)), "median_ms": median, "q1_ms": stats.get("q1_ms"), "q3_ms": stats.get("q3_ms"), "mad_ms": mad, "absolute_excess_ms": None, "ratio": None, "standardized_departure": None, "undefined_reasons": ["invalid_observed" if not math.isfinite(value) else "empty_reference"]}
    excess = value - float(median)
    return {"observed_ms": value, "n": int(stats.get("n", 0)), "median_ms": median, "q1_ms": stats.get("q1_ms"), "q3_ms": stats.get("q3_ms"), "mad_ms": mad, "absolute_excess_ms": excess, "ratio": value / median if median > 0 else None, "standardized_departure": excess / (1.4826 * mad) if mad and mad > 0 else None, "undefined_reasons": (["zero_reference_median"] if not median or median <= 0 else []) + (["zero_reference_mad"] if not mad or mad <= 0 else [])}


def _cohort_summary(refs: list[dict], queries: list[dict], lookback_minutes: int, *, ref_start_ms: int, ref_end_ms: int) -> tuple[dict, list[dict], dict]:
    support = support_diagnostics(refs, lookback_minutes)
    reference_durations = [float(row["duration_ms"]) for row in refs if row.get("duration_ms") is not None]
    cached_stats = _cached_reference_stats(reference_durations)
    uncertainty = bootstrap_median(refs, seed=BOOTSTRAP_SEED, replicates=BOOTSTRAP_REPLICATES, start_ms=ref_start_ms, end_ms=ref_end_ms)
    comparisons = []
    for query in queries:
        comparison = _compare_cached(query.get("duration_ms"), cached_stats)
        comparisons.append({
            "trace_id": query.get("trace_id"), "span_id": query.get("span_id"),
            "source": query.get("source"), **comparison,
        })
    supported = bool(support["supported"])
    positive = [row for row in comparisons if row.get("absolute_excess_ms") is not None and row["absolute_excess_ms"] > 0]
    ref_sorted = sorted(refs, key=lambda row: int(row.get("timestamp_ms", 0)))
    ref_values = reference_durations
    ref_median = statistics.median(ref_values) if ref_values else None
    ref_q1 = statistics.quantiles(ref_values, n=4, method="inclusive")[0] if len(ref_values) > 1 else ref_median
    ref_q3 = statistics.quantiles(ref_values, n=4, method="inclusive")[2] if len(ref_values) > 1 else ref_median
    ref_mad = statistics.median([abs(value - ref_median) for value in ref_values]) if ref_values else None
    by_minute: dict[int, list[float]] = defaultdict(list)
    for row in ref_sorted:
        if row.get("duration_ms") is not None:
            by_minute[int(row.get("timestamp_ms", 0)) // 60_000].append(float(row["duration_ms"]))
    midpoint = int(ref_start_ms) + (int(ref_end_ms) - int(ref_start_ms)) // 2
    earlier = [float(row["duration_ms"]) for row in ref_sorted if row.get("duration_ms") is not None and int(row.get("timestamp_ms", 0)) < midpoint]
    later = [float(row["duration_ms"]) for row in ref_sorted if row.get("duration_ms") is not None and int(row.get("timestamp_ms", 0)) >= midpoint]
    lomo = []
    if by_minute:
        for minute in sorted(by_minute):
            remain = [value for key, values in by_minute.items() if key != minute for value in values]
            lomo.append({"minute": minute, "center_ms": statistics.median(remain) if remain else None})
    return {
        "reference_support": support,
        "reference_support_sensitivity": {str(min_count): support_diagnostics(refs, lookback_minutes, min_count=int(min_count)) for min_count in (50, 100)},
        "reference_uncertainty": uncertainty,
        "reference_statistics": {"n": len(ref_values), "median_ms": ref_median, "q1_ms": ref_q1, "q3_ms": ref_q3, "mad_ms": ref_mad, "min_ms": min(ref_values) if ref_values else None, "max_ms": max(ref_values) if ref_values else None, "replica_counts": dict(Counter(str(row.get("cmdb_id", "")) for row in refs)), "earlier_half_median_ms": statistics.median(earlier) if earlier else None, "later_half_median_ms": statistics.median(later) if later else None, "half_change_ms": (statistics.median(later) - statistics.median(earlier)) if earlier and later else None, "leave_one_minute_out": lomo},
        "query_count": len(queries),
        "supported_query_count": len(comparisons) if supported else 0,
        "comparison_count": len(comparisons) if supported else 0,
        "positive_excess_count": len(positive) if supported else 0,
        "median_query_excess_ms": statistics.median([row["absolute_excess_ms"] for row in comparisons if row.get("absolute_excess_ms") is not None]) if supported and comparisons else None,
    }, comparisons if supported else [], {
        "reference_membership_hash": stable_membership_hash(refs),
        "query_membership_hash": stable_membership_hash(queries),
    }


def _structural_channel(ref_records: list[dict], query_records: list[dict], anchor_component: str | None, allowlist: list[str], anchor_ms: int, lookback_minutes: int) -> dict:
    ref_set: Counter[str] = Counter()
    query_set: Counter[str] = Counter()
    ref_children: Counter[str] = Counter()
    query_children: Counter[str] = Counter()
    ref_shapes: Counter[tuple[str, str, str]] = Counter()
    query_shapes: Counter[tuple[str, str, str]] = Counter()
    ref_unknown = 0
    query_unknown = 0
    for record in ref_records:
        if not record.get("identity_resolved"):
            continue
        if _reference_boundary_reason(record, anchor_ms) is not None:
            continue
        ref_sig = signature_key(record["signature"]["C0"])
        ref_set[ref_sig] += 1
        ref_shapes[(ref_sig, signature_key(record["signature"]["C1"]), signature_key(record["signature"]["C2"]))] += 1
        if record.get("structure_status") == "unknown_structure":
            ref_unknown += 1
        for child in (record.get("direct_children") or []):
            ref_children[json.dumps([child.get("operation_name", ""), child.get("type", "")], separators=(",", ":"))] += 1
    for record in query_records:
        query_set[signature_key(record["signature"]["C0"])] += 1
        query_sig = signature_key(record["signature"]["C0"])
        query_shapes[(query_sig, signature_key(record["signature"]["C1"]), signature_key(record["signature"]["C2"]))] += 1
        if record.get("structure_status") == "unknown_structure":
            query_unknown += 1
        for child in (record.get("direct_children") or []):
            query_children[json.dumps([child.get("operation_name", ""), child.get("type", "")], separators=(",", ":"))] += 1
    ref_c1 = Counter()
    ref_c2 = Counter()
    query_c1 = Counter()
    query_c2 = Counter()
    for (c0, c1, c2), count in ref_shapes.items():
        ref_c1[json.dumps([c0, c1], separators=(",", ":"))] += count
        ref_c2[json.dumps([c0, c2], separators=(",", ":"))] += count
    for (c0, c1, c2), count in query_shapes.items():
        query_c1[json.dumps([c0, c1], separators=(",", ":"))] += count
        query_c2[json.dumps([c0, c2], separators=(",", ":"))] += count
    return {
        "reference_c0_signature_frequencies": dict(ref_set),
        "query_c0_signature_frequencies": dict(query_set),
        "reference_direct_child_pair_frequencies": dict(ref_children),
        "query_direct_child_pair_frequencies": dict(query_children),
        "reference_c0_to_c1_c2_shape_frequencies": {"C1": dict(ref_c1), "C2": dict(ref_c2)},
        "query_c0_to_c1_c2_shape_frequencies": {"C1": dict(query_c1), "C2": dict(query_c2)},
        "novel_query_c1_shapes": sorted({(c0, c1) for c0, c1, _ in query_shapes} - {(c0, c1) for c0, c1, _ in ref_shapes}),
        "novel_query_c2_shapes": sorted({(c0, c2) for c0, _, c2 in query_shapes} - {(c0, c2) for c0, _, c2 in ref_shapes}),
        "unmatched_query_c1_count": sum(n for (c0, c1, _), n in query_shapes.items() if (c0, c1) not in {(r0, r1) for r0, r1, _ in ref_shapes}),
        "unmatched_query_c2_count": sum(n for (c0, _, c2), n in query_shapes.items() if (c0, c2) not in {(r0, r2) for r0, _, r2 in ref_shapes}),
        "novel_query_c0_signatures": sorted(set(query_set) - set(ref_set)),
        "unmatched_query_c0_count": sum(count for key, count in query_set.items() if key not in ref_set),
        "reference_unknown_structure_count": ref_unknown,
        "query_unknown_structure_count": query_unknown,
        "empty_recorded_children_reference_count": sum(1 for row in ref_records if row.get("structure_status") == "empty_recorded_children"),
        "empty_recorded_children_query_count": sum(1 for row in query_records if row.get("structure_status") == "empty_recorded_children"),
    }


def evaluate_policy(records: Mapping[tuple[str, str], Mapping], anchor: Mapping, lookback_minutes: int, mode: str, replica_policy: str, allowlist: list[str]) -> dict:
    """Evaluate one connected policy cell and return all reviewable tables.

    This is the selector/comparator seam used by controlled checks.  Every
    query root is retained; same-replica matching is a per-observation cohort
    key, while pooled matching uses the explicit allowlist.  Identity and
    structure uncertainty remain separate fields.
    """
    anchor_ms = int(anchor["epoch_ms"])
    ref_interval = tuple(anchor["reference_intervals"][str(lookback_minutes)])
    primary_interval = (anchor_ms, anchor_ms + PRIMARY_QUERY_MINUTES * 60_000)
    all_references = [record for record in records.values() if _record_in_interval(record, ref_interval) and _replica_matches(record, replica_policy, None, allowlist)]
    primary_query = [record for record in records.values() if _record_in_interval(record, primary_interval) and _replica_matches(record, replica_policy, None, allowlist)]
    cohorts: dict[str, list[dict]] = defaultdict(list)
    query_cohorts: dict[str, list[dict]] = defaultdict(list)
    ref_excluded = Counter()
    boundary_durations = []
    memberships: list[dict] = []
    for record in all_references:
        if not record.get("identity_resolved"):
            ref_excluded["unresolved_identity"] += 1
            memberships.append({"anchor_id": anchor["anchor_id"], "lookback_minutes": lookback_minutes, "mode": mode, "replica_policy": replica_policy, "role": "reference", "root_key": record["root_key"], "cohort_key": None, "status": "excluded", "reason": "unresolved_identity", "identity_resolved": False, "source": record["source"]})
            continue
        if record.get("duration_ms") is None:
            ref_excluded["invalid_duration"] += 1
            memberships.append({"anchor_id": anchor["anchor_id"], "lookback_minutes": lookback_minutes, "mode": mode, "replica_policy": replica_policy, "role": "reference", "root_key": record["root_key"], "cohort_key": None, "status": "excluded", "reason": "invalid_duration", "identity_resolved": True, "source": record["source"]})
            continue
        boundary = _reference_boundary_reason(record, anchor_ms)
        key, shape_reason = _policy_key(record, mode, replica_policy)
        if boundary:
            ref_excluded[boundary] += 1
            if record.get("duration_ms") is not None:
                boundary_durations.append(float(record["duration_ms"]))
        elif shape_reason:
            ref_excluded[shape_reason] += 1
        elif key is not None:
            cohorts[key].append(dict(record))
        memberships.append({"anchor_id": anchor["anchor_id"], "lookback_minutes": lookback_minutes, "mode": mode, "replica_policy": replica_policy, "role": "reference", "root_key": record["root_key"], "cohort_key": key, "status": "included" if key is not None and not boundary and not shape_reason else "excluded", "reason": boundary or shape_reason, "source": record["source"]})
    for record in primary_query:
        key, shape_reason = _policy_key(record, mode, replica_policy)
        if key is not None:
            query_cohorts[key].append(dict(record))
        query_status = "candidate" if key is not None and record.get("identity_resolved") and record.get("duration_ms") is not None else ("unresolved_identity" if not record.get("identity_resolved") else ("unavailable_duration" if record.get("duration_ms") is None else "unmatched"))
        memberships.append({"anchor_id": anchor["anchor_id"], "lookback_minutes": lookback_minutes, "mode": mode, "replica_policy": replica_policy, "role": "query", "root_key": record["root_key"], "cohort_key": key, "status": query_status, "reason": shape_reason or ("invalid_duration" if record.get("duration_ms") is None else None), "identity_resolved": bool(record.get("identity_resolved")), "source": record["source"]})
    uncertainty: list[dict] = []
    comparisons: list[dict] = []
    support_by_key: dict[str, dict] = {}
    width_checks: list[dict] = []
    zero_median_count = 0
    for key in sorted(set(cohorts) | set(query_cohorts)):
        refs = cohorts.get(key, [])
        # Ambiguous/missing query identities stay in coverage bookkeeping but
        # cannot become a duration comparison.
        queries = [row for row in query_cohorts.get(key, []) if row.get("identity_resolved") and row.get("duration_ms") is not None]
        summary, cohort_comparisons, hashes = _cohort_summary(refs, queries, lookback_minutes, ref_start_ms=int(ref_interval[0]), ref_end_ms=int(ref_interval[1]))
        supported = bool(summary["reference_support"]["supported"])
        support_by_key[key] = {"supported": supported, "summary": summary, "stats": summary["reference_statistics"]}
        if supported:
            for row in cohort_comparisons:
                comparisons.append({"anchor_id": anchor["anchor_id"], "lookback_minutes": lookback_minutes, "mode": mode, "replica_policy": replica_policy, "cohort_key": key, **row})
        median = summary["reference_statistics"].get("median_ms")
        positive_queries = sum(1 for row in queries if row.get("duration_ms") is not None and median is not None and median > 0) if supported else 0
        if median is not None and median > 0:
            width_checks.append({"cohort_key": key, "assessed": summary["reference_uncertainty"].get("usable_replicates", 0) >= 190, "usable_replicates": summary["reference_uncertainty"].get("usable_replicates", 0), "width_ms": summary["reference_uncertainty"].get("full_width_ms"), "median_ms": median, "within_width_gate": summary["reference_uncertainty"].get("full_width_ms") is not None and summary["reference_uncertainty"]["full_width_ms"] <= 0.4 * median, "positive_query_count": positive_queries})
        elif median == 0:
            zero_median_count += 1
        uncertainty.append({"anchor_id": anchor["anchor_id"], "lookback_minutes": lookback_minutes, "mode": mode, "replica_policy": replica_policy, "cohort_key": key, "summary": summary, "membership_hashes": hashes})
    identity_resolved = [row for row in primary_query if row.get("identity_resolved")]
    query_unknown_identity = len(primary_query) - len(identity_resolved)
    query_unknown_structure = sum(1 for row in identity_resolved if row.get("structure_status") == "unknown_structure")
    query_unavailable_duration = sum(1 for row in identity_resolved if row.get("duration_ms") is None)
    query_unresolved_completion = sum(1 for row in primary_query if row.get("query_completion_status") != "known_complete")
    supported_query_count = sum(1 for row in comparisons)
    coverage = supported_query_count / len(identity_resolved) if identity_resolved else 0.0
    positive_comparisons = [row for row in comparisons if row.get("absolute_excess_ms") is not None and row["absolute_excess_ms"] > 0]
    positive_comparisons.sort(key=lambda row: (-float(row["absolute_excess_ms"]), str(row.get("trace_id", "")), str(row.get("span_id", ""))))
    structural = _structural_channel(all_references, primary_query, None, allowlist, anchor_ms, lookback_minutes)
    adjacent_centers = {}
    for adjacent in LOOKBACKS:
        interval = (anchor_ms - adjacent * 60_000, anchor_ms)
        grouped: dict[str, list[float]] = defaultdict(list)
        for row in records.values():
            if _record_in_interval(row, interval) and row.get("identity_resolved") and _replica_matches(row, replica_policy, None, allowlist) and _reference_boundary_reason(row, anchor_ms) is None:
                key, reason = _policy_key(row, mode, replica_policy)
                if key is not None and row.get("duration_ms") is not None:
                    grouped[key].append(float(row["duration_ms"]))
        adjacent_centers[str(adjacent)] = {key: statistics.median(values) for key, values in grouped.items() if values}
    aging = []
    aging_comparisons = []
    for offset, query_interval in zip(AGING_OFFSETS, anchor["query_slices"]):
        aged = [record for record in records.values() if _record_in_interval(record, tuple(query_interval)) and _replica_matches(record, replica_policy, None, allowlist)]
        aged_resolved = [row for row in aged if row.get("identity_resolved")]
        aged_supported = []
        for record in aged_resolved:
            key, reason = _policy_key(record, mode, replica_policy)
            if key is None or not support_by_key.get(key, {}).get("supported"):
                continue
            refs = cohorts.get(key, [])
            cmp = _compare_cached(record.get("duration_ms"), support_by_key[key]["stats"])
            if cmp.get("absolute_excess_ms") is not None:
                aged_supported.append(cmp)
                aging_comparisons.append({"anchor_id": anchor["anchor_id"], "lookback_minutes": lookback_minutes, "mode": mode, "replica_policy": replica_policy, "offset_minutes": offset, "cohort_key": key, "trace_id": record.get("trace_id"), "span_id": record.get("span_id"), **cmp})
        aging.append({"offset_minutes": offset, "query_count": len(aged), "resolved_query_count": len(aged_resolved), "unknown_identity_count": len(aged) - len(aged_resolved), "unknown_structure_count": sum(1 for row in aged_resolved if row.get("structure_status") == "unknown_structure"), "supported_query_count": len(aged_supported), "request_coverage": len(aged_supported) / len(aged_resolved) if aged_resolved else 0.0, "median_absolute_excess_ms": statistics.median([row["absolute_excess_ms"] for row in aged_supported if row.get("absolute_excess_ms") is not None]) if aged_supported else None})
    policy_row = {
        "anchor_id": anchor["anchor_id"], "anchor_epoch_ms": anchor_ms, "mode": mode, "replica_policy": replica_policy, "lookback_minutes": lookback_minutes,
        "reference_raw_count": len(all_references), "reference_raw_record_count": sum(int(row.get("raw_root_records", 1)) for row in all_references), "reference_included_count": sum(len(rows) for rows in cohorts.values()), "reference_excluded_counts": dict(ref_excluded), "boundary_excluded_count": len(boundary_durations), "boundary_excluded_fraction": len(boundary_durations) / len(all_references) if all_references else 0.0, "boundary_excluded_durations_ms": boundary_durations,
        "cohort_count": len(set(cohorts) | set(query_cohorts)), "query_raw_count": len(primary_query), "query_raw_record_count": sum(int(row.get("raw_root_records", 1)) for row in primary_query), "query_resolved_count": len(identity_resolved), "query_unknown_identity_count": query_unknown_identity, "query_unknown_structure_count": query_unknown_structure, "query_unavailable_duration_count": query_unavailable_duration, "query_unresolved_completion_count": query_unresolved_completion, "supported_query_count": supported_query_count, "request_coverage": coverage, "adjacent_lookback_centers": adjacent_centers,
        "bootstrap_width_checks": width_checks, "zero_median_cohort_count": zero_median_count, "top5_positive_absolute_excess": positive_comparisons[:5], "aging": aging, "structural_channel": structural, "qualifications": ["pooled_replica_policy" if replica_policy == "pooled" else "same_replica_per_query_component", "health_unverified", "unknown_workload_and_configuration"],
    }
    return {"policy": policy_row, "memberships": memberships, "uncertainty": uncertainty, "structure": {"anchor_id": anchor["anchor_id"], "lookback_minutes": lookback_minutes, "mode": mode, "replica_policy": replica_policy, **structural}, "comparisons": comparisons, "aging_comparisons": aging_comparisons, "cost": {"anchor_id": anchor["anchor_id"], "lookback_minutes": lookback_minutes, "mode": mode, "replica_policy": replica_policy}}


def _selection_summary(policy_rows: list[dict]) -> list[dict]:
    """Apply predeclared gates per policy, preserving C0/C2 strata."""
    by_policy: dict[tuple, list[dict]] = defaultdict(list)
    for row in policy_rows:
        by_policy[(row["mode"], row["replica_policy"], row["lookback_minutes"])].append(row)
    decisions = []
    for (mode, replica, lookback), rows in sorted(by_policy.items()):
        total_resolved = sum(row["query_resolved_count"] for row in rows)
        total_supported = sum(row["supported_query_count"] for row in rows)
        coverage = total_supported / total_resolved if total_resolved else 0.0
        primary_pass = sum(1 for row in rows if row["query_resolved_count"] and row["request_coverage"] >= 0.8)
        width_checks = []
        zero_median = 0
        for row in rows:
            width_checks.extend(row.get("bootstrap_width_checks", []))
            zero_median += int(row.get("zero_median_cohort_count", 0))
        assessed = [check for check in width_checks if check.get("positive_query_count", 0) and check.get("assessed")]
        inconclusive = sum(int(check.get("positive_query_count", 0)) for check in width_checks if check.get("positive_query_count", 0) and not check.get("assessed"))
        assessed_observations = sum(int(check.get("positive_query_count", 0)) for check in assessed)
        passing_observations = sum(int(check.get("positive_query_count", 0)) for check in assessed if check.get("within_width_gate"))
        width_pass = bool(assessed_observations and not inconclusive and passing_observations / assessed_observations >= 0.8)
        decisions.append({
            "mode": mode, "replica_policy": replica, "lookback_minutes": lookback,
            "request_coverage": coverage, "primary_windows_at_least_80pct": primary_pass,
            "bootstrap_width_assessed_cohorts": len(assessed),
            "bootstrap_width_assessed_observations": assessed_observations,
            "bootstrap_width_inconclusive_observations": inconclusive,
            "bootstrap_width_gate": width_pass,
            "zero_median_cohort_count": zero_median,
            "gate_1_contract_checks": "pending_external_control_checks",
            "gate_2_coverage": bool(coverage >= 0.9 and primary_pass >= 10),
            "gate_3_uncertainty": width_pass,
            "status": "preliminary_coverage_uncertainty_pass" if coverage >= 0.9 and primary_pass >= 10 and width_pass else "unavailable_or_qualified",
            "qualifications": ["pooled_replica_policy" if replica == "pooled" else "", "observational_health_unverified", "unknown_workload_and_configuration"],
        })
    return decisions


def run_matrix(*, output_dir: Path = DEFAULT_ARTIFACT_ROOT, trace_root: Path = DEFAULT_TRACE_ROOT, index_path: Path = DEFAULT_INDEX, force_index: bool = False) -> dict:
    """Run all 360 policy-anchor cells and emit separate artifact tables."""
    started = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index_summary = build_index(index_path, trace_root, force=force_index)
    validation = validate_index(index_path, trace_root)
    if not validation.get("valid"):
        raise RuntimeError(f"trace index failed validation: {validation}")
    anchors = anchor_specs()
    conn = open_index(index_path)
    try:
        components = discover_frontend_components(conn)
    finally:
        conn.close()
    records, collection_cost = collect_observations(index_path, components, anchors)
    exposure_path = ROOT / "specs" / "001-candidate-recall-experiment" / "development-exposures.json"
    exposure_entry = {"path": str(exposure_path), "exists": exposure_path.exists()}
    if exposure_path.exists():
        exposure_entry["sha256"] = hashlib.sha256(exposure_path.read_bytes()).hexdigest()
        try:
            exposure_entry["content"] = json.loads(exposure_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            exposure_entry["content"] = "unreadable"
    manifest = {
        "version": "short-window-baselining-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_inventory": source_inventory(trace_root),
        "index": validation,
        "anchors": anchors,
        "component_allowlist": components,
        "matching_rules": {"observation": ["blank_parent_frontend_span", "composite_trace_id_span_id"], "modes": MODES, "replica_policies": REPLICA_POLICIES, "duration_raw_unit": "preserved; provisional microseconds", "duration_ms_conversion": "duration_raw / 1000"},
        "support_gates": {"minimum_count": 20, "minimum_bins": "max(3,ceil(L/2))", "minute_concentration": "no minute > half cohort", "sensitivity_counts": [50, 100]},
        "bootstrap": {"seed": BOOTSTRAP_SEED, "replicates": BOOTSTRAP_REPLICATES, "interval": "5th-95th percentile of one-minute block medians"},
        "exclusions": ["reference endpoint >= anchor", "ambiguous identity for shape-conditioned matching", "unresolved shape does not match C1/C2", "no latency/status/fault filtering"],
        "exposure_ledger": {"prior": exposure_entry, "current": "not yet populated; matrix run is descriptive"},
        "code_hashes": _hash_files(Path(__file__).parent.glob("*.py")),
        "collection_cost": collection_cost,
    }
    _write_json(output_dir / "manifest.json", manifest)
    _write_jsonl(output_dir / "observations.jsonl", records.values())

    policy_rows: list[dict] = []
    uncertainty_rows: list[dict] = []
    structure_rows: list[dict] = []
    cost_rows: list[dict] = []
    membership_handle = (output_dir / "memberships.jsonl").open("w", encoding="utf-8")
    comparison_handle = (output_dir / "comparisons.jsonl").open("w", encoding="utf-8")
    aging_handle = (output_dir / "aging_comparisons.jsonl").open("w", encoding="utf-8")
    for anchor in anchors:
        for lookback in LOOKBACKS:
            for mode in MODES:
                for replica_policy in REPLICA_POLICIES:
                    cell = evaluate_policy(records, anchor, lookback, mode, replica_policy, components)
                    policy_rows.append(cell["policy"])
                    for row in cell["memberships"]:
                        membership_handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=_json_default) + "\n")
                    uncertainty_rows.extend(cell["uncertainty"])
                    structure_rows.append(cell["structure"])
                    for row in cell["comparisons"]:
                        comparison_handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=_json_default) + "\n")
                    for row in cell.get("aging_comparisons", []):
                        aging_handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=_json_default) + "\n")
                    cell["cost"].update({"cost_scope": "shared_collection_once; do_not_sum_across_policy_cells", "rows_scanned": collection_cost["raw_root_rows"] + collection_cost["trace_rows_retrieved"], "rows_retrieved": collection_cost["trace_rows_retrieved"], "trace_closure_failures": collection_cost["trace_closure_failures"], "index_bytes": Path(index_path).stat().st_size if Path(index_path).exists() else None})
                    cost_rows.append(cell["cost"])
    membership_handle.close()
    comparison_handle.close()
    aging_handle.close()
    decisions = _selection_summary(policy_rows)
    # Memberships and per-request comparisons were streamed during evaluation
    # to keep the 18M-row study bounded in memory.
    _write_jsonl(output_dir / "coverage.jsonl", policy_rows)
    _write_jsonl(output_dir / "uncertainty.jsonl", uncertainty_rows)
    _write_jsonl(output_dir / "structure.jsonl", structure_rows)
    _write_jsonl(output_dir / "cost.jsonl", cost_rows)
    _write_json(output_dir / "decision.json", {"policies": decisions, "selection_status": "inconclusive_pending_independent_review", "staged_confirmation": "not_run"})
    _write_json(output_dir / "run_summary.json", {"policy_anchor_cells": len(policy_rows), "expected_policy_anchor_cells": 360, "observations": len(records), "elapsed_seconds": time.perf_counter() - started, "index": index_summary, "artifacts": {str(path.name): path.stat().st_size for path in sorted(output_dir.iterdir()) if path.is_file()}})
    return {"output_dir": str(output_dir), "cells": len(policy_rows), "observations": len(records), "decisions": decisions, "elapsed_seconds": time.perf_counter() - started}


def run_pilot(*, output_dir: Path, trace_root: Path = DEFAULT_TRACE_ROOT, index_path: Path = DEFAULT_INDEX, force_index: bool = False) -> dict:
    """Run the protocol's declared first slice without selecting a scope."""
    started = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index_summary = build_index(index_path, trace_root, force=force_index)
    validation = validate_index(index_path, trace_root)
    if not validation.get("valid"):
        raise RuntimeError(f"trace index failed validation: {validation}")
    anchors = anchor_specs()
    conn = open_index(index_path)
    try:
        components = discover_frontend_components(conn)
    finally:
        conn.close()
    records, collection_cost = collect_observations(index_path, components, anchors)
    cells = [evaluate_policy(records, anchor, 15, "C1", "same_replica", components) for anchor in anchors]
    manifest = {"version": "short-window-baselining-v1-pilot", "created_at_utc": datetime.now(timezone.utc).isoformat(), "source_inventory": source_inventory(trace_root), "index": validation, "anchors": anchors, "component_allowlist": components, "policy": {"lookback_minutes": 15, "mode": "C1", "replica_policy": "same_replica", "supported_statistic": "median and signed absolute excess"}, "collection_cost": collection_cost, "code_hashes": _hash_files(Path(__file__).parent.glob("*.py")), "status": "pilot_only_no_selection"}
    _write_json(output_dir / "manifest.json", manifest)
    _write_jsonl(output_dir / "coverage.jsonl", [cell["policy"] for cell in cells])
    _write_jsonl(output_dir / "memberships.jsonl", [row for cell in cells for row in cell["memberships"]])
    _write_jsonl(output_dir / "uncertainty.jsonl", [row for cell in cells for row in cell["uncertainty"]])
    _write_jsonl(output_dir / "structure.jsonl", [cell["structure"] for cell in cells])
    _write_jsonl(output_dir / "comparisons.jsonl", [row for cell in cells for row in cell["comparisons"]])
    _write_json(output_dir / "run_summary.json", {"cells": len(cells), "observations": len(records), "elapsed_seconds": time.perf_counter() - started, "status": "pilot_only_no_selection"})
    return {"output_dir": str(output_dir), "cells": len(cells), "observations": len(records), "elapsed_seconds": time.perf_counter() - started}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--trace-root", type=Path, default=DEFAULT_TRACE_ROOT)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--force-index", action="store_true")
    parser.add_argument("--pilot", action="store_true", help="run the declared C1/same-replica/15-minute first slice only")
    args = parser.parse_args(argv)
    if args.pilot:
        result = run_pilot(output_dir=args.output_dir / "pilot", trace_root=args.trace_root, index_path=args.index, force_index=args.force_index)
    else:
        result = run_matrix(output_dir=args.output_dir, trace_root=args.trace_root, index_path=args.index, force_index=args.force_index)
    print(json.dumps({"output_dir": result["output_dir"], "cells": result["cells"], "observations": result["observations"], "elapsed_seconds": result["elapsed_seconds"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
