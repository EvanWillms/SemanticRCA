"""Controlled, label-free contract tests for matching and comparison semantics.

The fixtures are deliberately small and intervention based.  They test the
declared behavior of the selector/comparator; they do not claim that passing
fixtures establish sensitivity to a real incident.
"""

from __future__ import annotations

from experiments.short_window_baselining_v1.contracts import (
    bootstrap_median,
    compare_duration,
    signature_for_root,
    signature_key,
    stable_membership_hash,
    support_diagnostics,
)


def _root() -> dict:
    return {
        "trace_id": "trace-a",
        "span_id": "root-a",
        "cmdb_id": "frontend-0",
        "operation_name": "Frontend/Recv.",
        "type": "http",
        "structure_status": "resolved",
        "children": [
            {"operation_name": "Checkout/PlaceOrder", "type": "rpc"},
            {"operation_name": "Cart/GetCart", "type": "rpc"},
            {"operation_name": "Cart/GetCart", "type": "rpc"},
        ],
    }


def test_c0_is_root_only_while_c1_and_c2_capture_recorded_shape() -> None:
    root = _root()
    c0 = signature_for_root(root, "C0")
    c1 = signature_for_root(root, "C1")
    c2 = signature_for_root(root, "C2")

    # Structure state is retained in the structural reporting channel but is
    # not allowed to fragment the broad C0 root operation/type cohort.
    assert c0 == {
        "mode": "C0",
        "root_operation_name": "Frontend/Recv.",
        "root_type": "http",
    }
    assert c1["direct_child_set"] == [
        ["Cart/GetCart", "rpc"],
        ["Checkout/PlaceOrder", "rpc"],
    ]
    assert c2["direct_child_multiset"] == [
        ["Cart/GetCart", "rpc", 2],
        ["Checkout/PlaceOrder", "rpc", 1],
    ]


def test_shape_interventions_are_visible_without_silent_losses() -> None:
    original = _root()
    novel_child = {"operation_name": "Currency/GetSupportedCurrencies", "type": "rpc"}

    added = {**original, "children": [*original["children"], novel_child]}
    multiplied = {**original, "children": [*original["children"], {"operation_name": "Cart/GetCart", "type": "rpc"}]}

    assert signature_key(signature_for_root(original, "C0")) == signature_key(signature_for_root(added, "C0"))
    assert signature_key(signature_for_root(original, "C1")) != signature_key(signature_for_root(added, "C1"))
    assert signature_key(signature_for_root(original, "C2")) != signature_key(signature_for_root(added, "C2"))
    assert signature_key(signature_for_root(original, "C1")) == signature_key(signature_for_root(multiplied, "C1"))
    assert signature_key(signature_for_root(original, "C2")) != signature_key(signature_for_root(multiplied, "C2"))


def test_unknown_structure_is_distinct_from_known_empty_structure_but_c0_matches() -> None:
    unknown = {
        **_root(),
        "children": None,
        "structure_status": "unknown_structure",
    }
    empty = {
        **_root(),
        "children": [],
        "structure_status": "empty_recorded_children",
    }

    assert signature_key(signature_for_root(unknown, "C0")) == signature_key(signature_for_root(empty, "C0"))
    unknown_c1 = signature_for_root(unknown, "C1")
    empty_c1 = signature_for_root(empty, "C1")
    assert unknown_c1["structure_state"] == "unknown_structure"
    assert unknown_c1["direct_child_set"] is None
    assert empty_c1["structure_state"] == "empty_recorded_children"
    assert empty_c1["direct_child_set"] == []
    assert signature_key(unknown_c1) != signature_key(empty_c1)


def test_support_gate_applies_count_time_bins_and_concentration_independently() -> None:
    distributed = [
        {"start_ms": minute * 60_000, "duration_ms": 10.0 + index}
        for minute in range(5)
        for index in range(4)
    ]
    supported = support_diagnostics(distributed, lookback_minutes=10)
    assert supported["n"] == 20
    assert supported["occupied_minutes"] == 5
    assert supported["required_minutes"] == 5
    assert supported["largest_minute_fraction"] == 0.2
    assert supported["supported"] is True

    thin = support_diagnostics(distributed[:10], lookback_minutes=10)
    assert thin["supported"] is False
    assert "minimum_count" in thin["failure_reasons"]

    concentrated = [
        {"start_ms": 0, "duration_ms": 10.0 + index}
        for index in range(20)
    ]
    concentrated_result = support_diagnostics(concentrated, lookback_minutes=5)
    assert concentrated_result["occupied_minutes"] == 1
    assert "occupied_minutes" in concentrated_result["failure_reasons"]
    assert "minute_concentration" in concentrated_result["failure_reasons"]


def test_support_keeps_invalid_rows_visible_and_excludes_them_from_support() -> None:
    rows = [
        {"start_ms": 0, "duration_ms": 1.0},
        {"start_ms": 60_000, "duration_ms": "not-a-number"},
    ]
    result = support_diagnostics(rows, lookback_minutes=5)
    assert result["input_records"] == 2
    assert result["n"] == 1
    assert result["invalid_duration_count"] == 1
    assert result["supported"] is False


def test_duration_intervention_changes_absolute_excess_exactly_and_preserves_membership() -> None:
    refs = [80.0, 100.0, 120.0]
    baseline = compare_duration(100.0, refs)
    plus_25 = compare_duration(125.0, refs)
    plus_50 = compare_duration(150.0, refs)
    plus_100 = compare_duration(200.0, refs)

    assert baseline["median_ms"] == 100.0
    assert baseline["absolute_excess_ms"] == 0.0
    assert plus_25["absolute_excess_ms"] - baseline["absolute_excess_ms"] == 25.0
    assert plus_50["absolute_excess_ms"] - baseline["absolute_excess_ms"] == 50.0
    assert plus_100["absolute_excess_ms"] - baseline["absolute_excess_ms"] == 100.0
    assert plus_100["ratio"] == 2.0


def test_zero_mad_and_zero_median_are_explicitly_undefined_only_where_required() -> None:
    constant = compare_duration(100.0, [42.0, 42.0, 42.0, 42.0])
    zero = compare_duration(10.0, [0.0, 0.0, 0.0])

    assert constant["median_ms"] == 42.0
    assert constant["mad_ms"] == 0.0
    assert constant["absolute_excess_ms"] == 58.0
    assert constant["ratio"] is not None
    assert constant["standardized_departure"] is None
    assert "zero_reference_mad" in constant["undefined_reasons"]
    assert zero["median_ms"] == 0.0
    assert zero["absolute_excess_ms"] == 10.0
    assert zero["ratio"] is None
    assert zero["standardized_departure"] is None
    assert "zero_reference_median" in zero["undefined_reasons"]


def test_block_bootstrap_is_seeded_and_uses_two_hundred_replicates() -> None:
    rows = [
        {"start_ms": minute * 60_000, "duration_ms": 100.0 + minute}
        for minute in range(5)
        for _ in range(4)
    ]
    first = bootstrap_median(rows, seed=42, replicates=200)
    second = bootstrap_median(rows, seed=42, replicates=200)
    assert first == second
    assert first["seed"] == 42
    assert first["replicates"] == 200
    assert first["usable_replicates"] == 200
    assert first["failed_or_empty_replicates"] == 0
    assert first["occupied_blocks"] == 5
    assert first["p05_ms"] is not None
    assert first["p95_ms"] is not None
    assert first["full_width_ms"] >= 0


def test_membership_hash_is_invariant_to_source_order() -> None:
    records = [
        {"trace_id": "t2", "span_id": "s2", "source_file": "day2.csv", "source_record": 8},
        {"trace_id": "t1", "span_id": "s1", "source_file": "day1.csv", "source_record": 4},
    ]
    assert stable_membership_hash(records) == stable_membership_hash(list(reversed(records)))
