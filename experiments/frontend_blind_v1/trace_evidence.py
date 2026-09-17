"""Deterministic parent-link and interval evidence for ranked traces."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable, Mapping


def interval_union(intervals: Iterable[tuple[int, int]], clip: tuple[int, int] | None = None) -> int:
    values = []
    for start, end in intervals:
        if clip:
            start, end = max(start, clip[0]), min(end, clip[1])
        if end > start:
            values.append((start, end))
    if not values:
        return 0
    values.sort()
    covered = 0
    current_start, current_end = values[0]
    for start, end in values[1:]:
        if start > current_end:
            covered += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    return covered + current_end - current_start


def _span(row: Mapping) -> dict:
    copy = dict(row)
    copy["timestamp_ms"] = int(row["timestamp"])
    # Trace timestamps are milliseconds while duration is microseconds in the
    # source CSV. Keep raw duration for provenance and use microseconds for
    # interval arithmetic to avoid silently introducing a 1000x error.
    copy["duration_us"] = int(row["duration"])
    copy["duration_ms"] = copy["duration_us"] / 1000.0
    copy["start_us"] = copy["timestamp_ms"] * 1000
    copy["end_us"] = copy["start_us"] + copy["duration_us"]
    copy["end_ms"] = copy["end_us"] / 1000.0
    return copy


def evidence_for_trace(root: Mapping, spans: Iterable[Mapping], *, max_depth: int = 8) -> dict:
    root = _span(root)
    all_spans = [_span(row) for row in spans]
    by_id: dict[str, list[dict]] = defaultdict(list)
    for row in all_spans:
        by_id[str(row.get("parent_span", ""))].append(row)
    for values in by_id.values():
        values.sort(key=lambda row: (-row["duration_ms"], str(row["cmdb_id"]), str(row["span_id"])))
    ids = [str(row["span_id"]) for row in all_spans]
    duplicate_span_ids = sorted({span_id for span_id in ids if ids.count(span_id) > 1})
    known_ids = set(ids)
    child_ids = {str(row["span_id"]): row for row in all_spans}
    root_id = str(root["span_id"])
    flags = {
        "duplicate_span_ids": duplicate_span_ids,
        "missing_parents": sorted({str(row["parent_span"]) for row in all_spans if row.get("parent_span") and str(row["parent_span"]) not in known_ids}),
        "roots": sorted(str(row["span_id"]) for row in all_spans if not row.get("parent_span")),
        "trace_id_mismatch": sorted({str(row.get("trace_id")) for row in all_spans if str(row.get("trace_id")) != str(root.get("trace_id"))}),
        "interval_inversions": sorted(str(row["span_id"]) for row in all_spans if row["duration_ms"] < 0),
        "depth_exceeded": False,
        "cycles": [],
    }
    parent_by_id = {str(row["span_id"]): str(row.get("parent_span", "")) for row in all_spans}
    for start_id in parent_by_id:
        seen = []
        current = start_id
        while current and current in parent_by_id:
            if current in seen:
                cycle = seen[seen.index(current):] + [current]
                if cycle not in flags["cycles"]:
                    flags["cycles"].append(cycle)
                break
            seen.append(current)
            current = parent_by_id[current]
    direct = list(by_id.get(root_id, []))
    root_interval = (root["start_us"], root["end_us"])
    direct_union = interval_union(((row["start_us"], row["end_us"]) for row in direct), root_interval)
    largest = direct[0] if direct else None
    linked_receivers = []
    if largest:
        linked_receivers = [child for child in by_id.get(str(largest["span_id"]), []) if child["cmdb_id"] != largest["cmdb_id"]]
    paths: list[dict] = []
    visited: set[str] = set()
    queue = deque([(root_id, [root_id], 0)])
    while queue:
        parent_id, path, depth = queue.popleft()
        if depth >= max_depth:
            if by_id.get(parent_id):
                flags["depth_exceeded"] = True
            continue
        for child in by_id.get(parent_id, []):
            child_id = str(child["span_id"])
            if child_id in path:
                flags["cycles"].append(path + [child_id])
                continue
            child_path = path + [child_id]
            paths.append({
                "trace_id": str(root.get("trace_id", "")),
                "span_id": child_id,
                "component": str(child["cmdb_id"]),
                "depth": depth + 1,
                "path_span_ids": child_path,
                "duration_ms": child["duration_ms"],
                "parent_span": parent_id,
                "source_file": child.get("source_file"),
                "source_record": child.get("source_record"),
            })
            if child_id in visited:
                continue
            visited.add(child_id)
            queue.append((child_id, child_path, depth + 1))
    receiver_rows = [row for row in paths if row["component"] != str(root["cmdb_id"])]
    component_order: list[str] = []
    for row in receiver_rows:
        component = row["component"]
        if component not in component_order:
            component_order.append(component)
    # Parent-path discovery follows the ranked request order. Within the same
    # discovery point, retain the largest observed child first and use the
    # component ID as the deterministic final key.
    component_order = sorted(component_order, key=lambda comp: (
        min((index for index, row in enumerate(receiver_rows) if row["component"] == comp), default=999999),
        -max((row["duration_ms"] for row in receiver_rows if row["component"] == comp), default=0),
        comp,
    ))
    child_uncovered = None
    receiver_uncovered = {}
    if largest:
        child_interval = (largest["start_us"], largest["end_us"])
        child_union = interval_union(((row["start_us"], row["end_us"]) for row in by_id.get(str(largest["span_id"]), [])), child_interval)
        child_uncovered = max(0, largest["duration_us"] - child_union) / 1000.0
        receiver_intervals = [(row["start_us"], row["end_us"]) for row in linked_receivers]
        for receiver in linked_receivers:
            receiver_children = by_id.get(str(receiver["span_id"]), [])
            receiver_clip = (receiver["start_us"], receiver["end_us"])
            receiver_union = interval_union(((child["start_us"], child["end_us"]) for child in receiver_children), receiver_clip)
            receiver_uncovered[str(receiver["span_id"])] = {
                "direct_child_union_ms": receiver_union / 1000.0,
                "uncovered_ms": max(0, receiver["duration_us"] - receiver_union) / 1000.0,
                "client_minus_receiver_ms": max(0, largest["duration_us"] - interval_union([(receiver["start_us"], receiver["end_us"])], child_interval)) / 1000.0,
            }
    for row in paths:
        source = child_ids.get(row["span_id"])
        if source:
            row.update({"operation_name": source.get("operation_name"), "timestamp": source.get("timestamp"), "duration": source.get("duration"), "start_us": source.get("start_us"), "end_us": source.get("end_us")})
    return {
        "trace_id": str(root.get("trace_id", "")),
        "root": root,
        "recorded_span_count": len(all_spans),
        "spans": all_spans,
        "flags": flags,
        "intervals": {
            "root_direct_child_union_ms": direct_union / 1000.0,
            "root_direct_child_uncovered_ms": max(0, root["duration_us"] - direct_union) / 1000.0,
            "child_uncovered_ms": child_uncovered,
            "receiver_uncovered_ms": receiver_uncovered,
        },
        "immediate_attribution": {
            "largest_direct_child": largest,
            "linked_receivers": linked_receivers,
            "receiver_interval_accounting": receiver_uncovered,
        },
        "dependency_reachability": {
            "components": component_order,
            "paths": paths,
            "prefixes": {str(size): component_order[:size] for size in (1, 3, 5)},
        },
        "provenance": sorted({(str(row.get("source_file")), int(row.get("source_record", 0))) for row in all_spans}),
    }


def build_evidence(roots: Iterable[Mapping], traces: Mapping[str, list[Mapping]], *, max_depth: int = 8) -> dict:
    records = []
    for root in roots:
        trace_id = str(root["trace_id"])
        records.append(evidence_for_trace(root, traces.get(trace_id, []), max_depth=max_depth))
    components: list[str] = []
    paths: list[dict] = []
    for record in records:
        for component in record["dependency_reachability"]["components"]:
            if component not in components:
                components.append(component)
        paths.extend(record["dependency_reachability"]["paths"])
    return {"traces": records, "component_shortlist": components, "paths": paths}
