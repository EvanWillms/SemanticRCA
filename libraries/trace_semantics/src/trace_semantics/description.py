"""Deterministic construction of plain JSON trace descriptions."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = "trace-description-v1"
PARTITION_SCHEMA_VERSION = "trace-semantics-v1"


def _copy_json(value: Any) -> Any:
    """Copy the transport value and reject Python-only/non-finite values."""
    try:
        _validate_json(value)
        return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise TypeError("description input must be finite JSON-compatible data") from exc


def _validate_json(value: Any, active: set[int] | None = None) -> None:
    active = set() if active is None else active
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("description input must be finite JSON-compatible data")
        return
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in active:
            raise TypeError("description input contains a cyclic JSON value")
        active.add(marker)
        try:
            if any(not isinstance(key, str) for key in value):
                raise TypeError("JSON object keys must be strings")
            for item in value.values():
                _validate_json(item, active)
        finally:
            active.remove(marker)
        return
    if isinstance(value, list):
        marker = id(value)
        if marker in active:
            raise TypeError("description input contains a cyclic JSON value")
        active.add(marker)
        try:
            for item in value:
                _validate_json(item, active)
        finally:
            active.remove(marker)
        return
    raise TypeError("description input must be finite JSON-compatible data")


def _canonical(value: Any) -> str:
    """Use one private ordering key for otherwise unordered JSON records."""
    return json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _scalar_identifier(value: Any) -> bool:
    return isinstance(value, (str, int, float)) and not isinstance(value, bool)


def _identifier_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, _canonical(value))


def _validate_evidence_ids(value: Any, available: set[str], label: str) -> None:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a list")
    for evidence_id in value:
        if not isinstance(evidence_id, str) or evidence_id not in available:
            raise ValueError(f"{label} contains unknown evidence_id")


def _validate_trace_partition(trace: Mapping[str, Any]) -> set[str]:
    for required in ("trace_id", "deployment", "raw", "nodes", "edges", "evidence", "coverage"):
        if required not in trace:
            raise ValueError(f"partition trace is missing required field: {required}")
    for field_name in ("nodes", "edges", "evidence"):
        if not isinstance(trace[field_name], list):
            raise TypeError(f"partition trace {field_name} must be a list")
    if not isinstance(trace["coverage"], Mapping):
        raise TypeError("partition trace coverage must be a mapping")

    evidence_ids: set[str] = set()
    for evidence in trace["evidence"]:
        if not isinstance(evidence, Mapping):
            raise TypeError("partition evidence entries must be mappings")
        evidence_id = evidence.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            raise ValueError("partition evidence requires a non-empty evidence_id")
        if evidence_id in evidence_ids:
            raise ValueError("partition evidence contains duplicate evidence_id")
        evidence_ids.add(evidence_id)

    node_by_span: dict[tuple[str, str], Mapping[str, Any]] = {}
    referenced_evidence: set[str] = set()
    for node in trace["nodes"]:
        if not isinstance(node, Mapping):
            raise TypeError("partition nodes must contain mappings")
        span_id = node.get("span_id")
        if not _scalar_identifier(span_id):
            raise ValueError("partition node span_id must be a scalar identifier")
        span_key = _identifier_key(span_id)
        if span_key in node_by_span:
            raise ValueError("partition nodes contain duplicate span_id")
        node_by_span[span_key] = node
        identity_conflict = node.get("identity_conflict", False)
        if not isinstance(identity_conflict, bool):
            raise TypeError("partition node identity_conflict must be boolean")
        if "occurrence_count" in node:
            occurrence_count = node["occurrence_count"]
            if occurrence_count is not None and not _nonnegative_int(occurrence_count):
                raise ValueError("partition node occurrence_count must be non-negative")
            if identity_conflict and occurrence_count is not None:
                raise ValueError("conflicting partition node must have null occurrence_count")
        if identity_conflict:
            for field_name in ("identity", "semantic_operation", "operation_name", "cmdb_id", "type", "status_code", "timing"):
                if field_name in node and node[field_name] is not None:
                    raise ValueError(f"conflicting partition node cannot provide {field_name}")
        occurrences = node.get("occurrences")
        if occurrences is not None:
            if not isinstance(occurrences, list):
                raise TypeError("partition node occurrences must be a list")
            if "record_count" in node and node["record_count"] != len(occurrences):
                raise ValueError("partition node record_count does not match occurrences")
            for occurrence in occurrences:
                if not isinstance(occurrence, Mapping):
                    raise TypeError("partition occurrences must contain mappings")
                occurrence_evidence_id = occurrence.get("evidence_id")
                if not isinstance(occurrence_evidence_id, str) or occurrence_evidence_id not in evidence_ids:
                    raise ValueError("partition occurrence contains unknown evidence_id")
                if occurrence_evidence_id in referenced_evidence:
                    raise ValueError("partition evidence is referenced by multiple occurrences")
                referenced_evidence.add(occurrence_evidence_id)
        if "record_count" in node and not _nonnegative_int(node["record_count"]):
            raise ValueError("partition node record_count must be non-negative")
        if "evidence_ids" in node:
            _validate_evidence_ids(node["evidence_ids"], evidence_ids, "partition node evidence_ids")

    resolved_parent: dict[tuple[str, str], tuple[str, str]] = {}
    for edge in trace["edges"]:
        if not isinstance(edge, Mapping):
            raise TypeError("partition edges must contain mappings")
        if "resolved" in edge and not isinstance(edge["resolved"], bool):
            raise TypeError("partition edge resolved must be boolean")
        if "evidence_ids" in edge:
            _validate_evidence_ids(edge["evidence_ids"], evidence_ids, "partition edge evidence_ids")
        if edge.get("resolved") is True:
            child = edge.get("child_span_id", edge.get("child", edge.get("span_id")))
            parent = edge.get("parent_span_id", edge.get("parent"))
            if not _scalar_identifier(child) or not _scalar_identifier(parent):
                raise ValueError("resolved partition edge endpoints must be scalar identifiers")
            child_key = _identifier_key(child)
            parent_key = _identifier_key(parent)
            if child_key not in node_by_span or parent_key not in node_by_span or child_key == parent_key:
                raise ValueError("resolved partition edge has unresolved endpoints")
            if node_by_span[child_key].get("identity_conflict") or node_by_span[parent_key].get("identity_conflict"):
                raise ValueError("resolved partition edge references conflicting identity")
            if child_key in resolved_parent and resolved_parent[child_key] != parent_key:
                raise ValueError("resolved partition node has conflicting parents")
            resolved_parent[child_key] = parent_key

    globally_done: set[tuple[str, str]] = set()
    for start in resolved_parent:
        if start in globally_done:
            continue
        path: list[tuple[str, str]] = []
        position: dict[tuple[str, str], int] = {}
        current = start
        while current in resolved_parent and current not in globally_done:
            if current in position:
                raise ValueError("resolved partition edges contain a cycle")
            position[current] = len(path)
            path.append(current)
            current = resolved_parent[current]
        globally_done.update(path)

    coverage = trace["coverage"]
    if "record_count" in coverage:
        if not _nonnegative_int(coverage["record_count"]):
            raise ValueError("partition coverage record_count must be non-negative")
        if coverage["record_count"] != len(trace["evidence"]):
            raise ValueError("partition coverage record_count does not match evidence")
    if "conflicting_identity_count" in coverage:
        if not _nonnegative_int(coverage["conflicting_identity_count"]):
            raise ValueError("partition coverage conflicting_identity_count must be non-negative")
        expected_conflicts = sum(1 for node in trace["nodes"] if node.get("identity_conflict", False))
        if coverage["conflicting_identity_count"] != expected_conflicts:
            raise ValueError("partition coverage conflicting_identity_count does not match nodes")
    if "occurrence_count" in coverage:
        if not _nonnegative_int(coverage["occurrence_count"]):
            raise ValueError("partition coverage occurrence_count must be non-negative")
        expected_occurrences = sum(1 for node in trace["nodes"] if not node.get("identity_conflict", False))
        if coverage["occurrence_count"] != expected_occurrences:
            raise ValueError("partition coverage occurrence_count does not match nodes")
    return evidence_ids


def _record_sort_key(record: Any) -> tuple[str, str]:
    if isinstance(record, Mapping):
        locator = record.get("locator", record.get("evidence_id", record.get("id", "")))
        return (_canonical(locator), _canonical(record))
    return ("", _canonical(record))


def _sorted_records(value: Any) -> Any:
    if isinstance(value, list):
        return sorted((_copy_json(item) for item in value), key=_record_sort_key)
    return _copy_json(value)


def _operation_parts(node: Mapping[str, Any]) -> tuple[Any, Any]:
    """Extract raw and semantic operation without collapsing unknown names."""
    raw = node.get("operation_name")
    meaning = node.get("semantic_operation")
    return raw, meaning


def _occurrence_operations(node: Mapping[str, Any], raw: Any, meaning: Any) -> list[tuple[Any, Any]]:
    """Expose operation names carried by every physical record, conflicts included."""
    observations = [(raw, meaning)]
    occurrences = node.get("occurrences", [])
    if isinstance(occurrences, list):
        for occurrence in occurrences:
            if not isinstance(occurrence, Mapping) or not isinstance(occurrence.get("raw"), Mapping):
                continue
            occurrence_raw = occurrence["raw"].get("operation_name")
            if occurrence_raw != raw:
                observations.append((occurrence_raw, None))
    return observations


def _node_sort_key(node: Any) -> tuple[str, str]:
    if not isinstance(node, Mapping):
        return ("", _canonical(node))
    identity = node.get("span_id")
    return (_canonical(identity), _canonical(node))


def _edge_sort_key(edge: Any) -> tuple[str, str]:
    if not isinstance(edge, Mapping):
        return ("", _canonical(edge))
    parent = edge.get("parent_span_id", edge.get("parent", ""))
    child = edge.get("child_span_id", edge.get("child", edge.get("span_id", "")))
    return (_canonical((parent, child)), _canonical(edge))


def _trace_qualification(
    trace: Mapping[str, Any],
    policy: Mapping[str, Any],
    evidence_ids: list[str],
) -> dict[str, Any]:
    return {
        "semantic_layer": "descriptive",
        "production_method": "code",
        "definition_version": SCHEMA_VERSION,
        "policy_version": _copy_json(policy["version"]),
        "validation_state": "structural_only",
        "mapping_state": "source_mapping_unverified",
        "claim_kinds": {
            "context": "supplied",
            "evidence": "observed",
            "nodes": "derived",
            "edges": "derived",
            "counts": "derived",
            "deferred": "derived",
        },
        "scope": {
            "trace_id": _copy_json(trace.get("trace_id")),
            "deployment": _copy_json(trace.get("deployment")),
        },
        "evidence_ids": list(evidence_ids),
        "limitations": ["no_causation", "no_outcome", "source_authenticity_unverified"],
        "applies_to": ["context", "evidence", "nodes", "edges", "counts", "deferred"],
    }


def _description_trace(trace: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    for required in ("trace_id", "deployment", "raw", "nodes", "edges", "evidence", "coverage"):
        if required not in trace:
            raise ValueError(f"partition trace is missing required field: {required}")
    nodes_value = trace["nodes"]
    nodes = sorted((_copy_json(node) for node in nodes_value), key=_node_sort_key) if isinstance(nodes_value, list) else _copy_json(nodes_value)
    edges_value = trace["edges"]
    edges = sorted((_copy_json(edge) for edge in edges_value), key=_edge_sort_key) if isinstance(edges_value, list) else _copy_json(edges_value)
    evidence = _sorted_records(trace["evidence"])
    source_context = trace.get("context")
    if "context" not in trace and isinstance(trace.get("raw"), Mapping):
        source_context = trace["raw"].get("context")
    operation_counts: Counter[tuple[str, str]] = Counter()
    dictionary: set[tuple[str, str]] = set()
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, Mapping):
                continue
            raw, meaning = _operation_parts(node)
            for observed_raw, observed_meaning in _occurrence_operations(node, raw, meaning):
                if observed_raw is not None:
                    dictionary.add((_canonical(observed_raw), _canonical(observed_meaning)))
            if node.get("occurrence_count", 1) is None or node.get("identity_conflict") is True or raw is None:
                continue
            operation_counts[(_canonical(raw), _canonical(meaning))] += 1
    counts = [
        {"raw_operation": json.loads(raw), "meaning": json.loads(meaning), "count": count}
        for (raw, meaning), count in sorted(operation_counts.items())
    ]
    result: dict[str, Any] = {
        "trace_id": _copy_json(trace["trace_id"]),
        "deployment": _copy_json(trace["deployment"]),
        "raw": _copy_json(trace["raw"]),
        "context": _copy_json(source_context),
        "coverage": _copy_json(trace["coverage"]),
        "evidence": evidence,
        "nodes": nodes,
        "edges": edges,
        "counts": counts,
        "qualifications": [_trace_qualification(trace, policy, sorted([
            evidence_item["evidence_id"]
            for evidence_item in evidence
            if isinstance(evidence_item, Mapping) and isinstance(evidence_item.get("evidence_id"), str)
        ]))],
    }
    if "raw_envelopes" in trace:
        result["raw_envelopes"] = _copy_json(trace["raw_envelopes"])
    if "deferred" in trace:
        result["deferred"] = _sorted_records(trace["deferred"])
    result["_operation_dictionary"] = dictionary
    return result


def describe(partition: Mapping[str, Any]) -> dict[str, Any]:
    """Build a detached, deterministic description from partitioned facts."""
    if not isinstance(partition, Mapping):
        raise TypeError("partition must be a mapping")
    partition = _copy_json(partition)
    if partition.get("schema_version") != PARTITION_SCHEMA_VERSION:
        raise ValueError("unsupported partition schema_version")
    for required in ("policy", "traces", "deferred"):
        if required not in partition:
            raise ValueError(f"partition is missing required field: {required}")
    policy = partition.get("policy", {})
    if not isinstance(policy, Mapping):
        raise TypeError("partition policy must be a mapping")
    if not isinstance(policy.get("version"), str) or not policy["version"]:
        raise ValueError("partition policy requires a non-empty version")
    if "operation_mappings" not in policy:
        raise ValueError("partition policy is missing operation_mappings")
    mappings = policy.get("operation_mappings", {})
    if not isinstance(mappings, Mapping):
        raise TypeError("partition operation_mappings must be a mapping")
    if any(not isinstance(raw_name, str) or not isinstance(meaning, str) for raw_name, meaning in mappings.items()):
        raise TypeError("partition operation_mappings must map strings to strings")
    traces_value = partition.get("traces", [])
    if not isinstance(traces_value, list):
        raise TypeError("partition traces must be a list")
    deferred_value = partition.get("deferred", [])
    if not isinstance(deferred_value, list):
        raise TypeError("partition deferred must be a list")
    all_evidence_ids: set[str] = set()
    built = []
    dictionary: set[tuple[str, str]] = set()
    for trace in traces_value:
        if not isinstance(trace, Mapping):
            raise TypeError("partition trace must be a mapping")
        evidence_ids = _validate_trace_partition(trace)
        all_evidence_ids.update(evidence_ids)
        if "deferred" in trace:
            if not isinstance(trace["deferred"], list):
                raise TypeError("partition trace deferred must be a list")
            for item in trace["deferred"]:
                if not isinstance(item, Mapping):
                    raise TypeError("partition trace deferred entries must be mappings")
                if "evidence_ids" in item:
                    _validate_evidence_ids(item["evidence_ids"], evidence_ids, "partition trace deferred evidence_ids")
        described = _description_trace(trace, policy)
        dictionary.update(described.pop("_operation_dictionary"))
        built.append(described)
    for item in deferred_value:
        if not isinstance(item, Mapping):
            raise TypeError("partition deferred entries must be mappings")
        if "evidence_ids" in item:
            _validate_evidence_ids(item["evidence_ids"], all_evidence_ids, "partition deferred evidence_ids")
    built.sort(key=lambda item: (_canonical(item.get("deployment")), _canonical(item.get("trace_id"))))
    operations = [
        {"raw": json.loads(raw), "meaning": json.loads(meaning)}
        for raw, meaning in sorted(dictionary)
    ]
    counts = [
        {"deployment": trace["deployment"], "trace_id": trace["trace_id"], "operations": trace["counts"]}
        for trace in built
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "policy": _copy_json(policy),
        "meaning_dictionary": {"version": _copy_json(policy.get("version")), "operations": operations},
        "traces": built,
        "deferred": _sorted_records(partition.get("deferred", [])),
        "counts": counts,
    }


def encode_traces(traces: list[dict[str, Any]], policy: Any = None) -> dict[str, Any]:
    """Run partitioning followed by description construction."""
    from .partition import partition_traces

    return describe(partition_traces(traces, policy))


def canonical_json(description: Mapping[str, Any]) -> str:
    """Serialize a description as strict, stable UTF-8-oriented JSON text."""
    if not isinstance(description, Mapping):
        raise TypeError("description must be a mapping")
    detached = _copy_json(description)
    return json.dumps(detached, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":"))


def description_digest(description: Mapping[str, Any]) -> str:
    """Return the SHA-256 digest of canonical description JSON."""
    return hashlib.sha256(canonical_json(description).encode("utf-8")).hexdigest()
