"""Contract checks for the label-free, provenance-preserving trace index.

These fixtures exercise the data boundary only.  They deliberately use two
small daily files so a passing test proves neither an out-of-range CSV row nor
a day boundary can silently truncate a recovered trace.
"""

from __future__ import annotations

import csv
from pathlib import Path

from experiments.short_window_baselining_v1.index import (
    EXPECTED_HEADER,
    build_index,
    discover_frontend_components,
    fetch_frontend_roots,
    fetch_traces,
    open_index,
    validate_index,
)


def _write_trace(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(EXPECTED_HEADER)
        writer.writerows(rows)


def _span(
    timestamp: int,
    component: str,
    span_id: str,
    trace_id: str,
    duration: int,
    parent: str = "",
    operation: str = "Frontend/Recv.",
    span_type: str = "http",
) -> list[str]:
    return [
        str(timestamp), component, span_id, trace_id, str(duration), span_type,
        "0", operation, parent,
    ]


def test_index_retrieves_complete_cross_day_trace_and_preserves_provenance(tmp_path: Path) -> None:
    telemetry = tmp_path / "telemetry"
    _write_trace(
        telemetry / "2022_03_20" / "trace" / "trace_span.csv",
        [
            # Deliberately out of order: a whole-file/indexed scan must keep
            # searching after this out-of-range row.
            _span(1300, "frontend-0", "late-a", "trace-late", 50, operation="Frontend/Recv."),
            _span(1000, "frontend-0", "root-a", "trace-a", 500, operation="Frontend/Recv."),
            _span(1010, "frontend-0", "child-a", "trace-a", 100, parent="root-a", operation="Checkout/PlaceOrder", span_type="rpc"),
        ],
    )
    _write_trace(
        telemetry / "2022_03_21" / "trace" / "trace_span.csv",
        [
            _span(1100, "checkoutservice-2", "receiver-a", "trace-a", 80, parent="child-a", operation="Checkout/PlaceOrder", span_type="rpc"),
            _span(1200, "frontend-0", "root-b", "trace-b", 200, operation="Frontend/Recv."),
        ],
    )

    index_path = tmp_path / "trace.sqlite3"
    summary = build_index(index_path, telemetry)
    assert summary["counts"]["trace"] == 5
    assert validate_index(index_path, telemetry)["valid"] is True

    with open_index(index_path) as conn:
        roots = fetch_frontend_roots(conn, 999, 1201, ["frontend-0"])
        assert [row["span_id"] for row in roots] == ["root-a", "root-b"]

        traces = fetch_traces(conn, ["trace-a", "missing"])

    assert [row["span_id"] for row in traces["trace-a"]] == ["root-a", "child-a", "receiver-a"]
    assert traces["missing"] == []
    cross_day = traces["trace-a"][-1]
    assert cross_day["source_file"].endswith("2022_03_21/trace/trace_span.csv")
    assert cross_day["source_record"] == 2
    assert cross_day["source_header"] == 1
    assert cross_day["duration_raw"] == "80"


def test_root_window_is_half_open_and_component_allowlist_is_explicit(tmp_path: Path) -> None:
    telemetry = tmp_path / "telemetry"
    rows = [
        _span(1000, "frontend-0", "at-start", "trace-a", 1),
        _span(1001, "frontend-0", "at-end", "trace-b", 1),
        _span(1000, "frontend-01", "near-match", "trace-c", 1),
    ]
    _write_trace(telemetry / "2022_03_20" / "trace" / "trace_span.csv", rows)
    _write_trace(telemetry / "2022_03_21" / "trace" / "trace_span.csv", [])
    index_path = tmp_path / "trace.sqlite3"
    build_index(index_path, telemetry)

    with open_index(index_path) as conn:
        assert [row["span_id"] for row in fetch_frontend_roots(conn, 1000, 1001, ["frontend-0"])] == ["at-start"]
        assert discover_frontend_components(conn) == ["frontend-0", "frontend-01"]
        assert fetch_frontend_roots(conn, 1000, 1001, ["frontend-0"])[0]["cmdb_id"] == "frontend-0"


def test_duplicate_composite_identity_is_retained_for_ambiguity_audit(tmp_path: Path) -> None:
    telemetry = tmp_path / "telemetry"
    duplicate = _span(1000, "frontend-0", "same-span", "trace-a", 5)
    _write_trace(telemetry / "2022_03_20" / "trace" / "trace_span.csv", [duplicate, duplicate])
    _write_trace(telemetry / "2022_03_21" / "trace" / "trace_span.csv", [])
    index_path = tmp_path / "trace.sqlite3"
    build_index(index_path, telemetry)

    with open_index(index_path) as conn:
        rows = fetch_traces(conn, ["trace-a"])["trace-a"]

    assert len(rows) == 2
    assert {(row["trace_id"], row["span_id"]) for row in rows} == {("trace-a", "same-span")}
    assert [row["source_record"] for row in rows] == [2, 3]


def test_source_mutation_invalidates_existing_index(tmp_path: Path) -> None:
    telemetry = tmp_path / "telemetry"
    path = telemetry / "2022_03_20" / "trace" / "trace_span.csv"
    _write_trace(path, [_span(1000, "frontend-0", "root", "trace", 1)])
    _write_trace(telemetry / "2022_03_21" / "trace" / "trace_span.csv", [])
    index_path = tmp_path / "trace.sqlite3"
    build_index(index_path, telemetry)

    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")

    validation = validate_index(index_path, telemetry)
    assert validation["valid"] is False
    assert validation["reason"] == "source_inventory_mismatch"
