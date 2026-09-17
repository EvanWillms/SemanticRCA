"""Trace closure and structural qualification contracts."""

from __future__ import annotations

from experiments.short_window_baselining_v1.observations import build_observation, group_root_rows


def _span(
    span_id: str,
    trace_id: str = "trace-a",
    parent_span: str = "",
    timestamp_ms: int = 1_000,
    duration_us: int = 2_000,
    component: str = "frontend-0",
    operation_name: str = "Frontend/Recv.",
    span_type: str = "http",
    source_record: int = 2,
) -> dict:
    return {
        "span_id": span_id,
        "trace_id": trace_id,
        "parent_span": parent_span,
        "timestamp_ms": timestamp_ms,
        "duration_us": duration_us,
        "duration_raw": str(duration_us),
        "cmdb_id": component,
        "operation_name": operation_name,
        "type": span_type,
        "source_file": "day.csv",
        "source_record": source_record,
        "source_header": 1,
    }


def test_observation_preserves_microsecond_conversion_children_and_endpoint_provenance() -> None:
    root = _span("root", timestamp_ms=1_000, duration_us=5_000)
    child = _span(
        "child",
        parent_span="root",
        timestamp_ms=1_001,
        duration_us=2_000,
        component="checkoutservice-2",
        operation_name="Checkout/PlaceOrder",
        span_type="rpc",
        source_record=3,
    )
    observation = build_observation([root], [root, child])

    assert observation["root_key"] == ["trace-a", "root"]
    assert observation["duration_raw"] == "5000"
    assert observation["duration_us"] == 5_000
    assert observation["duration_ms"] == 5.0
    assert observation["root_end_us"] == 1_005_000
    assert observation["max_recorded_end_us"] == 1_005_000
    assert observation["recorded_span_count"] == 2
    assert observation["raw_root_records"] == 1
    assert observation["structure_status"] == "resolved"
    assert observation["direct_children"][0]["source_record"] == 3
    assert observation["direct_children"][0]["cmdb_id"] == "checkoutservice-2"


def test_missing_parent_and_cycle_are_qualified_as_unknown_structure() -> None:
    root = _span("root")
    orphan = _span("orphan", parent_span="missing", component="checkoutservice-2")
    cycle_a = _span("cycle-a", parent_span="cycle-b", component="checkoutservice-2")
    cycle_b = _span("cycle-b", parent_span="cycle-a", component="checkoutservice-2")
    observation = build_observation([root], [root, orphan, cycle_a, cycle_b])

    assert observation["structure_status"] == "unknown_structure"
    assert observation["flags"]["missing_parents"] == ["missing"]
    assert observation["flags"]["cycles"]
    assert observation["direct_children"] == []


def test_duplicate_composite_identity_and_ambiguous_roots_are_visible() -> None:
    root = _span("root")
    duplicate = _span("child", parent_span="root", source_record=3)
    duplicate_again = _span("child", parent_span="root", source_record=4)
    observation = build_observation([root, dict(root)], [root, duplicate, duplicate_again])

    assert observation["structure_status"] == "unknown_structure"
    assert observation["flags"]["duplicate_root_rows"] is True
    assert observation["flags"]["duplicate_identity"] == [["trace-a", "child"]]
    assert observation["raw_root_records"] == 2
    assert observation["recorded_span_count"] == 3


def test_known_empty_children_are_distinct_from_unresolved_trace_retrieval() -> None:
    root = _span("root")
    empty = build_observation([root], [root])
    unresolved = build_observation([root], [root, _span("orphan", parent_span="missing")])

    assert empty["structure_status"] == "empty_recorded_children"
    assert empty["signature"]["C1"]["direct_child_set"] == []
    assert unresolved["structure_status"] == "unknown_structure"
    assert unresolved["signature"]["C1"]["direct_child_set"] is None


def test_missing_root_record_is_unresolved_and_extra_blank_parent_root_is_ambiguous() -> None:
    root = _span("root")
    missing_root = build_observation([root], [])
    extra_root = _span("extra-root", trace_id="trace-a", timestamp_ms=1_001)
    ambiguous = build_observation([root], [root, extra_root])

    assert missing_root["structure_status"] == "unknown_structure"
    assert missing_root["flags"].get("missing_root_record") is True
    assert ambiguous["structure_status"] == "unknown_structure"
    assert ambiguous["flags"].get("multiple_blank_parent_roots") is True
    assert ambiguous["flags"].get("blank_parent_roots") == ["extra-root", "root"]


def test_trace_id_mismatch_is_retained_and_grouping_uses_composite_identity() -> None:
    root_a = _span("root", trace_id="trace-a")
    foreign = _span("foreign", trace_id="trace-b")
    observation = build_observation([root_a], [root_a, foreign])
    assert observation["structure_status"] == "unknown_structure"
    assert observation["flags"]["trace_id_mismatch"] == ["trace-b"]

    roots = [root_a, dict(root_a), _span("root", trace_id="trace-b")]
    grouped = group_root_rows(roots)
    assert set(grouped) == {("trace-a", "root"), ("trace-b", "root")}
    assert len(grouped[("trace-a", "root")]) == 2
