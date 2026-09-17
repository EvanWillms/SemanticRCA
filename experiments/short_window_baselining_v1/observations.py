"""Observation construction from complete indexed traces."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable, Mapping, Sequence

from .contracts import signature_for_root


def _identity(row: Mapping) -> tuple[str, str]:
    return (str(row.get("trace_id", "")), str(row.get("span_id", "")))


def _duration_us(row: Mapping) -> int | None:
    value = row.get("duration_us", row.get("duration"))
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _start_ms(row: Mapping) -> int:
    return int(row.get("timestamp_ms", row.get("timestamp")))


def _source(row: Mapping) -> dict:
    return {
        "source_file": str(row.get("source_file", "")),
        "source_record": int(row.get("source_record", 0) or 0),
        "source_header": int(row.get("source_header", 1) or 1),
    }


def _cycle_ids(parent_by_id: Mapping[str, str]) -> list[list[str]]:
    cycles: list[list[str]] = []
    for start in parent_by_id:
        path: list[str] = []
        seen: dict[str, int] = {}
        current = start
        while current and current in parent_by_id:
            if current in seen:
                cycle = path[seen[current]:] + [current]
                if cycle not in cycles:
                    cycles.append(cycle)
                break
            seen[current] = len(path)
            path.append(current)
            current = parent_by_id[current]
    return cycles


def build_observation(root_rows: Sequence[Mapping], trace_rows: Iterable[Mapping]) -> dict:
    """Build one root observation while retaining every retrieval qualification."""
    roots = [dict(row) for row in root_rows]
    if not roots:
        raise ValueError("an observation requires at least one root row")
    spans = [dict(row) for row in trace_rows]
    root = roots[0]
    trace_id = str(root.get("trace_id", ""))
    ids = [_identity(row) for row in spans]
    counts = Counter(ids)
    duplicate_identity = sorted([list(identity) for identity, count in counts.items() if count > 1])
    root_id = str(root.get("span_id", ""))
    root_identity_count = counts.get((trace_id, root_id), 0)
    by_span: dict[str, list[dict]] = defaultdict(list)
    for row in spans:
        by_span[str(row.get("span_id", ""))].append(row)
    missing_parents = sorted({str(row.get("parent_span", "")) for row in spans if row.get("parent_span") and str(row.get("parent_span")) not in by_span})
    parent_by_id = {}
    for span_id, rows in by_span.items():
        parent_by_id[span_id] = str(rows[0].get("parent_span", ""))
    cycles = _cycle_ids(parent_by_id)
    direct = [row for row in spans if str(row.get("parent_span", "")) == root_id]
    direct_children = [{
        "trace_id": str(row.get("trace_id", "")),
        "span_id": str(row.get("span_id", "")),
        "cmdb_id": str(row.get("cmdb_id", "")),
        "operation_name": str(row.get("operation_name", "")),
        "type": str(row.get("type", "")),
        "duration_raw": str(row.get("duration_raw", row.get("duration", ""))),
        **_source(row),
    } for row in sorted(direct, key=lambda item: (str(item.get("operation_name", "")), str(item.get("type", "")), str(item.get("span_id", "")), str(item.get("source_file", "")), int(item.get("source_record", 0) or 0)))]
    invalid_duration = sorted(str(row.get("span_id", "")) for row in spans if (_duration_us(row) is not None and _duration_us(row) < 0) or _duration_us(row) is None)
    trace_mismatch = sorted({str(row.get("trace_id", "")) for row in spans if str(row.get("trace_id", "")) != trace_id})
    blank_parent_roots = sorted(str(row.get("span_id", "")) for row in spans if not str(row.get("parent_span", "")))
    source_files = sorted({_source(row)["source_file"] for row in spans})
    disconnected = []
    for span_id in by_span:
        seen: set[str] = set()
        current = span_id
        reached_root = False
        while current:
            if current == root_id:
                reached_root = True
                break
            if current in seen:
                break
            seen.add(current)
            parent = parent_by_id.get(current, "")
            if not parent:
                break
            current = parent
        if not reached_root and span_id != root_id:
            disconnected.append(span_id)
    identity_status = "resolved" if root_identity_count == 1 else ("missing_root_record" if root_identity_count == 0 else "ambiguous_identity")
    flags = {
        "duplicate_root_rows": len(roots) > 1,
        "root_identity_status": identity_status,
        "root_identity_count_in_trace": root_identity_count,
        "identity_resolved": identity_status == "resolved" and len(roots) == 1,
        "missing_root_record": identity_status == "missing_root_record",
        "duplicate_identity": duplicate_identity,
        "missing_parents": missing_parents,
        "cycles": cycles,
        "trace_id_mismatch": trace_mismatch,
        "invalid_duration": invalid_duration,
        "blank_parent_roots": blank_parent_roots,
        "multiple_blank_parent_roots": len(blank_parent_roots) > 1,
        "disconnected_span_ids": sorted(disconnected),
        "cross_file_boundary": len(source_files) > 1,
        "source_files": source_files,
    }
    unresolved = bool(identity_status != "resolved" or len(roots) > 1 or not spans or duplicate_identity or missing_parents or cycles or trace_mismatch or invalid_duration or len(blank_parent_roots) > 1 or disconnected)
    state = "unknown_structure" if unresolved else ("empty_recorded_children" if not direct_children else "resolved")
    endpoints = []
    for row in spans:
        duration = _duration_us(row)
        if duration is not None and duration >= 0:
            endpoints.append(_start_ms(row) * 1000 + duration)
    root_duration = _duration_us(root)
    return {
        "trace_id": trace_id,
        "span_id": root_id,
        "root_key": [trace_id, root_id],
        "cmdb_id": str(root.get("cmdb_id", "")),
        "operation_name": str(root.get("operation_name", "")),
        "type": str(root.get("type", "")),
        "timestamp_ms": _start_ms(root),
        "duration_raw": str(root.get("duration_raw", root.get("duration", ""))),
        "duration_us": root_duration,
        "duration_ms": (root_duration / 1000.0) if root_duration is not None and root_duration >= 0 else None,
        "root_end_us": (_start_ms(root) * 1000 + root_duration) if root_duration is not None and root_duration >= 0 else None,
        "max_recorded_end_us": max(endpoints, default=None),
        "recorded_span_count": len(spans),
        "raw_root_records": len(roots),
        "direct_children": direct_children,
        "structure_status": state,
        "identity_resolved": bool(identity_status == "resolved" and len(roots) == 1),
        "root_identity_status": identity_status,
        "query_completion_status": "known_complete" if spans and not unresolved else "unresolved_completion",
        "flags": flags,
        "status_code": str(root.get("status_code", "")),
        "source": _source(root),
        "all_sources": sorted({_source(row)["source_file"] + ":" + str(_source(row)["source_record"]) for row in spans}),
        "signature": {mode: signature_for_root({"operation_name": root.get("operation_name", ""), "type": root.get("type", ""), "direct_children": direct_children, "structure_status": state}, mode) for mode in ("C0", "C1", "C2")},
    }


def group_root_rows(roots: Iterable[Mapping]) -> dict[tuple[str, str], list[dict]]:
    """Group raw root rows by composite request identity."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for root in roots:
        groups[_identity(root)].append(dict(root))
    return dict(groups)
