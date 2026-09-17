"""Evidence-preserving partitioning of caller-selected traces.
This module deliberately stops at recorded facts.  It does not decide whether
an operation is a retry, whether a status means request failure, or what a
span's target and cause might be.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any

SCHEMA_VERSION = "trace-semantics-v1"
REQUIRED_SPAN_FIELDS = (
    "trace_id", "span_id", "parent_span", "cmdb_id", "operation_name",
    "type", "status_code", "timestamp", "duration",
)
def _copy_json(value: Any) -> Any:
    """Return a detached JSON value, rejecting non-JSON and non-finite data."""
    try:
        def validate(item: Any) -> None:
            if item is None or isinstance(item, (str, bool, int)):
                return
            if isinstance(item, float):
                if not math.isfinite(item):
                    raise ValueError("non-finite number")
                return
            if isinstance(item, list):
                for child in item:
                    validate(child)
                return
            if isinstance(item, dict):
                for key, child in item.items():
                    if not isinstance(key, str):
                        raise TypeError("JSON object keys must be strings")
                    validate(child)
                return
            raise TypeError(f"unsupported JSON value: {type(item).__name__}")
        validate(value)
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
        return json.loads(encoded)
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise TypeError("trace evidence must be JSON-compatible finite data") from exc
_UNSET = object()
@dataclass(frozen=True)
class EncodingPolicy:
    """Versioned caller-owned definitions used while extracting trace facts."""
    version: str = SCHEMA_VERSION
    operation_mappings: Mapping[str, str] = field(default_factory=dict)
    timestamp_unit: str | None = None
    duration_unit: str | None = None
    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or not self.version:
            raise ValueError("policy version must be a non-empty string")
        if not isinstance(self.operation_mappings, Mapping):
            raise TypeError("operation_mappings must be a mapping")
        copied: dict[str, str] = {}
        for raw_name, meaning in self.operation_mappings.items():
            if not isinstance(raw_name, str) or not isinstance(meaning, str):
                raise TypeError("operation mappings must map strings to strings")
            copied[raw_name] = meaning
        object.__setattr__(self, "operation_mappings", MappingProxyType(copied))
        for name, unit in (("timestamp_unit", self.timestamp_unit), ("duration_unit", self.duration_unit)):
            if unit is not None and (not isinstance(unit, str) or unit not in _TIME_FACTORS):
                raise ValueError(f"unsupported {name}: {unit!r}")
    def as_json(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "operation_mappings": dict(self.operation_mappings),
            "timestamp_unit": self.timestamp_unit,
            "duration_unit": self.duration_unit,
        }
_TIME_FACTORS = {
    "s": 1.0,
    "sec": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    "ms": 1e-3,
    "millisecond": 1e-3,
    "milliseconds": 1e-3,
    "us": 1e-6,
    "µs": 1e-6,
    "microsecond": 1e-6,
    "microseconds": 1e-6,
    "ns": 1e-9,
    "nanosecond": 1e-9,
    "nanoseconds": 1e-9,
}
def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
def _unit_kind(unit: Any) -> Any:
    return _TIME_FACTORS.get(unit) if isinstance(unit, str) else None
def _is_scalar_id(value: Any) -> bool:
    return isinstance(value, (str, int, float)) and not isinstance(value, bool)
def _deferred(
    *,
    reason: str,
    facet: str,
    trace_id: Any = None,
    deployment: Any = None,
    span_id: Any = None,
    evidence_ids: list[str] | None = None,
    raw: Any = None,
) -> dict[str, Any]:
    return {
        "reason": reason,
        "facet": facet,
        "trace_id": trace_id,
        "deployment": deployment,
        "span_id": span_id,
        "evidence_ids": list(evidence_ids or []),
        "raw": _copy_json(raw),
    }
def _span_record_parts(record: Any) -> tuple[Any, Any, bool]:
    """Return raw span payload, locator, and whether the wrapper is valid."""
    if not isinstance(record, dict) or "raw" not in record:
        return record, None, False
    return record.get("raw"), record.get("locator"), isinstance(record.get("raw"), dict)
def _new_evidence(record: Any, raw: Any, locator: Any, trace_id: Any, deployment: Any, ordinal: int) -> dict[str, Any]:
    """Build a stable, detached physical-record evidence item."""
    digest = hashlib.sha256(_canonical({
        "trace_id": trace_id,
        "deployment": deployment,
        "raw": raw,
        "locator": locator,
    }).encode("utf-8")).hexdigest()[:20]
    evidence_id = f"e-{digest}"
    return {
        "evidence_id": evidence_id,
        "trace_id": trace_id,
        "deployment": deployment,
        "raw": _copy_json(raw),
        "locator": _copy_json(locator),
        "record": _copy_json(record),
        "ordinal": ordinal,
    }
def _field(raw: Mapping[str, Any], name: str) -> Any:
    # Track-1's nine-column spelling is intentionally the only accepted shape.
    return raw.get(name)
def _node_identity(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "trace_id": _copy_json(_field(raw, "trace_id")),
        "span_id": _copy_json(_field(raw, "span_id")),
        "cmdb_id": _copy_json(_field(raw, "cmdb_id")),
        "operation_name": _copy_json(_field(raw, "operation_name")),
        "type": _copy_json(_field(raw, "type")),
    }
def _timing_facet(
    raw: Mapping[str, Any],
    trace_context: Any,
    policy: EncodingPolicy,
    *,
    trace_id: Any,
    deployment: Any,
    span_id: Any,
    evidence_id: str,
    deferred: list[dict[str, Any]],
) -> dict[str, Any] | None:
    timestamp = _field(raw, "timestamp")
    duration = _field(raw, "duration")
    if timestamp is None and duration is None:
        return None
    context = trace_context if isinstance(trace_context, dict) else {}
    context_ts_unit = context.get("timestamp_unit")
    context_duration_unit = context.get("duration_unit")
    if (context.get("__context_conflict__")
            or (context_ts_unit is not None and _unit_kind(context_ts_unit) != _unit_kind(policy.timestamp_unit))
            or (context_duration_unit is not None and _unit_kind(context_duration_unit) != _unit_kind(policy.duration_unit))):
        deferred.append(_deferred(
            reason="conflicting_timing_unit",
            facet="timing",
            trace_id=trace_id,
            deployment=deployment,
            span_id=span_id,
            evidence_ids=[evidence_id],
            raw=raw,
        ))
        return {"timestamp": _copy_json(timestamp), "duration": _copy_json(duration), "unit": None}
    if policy.timestamp_unit is None or policy.duration_unit is None:
        deferred.append(_deferred(
            reason="unknown_timing_unit",
            facet="timing",
            trace_id=trace_id,
            deployment=deployment,
            span_id=span_id,
            evidence_ids=[evidence_id],
            raw=raw,
        ))
        return {
            "timestamp": _copy_json(timestamp),
            "duration": _copy_json(duration),
            "timestamp_unit": policy.timestamp_unit,
            "duration_unit": policy.duration_unit,
        }
    def numeric(value: Any) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
        return parsed if parsed.is_finite() else None
    bad_value = any(value is not None and numeric(value) is None for value in (timestamp, duration))
    if duration is not None:
        parsed_duration = numeric(duration)
        if parsed_duration is None or not parsed_duration.is_finite() or parsed_duration < 0:
            bad_value = True
    if bad_value:
        deferred.append(_deferred(
            reason="invalid_timing_value",
            facet="timing",
            trace_id=trace_id,
            deployment=deployment,
            span_id=span_id,
            evidence_ids=[evidence_id],
            raw=raw,
        ))
    return {
        "timestamp": _copy_json(timestamp),
        "duration": _copy_json(duration),
        "timestamp_unit": policy.timestamp_unit,
        "duration_unit": policy.duration_unit,
        "valid": not bad_value,
    }
def _trace_shell(envelope: Any, trace_id: Any, deployment: Any) -> dict[str, Any]:
    return {
        "trace_id": _copy_json(trace_id),
        "deployment": _copy_json(deployment),
        "context": _copy_json(envelope.get("context") if isinstance(envelope, dict) else None),
        "raw": _copy_json(envelope),
        "nodes": [],
        "edges": [],
        "evidence": [],
        "coverage": {"record_count": 0, "occurrence_count": 0, "conflicting_identity_count": 0},
    }
def _process_trace(
    envelope: Any,
    policy: EncodingPolicy,
    output_deferred: list[dict[str, Any]],
    *,
    extra_envelopes: list[Any] | None = None,
    source_envelope: Any = None,
    context_conflict: bool = False,
) -> dict[str, Any]:
    trace_id = envelope.get("trace_id") if isinstance(envelope, dict) else None
    deployment = envelope.get("deployment") if isinstance(envelope, dict) else None
    result = _trace_shell(source_envelope if source_envelope is not None else envelope, trace_id, deployment)
    if extra_envelopes:
        result["raw_envelopes"] = [_copy_json(source_envelope if source_envelope is not None else envelope), *[_copy_json(item) for item in extra_envelopes]]
    if not isinstance(envelope, dict):
        output_deferred.append(_deferred(reason="malformed_trace", facet="trace", raw=envelope))
        return result
    context_valid = _is_scalar_id(trace_id) and isinstance(deployment, str) and bool(deployment)
    if not context_valid:
        output_deferred.append(_deferred(
            reason="malformed_trace_context",
            facet="trace_context",
            trace_id=trace_id,
            deployment=deployment,
            raw=envelope,
        ))
    spans = envelope.get("spans")
    if not isinstance(spans, list):
        output_deferred.append(_deferred(
            reason="malformed_spans",
            facet="trace",
            trace_id=trace_id,
            deployment=deployment,
            raw=spans,
        ))
        return result
    timing_context = envelope.get("context")
    if context_conflict:
        timing_context = {"__context_conflict__": True}
    groups: dict[Any, dict[str, Any]] = {}
    evidence_by_span: dict[Any, list[str]] = {}
    records_by_span: dict[Any, list[dict[str, Any]]] = {}
    evidence_ids_seen: dict[str, int] = {}
    for ordinal, record in enumerate(spans):
        raw, locator, wrapped_valid = _span_record_parts(record)
        evidence = _new_evidence(record, raw, locator, trace_id, deployment, ordinal)
        base_id = evidence["evidence_id"]
        suffix = evidence_ids_seen.get(base_id, 0)
        evidence_ids_seen[base_id] = suffix + 1
        if suffix:
            evidence["evidence_id"] = f"{base_id}-{suffix + 1}"
        evidence_id = evidence["evidence_id"]
        evidence["span_id"] = raw.get("span_id") if isinstance(raw, dict) else None
        result["evidence"].append(evidence)
        result["coverage"]["record_count"] += 1
        if locator is None:
            output_deferred.append(_deferred(
                reason="missing_locator",
                facet="provenance",
                trace_id=trace_id,
                deployment=deployment,
                span_id=evidence["span_id"],
                evidence_ids=[evidence_id],
                raw=record,
            ))
        if not wrapped_valid:
            output_deferred.append(_deferred(
                reason="malformed_span_record",
                facet="record",
                trace_id=trace_id,
                deployment=deployment,
                span_id=evidence["span_id"],
                evidence_ids=[evidence_id],
                raw=record,
            ))
            continue
        raw_trace_id = _field(raw, "trace_id")
        if not context_valid:
            continue
        if raw_trace_id != trace_id:
            output_deferred.append(_deferred(
                reason="trace_id_mismatch",
                facet="identity",
                trace_id=trace_id,
                deployment=deployment,
                span_id=_field(raw, "span_id"),
                evidence_ids=[evidence_id],
                raw=raw,
            ))
            # A span with a different envelope identity is retained as raw
            # evidence, but cannot participate in this trace's node or graph.
            continue
        missing_fields = [name for name in REQUIRED_SPAN_FIELDS if name not in raw]
        if missing_fields:
            for name in missing_fields:
                output_deferred.append(_deferred(
                    reason="missing_field",
                    facet="record",
                    trace_id=trace_id,
                    deployment=deployment,
                    span_id=_field(raw, "span_id"),
                    evidence_ids=[evidence_id],
                    raw={"field": name, "record": raw},
                ))
            # A malformed row is still available through evidence, but no
            # identity-dependent fact is accepted from it.
            continue
        span_id = _field(raw, "span_id")
        if not _is_scalar_id(span_id) or span_id == "":
            output_deferred.append(_deferred(
                reason="missing_span_id",
                facet="identity",
                trace_id=trace_id,
                deployment=deployment,
                evidence_ids=[evidence_id],
                raw=raw,
            ))
            continue
        evidence_by_span.setdefault(span_id, []).append(evidence_id)
        records_by_span.setdefault(span_id, []).append({"raw": raw, "evidence_id": evidence_id, "locator": locator})
        fingerprint = _canonical(raw)
        group = groups.get(span_id)
        if group is None:
            groups[span_id] = {
                "span_id": span_id,
                "fingerprint": fingerprint,
                "identity": _node_identity(raw),
                "records": records_by_span[span_id],
                "conflict": False,
            }
        else:
            group["records"] = records_by_span[span_id]
            if fingerprint != group["fingerprint"]:
                group["conflict"] = True
    # Emit nodes in first-seen order; no sorting is used to imply temporal order.
    for span_id, group in groups.items():
        records = group["records"]
        first_raw = records[0]["raw"]
        op_name = _field(first_raw, "operation_name")
        operation_known = isinstance(op_name, str) and op_name in policy.operation_mappings
        semantic_operation = policy.operation_mappings.get(op_name) if operation_known and not group["conflict"] else None
        node_evidence = [record["evidence_id"] for record in records]
        for record in records:
            raw = record["raw"]
            evidence_id = record["evidence_id"]
            if group["conflict"]:
                output_deferred.append(_deferred(
                    reason="conflicting_identity",
                    facet="identity",
                    trace_id=trace_id,
                    deployment=deployment,
                    span_id=span_id,
                    evidence_ids=[evidence_id],
                    raw=raw,
                ))
            if not isinstance(op_name, str) or op_name not in policy.operation_mappings:
                output_deferred.append(_deferred(
                    reason="unknown_operation",
                    facet="operation",
                    trace_id=trace_id,
                    deployment=deployment,
                    span_id=span_id,
                    evidence_ids=[evidence_id],
                    raw=raw,
                ))
            # Status mappings are intentionally absent from EncodingPolicy: raw
            # status is retained and its meaning stays unknown.
            output_deferred.append(_deferred(
                reason="unknown_status",
                facet="status",
                trace_id=trace_id,
                deployment=deployment,
                span_id=span_id,
                evidence_ids=[evidence_id],
                raw=raw,
            ))
            _timing_facet(
                raw,
                timing_context,
                policy,
                trace_id=trace_id,
                deployment=deployment,
                span_id=span_id,
                evidence_id=evidence_id,
                deferred=output_deferred,
            )
        result["nodes"].append({
            "span_id": _copy_json(span_id),
            "identity": None if group["conflict"] else group["identity"],
            "identity_conflict": group["conflict"],
            "record_count": len(records),
            "occurrence_count": None if group["conflict"] else 1,
            "occurrences": [{
                "evidence_id": record["evidence_id"],
                "raw": _copy_json(record["raw"]),
                "locator": _copy_json(record["locator"]),
            } for record in records],
            "semantic_operation": semantic_operation,
            "operation_name": None if group["conflict"] else _copy_json(op_name),
            "cmdb_id": None if group["conflict"] else _copy_json(_field(first_raw, "cmdb_id")),
            "type": None if group["conflict"] else _copy_json(_field(first_raw, "type")),
            "status_code": None if group["conflict"] else _copy_json(_field(first_raw, "status_code")),
            "timing": None if group["conflict"] else _timing_facet(
                first_raw,
                timing_context,
                policy,
                trace_id=trace_id,
                deployment=deployment,
                span_id=span_id,
                evidence_id=records[0]["evidence_id"],
                deferred=[],
            ),
        })
    result["coverage"]["conflicting_identity_count"] = sum(
        1 for group in groups.values() if group["conflict"]
    )
    result["coverage"]["occurrence_count"] = sum(
        1 for group in groups.values() if not group["conflict"]
    )
    # Parent references and cycle checks are scoped to this one trace envelope.
    parent_refs: dict[Any, Any] = {}
    parent_evidence: dict[tuple[Any, Any], list[str]] = {}
    for span_id, group in groups.items():
        all_refs = [_field(record["raw"], "parent_span") for record in group["records"]]
        refs = [ref for ref in all_refs if ref not in (None, "")]
        malformed_refs = [ref for ref in refs if not _is_scalar_id(ref)]
        if malformed_refs:
            output_deferred.append(_deferred(
                reason="malformed_parent",
                facet="parent",
                trace_id=trace_id,
                deployment=deployment,
                span_id=span_id,
                evidence_ids=evidence_by_span.get(span_id),
                raw=malformed_refs,
            ))
            refs = [ref for ref in refs if _is_scalar_id(ref)]
        if refs:
            parent_refs[span_id] = refs[0]
            for record, ref in zip(group["records"], all_refs):
                if ref not in (None, "") and _is_scalar_id(ref):
                    parent_evidence.setdefault((span_id, ref), []).append(record["evidence_id"])
        if len({_canonical(ref) for ref in refs}) > 1:
            output_deferred.append(_deferred(
                reason="conflicting_parent_reference",
                facet="parent",
                trace_id=trace_id,
                deployment=deployment,
                span_id=span_id,
                evidence_ids=evidence_by_span.get(span_id),
                raw=refs,
            ))
    cycle_nodes: set[Any] = set()
    globally_seen: set[Any] = set()
    for start in parent_refs:
        if start in globally_seen:
            continue
        path: list[Any] = []
        position: dict[Any, int] = {}
        current = start
        while current in parent_refs and current not in globally_seen:
            if current in position:
                cycle_nodes.update(path[position[current]:])
                break
            position[current] = len(path)
            path.append(current)
            current = parent_refs[current]
        globally_seen.update(path)
    for child, parent in parent_refs.items():
        edge_evidence = parent_evidence.get((child, parent), evidence_by_span.get(child, []))
        reasons: list[str] = []
        parent_group = groups.get(parent)
        child_group = groups.get(child)
        if parent_group is None:
            reasons.append("missing_parent")
        if child == parent:
            reasons.append("self_parent")
        if child in cycle_nodes:
            reasons.append("cyclic_parent")
        if child_group and child_group["conflict"]:
            reasons.append("conflicting_identity")
        if parent_group and parent_group["conflict"]:
            reasons.append("conflicting_parent_identity")
        resolved = not reasons
        result["edges"].append({
            "child_span_id": _copy_json(child),
            "parent_span_id": _copy_json(parent),
            "relation": "recorded_parent",
            "resolved": resolved,
            "evidence_ids": list(edge_evidence),
        })
        for reason in reasons:
            output_deferred.append(_deferred(
                reason=reason,
                facet="parent",
                trace_id=trace_id,
                deployment=deployment,
                span_id=child,
                evidence_ids=edge_evidence,
                raw={"parent_span": parent},
            ))
    return result
def partition_traces(traces: list[dict[str, Any]], policy: EncodingPolicy | None = None) -> dict[str, Any]:
    """Partition selected traces into deterministic facts and local deferrals.
    The input boundary is a JSON array of trace envelopes.  A detached copy is
    made before any processing; malformed JSON-shaped records are retained in
    ``raw``/``evidence`` and represented by deferred items.
    """
    if not isinstance(traces, list):
        raise TypeError("traces must be a JSON-compatible list")
    selected_policy = EncodingPolicy() if policy is None else policy
    if not isinstance(selected_policy, EncodingPolicy):
        raise TypeError("policy must be an EncodingPolicy")
    detached = _copy_json(traces)
    output = {
        "schema_version": SCHEMA_VERSION,
        "policy": selected_policy.as_json(),
        "traces": [],
        "deferred": [],
    }
    # Merge duplicate trace/deployment envelopes into one logical trace.  Their
    # raw envelopes remain available and the duplicate itself is deferred.
    grouped: dict[tuple[Any, Any], tuple[Any, list[Any]]] = {}
    order: list[tuple[Any, Any] | tuple[str, int]] = []
    for index, envelope in enumerate(detached):
        if isinstance(envelope, dict) and _is_scalar_id(envelope.get("trace_id")) and isinstance(envelope.get("deployment"), str):
            key = (envelope.get("trace_id"), envelope.get("deployment"))
            if key in grouped:
                grouped[key][1].append(envelope)
            else:
                grouped[key] = (envelope, [])
                order.append(key)
        else:
            key = ("__malformed__", index)
            order.append(key)
            grouped[key] = (envelope, [])
    for key in order:
        envelope, duplicates = grouped[key]
        if duplicates:
            for duplicate in duplicates:
                output["deferred"].append(_deferred(
                    reason="duplicate_trace_envelope",
                    facet="trace",
                    trace_id=envelope.get("trace_id") if isinstance(envelope, dict) else None,
                    raw=duplicate,
                ))
        combined = _copy_json(envelope)
        context_conflict = False
        if duplicates and isinstance(combined, dict) and isinstance(combined.get("spans"), list):
            for duplicate in duplicates:
                if _canonical(duplicate.get("context")) != _canonical(combined.get("context")):
                    context_conflict = True
                if isinstance(duplicate, dict) and isinstance(duplicate.get("spans"), list):
                    combined["spans"].extend(_copy_json(duplicate["spans"]))
        output["traces"].append(_process_trace(
            combined,
            selected_policy,
            output["deferred"],
            extra_envelopes=duplicates,
            source_envelope=envelope,
            context_conflict=context_conflict,
        ))
    return output
