"""Additional cache and source-schema contracts for the trace index."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import pytest

from experiments.short_window_baselining_v1.index import (
    EXPECTED_HEADER,
    INDEX_VERSION,
    build_index,
    validate_index,
)


def _write(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(EXPECTED_HEADER)
        writer.writerows(rows)


def _row(span_id: str = "root") -> list[str]:
    return ["1000", "frontend-0", span_id, "trace", "1", "http", "0", "Frontend/Recv.", ""]


def _two_day_root(tmp_path: Path) -> tuple[Path, Path]:
    telemetry = tmp_path / "telemetry"
    _write(telemetry / "2022_03_20" / "trace" / "trace_span.csv", [_row()])
    _write(telemetry / "2022_03_21" / "trace" / "trace_span.csv", [])
    return telemetry, tmp_path / "trace.sqlite3"


def test_default_source_contract_rejects_missing_required_day(tmp_path: Path) -> None:
    telemetry = tmp_path / "telemetry"
    _write(telemetry / "2022_03_20" / "trace" / "trace_span.csv", [_row()])
    with pytest.raises(FileNotFoundError):
        build_index(tmp_path / "trace.sqlite3", telemetry)


def test_cache_metadata_version_and_source_file_rows_are_validated(tmp_path: Path) -> None:
    telemetry, index = _two_day_root(tmp_path)
    build_index(index, telemetry)
    assert validate_index(index, telemetry)["valid"] is True

    with sqlite3.connect(index) as conn:
        conn.execute("UPDATE metadata SET value = ? WHERE key = 'version'", ("old-index",))
        conn.commit()
    invalid = validate_index(index, telemetry)
    assert invalid["valid"] is False
    assert invalid["reason"] == "index_version_mismatch"

    # Restore the version and corrupt the per-source manifest row.  The
    # top-level JSON manifest alone must not make this cache appear valid.
    with sqlite3.connect(index) as conn:
        conn.execute("UPDATE metadata SET value = ? WHERE key = 'version'", (INDEX_VERSION,))
        conn.execute("UPDATE source_files SET rows = rows + 1")
        conn.commit()
    invalid = validate_index(index, telemetry)
    assert invalid["valid"] is False
    assert invalid["reason"] == "source_file_metadata_mismatch"


def test_nonempty_malformed_csv_row_is_rejected(tmp_path: Path) -> None:
    telemetry = tmp_path / "telemetry"
    path = telemetry / "2022_03_20" / "trace" / "trace_span.csv"
    _write(path, [_row()])
    with path.open("a", encoding="utf-8") as handle:
        handle.write("bad,row\n")
    _write(telemetry / "2022_03_21" / "trace" / "trace_span.csv", [])
    with pytest.raises(ValueError, match="wrong field count"):
        build_index(tmp_path / "trace.sqlite3", telemetry)
