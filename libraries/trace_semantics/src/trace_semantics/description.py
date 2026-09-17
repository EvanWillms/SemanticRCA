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
    _validate_json(value)
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError("description input must be finite JSON-compatible data") from exc


def _validate_json(value: Any) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("description input must be finite JSON-compatible data")
        return
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("JSON object keys must be strings")
        for item in value.values():
            _validate_json(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_json(item)
        return
    raise TypeError("description input must be finite JSON-compatible data")


def _canonical(value: Any) -> str:
    """Use one private ordering key for otherwise unordered JSON records."""
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


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


def _description_trace(trace: Mapping[str, Any]) -> dict[str, Any]:
    for required in ("trace_id", "deployment", "raw", "nodes", "edges", "evidence", "coverage"):
        if required not in trace:
            raise ValueError(f"partition trace is missing required field: {required}")
    nodes_value = trace["nodes"]
    nodes = sorted((_copy_json(node) for node in nodes_value), key=_node_sort_key) if isinstance(nodes_value, list) else _copy_json(nodes_value)
    edges_value = trace["edges"]
    edges = sorted((_copy_json(edge) for edge in edges_value), key=_edge_sort_key) if isinstance(edges_value, list) else _copy_json(edges_value)
    evidence = _sorted_records(trace["evidence"])
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
        "coverage": _copy_json(trace["coverage"]),
        "evidence": evidence,
        "nodes": nodes,
        "edges": edges,
        "counts": counts,
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
    traces_value = partition.get("traces", [])
    if not isinstance(traces_value, list):
        raise TypeError("partition traces must be a list")
    built = []
    dictionary: set[tuple[str, str]] = set()
    for trace in traces_value:
        if not isinstance(trace, Mapping):
            raise TypeError("partition trace must be a mapping")
        described = _description_trace(trace)
        dictionary.update(described.pop("_operation_dictionary"))
        built.append(described)
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
    return json.dumps(detached, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def description_digest(description: Mapping[str, Any]) -> str:
    """Return the SHA-256 digest of canonical description JSON."""
    return hashlib.sha256(canonical_json(description).encode("utf-8")).hexdigest()
