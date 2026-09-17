"""Lean S02-S09 incremental semantic-encoding checks.

The runner is intentionally self contained and standard-library only.  It uses
the previously audited R0/R3 extracted records as read-only source references,
and keeps raw rows in packets while deriving qualified facts separately.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT_R0 = Path("/private/tmp/symbolicrca-trace-audit/graph/trace_9451fd8fdf746a80687451dae4c4e984.json")
R3_SOURCE = ROOT / "docs/research/examples/track-1-case-25-pyod-results/selected-traces.json"
EXPECTED_S02_R3 = Path(__file__).parent / "fixtures/expected_s02_r3.json"
EXPECTED_S03_RELATIONS = Path(__file__).parent / "fixtures/expected_s03_relations.json"
EXPECTED_S07 = Path(__file__).parent / "fixtures/expected_s07.json"
OUT_ROOT = ROOT / "data/experiments/semantic-encoding-v1"

RAW_FIELDS = (
    "timestamp", "cmdb_id", "span_id", "trace_id", "duration", "type",
    "status_code", "operation_name", "parent_span",
)


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def read_json(path: Path):
    return json.loads(path.read_text())


def base_row(span: str, parent: str, entity: str, *, ts: str = "1000", duration: str = "5",
             status: str = "0", operation: str = "op", typ: str = "rpc", trace: str = "synthetic"):
    return {
        "timestamp": ts, "cmdb_id": entity, "span_id": span, "trace_id": trace,
        "duration": duration, "type": typ, "status_code": status,
        "operation_name": operation, "parent_span": parent,
    }


def load_r0() -> tuple[list[dict], dict]:
    if not AUDIT_R0.exists():
        raise FileNotFoundError(f"audited R0 source missing: {AUDIT_R0}")
    source = read_json(AUDIT_R0)
    rows = []
    for row in source["rows"]:
        item = {key: row[key] for key in RAW_FIELDS}
        item["source_record"] = row.get("source_record")
        item["source_physical_end_line"] = row.get("source_physical_end_line", row.get("source_record"))
        rows.append(item)
    return rows, {
        "kind": "indexed_real_evidence_with_prior_full_scan",
        "path": str(AUDIT_R0), "trace_id": source["trace_id"],
        "full_source": "data/track-1/telemetry/2022_03_20/trace/trace_span.csv",
        "full_source_sha256": "42057b3325dc32bda37fc98feaf07a9edb48bcf394f5b511e18b38f23670f550",
        "scan_records": 9132857, "matched_records": 37,
        "instrumentation_completeness": "unknown",
    }


def load_frozen_expectations() -> dict:
    """Read the hash-checked expectation sheet authored from the prior audit."""
    expected = read_json(EXPECTED_S02_R3)
    if expected["R0"]["audit_artifact_sha256"] != sha_file(AUDIT_R0):
        raise ValueError("frozen R0 expectation does not match the audited fact sheet")
    if expected["R0"]["source_sha256"] != "42057b3325dc32bda37fc98feaf07a9edb48bcf394f5b511e18b38f23670f550":
        raise ValueError("frozen R0 source fingerprint changed")
    if expected["R3"]["source_sha256"] != sha_file(R3_SOURCE):
        raise ValueError("frozen R3 source fingerprint changed")
    return expected


def load_r3() -> tuple[list[dict], dict]:
    if not R3_SOURCE.exists():
        raise FileNotFoundError(f"indexed R3 source missing: {R3_SOURCE}")
    source = read_json(R3_SOURCE)
    rows = []
    for row in source["33ac121d12f9d81f70a93424c7312544"]:
        item = {key: row[key] for key in RAW_FIELDS}
        item["source_record"] = row.get("source_record")
        rows.append(item)
    return rows, {
        "kind": "indexed_real_evidence",
        "path": str(R3_SOURCE), "trace_id": "33ac121d12f9d81f70a93424c7312544",
        "source_record": rows[0].get("source_record"),
        "instrumentation_completeness": "unknown",
    }


def _identity_key(row):
    return (row["trace_id"], row["span_id"])


def encode_rows(rows: list[dict], packet_id: str, source_ref: dict, *, retrieval: str = "complete",
                timestamp_unit: str = "ms", duration_unit: str | None = "unknown",
                status_mapping: dict | None = None, request_verification: dict | None = None):
    """Encode losslessly; derived quality/timing facts never replace raw values."""
    if not rows:
        raise ValueError("packet requires at least one row")
    for row in rows:
        missing = set(RAW_FIELDS).difference(row)
        if missing:
            raise ValueError(f"missing raw fields: {sorted(missing)}")
    groups: dict[tuple, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        groups[_identity_key(row)].append(index)
    nodes = []
    pointers = {}
    for index, row in enumerate(rows):
        ident = _identity_key(row)
        occurrence = len([n for n in nodes if n["identity_key"] == list(ident)]) + 1
        node_id = row["span_id"] if len(groups[ident]) == 1 else f"{row['span_id']}#{occurrence}"
        evidence = f"{packet_id}:record:{index + 1}"
        source_record = row.get("source_record", index + 1)
        raw = {key: row[key] for key in RAW_FIELDS}
        nodes.append({
            "node_id": node_id, "identity_key": list(ident), "raw": raw,
            "parent_reference": row["parent_span"], "evidence": evidence,
            "conflict_group": ":".join(ident) if len(groups[ident]) > 1 else None,
        })
        pointers[evidence] = {
            "source_record": source_record, "source_line": row.get("source_physical_end_line", source_record),
            "trace_id": row["trace_id"], "span_id": row["span_id"], "row_sha256": sha_bytes(compact(raw)),
        }
    by_span: dict[str, list[dict]] = defaultdict(list)
    for node in nodes:
        by_span[node["raw"]["span_id"]].append(node)
    unresolved, ambiguous, edges = [], [], []
    for node in nodes:
        parent = node["parent_reference"]
        if parent == "":
            node["parent_resolution"] = "root_marker"
            continue
        candidates = by_span.get(parent, [])
        if len(candidates) == 1:
            node["parent_resolution"] = "resolved"
            edges.append([candidates[0]["node_id"], node["node_id"]])
        elif len(candidates) == 0:
            node["parent_resolution"] = "unresolved"
            unresolved.append({"child": node["node_id"], "parent_span": parent})
        else:
            node["parent_resolution"] = "conflicting"
            ambiguous.append({"child": node["node_id"], "parent_span": parent,
                              "candidate_nodes": [c["node_id"] for c in candidates]})
    conflict_groups = []
    for ident, indexes in groups.items():
        distinct = {sha_bytes(compact({key: rows[i][key] for key in RAW_FIELDS})) for i in indexes}
        if len(indexes) > 1 and len(distinct) > 1:
            conflict_groups.append({"identity_key": list(ident), "nodes": [nodes[i]["node_id"] for i in indexes],
                                    "evidence_ids": [nodes[i]["evidence"] for i in indexes]})
    root_nodes = [n for n in nodes if n["parent_resolution"] == "root_marker"]
    children_by_parent = Counter(edge[0] for edge in edges)
    quality = {
        "retrieval": retrieval,
        "instrumentation_completeness": source_ref.get("instrumentation_completeness", "unknown"),
        "unresolved_parent_references": unresolved,
        "ambiguous_parent_references": ambiguous,
        "conflicts": conflict_groups,
        "root_count": len(root_nodes),
        "root_recorded_children": sum(children_by_parent.get(root["node_id"], 0) for root in root_nodes),
        "root_child_observation": "empty_recorded_children" if root_nodes and not edges else "recorded_children_present",
        "structure_completeness": "unknown" if retrieval != "complete" or source_ref.get("instrumentation_completeness") == "unknown" else "qualified",
    }
    packet = {
        "packet_id": packet_id, "schema_version": "s02-s09-normalized-v1",
        "raw_fields": list(RAW_FIELDS), "records": [{key: row[key] for key in RAW_FIELDS} for row in rows],
        "nodes": nodes, "edges": sorted(edges), "entities": sorted({r["cmdb_id"] for r in rows}),
        "counts": dict(Counter(r["operation_name"] for r in rows)),
        "timing_policy": {"timestamp_unit": timestamp_unit, "duration_unit": duration_unit,
                          "absolute_anchor": "raw_timestamp", "clock": "qualified_by_source_or_emitter"},
        "status_mapping": status_mapping or {"version": None, "entries": {}, "scope": "none"},
        "request_verification": request_verification,
        "quality": quality, "source_reference": source_ref,
        "provenance_sidecar": f"{packet_id}.provenance.json",
        "unknowns": ["error_meaning", "business_success", "retry", "backend_target", "instrumentation_completeness"],
    }
    sidecar = {"source_reference": source_ref, "records": pointers}
    return packet, sidecar


def decode_packet(packet: dict) -> dict:
    """Decode retained facts from packet only; raw source is never consulted."""
    rows = packet["records"]
    return {
        "packet_id": packet["packet_id"], "records": rows, "edges": packet["edges"],
        "entities": packet["entities"], "counts": packet["counts"], "nodes": packet["nodes"],
        "quality": packet["quality"], "timing_policy": packet["timing_policy"],
        "status_mapping": packet["status_mapping"], "request_verification": packet["request_verification"],
        "unknowns": packet["unknowns"],
        "source_reference": packet["source_reference"],
    }


def relation_facts_rows(rows):
    """Independent raw-row projection used as the S02/S03 acceptance oracle."""
    group_sizes = Counter(_identity_key(row) for row in rows)
    node_ids = []
    occurrences = Counter()
    for row in rows:
        identity = _identity_key(row)
        occurrences[identity] += 1
        node_ids.append(row["span_id"] if group_sizes[identity] == 1 else f"{row['span_id']}#{occurrences[identity]}")
    by_span = defaultdict(list)
    for node_id, row in zip(node_ids, rows):
        by_span[row["span_id"]].append(node_id)
    entities = sorted({row["cmdb_id"] for row in rows})
    counts = dict(sorted(Counter(row["operation_name"] for row in rows).items()))
    parent_edges = []
    for node_id, row in zip(node_ids, rows):
        candidates = by_span.get(row["parent_span"], []) if row["parent_span"] else []
        if len(candidates) == 1:
            parent_edges.append([candidates[0], node_id])
    parent_edges.sort()
    pairs = node_ids
    by_id = {node_id: row for node_id, row in zip(node_ids, rows)}
    combinations = []
    for index, left in enumerate(pairs):
        for right in pairs[index + 1:]:
            combinations.append([left, right])
    same = sorted(pair for pair in combinations if by_id[pair[0]]["cmdb_id"] == by_id[pair[1]]["cmdb_id"])
    different = sorted(pair for pair in combinations if by_id[pair[0]]["cmdb_id"] != by_id[pair[1]]["cmdb_id"])
    return {"entities": entities, "counts": counts, "parent_edges": parent_edges,
            "same_entity_pairs": same, "different_entity_pairs": different,
            "span_count": len(rows), "edge_count": len(parent_edges)}


def relation_facts(decoded):
    """Project facts from explicit decoded structures, retaining packet mutations."""
    nodes = decoded["nodes"]
    node_ids = [node["node_id"] for node in nodes]
    by_id = {node["node_id"]: node for node in nodes}
    pairs = []
    for index, left in enumerate(node_ids):
        for right in node_ids[index + 1:]:
            pairs.append([left, right])
    return {
        "entities": decoded["entities"],
        "counts": decoded["counts"],
        "parent_edges": decoded["edges"],
        "same_entity_pairs": sorted(pair for pair in pairs
                                     if by_id[pair[0]]["raw"]["cmdb_id"] == by_id[pair[1]]["raw"]["cmdb_id"]),
        "different_entity_pairs": sorted(pair for pair in pairs
                                          if by_id[pair[0]]["raw"]["cmdb_id"] != by_id[pair[1]]["raw"]["cmdb_id"]),
        "span_count": len(nodes),
        "edge_count": len(decoded["edges"]),
    }


def audit_provenance(packet, sidecar, source_rows):
    differences = []
    indexed = {row.get("source_record", i + 1): row for i, row in enumerate(source_rows)}
    seen = []
    for node in packet["nodes"]:
        pointer = sidecar["records"].get(node["evidence"])
        if not pointer:
            differences.append(node["evidence"] + ":missing_pointer")
            continue
        source_record = pointer["source_record"]
        row = indexed.get(source_record)
        if row is None:
            differences.append(node["evidence"] + ":source_record")
            continue
        raw = {key: row[key] for key in RAW_FIELDS}
        if raw != node["raw"] or pointer["row_sha256"] != sha_bytes(compact(raw)):
            differences.append(node["evidence"] + ":raw")
        seen.append(source_record)
    if len(seen) != len(source_rows) or len(set(seen)) != len(source_rows):
        differences.append("source pointer one-to-one membership")
    return {"passed": not differences, "differences": differences,
            "audited_records": len(seen), "expected_records": len(source_rows),
            "unique_source_records": len(set(seen))}


def authored_s04_cases():
    complete = [base_row("root", "", "a", operation="request"), base_row("child", "root", "b", operation="work")]
    missing = [base_row("child", "root", "b", operation="work")]
    duplicate = [
        base_row("root", "", "a", operation="request"), base_row("root2", "", "a", operation="request"),
        base_row("child", "root", "b", operation="work", status="0"),
        base_row("child", "root2", "b", operation="work", status="14"),
    ]
    return complete, missing, duplicate


def authored_s05_cases():
    def make(child_ts, child_entity="service-a", duration_unit="ms"):
        rows = [base_row("p", "", "service-a", ts="1000", duration="20", operation="parent"),
                base_row("c", "p", child_entity, ts=str(child_ts), duration="5", operation="child")]
        return rows, {"timestamp_unit": "ms", "duration_unit": duration_unit}
    return {"same_3": make(1003), "same_13": make(1013), "cross_3": make(1003, "service-b"),
            "cross_13": make(1013, "service-b"), "unknown_duration": make(1003, duration_unit="unknown")}


def derive_offsets(packet):
    nodes = {node["raw"]["span_id"]: node for node in packet["nodes"]}
    facts = []
    for node in packet["nodes"]:
        parent = node["parent_reference"]
        if node["parent_resolution"] != "resolved":
            continue
        p = nodes.get(parent)
        if p is None:
            continue
        same = p["raw"]["cmdb_id"] == node["raw"]["cmdb_id"]
        facts.append({"parent": p["raw"]["span_id"], "child": node["raw"]["span_id"],
                      "offset": int(node["raw"]["timestamp"]) - int(p["raw"]["timestamp"]),
                      "unit": packet["timing_policy"]["timestamp_unit"],
                      "clock_qualification": "same_emitter_clock" if same else "cross_emitter_clock_alignment_unknown",
                      "clock_uncertainty": "none_declared" if same else "alignment_unknown",
                      "duration_raw": node["raw"]["duration"],
                      "end_timestamp": (int(node["raw"]["timestamp"]) + int(node["raw"]["duration"]))
                      if packet["timing_policy"]["duration_unit"] == packet["timing_policy"]["timestamp_unit"] else None})
    return facts


def authored_s06_cases():
    row = lambda status: base_row("s", "", "service", status=status, operation="status.case")
    return {
        "unmapped_14": ([row("14")], {"version": None, "entries": {}, "scope": "none"}, None),
        "mapped_error": ([row("14")], {"version": "producer-v1", "entries": {"14": "reported_error"}, "scope": "synthetic", "context_key": "synthetic-status-v1", "evidence_ids": ["synthetic:mapping:producer-v1"]}, None),
        "mapped_error_verified_success": ([row("14")], {"version": "producer-v1", "entries": {"14": "reported_error"}, "scope": "synthetic", "context_key": "synthetic-status-v1", "evidence_ids": ["synthetic:mapping:producer-v1"]},
                                           {"outcome": "verified_success", "evidence_id": "synthetic:verifier:success"}),
        "mapped_non_error": ([row("0")], {"version": "producer-v1", "entries": {"0": "reported_non_error"}, "scope": "synthetic", "context_key": "synthetic-status-v1", "evidence_ids": ["synthetic:mapping:producer-v1"]}, None),
    }


def interpret_status(packet):
    mapping = packet["status_mapping"]
    entries = mapping.get("entries", {})
    expected_context = mapping.get("context_key")
    actual_context = packet.get("source_reference", {}).get("producer_context")
    scope_supported = bool(entries and expected_context and actual_context == expected_context and mapping.get("evidence_ids"))
    results = []
    for node in packet["nodes"]:
        raw = node["raw"]["status_code"]
        results.append({"node": node["node_id"], "raw_status": raw,
                        "span_status_interpretation": entries.get(raw, "unknown") if scope_supported else "unknown",
                        "mapping_version": mapping.get("version"),
                        "mapping_scope": mapping.get("scope"),
                        "mapping_context_key": expected_context if scope_supported else None,
                        "mapping_evidence_ids": list(mapping.get("evidence_ids", [])) if scope_supported else []})
    request = packet.get("request_verification") or {"outcome": "unknown", "evidence_id": None}
    return {"spans": results, "request_outcome": request}


def parse_context_names():
    cases = [
        ("documented_container", "node-5.adservice-2", {"recording_entity": "node-5.adservice-2", "pod": "adservice-2", "node": "node-5", "service": "adservice", "replica": "2"}),
        ("unseen_container", "node-9.checkoutservice-7", {"recording_entity": "node-9.checkoutservice-7", "pod": "checkoutservice-7", "node": "node-9", "service": "checkoutservice", "replica": "7"}),
        ("documented_mesh", "adservice-0.destination.frontend.adservice", {"source": "adservice-0", "direction": "destination", "destination": "frontend.adservice"}),
        ("unseen_mesh", "checkoutservice-7.destination.currencyservice", {"source": "checkoutservice-7", "direction": "destination", "destination": "currencyservice"}),
        ("malformed_container", "node-xx..", None),
        ("malformed_mesh_trailing_dot", "x.destination.y.", None),
        ("malformed_mesh_empty_label", "x.destination..y", None),
    ]
    import re
    output = []
    for name, value, expected in cases:
        if ".destination." in value:
            label = r"[A-Za-z][A-Za-z0-9-]*"
            m = re.fullmatch(rf"({label})\.destination\.({label}(?:\.{label})*)", value)
            actual = {"source": m.group(1), "direction": "destination", "destination": m.group(2)} if m else None
        else:
            m = re.fullmatch(r"(node-[0-9]+)\.([A-Za-z][A-Za-z0-9-]*)-([0-9]+)", value)
            actual = {"recording_entity": value, "pod": m.group(2) + "-" + m.group(3),
                      "node": m.group(1), "service": m.group(2), "replica": m.group(3)} if m else None
        output.append({"case": name, "input": value, "actual": actual, "expected": expected,
                       "passed": actual == expected})
    return output


def context_time_check():
    seconds = "1647705600"
    milliseconds = "1647705600000"
    from datetime import datetime, timezone, timedelta
    a = datetime.fromtimestamp(int(seconds), tz=timezone.utc).astimezone(timezone(timedelta(hours=8)))
    b = datetime.fromtimestamp(int(milliseconds) / 1000, tz=timezone.utc).astimezone(timezone(timedelta(hours=8)))
    return {"seconds": seconds, "milliseconds": milliseconds, "same_instant": a == b,
            "utc_plus_8": a.isoformat(), "round_trip_seconds": int(a.timestamp()),
            "round_trip_milliseconds": int(b.timestamp() * 1000),
            "expected_local": "2022-03-20T00:00:00+08:00"}


def s08_representations(n):
    rows = []
    for i in range(n):
        root = f"r{i:03d}"; child = f"c{i:03d}"; entity = f"worker-{i:03d}"
        rows.extend([base_row(root, "", entity, ts=str(1000 + i * 10), duration="20", operation="template.root"),
                     base_row(child, root, entity, ts=str(1003 + i * 10), duration=str(i + 1), operation="template.child")])
    pointers = {row["span_id"]: {"source": f"synthetic:s08:{row['span_id']}", "row_sha256": sha_bytes(compact(row))} for row in rows}
    normalized = {"schema": "normalized-v1", "records": rows, "provenance": pointers, "quality": {"instrumentation": "authored"}}
    op_dict = {"template.root": "o0", "template.child": "o1"}
    entity_dict = {f"worker-{i:03d}": f"e{i}" for i in range(n)}
    symbolic_rows = []
    for row in rows:
        symbolic_rows.append([row["timestamp"], entity_dict[row["cmdb_id"]], row["span_id"], row["trace_id"],
                              row["duration"], row["type"], row["status_code"], op_dict[row["operation_name"]], row["parent_span"]])
    symbolic = {"schema": "symbolic-v1", "ops": {v: k for k, v in op_dict.items()}, "entities": {v: k for k, v in entity_dict.items()},
                "fields": list(RAW_FIELDS), "records": symbolic_rows, "provenance": pointers, "quality": {"instrumentation": "authored"}}
    return normalized, symbolic, rows


def expand_symbolic(packet):
    ops, entities = packet["ops"], packet["entities"]
    return [dict(zip(packet["fields"], [row[0], entities[row[1]], row[2], row[3], row[4], row[5], row[6], ops[row[7]], row[8]])) for row in packet["records"]]


def s09_requests(s06_facts):
    """Freeze exactly six slots; call only when an authorized client is configured."""
    cases = ["unmapped_14", "mapped_error", "mapped_error_verified_success"]
    prompt = ("Describe only supported status facts. Return raw_status, mapping_support, "
              "span_status_interpretation, request_outcome, evidence_ids, and explicit_unknowns. "
              "Do not infer error or request failure from an unmapped value or child status.")
    configured = bool(os.environ.get("FEATHERLESS_API_KEY"))
    slots = []
    for case in cases:
        for representation in ("normalized_json", "symbolic_packet"):
            decoded = s06_facts[case]
            if representation == "normalized_json":
                payload = {"format": "normalized_json", "records": decoded["records"],
                           "status_mapping": decoded["status_mapping"],
                           "request_verification": decoded["request_verification"],
                           "evidence_ids": [node["evidence"] for node in decoded["nodes"]],
                           "unknowns": decoded["unknowns"]}
                definition = "Normalized JSON: each record retains all nine raw fields; mapping and verifier are explicit context objects."
            else:
                raw = decoded["records"]
                payload = {"format": "symbolic_packet", "fields": list(RAW_FIELDS),
                           "operation_dictionary": {"o0": raw[0]["operation_name"]},
                           "entity_dictionary": {"e0": raw[0]["cmdb_id"]},
                           "records": [[raw[0][key] if key not in ("cmdb_id", "operation_name") else ("e0" if key == "cmdb_id" else "o0") for key in RAW_FIELDS]],
                           "status_mapping": decoded["status_mapping"],
                           "request_verification": decoded["request_verification"],
                           "evidence_ids": [node["evidence"] for node in decoded["nodes"]],
                           "unknowns": decoded["unknowns"]}
                definition = "Symbolic packet: cold operation/entity dictionaries plus a field-ordered record; mapping, verifier, evidence and unknowns remain explicit."
            slots.append({"case": case, "representation": representation, "prompt": prompt,
                          "format_definition": definition, "input_sha256": sha_bytes(compact(payload)),
                          "input_payload": payload,
                          "model": os.environ.get("FEATHERLESS_MODEL", "unconfigured"),
                          "settings": {"temperature": 0, "max_output_tokens": 300},
                          "status": "not_run" if not configured else "client_not_implemented",
                          "input_tokens": None, "output_tokens": None, "latency_ms": None, "cost": None,
                          "reason": "no authorized configured model client" if not configured else "available client is not part of this lean runner"})
    return {"call_count_requested": 6, "calls": slots, "executed": False,
            "model_access": "absent" if not configured else "configured_but_unimplemented",
            "adjudication": "not applicable; no model outputs"}


def compare_rows(actual, expected):
    if actual == expected:
        return {"passed": True, "first_difference": None}
    for index, (a, e) in enumerate(zip(actual, expected)):
        if a != e:
            return {"passed": False, "first_difference": {"index": index, "actual": a, "expected": e}}
    return {"passed": False, "first_difference": {"index": min(len(actual), len(expected)), "actual_length": len(actual), "expected_length": len(expected)}}


def validate_decoded(decoded, *, expected_rows, expected_relations, packet=None, sidecar=None, source_rows=None):
    """Apply the same pass gate to a normal decode or an intentionally mutated decode."""
    actual_relations = relation_facts(decoded)
    raw_relations = relation_facts_rows(decoded["records"])
    relation_check = {key: {"passed": actual_relations[key] == expected_relations[key],
                            "actual": actual_relations[key], "expected": expected_relations[key]}
                      for key in actual_relations}
    raw_consistency = {key: {"passed": actual_relations[key] == raw_relations[key],
                             "explicit": actual_relations[key], "raw": raw_relations[key]}
                       for key in actual_relations}
    provenance = audit_provenance(packet, sidecar, source_rows) if packet is not None and sidecar is not None and source_rows is not None else {"passed": True}
    check = {"round_trip": compare_rows(decoded["records"], expected_rows),
             "provenance": provenance, "relations": relation_check,
             "raw_consistency": raw_consistency, "quality": decoded["quality"]}
    check["passed"] = (check["round_trip"]["passed"] and check["provenance"]["passed"]
                       and all(item["passed"] for item in relation_check.values())
                       and all(item["passed"] for item in raw_consistency.values()))
    return check


def run_slice(out: Path, name: str, rows, source_ref, *, retrieval="complete", duration_unit="unknown",
              timestamp_unit="ms", status_mapping=None, request_verification=None, expected_rows=None,
              expected_relations=None):
    packet, sidecar = encode_rows(rows, name, source_ref, retrieval=retrieval, timestamp_unit=timestamp_unit, duration_unit=duration_unit,
                                  status_mapping=status_mapping, request_verification=request_verification)
    decoded = decode_packet(packet)
    write_json(out / f"{name}.packet.json", packet)
    write_json(out / f"{name}.provenance.json", sidecar)
    write_json(out / f"{name}.decoded.json", decoded)
    expected_relations = expected_relations or relation_facts_rows(expected_rows or rows)
    check = validate_decoded(decoded, expected_rows=expected_rows or rows, expected_relations=expected_relations,
                             packet=packet, sidecar=sidecar, source_rows=rows)
    return packet, decoded, check


def create_run_dir(run_id: str) -> Path:
    if not run_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in run_id):
        raise ValueError("run-id must be a simple directory name")
    out = OUT_ROOT / run_id
    out.mkdir(parents=True, exist_ok=False)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    out = create_run_dir(args.run_id)
    started = datetime.now(timezone.utc).isoformat()
    frozen_expectations = load_frozen_expectations()
    r0, r0_ref = load_r0()
    r3, r3_ref = load_r3()
    # Freeze source and authored expectations before any packet is encoded.
    freeze = {
        "protocol": "S02-S09 incremental run; S09 exploratory six-slot reduction",
        "frozen_at": started, "source_hashes": {"R0_audit": sha_file(AUDIT_R0), "R3_index": sha_file(R3_SOURCE)},
        "expectation_fixture": str(EXPECTED_S02_R3.relative_to(ROOT)),
        "expectation_fixture_sha256": sha_file(EXPECTED_S02_R3),
        "S03_relation_expectation_fixture": str(EXPECTED_S03_RELATIONS.relative_to(ROOT)),
        "S03_relation_expectation_fixture_sha256": sha_file(EXPECTED_S03_RELATIONS),
        "R0_expected": {"trace_id": frozen_expectations["R0"]["trace_id"],
                        "record_count": len(frozen_expectations["R0"]["rows"]),
                        "entity_count": len(frozen_expectations["R0"]["entities"]), "root_count": 1,
                        "raw_statuses": dict(Counter(r["status_code"] for r in frozen_expectations["R0"]["rows"])),
                        "raw_types": dict(Counter(r["type"] for r in frozen_expectations["R0"]["rows"])),
                        "rows": frozen_expectations["R0"]["rows"]},
        "R3_expected": {"trace_id": frozen_expectations["R3"]["trace_id"], "record_count": 1, "root_count": 1, "children_observed": 0},
        "S03_expected": {"changed_span": "1ef5", "new_entity": "catalog#new", "counts_and_edges_unchanged": True,
                         "relation_expectation_fixture": str(EXPECTED_S03_RELATIONS.relative_to(ROOT)),
                         "relation_expectation_fixture_sha256": sha_file(EXPECTED_S03_RELATIONS)},
        "S04_expected": {"missing_parent": "unresolved", "duplicate": "conflicting", "root_only": "empty_recorded_children_with_unknown_instrumentation"},
        "S05_expected": {"offsets_ms": {"same_3": 3, "same_13": 13, "cross_3": 3, "cross_13": 13}, "delta_ms": 10, "unknown_endpoint": None},
        "S06_expected": {"unmapped_14": "unknown", "mapped_error": "reported_error", "mapped_error_verified_success": ["reported_error", "verified_success"], "mapped_non_error": "reported_non_error"},
        "S07_expected": {"fixture": str(EXPECTED_S07.relative_to(ROOT)), "fixture_sha256": sha_file(EXPECTED_S07)},
        "S08_expected": {"instances": [1, 10, 100], "fidelity": "exact"},
        "S09_expected": {"requested_calls": 6, "cases": ["unmapped_14", "mapped_error", "mapped_error_verified_success"], "representations": ["normalized_json", "symbolic_packet"]},
    }
    write_json(out / "expected-facts.json", freeze)
    write_json(out / "expected-s02-r3.json", frozen_expectations)
    write_json(out / "s02-fact-sheet-reviewed.json", {"reviewed_once_before_encoder": True, "source": r0_ref,
                                                         "record_count": len(r0), "rows": r0})

    table = []
    r0_raw = [{key: row[key] for key in RAW_FIELDS} for row in r0]
    r0_expected = frozen_expectations["R0"]
    r0_relations = {key: r0_expected[key] for key in
                    ("entities", "counts", "parent_edges", "same_entity_pairs",
                     "different_entity_pairs", "span_count", "edge_count")}
    _, d2, c2 = run_slice(out, "S02-R0", r0, {**r0_ref, "retrieval": "complete_indexed"},
                          retrieval="complete_indexed", duration_unit="unknown",
                          expected_rows=r0_expected["rows"], expected_relations=r0_relations)
    c2["trace_id_exact"] = r0[0]["trace_id"] == r0_expected["trace_id"]
    c2["inventory_exact"] = (len(r0) == 37 and len({r["cmdb_id"] for r in r0}) == 13
                              and sum(r["parent_span"] == "" for r in r0) == 1
                              and dict(Counter(r["status_code"] for r in r0)) == r0_expected["raw_statuses"])
    c2["full_fact_sheet_review"] = True
    c2["recorded_summary"] = {"records": len(r0), "entities": len(d2["entities"]), "edges": len(d2["edges"]),
                               "statuses": dict(Counter(r["status_code"] for r in r0))}
    c2["passed"] = c2["passed"] and c2["trace_id_exact"] and c2["inventory_exact"]
    integrated_ok = c2["passed"]
    table.append({"slice": "S02", "status": "supported_on_fixture" if c2["passed"] else "falsified", "detail": c2})

    # S03 is dependent on S02; stop it if the real round trip fails.
    if integrated_ok:
        t0 = read_json(ROOT / "experiments/semantic_encoding_v1/fixtures/T0.json")
        mutated = json.loads(json.dumps(t0))
        next(r for r in mutated["records"] if r["span_id"] == "1ef5")["cmdb_id"] = "catalog#new"
        ref = {"kind": "synthetic_authored", "fixture": "T0_copy_entity_rebind"}
        frozen_s03 = read_json(EXPECTED_S03_RELATIONS)
        original_relations = frozen_s03["T0"]
        mutated_relations = frozen_s03["rebind"]
        _, d3, c3 = run_slice(out, "S03-rebind", mutated["records"], ref, timestamp_unit="ms", duration_unit="ms",
                              expected_rows=mutated["records"], expected_relations=mutated_relations)
        c3["counts_unchanged"] = mutated_relations["counts"] == original_relations["counts"]
        c3["edges_unchanged"] = mutated_relations["parent_edges"] == original_relations["parent_edges"]
        c3["same_entity_pairs_exact"] = c3["relations"]["same_entity_pairs"]["passed"]
        c3["different_entity_pairs_exact"] = c3["relations"]["different_entity_pairs"]["passed"]
        c3["changed_entity_relations_present"] = mutated_relations["same_entity_pairs"] != original_relations["same_entity_pairs"] and mutated_relations["different_entity_pairs"] != original_relations["different_entity_pairs"]
        c3["constant_relation_control_rejected"] = original_relations["same_entity_pairs"] != mutated_relations["same_entity_pairs"]
        c3["passed"] = (c3["passed"] and c3["counts_unchanged"] and c3["edges_unchanged"]
                         and c3["same_entity_pairs_exact"] and c3["different_entity_pairs_exact"]
                         and c3["changed_entity_relations_present"] and c3["constant_relation_control_rejected"])
        table.append({"slice": "S03", "status": "supported_on_fixture" if c3["passed"] else "falsified", "detail": c3})
    else:
        table.append({"slice": "S03", "status": "stopped_dependent_on_S02", "detail": {}})

    # S04-S08 use independently authored inputs and remain runnable as isolated checks.
    complete, missing, duplicate = authored_s04_cases()
    _, _, complete_check = run_slice(out, "S04-complete", complete, {"kind": "synthetic_authored"}, expected_rows=complete)
    _, missing_decoded, missing_check = run_slice(out, "S04-missing-parent", missing, {"kind": "synthetic_authored", "retrieval": "incomplete_explicit"}, retrieval="incomplete_explicit", expected_rows=missing)
    _, duplicate_decoded, duplicate_check = run_slice(out, "S04-conflicting-duplicate", duplicate, {"kind": "synthetic_authored"}, expected_rows=duplicate)
    r3_expected = frozen_expectations["R3"]
    _, r3_decoded, r3_check = run_slice(out, "S04-R3-root-only", r3, r3_ref,
                                        expected_rows=r3_expected["rows"],
                                        expected_relations={key: r3_expected[key] for key in
                                                            ("entities", "counts", "parent_edges", "same_entity_pairs",
                                                             "different_entity_pairs", "span_count", "edge_count")})
    s04_pass = (complete_check["passed"] and missing_check["passed"] and duplicate_check["passed"] and r3_check["passed"]
                and len(missing_decoded["quality"]["unresolved_parent_references"]) == 1
                and missing_decoded["quality"]["structure_completeness"] == "unknown"
                and len(duplicate_decoded["quality"]["conflicts"]) == 1
                and set(duplicate_decoded["quality"]["conflicts"][0]["nodes"]) == {"child#1", "child#2"}
                and all(node["evidence"] in duplicate_decoded["quality"]["conflicts"][0]["evidence_ids"]
                        for node in duplicate_decoded["nodes"] if node["node_id"] in {"child#1", "child#2"})
                and r3_decoded["quality"]["root_child_observation"] == "empty_recorded_children"
                and r3_decoded["quality"]["structure_completeness"] == "unknown")
    table.append({"slice": "S04", "status": "supported_on_fixture" if s04_pass else "falsified",
                  "detail": {"missing": missing_decoded["quality"], "duplicate": duplicate_decoded["quality"], "R3": r3_decoded["quality"]}})

    s05_results = {}
    for case, (rows, timing) in authored_s05_cases().items():
        _, decoded, check = run_slice(out, "S05-" + case, rows, {"kind": "synthetic_authored", "emitters": "same" if rows[0]["cmdb_id"] == rows[1]["cmdb_id"] else "different"}, duration_unit=timing["duration_unit"], expected_rows=rows)
        facts = derive_offsets(decoded)
        check["timing_facts"] = facts
        expected_offset = 13 if "13" in case else 3
        expected_clock = "cross_emitter_clock_alignment_unknown" if "cross" in case else "same_emitter_clock"
        expected_uncertainty = "alignment_unknown" if "cross" in case else "none_declared"
        check["clock_qualification_exact"] = bool(facts) and facts[0]["clock_qualification"] == expected_clock and facts[0]["clock_uncertainty"] == expected_uncertainty
        check["passed"] = (check["passed"] and facts and facts[0]["offset"] == expected_offset
                           and check["clock_qualification_exact"]
                           and (facts[0]["end_timestamp"] is None if case == "unknown_duration" else facts[0]["end_timestamp"] is not None))
        s05_results[case] = check
    s05_pass = all(c["passed"] for c in s05_results.values()) and s05_results["same_13"]["timing_facts"][0]["offset"] - s05_results["same_3"]["timing_facts"][0]["offset"] == 10
    table.append({"slice": "S05", "status": "supported_on_fixture" if s05_pass else "falsified", "detail": s05_results})

    s06_results = {}
    s06_decoded = {}
    for case, (rows, mapping, verification) in authored_s06_cases().items():
        source_ref = {"kind": "synthetic_authored", "producer_context": "synthetic-status-v1", "mapping_evidence": mapping}
        _, decoded, check = run_slice(out, "S06-" + case, rows, source_ref, duration_unit="ms", status_mapping=mapping, request_verification=verification, expected_rows=rows)
        facts = interpret_status(decoded)
        expected_status = freeze["S06_expected"][case]
        actual_status = facts["spans"][0]["span_status_interpretation"]
        expected_outcome = verification or {"outcome": "unknown", "evidence_id": None}
        check["status_facts"] = facts
        expected_value = expected_status[0] if isinstance(expected_status, list) else expected_status
        expected_scope = mapping.get("context_key") if mapping.get("entries") else None
        expected_evidence = mapping.get("evidence_ids", []) if mapping.get("entries") else []
        check["mapping_scope_exact"] = facts["spans"][0]["mapping_context_key"] == expected_scope
        check["mapping_evidence_exact"] = facts["spans"][0]["mapping_evidence_ids"] == expected_evidence
        check["passed"] = (check["passed"] and actual_status == expected_value
                           and facts["request_outcome"] == expected_outcome
                           and check["mapping_scope_exact"] and check["mapping_evidence_exact"])
        s06_results[case] = check
        s06_decoded[case] = decoded
    s06_pass = all(c["passed"] for c in s06_results.values())
    table.append({"slice": "S06", "status": "supported_on_fixture" if s06_pass else "falsified", "detail": s06_results})

    s07_time = context_time_check(); s07_names = parse_context_names(); s07_expected = read_json(EXPECTED_S07)
    expected_name_map = {(item["case"], item["input"]): item["expected"] for item in s07_expected["names"]}
    s07_name_exact = all(expected_name_map.get((item["case"], item["input"])) == item["actual"] for item in s07_names)
    s07_time_exact = all(s07_time.get(key) == value for key, value in s07_expected["time"].items())
    s07_pass = s07_time_exact and s07_name_exact and all(c["passed"] for c in s07_names)
    write_json(out / "S07-time.json", s07_time); write_json(out / "S07-names.json", s07_names)
    table.append({"slice": "S07", "status": "supported_on_fixture" if s07_pass else "falsified", "detail": {"time": s07_time, "names": s07_names, "authored_expectation_exact": s07_time_exact and s07_name_exact}})

    s08_results = []
    for n in (1, 10, 100):
        normalized, symbolic, source_rows = s08_representations(n)
        norm_bytes, sym_bytes = len(compact(normalized)), len(compact(symbolic))
        normalized_roundtrip = normalized["records"] == source_rows
        symbolic_roundtrip = expand_symbolic(symbolic) == source_rows
        normalized_schema = {"schema": normalized["schema"], "quality": normalized["quality"]}
        normalized_payload = {"records": normalized["records"], "provenance": normalized["provenance"]}
        symbolic_dictionary_schema = {"schema": symbolic["schema"], "ops": symbolic["ops"], "entities": symbolic["entities"], "fields": symbolic["fields"]}
        symbolic_payload = {"records": symbolic["records"], "provenance": symbolic["provenance"], "quality": symbolic["quality"]}
        normalized_schema_bytes = len(compact(normalized_schema))
        normalized_payload_bytes = len(compact(normalized_payload))
        dictionary_schema_bytes = len(compact(symbolic_dictionary_schema))
        symbolic_payload_bytes = len(compact(symbolic_payload))
        result = {"instances": n, "reuse_population": n,
                  "normalized_bytes_cold": norm_bytes, "symbolic_bytes_cold": sym_bytes,
                  "normalized_schema_bytes": normalized_schema_bytes, "normalized_payload_bytes": normalized_payload_bytes,
                  "dictionary_schema_bytes_cold": dictionary_schema_bytes, "symbolic_payload_bytes": symbolic_payload_bytes,
                  "normalized_bytes_amortized_per_instance": (normalized_schema_bytes + normalized_payload_bytes) / n,
                  "symbolic_bytes_amortized_per_instance": (dictionary_schema_bytes + symbolic_payload_bytes) / n,
                  "amortized_formula": "(cold_dictionary_schema_bytes + symbolic_payload_bytes) / reuse_population",
                  "ratio_symbolic_over_normalized_cold": sym_bytes / norm_bytes,
                  "ratio_symbolic_over_normalized_amortized": ((dictionary_schema_bytes + symbolic_payload_bytes) / n) / ((normalized_schema_bytes + normalized_payload_bytes) / n),
                  "normalized_exact": normalized_roundtrip, "symbolic_exact": symbolic_roundtrip,
                  "symbolic_smaller_cold": sym_bytes < norm_bytes,
                  "symbolic_smaller_amortized": (dictionary_schema_bytes + symbolic_payload_bytes) / n < (normalized_schema_bytes + normalized_payload_bytes) / n}
        s08_results.append(result); write_json(out / f"S08-{n}.json", {"normalized": normalized, "symbolic": symbolic, "result": result})
    s08_pass = all(r["normalized_exact"] and r["symbolic_exact"] and r["symbolic_smaller_cold"] and r["symbolic_smaller_amortized"] for r in s08_results)
    table.append({"slice": "S08", "status": "supported_on_fixture" if s08_pass else "falsified", "detail": s08_results})

    s09 = s09_requests(s06_decoded)
    s09["reason"] = "live credential-authenticated transport was blocked by automatic review; deterministic six-slot request freeze retained"
    write_json(out / "S09-calls.json", s09)
    table.append({"slice": "S09", "status": "not_run" if not s09["executed"] else "supported_on_fixture", "detail": s09})

    manifest = {"run_id": args.run_id, "started": started, "finished": datetime.now(timezone.utc).isoformat(),
                "python": sys.version, "platform": platform.platform(), "slices": [r["slice"] for r in table],
                "source_hashes": freeze["source_hashes"], "expected_facts_sha256": sha_file(out / "expected-facts.json"),
                "code_sha256": sha_file(Path(__file__)), "s09_requested_calls": 6, "model_credentials_present": bool(os.environ.get("FEATHERLESS_API_KEY"))}
    write_json(out / "manifest.json", manifest)
    write_json(out / "fact-diff.json", table)
    rows = ["| Slice | Status | First differing fact / note |", "|---|---|---|"]
    for item in table:
        note = "none" if item["status"] == "supported_on_fixture" else ("live transport deferred/blocked; six slots frozen" if item["status"] == "not_run" else "see detail")
        rows.append(f"| {item['slice']} | {item['status']} | {note} |")
    result_md = "# S02-S09 lean incremental result\n\n" + "\n".join(rows) + "\n\n"
    result_md += "S02 used the hash-checked frozen prior-audit expectation sheet and compared all nine raw fields, exact parent edges, entities, counts, entity relations and one-to-one provenance pointers. S04-S08 are isolated authored checks. S09 has six frozen case/representation slots but live transport is deferred to the separate client; no model responses or token counts are claimed in this deterministic run.\n"
    (out / "result.md").write_text(result_md)
    print(result_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
