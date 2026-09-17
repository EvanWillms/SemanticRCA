from trace_semantics import EncodingPolicy, encode_traces
from trace_semantics.description import canonical_json, describe


def _raw_span(trace_id, span_id, operation, parent=""):
    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span": parent,
        "cmdb_id": "frontend-1",
        "operation_name": operation,
        "type": "http",
        "status_code": "200",
        "timestamp": "1000",
        "duration": "12",
    }


def _partition_with_mixed_nodes():
    raw = {
        "trace_id": "trace-1",
        "deployment": "prod-a",
        "context": {"route": "/cart"},
        "spans": [
            {"raw": _raw_span("trace-1", "root", "GET /cart"), "locator": {"record": 2}},
            {"raw": _raw_span("trace-1", "child", "mystery.read", "root"), "locator": {"record": 3}},
        ],
    }
    return {
        "schema_version": "trace-semantics-v1",
        "policy": {
            "version": "ops-v1",
            "operation_mappings": {"GET /cart": "cart.request"},
            "timestamp_unit": "ms",
            "duration_unit": "ms",
        },
        "traces": [
            {
                "trace_id": "trace-1",
                "deployment": "prod-a",
                "raw": raw,
                "nodes": [
                    {
                        "span_id": "root",
                        "operation_name": "GET /cart",
                        "semantic_operation": "cart.request",
                        "occurrence_count": 1,
                    },
                    {
                        "span_id": "child",
                        "operation_name": "mystery.read",
                        "semantic_operation": None,
                        "occurrence_count": 1,
                    },
                ],
                "edges": [{"child_span_id": "child", "parent_span_id": "root", "resolved": True}],
                "evidence": [
                    {"locator": {"record": 3}, "raw": _raw_span("trace-1", "child", "mystery.read", "root")},
                    {"locator": {"record": 2}, "raw": _raw_span("trace-1", "root", "GET /cart")},
                ],
                "coverage": {"record_count": 2, "occurrence_count": 2},
            }
        ],
        "deferred": [
            {"reason": "unknown_operation", "facet": "operation", "trace_id": "trace-1", "span_id": "child", "raw": "mystery.read"}
        ],
    }


def test_describe_empty_partition_returns_versioned_empty_result():
    assert describe({
        "schema_version": "trace-semantics-v1",
        "policy": {"version": "ops-v1", "operation_mappings": {}},
        "traces": [],
        "deferred": [],
    }) == {
        "schema_version": "trace-description-v1",
        "policy": {"version": "ops-v1", "operation_mappings": {}},
        "meaning_dictionary": {"version": "ops-v1", "operations": []},
        "traces": [],
        "deferred": [],
        "counts": [],
    }


def test_describe_preserves_raw_evidence_and_mixed_operation_counts():
    result = describe(_partition_with_mixed_nodes())
    trace = result["traces"][0]

    assert trace["raw"]["context"] == {"route": "/cart"}
    assert trace["edges"] == [{"child_span_id": "child", "parent_span_id": "root", "resolved": True}]
    assert trace["counts"] == [
        {"raw_operation": "GET /cart", "meaning": "cart.request", "count": 1},
        {"raw_operation": "mystery.read", "meaning": None, "count": 1},
    ]
    assert result["deferred"][0]["reason"] == "unknown_operation"
    assert result["meaning_dictionary"]["operations"] == [
        {"raw": "GET /cart", "meaning": "cart.request"},
        {"raw": "mystery.read", "meaning": None},
    ]


def test_encode_traces_wires_partition_early_deferral_and_stable_serialization():
    traces = [_partition_with_mixed_nodes()["traces"][0]["raw"]]
    policy = EncodingPolicy(
        version="ops-v1",
        operation_mappings={"GET /cart": "cart.request"},
        timestamp_unit="ms",
        duration_unit="ms",
    )

    first = encode_traces(traces, policy)
    second = encode_traces(traces, policy)

    assert first["traces"][0]["raw"] == traces[0]
    assert {item["reason"] for item in first["deferred"]} >= {"unknown_operation", "unknown_status"}
    assert canonical_json(first) == canonical_json(second)
