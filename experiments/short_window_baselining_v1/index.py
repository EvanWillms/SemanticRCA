"""Validated, provenance preserving index for the two supplied trace files.

The old frontend experiment index was intentionally not reused.  It has no
source manifest and its component lookup uses a broad SQL ``LIKE`` predicate.
This index stores every trace row from both daily files and records the exact
source hashes and parser schema in its metadata.  Trace retrieval is by
``trace_id`` and keeps the composite ``(trace_id, span_id)`` identity visible.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRACE_ROOT = ROOT / "data" / "track-1" / "telemetry"
DEFAULT_ARTIFACT_ROOT = ROOT / "data" / "experiments" / "short-window-baselining-v1"
DEFAULT_INDEX = DEFAULT_ARTIFACT_ROOT / "trace.sqlite3"
TRACE_FIELDS = (
    "timestamp", "cmdb_id", "span_id", "trace_id", "duration", "type",
    "status_code", "operation_name", "parent_span",
)
EXPECTED_HEADER = list(TRACE_FIELDS)
INDEX_VERSION = "short-window-baselining-v1/index-2"
PARSER_VERSION = "csv-dictreader-1"
DEFAULT_EXPECTED_DAYS = ("2022_03_20", "2022_03_21")
INSERT_BATCH_SIZE = 20_000


def trace_files(
    trace_root: Path = DEFAULT_TRACE_ROOT,
    *,
    expected_days: Sequence[str] | None = DEFAULT_EXPECTED_DAYS,
) -> list[Path]:
    """Return complete daily trace files, requiring the supplied data days.

    The short-window protocol is defined over the two supplied daily files.
    Requiring those directory names by default prevents a partial or silently
    expanded dataset from being treated as the same source.  Synthetic tests
    and future declared revisions can pass an explicit day list.
    """
    root = Path(trace_root)
    if expected_days is None:
        files = sorted(root.glob("*/trace/trace_span.csv"))
    else:
        days = tuple(str(day) for day in expected_days)
        files = [root / day / "trace" / "trace_span.csv" for day in days]
        missing = [str(path) for path in files if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"required trace source(s) missing: {missing}")
        discovered = set(root.glob("*/trace/trace_span.csv"))
        unexpected = sorted(str(path) for path in discovered if path not in set(files))
        if unexpected:
            raise ValueError(f"unexpected trace source(s) under {root}: {unexpected}")
    if not files:
        raise FileNotFoundError(f"no trace_span.csv files under {root}")
    return files


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _scan_header_and_rows(path: Path) -> tuple[list[str], int]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        count = 0
        for logical_record, row in enumerate(reader, 2):
            # A trailing blank line is harmless CSV formatting and must not
            # change logical data membership.  Non-empty malformed rows are a
            # source/schema error, rather than a silently shortened index.
            if not row:
                continue
            if len(row) != len(EXPECTED_HEADER):
                raise ValueError(f"wrong field count at {path}:{logical_record}: {len(row)}")
            count += 1
    return header, count


def source_inventory(
    trace_root: Path = DEFAULT_TRACE_ROOT,
    *,
    hash_sources: bool = True,
    expected_days: Sequence[str] | None = DEFAULT_EXPECTED_DAYS,
) -> list[dict]:
    """Collect source hashes, headers and complete logical row counts."""
    root = Path(trace_root)
    entries = []
    for path in trace_files(root, expected_days=expected_days):
        header, rows = _scan_header_and_rows(path)
        if header != EXPECTED_HEADER:
            raise ValueError(f"unexpected trace header in {path}: {header!r}")
        entries.append({
            "source_file": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
            "absolute_path": str(path.resolve()),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path) if hash_sources else None,
            "header": header,
            "source_header": 1,
            "rows": rows,
        })
    return entries


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def _metadata(conn: sqlite3.Connection) -> dict[str, str]:
    try:
        return {str(row["key"]): str(row["value"]) for row in conn.execute("SELECT key,value FROM metadata")}
    except sqlite3.Error:
        return {}


def validate_index(index_path: Path, trace_root: Path = DEFAULT_TRACE_ROOT, *, hash_sources: bool = True) -> dict:
    """Validate completeness and source identity before retrieval."""
    path = Path(index_path)
    if not path.is_file():
        return {"valid": False, "reason": "missing_index", "index": str(path)}
    expected = source_inventory(trace_root, hash_sources=hash_sources)
    try:
        with _connect(path) as conn:
            metadata = _metadata(conn)
            if metadata.get("complete") != "1":
                return {"valid": False, "reason": "incomplete_index", "index": str(path)}
            if metadata.get("version") != INDEX_VERSION:
                return {"valid": False, "reason": "index_version_mismatch", "index": str(path), "stored_version": metadata.get("version")}
            if metadata.get("parser_version") != PARSER_VERSION:
                return {"valid": False, "reason": "parser_version_mismatch", "index": str(path), "stored_parser_version": metadata.get("parser_version")}
            stored = json.loads(metadata.get("source_inventory", "[]"))
            if stored != expected:
                return {"valid": False, "reason": "source_inventory_mismatch", "index": str(path), "stored": stored, "expected": expected}
            row_count = int(conn.execute("SELECT COUNT(*) FROM spans").fetchone()[0])
            expected_count = sum(int(entry["rows"]) for entry in expected)
            if row_count != expected_count:
                return {"valid": False, "reason": "row_count_mismatch", "index": str(path), "stored_rows": row_count, "expected_rows": expected_count}
            expected_counts = {str(entry["source_file"]): int(entry["rows"]) for entry in expected}
            stored_counts = dict.fromkeys(expected_counts, 0)
            stored_counts.update({
                str(row["source_file"]): int(row["row_count"])
                for row in conn.execute("SELECT source_file,COUNT(*) AS row_count FROM spans GROUP BY source_file")
            })
            if stored_counts != expected_counts:
                return {"valid": False, "reason": "source_row_count_mismatch", "index": str(path), "stored": stored_counts, "expected": expected_counts}
            source_rows = conn.execute(
                "SELECT source_file,absolute_path,bytes,sha256,header_json,source_header,rows "
                "FROM source_files ORDER BY source_file"
            ).fetchall()
            expected_rows = []
            for entry in expected:
                expected_rows.append((
                    str(entry["source_file"]), str(entry["absolute_path"]), int(entry["bytes"]),
                    str(entry["sha256"]), json.dumps(entry["header"], separators=(",", ":")),
                    int(entry["source_header"]), int(entry["rows"]),
                ))
            actual_rows = [tuple(row) for row in source_rows]
            if actual_rows != expected_rows:
                return {"valid": False, "reason": "source_file_metadata_mismatch", "index": str(path), "stored": actual_rows, "expected": expected_rows}
    except (sqlite3.Error, json.JSONDecodeError, OSError, ValueError) as exc:
        return {"valid": False, "reason": f"validation_error:{type(exc).__name__}", "index": str(path)}
    return {"valid": True, "index": str(path), "rows": expected_count, "source_inventory": expected}


def _schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        PRAGMA temp_store=MEMORY;
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE source_files(
          source_file TEXT PRIMARY KEY, absolute_path TEXT NOT NULL, bytes INTEGER NOT NULL,
          sha256 TEXT NOT NULL, header_json TEXT NOT NULL, source_header INTEGER NOT NULL,
          rows INTEGER NOT NULL
        );
        CREATE TABLE spans(
          row_id INTEGER PRIMARY KEY, timestamp_ms INTEGER NOT NULL, trace_id TEXT NOT NULL,
          span_id TEXT NOT NULL, parent_span TEXT NOT NULL, cmdb_id TEXT NOT NULL,
          duration_raw TEXT NOT NULL, duration_us INTEGER, type TEXT NOT NULL,
          status_code TEXT NOT NULL, operation_name TEXT NOT NULL, source_file TEXT NOT NULL,
          source_record INTEGER NOT NULL, source_header INTEGER NOT NULL, raw_json TEXT NOT NULL
        );
        """
    )


def _create_indexes(conn: sqlite3.Connection) -> None:
    """Create lookup indexes after bulk loading, then make them durable."""
    conn.executescript(
        """
        CREATE INDEX spans_time ON spans(timestamp_ms);
        CREATE INDEX spans_trace ON spans(trace_id, source_file, source_record);
        CREATE INDEX spans_root ON spans(cmdb_id, parent_span, timestamp_ms);
        CREATE INDEX spans_identity ON spans(trace_id, span_id);
        """
    )


def _raw_row(row: Mapping[str, str]) -> dict[str, str]:
    return {field: str(row.get(field, "")) for field in TRACE_FIELDS}


def build_index(
    index_path: Path = DEFAULT_INDEX,
    trace_root: Path = DEFAULT_TRACE_ROOT,
    *,
    force: bool = False,
    progress_every: int = 1_000_000,
    progress: Callable[[dict], None] | None = None,
) -> dict:
    """Build or reuse the complete two-day trace index.

    The source inventory is hashed before reuse.  A partially written index is
    never considered valid and can be safely rebuilt with ``force=True``.
    """
    index_path, trace_root = Path(index_path), Path(trace_root)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    inventory = source_inventory(trace_root)
    existing = validate_index(index_path, trace_root)
    if existing.get("valid") and not force:
        return {"index": str(index_path), "reused": True, "counts": {"trace": int(existing["rows"])}, "source_inventory": inventory}
    if index_path.exists():
        index_path.unlink()
    for sidecar in (Path(str(index_path) + "-wal"), Path(str(index_path) + "-shm")):
        if sidecar.exists():
            sidecar.unlink()
    counts = 0
    conn = _connect(index_path)
    try:
        _schema(conn)
        batch: list[tuple] = []
        for source in trace_files(trace_root):
            entry = next(item for item in inventory if Path(item["absolute_path"]) == source.resolve())
            conn.execute(
                "INSERT INTO source_files(source_file,absolute_path,bytes,sha256,header_json,source_header,rows) VALUES(?,?,?,?,?,?,?)",
                (entry["source_file"], entry["absolute_path"], entry["bytes"], entry["sha256"], json.dumps(entry["header"], separators=(",", ":")), 1, entry["rows"]),
            )
            with source.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames != EXPECTED_HEADER:
                    raise ValueError(f"unexpected trace header in {source}: {reader.fieldnames!r}")
                for source_record, source_row in enumerate(reader, 2):
                    if not source_row or all(value is None for value in source_row.values()):
                        continue
                    if None in source_row or any(source_row.get(field) is None for field in TRACE_FIELDS):
                        raise ValueError(f"wrong field count at {source}:{source_record}")
                    raw = _raw_row(source_row)
                    try:
                        timestamp_ms = int(raw["timestamp"])
                    except ValueError as exc:
                        raise ValueError(f"invalid timestamp at {source}:{source_record}") from exc
                    try:
                        duration_us = int(raw["duration"])
                    except ValueError as exc:
                        raise ValueError(f"invalid duration at {source}:{source_record}") from exc
                    batch.append((
                        timestamp_ms, raw["trace_id"], raw["span_id"], raw["parent_span"],
                        raw["cmdb_id"], raw["duration"], duration_us, raw["type"],
                        raw["status_code"], raw["operation_name"], entry["source_file"],
                        source_record, 1, json.dumps(raw, separators=(",", ":")),
                    ))
                    counts += 1
                    if len(batch) >= INSERT_BATCH_SIZE:
                        conn.executemany(
                            "INSERT INTO spans(timestamp_ms,trace_id,span_id,parent_span,cmdb_id,duration_raw,duration_us,type,status_code,operation_name,source_file,source_record,source_header,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            batch,
                        )
                        batch.clear()
                        conn.commit()
                    if progress and progress_every > 0 and counts % progress_every == 0:
                        progress({"rows_loaded": counts, "source_file": entry["source_file"], "source_record": source_record})
                if batch:
                    conn.executemany(
                        "INSERT INTO spans(timestamp_ms,trace_id,span_id,parent_span,cmdb_id,duration_raw,duration_us,type,status_code,operation_name,source_file,source_record,source_header,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        batch,
                    )
                    batch.clear()
                    conn.commit()
        # Hash and count the sources again after loading.  A source mutation
        # during the long scan must invalidate the build rather than produce a
        # valid-looking index whose rows do not match its manifest.
        final_inventory = source_inventory(trace_root)
        if final_inventory != inventory:
            raise RuntimeError("trace source changed while building index")
        expected_counts = {str(entry["source_file"]): int(entry["rows"]) for entry in inventory}
        loaded_counts = dict.fromkeys(expected_counts, 0)
        loaded_counts.update({
            str(row["source_file"]): int(row["row_count"])
            for row in conn.execute("SELECT source_file,COUNT(*) AS row_count FROM spans GROUP BY source_file")
        })
        if loaded_counts != expected_counts:
            raise RuntimeError(f"loaded per-source row counts differ from source inventory: {loaded_counts!r} != {expected_counts!r}")
        _create_indexes(conn)
        conn.execute("INSERT INTO metadata(key,value) VALUES('complete','1')")
        conn.execute("INSERT INTO metadata(key,value) VALUES('version',?)", (INDEX_VERSION,))
        conn.execute("INSERT INTO metadata(key,value) VALUES('parser_version',?)", (PARSER_VERSION,))
        conn.execute("INSERT INTO metadata(key,value) VALUES('source_inventory',?)", (json.dumps(inventory, sort_keys=True, separators=(",", ":")),))
        conn.execute("INSERT INTO metadata(key,value) VALUES('duration_unit','raw duration preserved; provisional microseconds for duration_ms')")
        conn.commit()
    finally:
        conn.close()
    return {"index": str(index_path), "reused": False, "counts": {"trace": counts}, "source_inventory": inventory}


def _rows_to_dict(rows: Iterable[sqlite3.Row]) -> list[dict]:
    output = []
    for row in rows:
        raw = json.loads(row["raw_json"])
        raw.update({
            "timestamp_ms": int(row["timestamp_ms"]),
            "duration_raw": row["duration_raw"],
            "duration_us": int(row["duration_us"]) if row["duration_us"] is not None else None,
            "source_file": row["source_file"],
            "source_record": int(row["source_record"]),
            "source_header": int(row["source_header"]),
        })
        output.append(raw)
    return output


def fetch_frontend_roots(conn: sqlite3.Connection, start_ms: int, end_ms: int, components: Sequence[str]) -> list[dict]:
    """Fetch blank-parent roots using an explicit frozen component list."""
    if not components:
        return []
    placeholders = ",".join("?" for _ in components)
    rows = conn.execute(
        f"SELECT * FROM spans WHERE cmdb_id IN ({placeholders}) AND parent_span='' AND timestamp_ms>=? AND timestamp_ms<? ORDER BY timestamp_ms,trace_id,span_id,source_file,source_record",
        (*components, int(start_ms), int(end_ms)),
    ).fetchall()
    return _rows_to_dict(rows)


def fetch_traces(conn: sqlite3.Connection, trace_ids: Iterable[str]) -> dict[str, list[dict]]:
    """Fetch complete indexed traces in bounded IN chunks."""
    ids = list(dict.fromkeys(str(value) for value in trace_ids))
    result = {trace_id: [] for trace_id in ids}
    for offset in range(0, len(ids), 700):
        chunk = ids[offset:offset + 700]
        if not chunk:
            continue
        placeholders = ",".join("?" for _ in chunk)
        rows = conn.execute(
            f"SELECT * FROM spans WHERE trace_id IN ({placeholders}) ORDER BY trace_id,source_file,source_record,row_id",
            chunk,
        ).fetchall()
        for raw in _rows_to_dict(rows):
            result.setdefault(str(raw["trace_id"]), []).append(raw)
    return result


def discover_frontend_components(conn: sqlite3.Connection) -> list[str]:
    """Inventory then return the explicit frontend recording allowlist."""
    values = [str(row[0]) for row in conn.execute("SELECT DISTINCT cmdb_id FROM spans ORDER BY cmdb_id")]
    # The prefix is only used during the inventory step.  All subsequent
    # retrieval uses this frozen explicit list with an IN predicate.
    return [value for value in values if value.startswith("frontend-")]


def open_index(index_path: Path) -> sqlite3.Connection:
    conn = _connect(Path(index_path))
    conn.execute("PRAGMA query_only=ON")
    return conn
