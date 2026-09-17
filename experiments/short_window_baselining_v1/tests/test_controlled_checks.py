"""Contract tests for copied-observation interventions."""

from __future__ import annotations

from experiments.short_window_baselining_v1.controlled_checks import (
    apply_intervention,
    evaluate_records,
    run_control_checks,
)


def _record(index: int, role: str, duration_ms: float, *, replica: str = "frontend-0", child_count: int = 1) -> dict:
    return {
        "trace_id": f"trace-{role}-{index}",
        "span_id": f"span-{role}-{index}",
        "cmdb_id": replica,
        "role": role,
        "operation_name": "Frontend/Recv.",
        "type": "http",
        "timestamp_ms": index * 60_000,
        "start_ms": index * 60_000,
        "duration_ms": duration_ms,
        "source_file": "synthetic.csv",
        "source_record": index + 2,
        "source_header": 1,
        "children": [
            {
                "trace_id": f"trace-{role}-{index}",
                "span_id": f"child-{role}-{index}-{child_index}",
                "parent_span": f"span-{role}-{index}",
                "operation_name": "Checkout/PlaceOrder",
                "type": "rpc",
            }
            for child_index in range(child_count)
        ],
        "structure_status": "resolved",
    }


def _fixture() -> list[dict]:
    references = []
    for index in range(100):
        row = _record(index, "reference", 100.0 + index, replica="frontend-0" if index % 2 == 0 else "frontend-1")
        # Ten observations in each of the ten minutes immediately preceding
        # the synthetic anchor provide count, occupied-minute, and replica
        # support for both pooled and same-replica policies.
        row["timestamp_ms"] = (index // 10) * 60_000
        row["start_ms"] = row["timestamp_ms"]
        row["max_recorded_end_us"] = row["timestamp_ms"] * 1000 + int(row["duration_ms"] * 1000)
        references.append(row)
    query_a = _record(101, "query", 100.0, replica="frontend-0")
    query_b = _record(102, "query", 100.0, replica="frontend-1")
    for row in (query_a, query_b):
        row["timestamp_ms"] = 600_000
        row["start_ms"] = 600_000
        row["max_recorded_end_us"] = row["timestamp_ms"] * 1000 + int(row["duration_ms"] * 1000)
    return [*references, query_a, query_b]


def test_evaluate_records_uses_reusable_signature_selector_and_duration_comparator() -> None:
    result = evaluate_records(_fixture(), mode="C0")
    assert result["reference_count"] == 100
    assert result["query_count"] == 2
    assert result["matched_query_count"] == 2
    assert all(row["median_ms"] == 149.5 for row in result["comparisons"])
    assert all(row["absolute_excess_ms"] == -49.5 for row in result["comparisons"])


def test_duration_interventions_keep_source_membership_and_add_exact_excess() -> None:
    original = _fixture()
    baseline = evaluate_records(original, mode="C0")
    transformed = apply_intervention(original, "query_duration_plus_25_percent")["records"]
    after = evaluate_records(transformed, mode="C0")

    assert baseline["membership_hash"] == after["membership_hash"]
    assert [row["absolute_excess_ms"] for row in after["comparisons"]] == [-24.5, -24.5]
    assert all(row["control_source"]["source_file"] == "synthetic.csv" for row in transformed)
    assert all(row["control_original_identity"] == [row["trace_id"], row["span_id"]] for row in transformed)


def test_id_rename_and_reorder_preserves_inverse_source_links() -> None:
    original = _fixture()
    result = apply_intervention(original, "reorder_and_rename_ids")
    transformed = result["records"]
    manifest = result["manifest"]

    assert len(transformed) == len(original)
    assert manifest["inverse_id_mapping_required"] is True
    assert manifest["input_membership_hash"] != manifest["output_membership_hash"]
    assert {tuple(link["original"].values()) for link in result["source_links"]}  # all source pointers survive
    assert all("control_source" in row for row in transformed)
    original_child_ids = {
        (child["trace_id"], child["span_id"])
        for row in original
        for child in row["children"]
    }
    transformed_child_ids = {
        (child["trace_id"], child["span_id"])
        for row in transformed
        for child in row["children"]
    }
    assert original_child_ids.isdisjoint(transformed_child_ids)


def test_thinning_only_removes_reference_rows_and_records_insufficient_support() -> None:
    original = _fixture()
    thinned = apply_intervention(original, "thin_references", target_count=10, seed=1)
    rows = thinned["records"]
    assert sum(row["role"] == "reference" for row in rows) == 10
    assert sum(row["role"] == "query" for row in rows) == 2
    assert thinned["manifest"]["insufficient_original_support"] is False

    over_target = apply_intervention(original, "thin_references", target_count=200, seed=1)
    assert len(over_target["records"]) == len(original)
    assert over_target["manifest"]["insufficient_original_support"] is True


def test_shape_and_retrieval_interventions_never_drop_observations() -> None:
    original = _fixture()
    for name in ("add_novel_direct_child", "remove_direct_child", "change_child_multiplicity_only", "remove_children_mark_incomplete"):
        result = apply_intervention(original, name)
        assert len(result["records"]) == len(original)
        assert all("control_source" in row for row in result["records"])

    added = apply_intervention(original, "add_novel_direct_child")["records"]
    added_query = [row for row in added if row["role"] == "query"]
    added_reference = [row for row in added if row["role"] == "reference"]
    assert all(len(row["children"]) == 2 for row in added_query)
    assert all(row["children"][-1]["control_added"] is True for row in added_query)
    assert all(len(row["children"]) == 1 for row in added_reference)
    incomplete = apply_intervention(original, "remove_children_mark_incomplete")["records"]
    assert all(row["structure_status"] == "unknown_structure" for row in incomplete)


def test_run_control_checks_is_manifest_backed_and_never_certifies_health() -> None:
    import json

    result = run_control_checks(_fixture())
    names = {row["name"] for row in result["checks"]}
    assert {"query_duration_plus_25_percent", "query_duration_plus_50_percent", "query_duration_plus_100_percent"} <= names
    assert "thin_references" in names
    assert result["health_certification"] == "never_emitted"
    assert all(row["health_certified"] is False for row in result["checks"])
    assert result["zero_silent_losses"] is True
    assert result["all_checks_pass"] is True
    json.dumps(result, sort_keys=True)
