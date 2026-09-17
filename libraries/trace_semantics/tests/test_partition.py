import copy

import pytest
from trace_semantics.partition import EncodingPolicy, partition_traces


def test_empty_partition_has_versioned_json_shape():
    result = partition_traces([])

    assert result == {
        "schema_version": "trace-semantics-v1",
        "policy": {
            "version": "trace-semantics-v1",
            "operation_mappings": {},
            "timestamp_unit": None,
            "duration_unit": None,
        },
        "traces": [],
        "deferred": [],
    }


def test_policy_is_frozen_and_serialized_without_aliasing_mapping():
    mappings = {"GET /health": "http_request"}
    policy = EncodingPolicy(operation_mappings=mappings)
    mappings["POST /write"] = "http_request"

    assert policy.operation_mappings == {"GET /health": "http_request"}
    assert partition_traces([], policy)["policy"]["operation_mappings"] == {
        "GET /health": "http_request"
    }


def test_known_operation_keeps_raw_trace_and_emits_one_recorded_node():
    raw_span = {
        "trace_id": "t1",
        "span_id": "s1",
        "parent_span": "",
        "cmdb_id": "frontend",
        "operation_name": "GET /health",
        "type": "server",
        "status_code": "OK",
        "timestamp": "1000",
        "duration": "2",
    }
    trace = {
        "trace_id": "t1",
        "deployment": "prod-a",
        "context": {"timestamp_unit": "ms", "duration_unit": "ms"},
        "spans": [{"raw": raw_span, "locator": {"source": "traces.json", "row": 8}}],
    }

    result = partition_traces(
        [trace],
        EncodingPolicy(
            operation_mappings={"GET /health": "http_request"},
            timestamp_unit="ms",
            duration_unit="ms",
        ),
    )
    partitioned = result["traces"][0]
    node = partitioned["nodes"][0]

    assert partitioned["raw"] == trace
    assert partitioned["evidence"][0]["raw"] == raw_span
    assert partitioned["evidence"][0]["locator"] == {"source": "traces.json", "row": 8}
    assert node["span_id"] == "s1"
    assert node["record_count"] == 1
    assert node["occurrence_count"] == 1
    assert node["semantic_operation"] == "http_request"
    assert node["occurrences"][0]["raw"] == raw_span


def test_non_json_input_is_rejected_before_partial_processing():
    with pytest.raises(TypeError, match="JSON-compatible"):
        partition_traces(([] ,))
    with pytest.raises(TypeError, match="JSON-compatible"):
        partition_traces([{"trace_id": "t", "deployment": "d", "spans": [], "extra": object()}])
    with pytest.raises(TypeError, match="JSON-compatible"):
        partition_traces([{"trace_id": "t", "deployment": "d", "spans": [], 7: "numeric key"}])


def test_numeric_string_timing_is_retained_but_deferred():
    trace = {
        "trace_id": "t2",
        "deployment": "prod-a",
        "spans": [{
            "raw": {
                "trace_id": "t2", "span_id": "s1", "parent_span": "",
                "cmdb_id": "worker", "operation_name": "READ", "type": "server",
                "status_code": "0", "timestamp": "NaN", "duration": "4",
            },
            "locator": {"source": "fixture.json", "row": 1},
        }],
    }
    result = partition_traces(
        [trace],
        EncodingPolicy(operation_mappings={"READ": "storage_read"}, timestamp_unit="ms", duration_unit="ms"),
    )

    timing = result["traces"][0]["nodes"][0]["timing"]
    assert timing["timestamp"] == "NaN"
    assert any(item["reason"] == "invalid_timing_value" for item in result["deferred"])


def test_csv_numeric_strings_are_valid_when_policy_declares_units():
    trace = {
        "trace_id": "t3", "deployment": "prod-a", "spans": [{"raw": {
            "trace_id": "t3", "span_id": "s1", "parent_span": "",
            "cmdb_id": "worker", "operation_name": "READ", "type": "server",
            "status_code": "200", "timestamp": "1000", "duration": "4",
        }, "locator": {"source": "fixture.csv", "row": 2}}],
    }

    result = partition_traces(
        [trace], EncodingPolicy(operation_mappings={"READ": "storage_read"}, timestamp_unit="ms", duration_unit="ms")
    )

    assert result["traces"][0]["nodes"][0]["timing"]["valid"] is True
    assert not any(item["reason"] == "invalid_timing_value" for item in result["deferred"])


def _span(span_id="s1", **changes):
    value = {
        "trace_id": "t4", "span_id": span_id, "parent_span": "",
        "cmdb_id": "worker", "operation_name": "READ", "type": "server",
        "status_code": "200", "timestamp": "1000", "duration": "4",
    }
    value.update(changes)
    return {"raw": value, "locator": {"source": "fixture.csv", "row": 1}}


def test_missing_required_raw_field_is_deferred_and_does_not_become_a_root():
    raw = _span()["raw"]
    del raw["parent_span"]
    result = partition_traces([{"trace_id": "t4", "deployment": "prod-a", "spans": [{"raw": raw, "locator": {"row": 1}}]}])

    assert any(item["reason"] == "missing_field" and item["facet"] == "record" for item in result["deferred"])
    assert result["traces"][0]["edges"] == []


def test_malformed_parent_value_is_deferred_without_hashing_or_crashing():
    result = partition_traces([{
        "trace_id": "t4", "deployment": "prod-a",
        "spans": [_span("s1", parent_span=[]), _span("s2", parent_span="s1")],
    }])

    assert any(item["reason"] == "malformed_parent" for item in result["deferred"])


def test_exact_duplicate_records_keep_physical_evidence_without_inflating_occurrence():
    first = _span("same")
    second = copy.deepcopy(first)
    second["locator"] = {"source": "fixture.csv", "row": 9}
    result = partition_traces([{"trace_id": "t4", "deployment": "prod-a", "spans": [first, second]}])

    node = result["traces"][0]["nodes"][0]
    assert node["record_count"] == 2
    assert node["occurrence_count"] == 1
    assert len(node["occurrences"]) == 2
    assert result["traces"][0]["coverage"]["occurrence_count"] == 1


def test_changed_raw_record_with_same_span_id_is_a_conflict_without_winner():
    result = partition_traces([{
        "trace_id": "t4", "deployment": "prod-a",
        "spans": [_span("same", duration="4"), _span("same", duration="5")],
    }], EncodingPolicy(operation_mappings={"READ": "storage_read"}))

    node = result["traces"][0]["nodes"][0]
    assert node["identity_conflict"] is True
    assert node["occurrence_count"] is None
    assert node["semantic_operation"] is None
    assert node["operation_name"] is None
    assert any(item["reason"] == "conflicting_identity" for item in result["deferred"])


def test_conflict_deferrals_reference_each_record_and_keep_group_membership():
    result = partition_traces([{
        "trace_id": "t4", "deployment": "prod-a",
        "spans": [
            _span("same", duration="4"),
            _span("same", duration="5"),
            _span("same", duration="6"),
        ],
    }])

    node = result["traces"][0]["nodes"][0]
    evidence_ids = [occurrence["evidence_id"] for occurrence in node["occurrences"]]
    conflict_deferrals = [
        item for item in result["deferred"] if item["reason"] == "conflicting_identity"
    ]

    assert [item["evidence_ids"] for item in conflict_deferrals] == [[evidence_id] for evidence_id in evidence_ids]
    assert [item["raw"]["duration"] for item in conflict_deferrals] == ["4", "5", "6"]
    assert len(evidence_ids) == 3


def test_unknown_operation_and_status_defer_locally_while_known_node_survives():
    result = partition_traces([{
        "trace_id": "t4", "deployment": "prod-a",
        "spans": [_span("known"), _span("unknown", operation_name="NEW_OP", status_code="ERR")],
    }], EncodingPolicy(operation_mappings={"READ": "storage_read"}))

    nodes = result["traces"][0]["nodes"]
    assert nodes[0]["semantic_operation"] == "storage_read"
    assert nodes[1]["semantic_operation"] is None
    assert any(item["reason"] == "unknown_operation" and item["span_id"] == "unknown" for item in result["deferred"])
    assert sum(item["reason"] == "unknown_status" for item in result["deferred"]) == 2


def test_parent_edges_are_trace_scoped_and_unresolved_for_missing_or_self_links():
    left_root = _span("root")
    left_child = _span("child", parent_span="root")
    right_root = _span("root")
    right_child = _span("child", parent_span="root")
    left_root["raw"]["trace_id"] = "left"
    left_child["raw"]["trace_id"] = "left"
    right_root["raw"]["trace_id"] = "right"
    right_child["raw"]["trace_id"] = "right"
    left_missing = _span("missing-child", parent_span="does-not-exist")
    left_missing["raw"]["trace_id"] = "left"
    self_link = _span("self", parent_span="self")
    self_link["raw"]["trace_id"] = "left"
    result = partition_traces([
        {"trace_id": "left", "deployment": "prod-a", "spans": [left_root, left_child, left_missing, self_link]},
        {"trace_id": "right", "deployment": "prod-a", "spans": [right_root, right_child]},
    ])

    left_edges = result["traces"][0]["edges"]
    right_edges = result["traces"][1]["edges"]
    assert any(edge["child_span_id"] == "child" and edge["resolved"] for edge in left_edges)
    assert any(edge["child_span_id"] == "child" and edge["resolved"] for edge in right_edges)
    assert any(edge["child_span_id"] == "missing-child" and not edge["resolved"] for edge in left_edges)
    assert any(edge["child_span_id"] == "self" and not edge["resolved"] for edge in left_edges)
    assert any(item["reason"] == "missing_parent" for item in result["deferred"])
    assert any(item["reason"] == "self_parent" for item in result["deferred"])


def test_deep_parent_cycle_is_detected_iteratively():
    spans = []
    depth = 250
    for index in range(depth):
        parent = str(index - 1) if index else str(depth - 1)
        spans.append(_span(str(index), parent_span=parent))
        spans[-1]["raw"]["trace_id"] = "cycle"
    result = partition_traces([{"trace_id": "cycle", "deployment": "prod-a", "spans": spans}])

    assert all(not edge["resolved"] for edge in result["traces"][0]["edges"])
    assert any(item["reason"] == "cyclic_parent" for item in result["deferred"])


def test_span_from_another_trace_is_retained_but_never_promoted_or_mapped():
    foreign = _span("foreign")
    foreign["raw"]["trace_id"] = "other"
    result = partition_traces([{"trace_id": "t4", "deployment": "prod-a", "spans": [foreign]}], EncodingPolicy(operation_mappings={"READ": "storage_read"}))

    assert result["traces"][0]["nodes"] == []
    assert result["traces"][0]["evidence"][0]["raw"] == foreign["raw"]
    assert any(item["reason"] == "trace_id_mismatch" for item in result["deferred"])


def test_duplicate_trace_envelopes_merge_evidence_and_retain_every_raw_envelope():
    first = {"trace_id": "dup", "deployment": "prod-a", "context": {"duration_unit": "ms"}, "spans": [_span("s1")]}
    first["spans"][0]["raw"]["trace_id"] = "dup"
    second = copy.deepcopy(first)
    second["context"] = {"duration_unit": "s"}
    second["spans"][0]["locator"] = {"source": "other.csv", "row": 3}
    result = partition_traces([first, second])

    trace = result["traces"][0]
    assert len(result["traces"]) == 1
    assert trace["raw_envelopes"] == [first, second]
    assert trace["coverage"]["record_count"] == 2
    assert any(item["reason"] == "duplicate_trace_envelope" for item in result["deferred"])
    assert any(item["reason"] == "conflicting_timing_unit" for item in result["deferred"])


def test_partition_is_detached_and_serialization_is_repeatable():
    source = {"trace_id": "copy", "deployment": "prod-a", "spans": [_span("s1")]}
    source["spans"][0]["raw"]["trace_id"] = "copy"
    before = copy.deepcopy(source)
    first = partition_traces([source])
    source["spans"][0]["raw"]["duration"] = "999"
    second = partition_traces([before])

    assert source != first["traces"][0]["raw"]
    assert first == second
