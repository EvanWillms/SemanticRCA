"""Pure checks for independent matrix reconciliation and paired summaries."""

from __future__ import annotations

from pathlib import Path

from experiments.short_window_baselining_v1.analysis import (
    _artifact_reconciliation,
    _paired_sensitivities,
)


def _coverage(replica: str, top: list[dict]) -> dict:
    return {
        "anchor_id": "2022-03-20T01:00:00+08:00",
        "lookback_minutes": 5,
        "mode": "C0",
        "replica_policy": replica,
        "query_resolved_count": 2,
        "supported_query_count": 2,
        "request_coverage": 1.0,
        "aging": [{"offset_minutes": offset} for offset in (0, 5, 10, 15, 20, 25)],
        "top5_positive_absolute_excess": top,
        "zero_median_cohort_count": 0,
    }


def _comparison(replica: str, span: str) -> dict:
    return {
        "anchor_id": "2022-03-20T01:00:00+08:00",
        "lookback_minutes": 5,
        "mode": "C0",
        "replica_policy": replica,
        "trace_id": "trace",
        "span_id": span,
        "absolute_excess_ms": 1.0,
    }


def _membership(replica: str, span: str) -> dict:
    return {
        "anchor_id": "2022-03-20T01:00:00+08:00",
        "lookback_minutes": 5,
        "mode": "C0",
        "replica_policy": replica,
        "role": "query",
        "trace_id": "trace",
        "span_id": span,
    }


def test_reconciliation_detects_missing_cells_and_bad_aging_without_silence() -> None:
    row = _coverage("same_replica", [{"trace_id": "trace", "span_id": "s1"}])
    result = _artifact_reconciliation(Path("/tmp"), Path("/tmp"), {"version": "test"}, [], [row], [], [], [])
    assert result["coverage_rows"] == 1
    assert result["all_coverage_cells_present_once"] is False
    assert result["coverage_missing_cells"]


def test_paired_summary_reports_full_and_common_supported_denominators() -> None:
    coverage = [
        _coverage("same_replica", [{"trace_id": "trace", "span_id": "s1"}]),
        _coverage("pooled", [{"trace_id": "trace", "span_id": "s1"}]),
    ]
    comparisons = [_comparison("same_replica", "s1"), _comparison("pooled", "s1")]
    memberships = [_membership("same_replica", "s1"), _membership("same_replica", "s2"), _membership("pooled", "s1"), _membership("pooled", "s2")]
    observations = [{
        "trace_id": "trace",
        "span_id": "s1",
        "cmdb_id": "frontend-0",
        "signature": {"C0": {"root_operation_name": "root"}, "C2": {"shape": "shape"}},
    }, {
        "trace_id": "trace",
        "span_id": "s2",
        "cmdb_id": "frontend-0",
        "signature": {"C0": {"root_operation_name": "root"}, "C2": {"shape": "shape"}},
    }]
    result = _paired_sensitivities(coverage, comparisons, [], memberships, observations)
    pair = result["same_vs_pooled_per_query"][0]
    assert pair["common_supported_count"] == 1
    assert pair["query_population_count"] == 2
    assert pair["same_vs_pooled_full_population_overlap"] == 0.5
    assert pair["same_vs_pooled_common_supported_overlap"] == 1.0
