import pytest
from trace_semantics import EncodingPolicy, encode_traces
from trace_semantics.description import canonical_json, describe, description_digest


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
                    {"evidence_id": "e-child", "locator": {"record": 3}, "raw": _raw_span("trace-1", "child", "mystery.read", "root")},
                    {"evidence_id": "e-root", "locator": {"record": 2}, "raw": _raw_span("trace-1", "root", "GET /cart")},
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


def test_describe_exposes_context_and_one_scoped_structural_qualification():
    result = describe(_partition_with_mixed_nodes())
    trace = result["traces"][0]

    assert trace["context"] == {"route": "/cart"}
    assert trace["qualifications"] == [{
        "semantic_layer": "descriptive",
        "production_method": "code",
        "definition_version": "trace-description-v1",
        "policy_version": "ops-v1",
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
        "scope": {"trace_id": "trace-1", "deployment": "prod-a"},
        "evidence_ids": ["e-child", "e-root"],
        "limitations": ["no_causation", "no_outcome", "source_authenticity_unverified"],
        "applies_to": ["context", "evidence", "nodes", "edges", "counts", "deferred"],
    }]


def test_describe_rejects_forged_coverage_and_evidence_references():
    partition = _partition_with_mixed_nodes()
    partition["traces"][0]["coverage"]["record_count"] = 99
    with pytest.raises(ValueError, match="record_count"):
        describe(partition)

    partition = _partition_with_mixed_nodes()
    partition["traces"][0]["nodes"][0]["occurrences"] = [{"evidence_id": "forged"}]
    with pytest.raises(ValueError, match="evidence_id"):
        describe(partition)


def test_describe_rejects_cycles_and_non_finite_partition_values():
    cyclic = _partition_with_mixed_nodes()
    cyclic["cycle"] = cyclic
    with pytest.raises(TypeError, match="finite JSON-compatible|cyclic"):
        describe(cyclic)

    non_finite = _partition_with_mixed_nodes()
    non_finite["metadata"] = float("nan")
    with pytest.raises(TypeError, match="finite JSON-compatible"):
        describe(non_finite)


def test_canonical_json_escapes_lone_surrogates_for_digest_stability():
    description = {"text": "\ud800"}

    encoded = canonical_json(description)

    assert "\\ud800" in encoded
    assert description_digest(description) == "7d38e2388498cec03881027e7753b07826c5af2d61dd589b4c1caaab14ec2cc4"


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
