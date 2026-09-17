"""Pure runner contracts for anchors, interval boundaries, and screening gates."""

from __future__ import annotations

from experiments.short_window_baselining_v1.runner import (
    AGING_OFFSETS,
    LOOKBACKS,
    _reference_boundary_reason,
    _root_intervals,
    _selection_summary,
    anchor_specs,
)


def test_anchor_matrix_has_twelve_declared_utc8_anchors_and_six_aging_slices() -> None:
    anchors = anchor_specs()
    assert len(anchors) == 12
    assert [anchor["anchor_id"] for anchor in anchors[:6]] == [
        "2022-03-20T01:00:00+08:00",
        "2022-03-20T05:00:00+08:00",
        "2022-03-20T09:00:00+08:00",
        "2022-03-20T13:00:00+08:00",
        "2022-03-20T17:00:00+08:00",
        "2022-03-20T21:00:00+08:00",
    ]
    for anchor in anchors:
        start_ms = anchor["epoch_ms"]
        assert sorted(int(key) for key in anchor["reference_intervals"]) == list(LOOKBACKS)
        assert len(anchor["query_slices"]) == len(AGING_OFFSETS) == 6
        assert anchor["query_slices"][0] == [start_ms, start_ms + 5 * 60_000]
        assert anchor["query_slices"][-1] == [start_ms + 25 * 60_000, start_ms + 30 * 60_000]
        assert all(end > begin for begin, end in anchor["query_slices"])


def test_collection_root_intervals_cover_exactly_the_declared_90_minute_support_horizon() -> None:
    anchors = anchor_specs()
    intervals = _root_intervals(anchors)
    assert len(intervals) == 12
    for anchor, (begin, end) in zip(anchors, intervals):
        assert begin == anchor["epoch_ms"] - 60 * 60_000
        assert end == anchor["epoch_ms"] + 30 * 60_000
        assert end - begin == 90 * 60_000


def test_reference_completion_boundary_is_half_open_and_integer_precise() -> None:
    anchor_ms = 1_000_000
    before = {"max_recorded_end_us": anchor_ms * 1000 - 1}
    at = {"max_recorded_end_us": anchor_ms * 1000}
    after = {"max_recorded_end_us": anchor_ms * 1000 + 1}
    unresolved = {"max_recorded_end_us": None}

    assert _reference_boundary_reason(before, anchor_ms) is None
    assert _reference_boundary_reason(at, anchor_ms) == "endpoint_reaches_anchor"
    assert _reference_boundary_reason(after, anchor_ms) == "endpoint_reaches_anchor"
    assert _reference_boundary_reason(unresolved, anchor_ms) == "unresolved_endpoint"


def test_selection_gate_does_not_screen_pass_while_control_checks_are_pending() -> None:
    rows = []
    for index in range(12):
        rows.append({
            "mode": "C1",
            "replica_policy": "same_replica",
            "lookback_minutes": 15,
            "query_resolved_count": 1,
            "supported_query_count": 1 if index < 10 else 0,
            "request_coverage": 1.0 if index < 10 else 0.0,
            "bootstrap_width_checks": [{
                "assessed": True,
                "usable_replicates": 200,
                "within_width_gate": True,
                "positive_query_count": 1 if index < 10 else 0,
            }],
            "zero_median_cohort_count": 0,
        })
    decision = _selection_summary(rows)[0]

    assert decision["request_coverage"] == 10 / 12
    assert decision["primary_windows_at_least_80pct"] == 10
    assert decision["gate_2_coverage"] is False
    assert decision["gate_3_uncertainty"] is True
    assert decision["gate_1_contract_checks"] == "pending_external_control_checks"
    assert decision["status"] != "screen_pass"
