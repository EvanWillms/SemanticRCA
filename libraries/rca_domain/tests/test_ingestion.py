import copy

import pytest

from rca_domain.ingestion import from_semantic_traces


SCOPE = {
    "case_id": "case-1",
    "deployment": "prod-a",
    "incident_count": 1,
    "projection": ["component", "reason", "occurrence_time"],
    "window_start": "2026-09-17T00:00:00+08:00",
    "window_end": "2026-09-17T01:00:00+08:00",
}


def native_description():
    raw = {
        "trace_id": "trace-1",
        "span_id": "span-1",
        "parent_span": "",
        "cmdb_id": "frontend-1",
        "operation_name": "GET /cart",
        "type": "http",
        "status_code": "200",
        "timestamp": "1000",
        "duration": "25",
    }
    locator = {"path": "telemetry/trace.csv", "record": 2, "source_digest": "sha"}
    return {
        "schema_version": "trace-description-v1",
        "policy": {
            "version": "operations-v1",
            "operation_mappings": {"GET /cart": "cart.request"},
            "timestamp_unit": "ms",
            "duration_unit": "ms",
        },
        "meaning_dictionary": {
            "version": "operations-v1",
            "operations": [{"raw": "GET /cart", "meaning": "cart.request"}],
        },
        "traces": [{
            "trace_id": "trace-1",
            "deployment": "prod-a",
            "raw": {
                "trace_id": "trace-1",
                "deployment": "prod-a",
                "recorded_recovery": "complete_relative_to_snapshot",
                "context": {"timestamp_unit": "ms", "duration_unit": "ms"},
            },
            "coverage": {
                "record_count": 1,
                "occurrence_count": 1,
                "conflicting_identity_count": 0,
            },
            "evidence": [{
                "evidence_id": "e-1",
                "trace_id": "trace-1",
                "deployment": "prod-a",
                "raw": raw,
                "locator": locator,
                "record": {"raw": raw, "locator": locator},
                "ordinal": 0,
                "span_id": "span-1",
            }],
            "nodes": [{
                "span_id": "span-1",
                "identity": {
                    "trace_id": "trace-1",
                    "span_id": "span-1",
                    "cmdb_id": "frontend-1",
                    "operation_name": "GET /cart",
                    "type": "http",
                },
                "identity_conflict": False,
                "record_count": 1,
                "occurrence_count": 1,
                "occurrences": [{"evidence_id": "e-1", "raw": raw, "locator": locator}],
                "semantic_operation": "cart.request",
                "operation_name": "GET /cart",
                "cmdb_id": "frontend-1",
                "type": "http",
                "status_code": "200",
                "timing": {
                    "timestamp": "1000",
                    "duration": "25",
                    "timestamp_unit": "ms",
                    "duration_unit": "ms",
                },
            }],
            "edges": [],
            "counts": [{
                "deployment": "prod-a",
                "trace_id": "trace-1",
                "operations": [{"raw_operation": "GET /cart", "meaning": "cart.request", "count": 1}],
            }],
        }],
        "deferred": [{
            "reason": "unknown_status",
            "facet": "status",
            "trace_id": "trace-1",
            "span_id": "span-1",
            "evidence_ids": ["e-1"],
            "raw": {"status_code": "200"},
        }],
        "counts": [{
            "deployment": "prod-a",
            "trace_id": "trace-1",
            "operations": [{"raw_operation": "GET /cart", "meaning": "cart.request", "count": 1}],
        }],
    }


def envelope(description=None, *, packet_id="packet-1", source_snapshot_id="snapshot-1"):
    return {
        "packet_id": packet_id,
        "source_snapshot_id": source_snapshot_id,
        "description": native_description() if description is None else description,
    }


def test_from_semantic_traces_preserves_native_evidence_and_unknowns_detached():
    source = envelope()
    original = copy.deepcopy(source)

    result = from_semantic_traces([source], SCOPE)

    assert result["schema_version"] == "rca-evidence-v1"
    assert result["revision"] == 0
    assert len(result["observations"]) == 1
    stable_id, observation = next(iter(result["observations"].items()))
    assert observation == {
        "evidence_id": stable_id,
        "source_snapshot_id": "snapshot-1",
        "deployment": "prod-a",
        "trace_id": "trace-1",
        "span_id": "span-1",
        "semantic_operation": "cart.request",
        "recording_component": "frontend-1",
        "raw": original["description"]["traces"][0]["evidence"][0]["raw"],
        "locator": original["description"]["traces"][0]["evidence"][0]["locator"],
        "conflict": False,
    }
    assert result["coverage"][0]["trace_raw"]["recorded_recovery"] == "complete_relative_to_snapshot"
    assert result["coverage"][0]["trace_raw"]["context"]["duration_unit"] == "ms"
    assert any(
        item["kind"] == "deferred" and item["item"]["reason"] == "unknown_status"
        for item in result["qualifications"]
    )
    assert result["definitions"][0]["evidence_aliases"] == {"e-1": stable_id}

    source["description"]["traces"][0]["evidence"][0]["raw"]["status_code"] = "changed"
    assert observation["raw"]["status_code"] == "200"


def test_from_semantic_traces_collapses_identical_views_and_rejects_conflicting_identity():
    first = envelope()
    duplicate = envelope(packet_id="packet-duplicate")
    result = from_semantic_traces([first, duplicate], SCOPE)

    assert len(result["observations"]) == 1
    repeated = from_semantic_traces([first], SCOPE)
    assert next(iter(result["observations"])) == next(iter(repeated["observations"]))
    assert [entry["packet_id"] for entry in result["coverage"]] == ["packet-1", "packet-duplicate"]

    conflicting = envelope(packet_id="packet-conflict")
    conflicting["description"]["traces"][0]["evidence"][0]["raw"]["cmdb_id"] = "other"
    with pytest.raises(ValueError, match="conflicting observation identity"):
        from_semantic_traces([first, conflicting], SCOPE)


def test_from_semantic_traces_rejects_schema_or_reference_mismatch():
    bad_schema = envelope()
    bad_schema["description"]["schema_version"] = "other-v1"
    with pytest.raises(ValueError, match="trace-description-v1"):
        from_semantic_traces([bad_schema], SCOPE)

    bad_reference = envelope()
    bad_reference["description"]["traces"][0]["nodes"][0]["occurrences"][0]["evidence_id"] = "missing"
    with pytest.raises(ValueError, match="evidence reference"):
        from_semantic_traces([bad_reference], SCOPE)
