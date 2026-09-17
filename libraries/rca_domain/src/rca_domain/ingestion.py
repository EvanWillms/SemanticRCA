"""Translate native semantic trace descriptions into RCA evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any


_DESCRIPTION_VERSION = "trace-description-v1"
_EVIDENCE_VERSION = "rca-evidence-v1"
_RAW_FIELDS = (
    "trace_id",
    "span_id",
    "parent_span",
    "cmdb_id",
    "operation_name",
    "type",
    "status_code",
    "timestamp",
    "duration",
)
_PROJECTION_FIELDS = frozenset({"component", "reason", "occurrence_time"})
_REQUIRED_DESCRIPTION = (
    "schema_version",
    "policy",
    "meaning_dictionary",
    "traces",
    "deferred",
    "counts",
)
_REQUIRED_TRACE = ("trace_id", "deployment", "raw", "coverage", "evidence", "nodes", "edges", "counts")
_REQUIRED_EVIDENCE = ("evidence_id", "trace_id", "deployment", "raw", "locator", "record", "ordinal", "span_id")
_REQUIRED_NODE = (
    "span_id",
    "identity",
    "identity_conflict",
    "record_count",
    "occurrence_count",
    "occurrences",
    "semantic_operation",
    "operation_name",
    "cmdb_id",
    "type",
    "status_code",
    "timing",
)
_REQUIRED_EDGE = ("child_span_id", "parent_span_id", "relation", "resolved", "evidence_ids")


def _detached(value: Any, label: str) -> Any:
    """Return a detached strict JSON value, with one public error type."""

    try:
        return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ValueError(f"{label} must be finite JSON-compatible data") from exc


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ValueError(f"{label} missing required field(s): {', '.join(missing)}")


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _trace_id(value: Any, label: str) -> Any:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{label} must be a scalar trace identity")
    if isinstance(value, str) and not value:
        raise ValueError(f"{label} must be non-empty")
    return value


def _scope(scope: Any) -> dict[str, Any]:
    value = _detached(scope, "scope")
    if not isinstance(value, dict):
        raise ValueError("scope must be an object")
    _require_fields(value, ("case_id", "deployment", "incident_count", "projection"), "scope")
    _nonempty_string(value["case_id"], "scope.case_id")
    deployment = _nonempty_string(value["deployment"], "scope.deployment")
    incident_count = value["incident_count"]
    if isinstance(incident_count, bool) or not isinstance(incident_count, int) or incident_count <= 0:
        raise ValueError("scope.incident_count must be a positive integer")
    projection = value["projection"]
    if not isinstance(projection, list) or not projection:
        raise ValueError("scope.projection must be a non-empty list")
    if any(item not in _PROJECTION_FIELDS for item in projection) or len(set(projection)) != len(projection):
        raise ValueError("scope.projection contains an unsupported or repeated field")

    has_start = "window_start" in value
    has_end = "window_end" in value
    if has_start != has_end:
        raise ValueError("scope.window_start and scope.window_end must be supplied together")
    if has_start:
        try:
            start = datetime.fromisoformat(value["window_start"])
            end = datetime.fromisoformat(value["window_end"])
        except (TypeError, ValueError) as exc:
            raise ValueError("scope window bounds must be ISO datetimes") from exc
        offset = timedelta(hours=8)
        if start.utcoffset() != offset or end.utcoffset() != offset:
            raise ValueError("scope window bounds must use the +08:00 offset")
        if start >= end:
            raise ValueError("scope.window_start must precede scope.window_end")
    return value


def _stable_id(source_snapshot_id: str, deployment: str, trace_id: Any, producer_evidence_id: str) -> str:
    identity = [source_snapshot_id, deployment, trace_id, producer_evidence_id]
    return hashlib.sha256(_canonical(identity).encode("utf-8")).hexdigest()


def _validate_policy(description: Mapping[str, Any], label: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    policy = _require_mapping(description["policy"], f"{label}.policy")
    _require_fields(policy, ("version", "operation_mappings", "timestamp_unit", "duration_unit"), f"{label}.policy")
    version = _nonempty_string(policy["version"], f"{label}.policy.version")
    mappings = _require_mapping(policy["operation_mappings"], f"{label}.policy.operation_mappings")
    normalized_mappings: dict[str, str] = {}
    for raw_name, meaning in mappings.items():
        _nonempty_string(raw_name, f"{label}.policy.operation_mappings key")
        normalized_mappings[raw_name] = _nonempty_string(meaning, f"{label}.policy.operation_mappings[{raw_name!r}]")
    dictionary = _require_mapping(description["meaning_dictionary"], f"{label}.meaning_dictionary")
    _require_fields(dictionary, ("version", "operations"), f"{label}.meaning_dictionary")
    if dictionary["version"] != version:
        raise ValueError(f"{label} policy/dictionary version mismatch")
    operations = dictionary["operations"]
    if not isinstance(operations, list):
        raise ValueError(f"{label}.meaning_dictionary.operations must be a list")
    seen: dict[str, Any] = {}
    for index, operation in enumerate(operations):
        item = _require_mapping(operation, f"{label}.meaning_dictionary.operations[{index}]")
        _require_fields(item, ("raw", "meaning"), f"{label}.meaning_dictionary.operations[{index}]")
        raw_name = _nonempty_string(item["raw"], f"{label}.meaning_dictionary.operations[{index}].raw")
        meaning = item["meaning"]
        if meaning is not None:
            meaning = _nonempty_string(meaning, f"{label}.meaning_dictionary.operations[{index}].meaning")
            if normalized_mappings.get(raw_name) != meaning:
                raise ValueError(f"{label} operation dictionary disagrees with policy")
        elif raw_name in normalized_mappings:
            raise ValueError(f"{label} unknown operation disagrees with policy")
        if raw_name in seen and seen[raw_name] != meaning:
            raise ValueError(f"{label} operation dictionary repeats a conflicting raw name")
        seen[raw_name] = meaning
    return dict(policy), dict(dictionary), normalized_mappings


def _validate_raw(raw: Any, label: str, trace_id: Any, deployment: str) -> dict[str, Any]:
    value = _require_mapping(raw, label)
    _require_fields(value, _RAW_FIELDS, label)
    if value["trace_id"] != trace_id:
        raise ValueError(f"{label}.trace_id does not match its trace")
    if not isinstance(value["span_id"], (str, int, float)) or isinstance(value["span_id"], bool) or value["span_id"] == "":
        raise ValueError(f"{label}.span_id must be a scalar identity")
    return dict(value)


def _validate_description(
    envelope: Mapping[str, Any],
    scope: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    packet_id = _nonempty_string(envelope["packet_id"], "envelope.packet_id")
    source_snapshot_id = _nonempty_string(envelope["source_snapshot_id"], "envelope.source_snapshot_id")
    description = _require_mapping(envelope["description"], f"envelope {packet_id}.description")
    _require_fields(description, _REQUIRED_DESCRIPTION, f"envelope {packet_id}.description")
    if description["schema_version"] != _DESCRIPTION_VERSION:
        raise ValueError(f"envelope {packet_id} requires {_DESCRIPTION_VERSION}")
    policy, dictionary, mappings = _validate_policy(description, f"envelope {packet_id}.description")
    traces = description["traces"]
    deferred = description["deferred"]
    counts = description["counts"]
    if not isinstance(traces, list) or not isinstance(deferred, list) or not isinstance(counts, list):
        raise ValueError(f"envelope {packet_id}.description has invalid collection fields")

    validated_traces: list[dict[str, Any]] = []
    evidence_by_id: dict[str, dict[str, Any]] = {}
    node_meanings: dict[str, tuple[Any, bool]] = {}
    for trace_index, raw_trace in enumerate(traces):
        trace = _require_mapping(raw_trace, f"envelope {packet_id}.description.traces[{trace_index}]")
        _require_fields(trace, _REQUIRED_TRACE, f"envelope {packet_id}.description.traces[{trace_index}]")
        trace_id = _trace_id(trace["trace_id"], f"envelope {packet_id} trace_id")
        deployment = _nonempty_string(trace["deployment"], f"envelope {packet_id} trace deployment")
        if deployment != scope["deployment"]:
            raise ValueError(f"envelope {packet_id} trace deployment is outside scope")
        trace_raw = _require_mapping(trace["raw"], f"envelope {packet_id} trace raw")
        if trace_raw.get("trace_id", trace_id) != trace_id or trace_raw.get("deployment", deployment) != deployment:
            raise ValueError(f"envelope {packet_id} trace raw identity mismatch")
        _require_mapping(trace["coverage"], f"envelope {packet_id} trace coverage")
        evidence = trace["evidence"]
        nodes = trace["nodes"]
        edges = trace["edges"]
        trace_counts = trace["counts"]
        if not isinstance(evidence, list) or not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(trace_counts, list):
            raise ValueError(f"envelope {packet_id} trace has invalid collection fields")
        trace_evidence: dict[str, dict[str, Any]] = {}
        for evidence_index, raw_evidence in enumerate(evidence):
            item = _require_mapping(raw_evidence, f"envelope {packet_id} evidence[{evidence_index}]")
            _require_fields(item, _REQUIRED_EVIDENCE, f"envelope {packet_id} evidence[{evidence_index}]")
            evidence_id = _nonempty_string(item["evidence_id"], "producer evidence_id")
            if evidence_id in trace_evidence:
                raise ValueError(f"envelope {packet_id} repeats producer evidence_id {evidence_id!r}")
            if item["trace_id"] != trace_id or item["deployment"] != deployment:
                raise ValueError(f"envelope {packet_id} evidence identity mismatch")
            raw = _validate_raw(item["raw"], f"envelope {packet_id} evidence[{evidence_index}].raw", trace_id, deployment)
            if item["span_id"] != raw["span_id"]:
                raise ValueError(f"envelope {packet_id} evidence span reference mismatch")
            ordinal = item["ordinal"]
            if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
                raise ValueError(f"envelope {packet_id} evidence ordinal is invalid")
            validated = {
                "evidence_id": evidence_id,
                "trace_id": trace_id,
                "deployment": deployment,
                "raw": raw,
                "locator": _detached(item["locator"], "evidence locator"),
                "record": _detached(item["record"], "evidence record"),
                "ordinal": ordinal,
                "span_id": item["span_id"],
            }
            trace_evidence[evidence_id] = validated
            evidence_by_id[evidence_id] = validated

        node_ids: set[Any] = set()
        node_by_id: dict[Any, Mapping[str, Any]] = {}
        for node_index, raw_node in enumerate(nodes):
            node = _require_mapping(raw_node, f"envelope {packet_id} node[{node_index}]")
            _require_fields(node, _REQUIRED_NODE, f"envelope {packet_id} node[{node_index}]")
            span_id = node["span_id"]
            if isinstance(span_id, bool) or not isinstance(span_id, (str, int, float)) or span_id == "":
                raise ValueError(f"envelope {packet_id} node span_id is invalid")
            if span_id in node_ids:
                raise ValueError(f"envelope {packet_id} repeats node span_id {span_id!r}")
            node_ids.add(span_id)
            node_by_id[span_id] = node
            if not isinstance(node["identity_conflict"], bool):
                raise ValueError(f"envelope {packet_id} node conflict flag is invalid")
            occurrences = node["occurrences"]
            if not isinstance(occurrences, list) or node["record_count"] != len(occurrences):
                raise ValueError(f"envelope {packet_id} node occurrence membership is invalid")
            meaning = node["semantic_operation"]
            if meaning is not None:
                _nonempty_string(meaning, f"envelope {packet_id} node semantic_operation")
                operation_name = node["operation_name"]
                if mappings.get(operation_name) != meaning:
                    raise ValueError(f"envelope {packet_id} node meaning disagrees with policy")
            elif node["operation_name"] in mappings:
                raise ValueError(f"envelope {packet_id} mapped operation has no semantic meaning")
            conflict = bool(node["identity_conflict"] or node["occurrence_count"] is None)
            for occurrence_index, raw_occurrence in enumerate(occurrences):
                occurrence = _require_mapping(raw_occurrence, f"envelope {packet_id} node occurrence[{occurrence_index}]")
                _require_fields(occurrence, ("evidence_id", "raw", "locator"), f"envelope {packet_id} node occurrence[{occurrence_index}]")
                evidence_id = _nonempty_string(occurrence["evidence_id"], "node producer evidence_id")
                referenced = trace_evidence.get(evidence_id)
                if referenced is None:
                    raise ValueError(f"envelope {packet_id} node evidence reference is missing")
                occurrence_raw = _validate_raw(occurrence["raw"], f"envelope {packet_id} node occurrence raw", trace_id, deployment)
                if occurrence_raw != referenced["raw"] or occurrence["locator"] != referenced["locator"]:
                    raise ValueError(f"envelope {packet_id} node evidence reference disagrees with raw evidence")
                if occurrence_raw["span_id"] != span_id:
                    raise ValueError(f"envelope {packet_id} node occurrence span mismatch")
                previous = node_meanings.get(evidence_id)
                current = (meaning, conflict)
                if previous is not None and previous != current:
                    raise ValueError(f"envelope {packet_id} evidence has conflicting node meaning")
                node_meanings[evidence_id] = current

        for edge_index, raw_edge in enumerate(edges):
            edge = _require_mapping(raw_edge, f"envelope {packet_id} edge[{edge_index}]")
            _require_fields(edge, _REQUIRED_EDGE, f"envelope {packet_id} edge[{edge_index}]")
            if edge["child_span_id"] not in node_by_id or edge["parent_span_id"] not in node_by_id:
                raise ValueError(f"envelope {packet_id} edge endpoint is outside scoped nodes")
            if edge["relation"] != "recorded_parent" or not isinstance(edge["resolved"], bool):
                raise ValueError(f"envelope {packet_id} edge relation is invalid")
            if not isinstance(edge["evidence_ids"], list) or any(eid not in trace_evidence for eid in edge["evidence_ids"]):
                raise ValueError(f"envelope {packet_id} edge evidence reference is missing")

        validated_trace = {
            "trace_id": trace_id,
            "deployment": deployment,
            "raw": _detached(trace["raw"], "trace raw"),
            "coverage": _detached(trace["coverage"], "trace coverage"),
            "evidence": list(trace_evidence.values()),
            "edges": _detached(edges, "trace edges"),
            "counts": _detached(trace_counts, "trace counts"),
            "deferred": _detached(trace.get("deferred", []), "trace deferred"),
        }
        validated_traces.append(validated_trace)

    trace_keys = {(trace["deployment"], trace["trace_id"]) for trace in validated_traces}
    for index, raw_deferred in enumerate(deferred):
        item = _require_mapping(raw_deferred, f"envelope {packet_id} deferred[{index}]")
        evidence_ids = item.get("evidence_ids", [])
        if not isinstance(evidence_ids, list) or any(eid not in evidence_by_id for eid in evidence_ids):
            raise ValueError(f"envelope {packet_id} deferred evidence reference is missing")
        item_trace = item.get("trace_id")
        if item_trace is not None and not any(trace_id == item_trace for _, trace_id in trace_keys):
            raise ValueError(f"envelope {packet_id} deferred trace is outside description")
    if not all(isinstance(item, Mapping) for item in counts):
        raise ValueError(f"envelope {packet_id} counts must contain objects")
    return {
        "packet_id": packet_id,
        "source_snapshot_id": source_snapshot_id,
        "policy": policy,
        "meaning_dictionary": dictionary,
        "traces": validated_traces,
        "deferred": _detached(deferred, "description deferred"),
    }, validated_traces, evidence_by_id, [dict(item) for item in counts]


def from_semantic_traces(envelopes: list[dict[str, Any]], scope: dict[str, Any]) -> dict[str, Any]:
    """Build an RCA evidence packet from explicit native descriptions."""

    if not isinstance(envelopes, list):
        raise ValueError("envelopes must be a list")
    validated_scope = _scope(scope)
    detached_envelopes = _detached(envelopes, "envelopes")
    if not isinstance(detached_envelopes, list):
        raise ValueError("envelopes must be a list")

    observations: dict[str, dict[str, Any]] = {}
    coverage: list[dict[str, Any]] = []
    qualifications: list[dict[str, Any]] = []
    definitions: list[dict[str, Any]] = []
    packet_identity: dict[tuple[str, str], str] = {}
    for envelope_index, raw_envelope in enumerate(detached_envelopes):
        envelope = _require_mapping(raw_envelope, f"envelope[{envelope_index}]")
        _require_fields(envelope, ("packet_id", "source_snapshot_id", "description"), f"envelope[{envelope_index}]")
        packet, traces, evidence_by_id, _counts = _validate_description(envelope, validated_scope)
        packet_key = (packet["source_snapshot_id"], packet["packet_id"])
        packet_digest = hashlib.sha256(_canonical(envelope["description"]).encode("utf-8")).hexdigest()
        if packet_key in packet_identity and packet_identity[packet_key] != packet_digest:
            raise ValueError("conflicting packet identity")
        packet_identity[packet_key] = packet_digest
        definitions.append({
            "packet_id": packet["packet_id"],
            "source_snapshot_id": packet["source_snapshot_id"],
            "schema_version": _DESCRIPTION_VERSION,
            "policy": _detached(packet["policy"], "policy"),
            "meaning_dictionary": _detached(packet["meaning_dictionary"], "meaning dictionary"),
            "evidence_aliases": {
                evidence_id: _stable_id(
                    packet["source_snapshot_id"],
                    evidence["deployment"],
                    evidence["trace_id"],
                    evidence_id,
                )
                for evidence_id, evidence in evidence_by_id.items()
            },
        })

        for trace in traces:
            trace_id = trace["trace_id"]
            deployment = trace["deployment"]
            coverage.append({
                "packet_id": packet["packet_id"],
                "source_snapshot_id": packet["source_snapshot_id"],
                "deployment": deployment,
                "trace_id": trace_id,
                "trace_raw": _detached(trace["raw"], "trace raw"),
                "coverage": _detached(trace["coverage"], "trace coverage"),
                "edges": _detached(trace["edges"], "trace edges"),
                "counts": _detached(trace["counts"], "trace counts"),
                "deferred": _detached(trace["deferred"], "trace deferred"),
            })
            for evidence_id, evidence in evidence_by_id.items():
                if evidence["trace_id"] != trace_id:
                    continue
                meaning, node_conflict = _meaning_for_evidence(envelope["description"], trace_id, evidence_id)
                stable_id = _stable_id(packet["source_snapshot_id"], deployment, trace_id, evidence_id)
                observation = {
                    "evidence_id": stable_id,
                    "source_snapshot_id": packet["source_snapshot_id"],
                    "deployment": deployment,
                    "trace_id": trace_id,
                    "span_id": evidence["span_id"],
                    "semantic_operation": meaning,
                    "recording_component": evidence["raw"].get("cmdb_id"),
                    "raw": _detached(evidence["raw"], "raw evidence"),
                    "locator": _detached(evidence["locator"], "evidence locator"),
                    "conflict": node_conflict,
                }
                existing = observations.get(stable_id)
                if existing is not None and existing != observation:
                    raise ValueError("conflicting observation identity")
                observations[stable_id] = observation

        for item in packet["deferred"]:
            qualifications.append({
                "kind": "deferred",
                "packet_id": packet["packet_id"],
                "source_snapshot_id": packet["source_snapshot_id"],
                "item": _detached(item, "deferred item"),
            })
        for trace in traces:
            for item in trace.get("deferred", []):
                qualifications.append({
                    "kind": "deferred",
                    "packet_id": packet["packet_id"],
                    "source_snapshot_id": packet["source_snapshot_id"],
                    "item": _detached(item, "trace deferred item"),
                })

    return {
        "schema_version": _EVIDENCE_VERSION,
        "scope": _detached(validated_scope, "scope"),
        "revision": 0,
        "observations": observations,
        "coverage": coverage,
        "qualifications": qualifications,
        "definitions": definitions,
    }


def _meaning_for_evidence(description: Mapping[str, Any], trace_id: Any, evidence_id: str) -> tuple[Any, bool]:
    meaning: Any = None
    conflict = False
    for trace in description["traces"]:
        if trace.get("trace_id") != trace_id:
            continue
        for node in trace["nodes"]:
            for occurrence in node.get("occurrences", []):
                if occurrence.get("evidence_id") == evidence_id:
                    current = node.get("semantic_operation")
                    current_conflict = bool(node.get("identity_conflict") or node.get("occurrence_count") is None)
                    if meaning is not None and meaning != current:
                        raise ValueError("conflicting observation identity")
                    meaning = current
                    conflict = conflict or current_conflict
    return meaning, conflict
