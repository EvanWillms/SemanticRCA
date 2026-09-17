"""Source-bound frontend observation extraction for qualified baselines.

``collect_requests`` is deliberately a collection boundary.  It selects roots
from a frozen time/replica policy, recovers every indexed span for selected
traces, then builds JSON-friendly observations with exact ``Decimal`` endpoint
arithmetic.  Baseline membership, support and statistics belong to the next
layer and are not performed here.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import json
from typing import Any, Iterable, Iterator, Mapping, Sequence

from rca.telemetry.trace_index import PreparedTraceView, TraceIndexBudgetExceeded
from .contracts import (
    ChildOccurrence,
    Measurement,
    Observation,
    ObservationBatch as DomainObservationBatch,
    ObservationIdentity,
    RetrievalReceipt,
    SourceLocator,
)


DEFAULT_COMPONENT_ALLOWLIST = ("frontend-0", "frontend-1", "frontend-2")
DEFAULT_LOOKBACK_MS = 300_000
DEFAULT_SLICE_MS = 300_000
DEFAULT_HORIZON_MS = 1_800_000


def _get(value: Any, *names: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
    else:
        for name in names:
            if hasattr(value, name):
                return getattr(value, name)
    return default


def _check_budget(work_budget: Any) -> None:
    if work_budget is None:
        return
    checker = getattr(work_budget, "check", None)
    if checker is None and callable(work_budget):
        checker = work_budget
    if checker is not None:
        try:
            checker()
        except TraceIndexBudgetExceeded:
            raise
        except Exception as exc:
            if exc.__class__.__name__ in {"BudgetExceeded", "WorkBudgetExceeded"}:
                raise TraceIndexBudgetExceeded(str(exc)) from exc
            raise


def _decimal(value: Any) -> Decimal | None:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return result if result.is_finite() else None


def _json_number(value: Decimal | None) -> Any:
    """Keep exact values usable in Python while offering JSON-safe strings.

    The pure API returns Decimal values.  ``ObservationBatch.to_dict`` uses
    decimal strings where a standard JSON encoder cannot preserve the exact
    endpoint, and retains the original raw text alongside them.
    """
    return value


def _locator(row: Mapping[str, Any]) -> dict[str, Any]:
    if row.get("locator"):
        return dict(row["locator"])
    return {
        "path": str(row.get("source_path", "")),
        "source_digest": str(row.get("source_digest", "")),
        "record": int(row.get("source_record", 0) or 0),
        "header": 1,
    }


def _raw_fields(row: Mapping[str, Any]) -> dict[str, str]:
    return {field: str(row.get(field, "")) for field in (
        "timestamp", "cmdb_id", "span_id", "trace_id", "duration", "type",
        "status_code", "operation_name", "parent_span",
    )}


def _identity(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("trace_id", "")), str(row.get("span_id", ""))


def _row_sort(row: Mapping[str, Any]) -> tuple[Any, ...]:
    stamp = _decimal(row.get("timestamp", ""))
    return (stamp if stamp is not None else Decimal("Infinity"),
            str(row.get("trace_id", "")), str(row.get("span_id", "")),
            str(row.get("source_path", "")), int(row.get("source_record", 0) or 0))


def _duration_us(row: Mapping[str, Any]) -> Decimal | None:
    """Interpret raw duration as provisional microseconds, exactly."""
    return _decimal(row.get("duration", ""))


def _end_ms(row: Mapping[str, Any]) -> Decimal | None:
    start = _decimal(row.get("timestamp", ""))
    duration_us = _duration_us(row)
    if start is None or duration_us is None or duration_us < 0:
        return None
    # Track 1 stores timestamps in ms and the reviewed provisional duration
    # interpretation is microseconds.  Do not float this boundary.
    return start + duration_us / Decimal(1000)


def _operation_pair(row: Mapping[str, Any]) -> tuple[str, str]:
    return str(row.get("operation_name", "")), str(row.get("type", ""))


def _signature(root: Mapping[str, Any], children: Sequence[Mapping[str, Any]], state: str) -> dict[str, Any]:
    pairs = [_operation_pair(child) for child in children]
    unique = sorted(set(pairs))
    counts = Counter(pairs)
    c0 = {
        "root_operation_name": str(root.get("operation_name", "")),
        "root_type": str(root.get("type", "")),
    }
    c1 = {**c0, "structure_state": state,
          "direct_child_set": [[operation, typ] for operation, typ in unique] if state != "unknown_structure" else None}
    c2 = {**c1, "direct_child_multiset": [[operation, typ, count]
                                            for (operation, typ), count in sorted(counts.items())]
          if state != "unknown_structure" else None}
    return {"C0": c0, "C1": c1, "C2": c2}


def _deduplicate_spans(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    """Collapse byte-equivalent parsed rows; retain conflicts and locators."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_identity(row)].append(dict(row))
    collapsed: list[dict[str, Any]] = []
    audit: dict[tuple[str, str], dict[str, Any]] = {}
    for identity, candidates in grouped.items():
        ordered = sorted(candidates, key=_row_sort)
        fields = [_raw_fields(candidate) for candidate in ordered]
        unique = {json.dumps(field, sort_keys=True, separators=(",", ":")) for field in fields}
        selected = dict(ordered[0])
        locators = [_locator(candidate) for candidate in ordered]
        audit[identity] = {
            "identity": list(identity),
            "duplicate_count": len(ordered),
            "conflict": len(unique) > 1,
            "locators": locators,
        }
        selected["locators"] = locators
        selected["duplicate_count"] = len(ordered)
        selected["conflict"] = len(unique) > 1
        collapsed.append(selected)
    collapsed.sort(key=_row_sort)
    return collapsed, audit


def _cycles(parent_by_id: Mapping[str, str]) -> list[list[str]]:
    found: list[list[str]] = []
    for start in parent_by_id:
        path: list[str] = []
        positions: dict[str, int] = {}
        current = start
        while current and current in parent_by_id:
            if current in positions:
                cycle = path[positions[current]:] + [current]
                if cycle not in found:
                    found.append(cycle)
                break
            positions[current] = len(path)
            path.append(current)
            current = parent_by_id[current]
    return sorted(found)


def _make_observation(root_rows: Sequence[Mapping[str, Any]], trace_rows: Sequence[Mapping[str, Any]],
                      deployment: str, anchor_ms: Decimal, lookback_ms: Decimal,
                      horizon_end_ms: Decimal) -> dict[str, Any]:
    roots = sorted((dict(row) for row in root_rows), key=_row_sort)
    root = roots[0]
    collapsed, audit = _deduplicate_spans(trace_rows)
    trace_id, root_id = _identity(root)
    by_span: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in collapsed:
        by_span[str(row.get("span_id", ""))].append(row)
    root_candidates = [row for row in collapsed if not str(row.get("parent_span", ""))]
    root_rows_for_identity = [row for row in roots if _identity(row) == (trace_id, root_id)]
    root_audit = audit.get((trace_id, root_id), {"duplicate_count": len(root_rows_for_identity), "conflict": False})
    root_raw_fields = {_raw_fields(row).__repr__() for row in root_rows_for_identity}
    root_duplicate_conflict = len(root_raw_fields) > 1
    root_identity_count = sum(1 for row in collapsed if _identity(row) == (trace_id, root_id))
    missing_parents = sorted({str(row.get("parent_span", "")) for row in collapsed
                              if row.get("parent_span") and str(row.get("parent_span")) not in by_span})
    parent_by_id = {span_id: str(rows[0].get("parent_span", "")) for span_id, rows in by_span.items()}
    cycles = _cycles(parent_by_id)
    trace_mismatch = sorted({str(row.get("trace_id", "")) for row in collapsed if str(row.get("trace_id", "")) != trace_id})
    invalid = sorted(str(row.get("span_id", "")) for row in collapsed
                     if (_duration_us(row) is None or (_duration_us(row) is not None and _duration_us(row) < 0)))
    direct = [row for row in collapsed if str(row.get("parent_span", "")) == root_id]
    direct.sort(key=lambda row: (_operation_pair(row), str(row.get("span_id", "")), _row_sort(row)))
    known_span_ids = set(by_span)
    disconnected: list[str] = []
    for span_id in known_span_ids:
        if span_id == root_id:
            continue
        seen: set[str] = set()
        current = span_id
        reached = False
        while current:
            if current == root_id:
                reached = True
                break
            if current in seen:
                break
            seen.add(current)
            parent = parent_by_id.get(current, "")
            if not parent:
                break
            current = parent
        if not reached:
            disconnected.append(current or span_id)
    unresolved = bool(
        root_identity_count != 1 or not collapsed or root_duplicate_conflict or root_audit.get("conflict") or
        any(item.get("conflict") for item in collapsed) or missing_parents or cycles or
        trace_mismatch or invalid or len(root_candidates) != 1 or disconnected
    )
    structure_state = "unknown_structure" if unresolved else ("empty_recorded_children" if not direct else "resolved")
    endpoints = [_end_ms(row) for row in collapsed]
    known_endpoints = [endpoint for endpoint in endpoints if endpoint is not None]
    root_start = _decimal(root.get("timestamp", ""))
    root_duration = _duration_us(root)
    root_end = _end_ms(root)
    measurement_reasons: list[str] = []
    if root_duration is None:
        measurement_reasons.append("invalid_measurement")
    elif root_duration < 0:
        measurement_reasons.append("invalid_measurement")
    endpoint_state = "resolved" if len(known_endpoints) == len(collapsed) else "unresolved_completion"
    identity_state = "resolved" if root_identity_count == 1 and not root_duplicate_conflict else "ambiguous_identity"
    if root_audit.get("conflict") or root_duplicate_conflict or any(item.get("conflict") for item in collapsed):
        identity_state = "conflict"
    reference_start = anchor_ms - lookback_ms
    reference_candidate = (root_start is not None and reference_start <= root_start < anchor_ms)
    query_candidate = (root_start is not None and anchor_ms <= root_start < horizon_end_ms)
    complete_before_anchor = bool(known_endpoints and len(known_endpoints) == len(collapsed)
                                  and all(endpoint < anchor_ms for endpoint in known_endpoints))
    reasons = list(measurement_reasons)
    if endpoint_state != "resolved":
        reasons.append("unresolved_completion")
    if identity_state != "resolved":
        reasons.append("invalid_identity" if identity_state == "ambiguous_identity" else "conflict")
    if structure_state == "unknown_structure":
        reasons.append("unknown_structure")
    if reference_candidate and not complete_before_anchor:
        reasons.append("completion_boundary")
    observation_id = f"{deployment}:{trace_id}:{root_id}"
    children = [{
        "trace_id": str(row.get("trace_id", "")), "span_id": str(row.get("span_id", "")),
        "cmdb_id": str(row.get("cmdb_id", "")), "operation_name": str(row.get("operation_name", "")),
        "type": str(row.get("type", "")), "duration_raw": str(row.get("duration", "")),
        "end_ms": _end_ms(row),
        "locator": _locator(row), "locators": list(row.get("locators", [_locator(row)])),
        "duplicate_count": int(row.get("duplicate_count", 1)),
        "conflict": bool(row.get("conflict", False)),
    } for row in direct]
    return {
        "observation_id": observation_id,
        "id": observation_id,
        "deployment": deployment,
        "trace_id": trace_id,
        "root_span_id": root_id,
        "span_id": root_id,
        "cmdb_id": str(root.get("cmdb_id", "")),
        "operation_name": str(root.get("operation_name", "")),
        "type": str(root.get("type", "")),
        "start_ms": root_start,
        "timestamp_ms": root_start,
        "duration_raw": str(root.get("duration", "")),
        "duration_unit": "microseconds",
        "normalization_id": "provisional-us-to-ms-v1",
        "duration_us": root_duration,
        "duration_ms": (root_duration / Decimal(1000) if root_duration is not None and root_duration >= 0 else None),
        "root_end_ms": root_end,
        "max_recorded_end_ms": max(known_endpoints) if known_endpoints else None,
        "recorded_span_count": len(collapsed),
        "raw_root_records": len(roots),
        "duplicate_count": sum(max(0, int(item.get("duplicate_count", 1)) - 1) for item in collapsed),
        "structure_status": structure_state,
        "identity_status": identity_state,
        "completion_status": endpoint_state,
        "query_completion_status": "known_complete" if endpoint_state == "resolved" and not unresolved else "unresolved_completion",
        "reference_candidate": reference_candidate,
        "reference_eligible": bool(reference_candidate and complete_before_anchor and not unresolved),
        "query_candidate": query_candidate,
        "completion_before_anchor": complete_before_anchor,
        "reasons": sorted(set(reasons)),
        "flags": {
            "duplicate_identity": sorted([list(identity) for identity, item in audit.items() if item.get("duplicate_count", 1) > 1]),
            "conflicting_identity": sorted([list(identity) for identity, item in audit.items() if item.get("conflict")]),
            "missing_parents": missing_parents, "cycles": cycles,
            "trace_id_mismatch": trace_mismatch, "invalid_duration": invalid,
            "blank_parent_roots": sorted(str(row.get("span_id", "")) for row in root_candidates),
            "disconnected_span_ids": sorted(disconnected),
            "endpoint_count": len(known_endpoints),
            "span_count": len(collapsed),
        },
        "direct_children": children,
        "signature": _signature(root, direct, structure_state),
        "source": _locator(root),
        "locators": list(root.get("locators", [_locator(root)])),
        "all_locators": [_locator(row) for row in collapsed for _ in (0,)],
        "qualifications": [
            "Recorded recovery does not establish complete instrumentation.",
            "Duration units are provisionally interpreted as microseconds.",
            "Root and child endpoint eligibility uses strict millisecond Decimal arithmetic.",
        ],
    }


def _source_locator(view: PreparedTraceView, locator: Mapping[str, Any]) -> SourceLocator:
    return SourceLocator(
        view.snapshot_id,
        str(locator.get("source_digest", locator.get("sha256", ""))),
        representation="csv",
        record=int(locator.get("record", locator.get("source_record", 0)) or 0),
        selector=str(locator.get("path", locator.get("source_path", ""))),
    )


def _typed_observation(view: PreparedTraceView, item: Mapping[str, Any]) -> Observation:
    """Convert extraction evidence to the shared immutable domain value."""
    raw_measurement = str(item.get("duration_raw", ""))
    normalized = item.get("duration_ms")
    measurement_locator = SourceLocator(
        view.snapshot_id,
        str(item["source"].get("source_digest", "")),
        representation="csv",
        record=int(item["source"].get("record", 0) or 0),
        field="duration",
        selector=str(item["source"].get("path", "")),
    )
    if normalized is None or _decimal(normalized) is None or _decimal(normalized) < 0:
        measurement = Measurement(raw_measurement, "microseconds", None,
                                  "provisional-us-to-ms-v1", False,
                                  tuple(item.get("reasons") or ("invalid_measurement",)),
                                  measurement_locator)
    else:
        measurement = Measurement(raw_measurement, "microseconds", float(normalized),
                                  "provisional-us-to-ms-v1", True, (), measurement_locator)
    children_by_pair: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for child in item.get("direct_children", ()):
        children_by_pair[(str(child.get("operation_name", "")), str(child.get("type", "")))].append(child)
    children = tuple(
        ChildOccurrence(operation, typ, len(items),
                        max((child.get("end_ms") for child in items if child.get("end_ms") is not None), default=None))
        for (operation, typ), items in sorted(children_by_pair.items())
    )
    locators = tuple(_source_locator(view, locator) for locator in item.get("all_locators", ()))
    if not locators:
        locators = (measurement_locator,)
    state = "known" if item.get("structure_status") != "unknown_structure" else "unknown"
    completion = str(item.get("completion_status", "resolved"))
    if item.get("identity_status") == "conflict":
        completion = "conflict"
    if completion not in {"resolved", "unknown", "conflict", "excluded"}:
        completion = "unknown"
    return Observation(
        identity=ObservationIdentity(view.snapshot_id, str(item["deployment"]),
                                     str(item["trace_id"]), str(item["root_span_id"])),
        root_operation=str(item.get("operation_name", "")),
        root_type=str(item.get("type", "")),
        replica=str(item.get("cmdb_id", "")),
        # Start coordinates participate in slice arithmetic in the pure
        # baseline kernels, whose public type is float.  Endpoints retain
        # Decimal precision because strict completion boundaries depend on
        # exact provisional-us-to-ms conversion.
        start_ms=float(item.get("start_ms") if item.get("start_ms") is not None else 0),
        # ``Observation.endpoint_ms`` also considers child endpoints, but the
        # shared domain object exposes one end field.  Store the recovered
        # maximum so a descendant ending at T cannot be lost at the typed
        # boundary; root_end_ms remains available in the extraction evidence
        # before this conversion.
        end_ms=item.get("max_recorded_end_ms"),
        measurement=measurement,
        children=children,
        structure_state=state,
        role="reference" if item.get("reference_candidate") else ("query" if item.get("query_candidate") else None),
        source_locators=locators,
        completion_state=completion,
        raw_id=str(item.get("observation_id", "")),
    )


ObservationBatch = DomainObservationBatch


def _policy_components(policy: Any) -> tuple[str, ...]:
    values = _get(policy, "allowlist", "components", "component_allowlist", default=DEFAULT_COMPONENT_ALLOWLIST)
    if isinstance(values, Mapping):
        values = values.get("frontend", values.get("components", DEFAULT_COMPONENT_ALLOWLIST))
    return tuple(str(value) for value in (values or DEFAULT_COMPONENT_ALLOWLIST))


def collect_requests(view: PreparedTraceView, deployment: str, anchor_ms: Any,
                     policy: Any = None, work_budget: Any = None) -> ObservationBatch:
    """Select reference/query roots and recover complete recorded executions."""
    if not isinstance(view, PreparedTraceView):
        raise TypeError("view must be a PreparedTraceView")
    deployment = str(deployment)
    if deployment != view.deployment:
        raise ValueError("deployment does not match prepared source snapshot")
    anchor = _decimal(anchor_ms)
    if anchor is None:
        raise ValueError("anchor_ms must be a finite timestamp")
    lookback = _decimal(_get(policy, "lookback_ms", "lookback", default=DEFAULT_LOOKBACK_MS)) or Decimal(DEFAULT_LOOKBACK_MS)
    slice_ms = _decimal(_get(policy, "slice_ms", "query_slice_ms", default=DEFAULT_SLICE_MS)) or Decimal(DEFAULT_SLICE_MS)
    horizon = _decimal(_get(policy, "horizon_ms", "horizon", default=DEFAULT_HORIZON_MS)) or Decimal(DEFAULT_HORIZON_MS)
    if lookback <= 0 or slice_ms <= 0 or horizon <= 0:
        raise ValueError("policy windows must be positive")
    end = anchor + horizon
    components = _policy_components(policy)
    _check_budget(work_budget)
    all_roots = view.all_roots(anchor - lookback, end)
    selected = [row for row in all_roots if str(row.get("cmdb_id", "")) in set(components)]
    trace_ids = sorted({str(row.get("trace_id", "")) for row in selected})
    recovered = view.traces(trace_ids)
    observations: list[dict[str, Any]] = []
    raw_outcomes: list[dict[str, Any]] = []
    selected_by_identity: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        selected_by_identity[_identity(row)].append(row)
    for identity, roots in sorted(selected_by_identity.items()):
        _check_budget(work_budget)
        trace_rows = recovered.get(identity[0], [])
        observation = _make_observation(roots, trace_rows, deployment, anchor, lookback, end)
        observations.append(observation)
    allowed = set(components)
    for row in all_roots:
        if str(row.get("cmdb_id", "")) not in allowed:
            raw_outcomes.append({
                "outcome_id": f"raw:{deployment}:{row.get('trace_id', '')}:{row.get('span_id', '')}:{row.get('source_path', '')}:{row.get('source_record', '')}",
                "trace_id": str(row.get("trace_id", "")), "span_id": str(row.get("span_id", "")),
                "cmdb_id": str(row.get("cmdb_id", "")), "start_ms": _decimal(row.get("timestamp", "")),
                "source": _locator(row), "reasons": ["out_of_scope"], "state": "unresolved_raw",
            })
    observations.sort(key=lambda item: (item.get("start_ms") if item.get("start_ms") is not None else Decimal("Infinity"),
                                        item["observation_id"]))
    raw_outcomes.sort(key=lambda item: item["outcome_id"])
    reference_count = sum(1 for item in observations if item["reference_candidate"])
    query_count = sum(1 for item in observations if item["query_candidate"])
    recovered_span_count = sum(len(recovered.get(trace_id, [])) for trace_id in trace_ids)
    selection_receipt = RetrievalReceipt(
        inventory_id=view.snapshot_id,
        selected_count=len(selected),
        resolved_count=len(observations),
        unresolved_count=len(raw_outcomes),
        scanned_records=view.record_count,
        recovered_records=recovered_span_count,
        completed_batches=1,
        status="complete",
    )
    recovery_receipt = RetrievalReceipt(
        inventory_id=view.snapshot_id,
        selected_count=len(trace_ids),
        resolved_count=len(observations),
        unresolved_count=sum(1 for item in observations if item["completion_status"] != "resolved"),
        scanned_records=view.record_count,
        recovered_records=recovered_span_count,
        completed_batches=1,
        status="complete",
    )
    typed_observations = tuple(_typed_observation(view, item) for item in observations)
    return ObservationBatch(
        observations=typed_observations,
        selection_receipt=selection_receipt,
        recovery_receipt=recovery_receipt,
        unresolved=tuple(raw_outcomes),
        extraction_version="logical-span-dedup-v1",
    )


__all__ = [
    "DEFAULT_COMPONENT_ALLOWLIST", "ObservationBatch", "collect_requests",
]
