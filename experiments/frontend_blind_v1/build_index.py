"""Label-free SQLite index for trace, metric, and log telemetry."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
TRACE_ROOT = ROOT / "data" / "track-1" / "telemetry"
ARTIFACT_ROOT = ROOT / "data" / "experiments" / "frontend-blind-v1"
DEFAULT_INDEX = ARTIFACT_ROOT / "telemetry.sqlite3"
DEFAULT_DB = DEFAULT_INDEX
TRACE_FIELDS = ("timestamp", "cmdb_id", "span_id", "trace_id", "duration", "type", "status_code", "operation_name", "parent_span")


def estimate_sources(telemetry_root: Path = TRACE_ROOT) -> dict:
    """Estimate source bytes/rows before the one-time SQLite build."""
    files = []
    total_bytes = total_rows = 0
    for kind in ("trace", "metric", "log"):
        for source in _files(Path(telemetry_root), kind):
            size = source.stat().st_size
            rows = max(0, sum(1 for _ in source.open("rb")) - 1)
            files.append({"kind": kind, "source_file": str(source.relative_to(ROOT) if source.is_relative_to(ROOT) else source), "bytes": size, "rows": rows})
            total_bytes += size
            total_rows += rows
    return {"files": files, "bytes": total_bytes, "rows": total_rows, "estimated_sqlite_bytes": int(total_bytes * 2.2)}


def _files(root: Path, kind: str) -> list[Path]:
    return sorted(root.glob(f"*/{kind}/*.csv"))


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def build_index(index_path: Path = DEFAULT_INDEX, telemetry_root: Path = TRACE_ROOT, *, force: bool = False) -> dict:
    """Scan telemetry once. Returned summary is safe to persist in run metadata."""
    index_path, telemetry_root = Path(index_path), Path(telemetry_root)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if index_path.exists() and not force:
        try:
            with _connect(index_path) as conn:
                marker = conn.execute("SELECT value FROM metadata WHERE key='complete'").fetchone()
                if marker is not None and marker["value"] == "1":
                    return {"index": str(index_path), "counts": dict(conn.execute("SELECT kind, n FROM row_counts").fetchall())}
        except sqlite3.Error:
            pass
    if index_path.exists():
        index_path.unlink()
    counts = {"trace": 0, "metric": 0, "log": 0}
    with _connect(index_path) as conn:
        conn.executescript("""
          PRAGMA journal_mode=WAL;
          CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE row_counts(kind TEXT PRIMARY KEY, n INTEGER NOT NULL);
          CREATE TABLE spans(row_id INTEGER PRIMARY KEY, timestamp_ms INTEGER NOT NULL, trace_id TEXT NOT NULL,
            span_id TEXT NOT NULL, parent_span TEXT NOT NULL, cmdb_id TEXT NOT NULL, duration TEXT NOT NULL,
            type TEXT NOT NULL, status_code TEXT NOT NULL, operation_name TEXT NOT NULL,
            source_file TEXT NOT NULL, source_record INTEGER NOT NULL, source_header INTEGER NOT NULL, raw_json TEXT NOT NULL);
          CREATE INDEX spans_time ON spans(timestamp_ms);
          CREATE INDEX spans_trace ON spans(trace_id);
          CREATE INDEX spans_frontend ON spans(cmdb_id, timestamp_ms);
          CREATE TABLE metric_rows(row_id INTEGER PRIMARY KEY, source TEXT NOT NULL, identity TEXT NOT NULL,
            kpi_name TEXT NOT NULL, timestamp_ms INTEGER NOT NULL, source_file TEXT NOT NULL,
            source_record INTEGER NOT NULL, source_header INTEGER NOT NULL, raw_json TEXT NOT NULL);
          CREATE INDEX metric_lookup ON metric_rows(source, identity, timestamp_ms);
          CREATE TABLE log_rows(row_id INTEGER PRIMARY KEY, source TEXT NOT NULL, identity TEXT NOT NULL,
            timestamp_ms INTEGER NOT NULL, log_id TEXT NOT NULL, source_file TEXT NOT NULL,
            source_record INTEGER NOT NULL, source_header INTEGER NOT NULL, raw_json TEXT NOT NULL);
          CREATE INDEX log_lookup ON log_rows(source, identity, timestamp_ms);
        """)
        for source in _files(telemetry_root, "trace"):
            with source.open(newline="") as handle:
                reader = csv.DictReader(handle)
                for source_record, row in enumerate(reader, 2):
                    raw = {field: row.get(field, "") for field in TRACE_FIELDS}
                    conn.execute("INSERT INTO spans(timestamp_ms,trace_id,span_id,parent_span,cmdb_id,duration,type,status_code,operation_name,source_file,source_record,source_header,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                 (int(raw["timestamp"]), raw["trace_id"], raw["span_id"], raw["parent_span"], raw["cmdb_id"], raw["duration"], raw["type"], raw["status_code"], raw["operation_name"], str(source.relative_to(ROOT) if source.is_relative_to(ROOT) else source), source_record, 1, json.dumps(raw, separators=(",", ":"))))
                    counts["trace"] += 1
        for source in _files(telemetry_root, "metric"):
            source_name = source.stem.removeprefix("metric_")
            with source.open(newline="") as handle:
                reader = csv.DictReader(handle)
                for source_record, row in enumerate(reader, 2):
                    raw = dict(row)
                    identity = str(raw.get("service", "") if source_name == "service" else raw.get("cmdb_id", ""))
                    conn.execute("INSERT INTO metric_rows(source,identity,kpi_name,timestamp_ms,source_file,source_record,source_header,raw_json) VALUES(?,?,?,?,?,?,?,?)",
                                 (source_name, identity, str(raw.get("kpi_name", "")), int(raw["timestamp"]) * 1000, str(source.relative_to(ROOT) if source.is_relative_to(ROOT) else source), source_record, 1, json.dumps(raw, separators=(",", ":"))))
                    counts["metric"] += 1
        for source in _files(telemetry_root, "log"):
            source_name = source.stem.removeprefix("log_")
            with source.open(newline="") as handle:
                reader = csv.DictReader(handle)
                for source_record, row in enumerate(reader, 2):
                    raw = dict(row)
                    identity = str(raw.get("cmdb_id", ""))
                    conn.execute("INSERT INTO log_rows(source,identity,timestamp_ms,log_id,source_file,source_record,source_header,raw_json) VALUES(?,?,?,?,?,?,?,?)",
                                 (source_name, identity, int(raw["timestamp"]) * 1000, str(raw.get("log_id", "")), str(source.relative_to(ROOT) if source.is_relative_to(ROOT) else source), source_record, 1, json.dumps(raw, separators=(",", ":"))))
                    counts["log"] += 1
        for kind, count in counts.items():
            conn.execute("INSERT INTO row_counts(kind,n) VALUES(?,?)", (kind, count))
        conn.execute("INSERT INTO metadata(key,value) VALUES('complete','1')")
        conn.commit()
    return {"index": str(index_path), "counts": counts}


def _raw_rows(conn: sqlite3.Connection, sql: str, args: Iterable[object]) -> list[dict]:
    output = []
    for row in conn.execute(sql, tuple(args)).fetchall():
        raw = json.loads(row["raw_json"])
        raw.update(source_file=row["source_file"], source_record=int(row["source_record"]), source_header=int(row["source_header"]))
        output.append(raw)
    return output


def get_frontend(start_ms: int, end_ms: int, index_path: Path = DEFAULT_INDEX) -> list[dict]:
    """Return frontend spans whose own start is in the half-open interval."""
    with _connect(Path(index_path)) as conn:
        return _raw_rows(conn, "SELECT * FROM spans WHERE cmdb_id LIKE 'frontend-%' AND timestamp_ms>=? AND timestamp_ms<? ORDER BY timestamp_ms,trace_id,span_id,source_record", (int(start_ms), int(end_ms)))


def get_traces(trace_ids: Iterable[str], index_path: Path = DEFAULT_INDEX) -> dict[str, list[dict]]:
    ids = list(dict.fromkeys(str(value) for value in trace_ids))
    result = {trace_id: [] for trace_id in ids}
    if not ids:
        return result
    with _connect(Path(index_path)) as conn:
        for offset in range(0, len(ids), 900):
            chunk = ids[offset:offset + 900]
            placeholders = ",".join("?" for _ in chunk)
            for row in conn.execute(f"SELECT * FROM spans WHERE trace_id IN ({placeholders}) ORDER BY trace_id, source_file, source_record", chunk).fetchall():
                raw = json.loads(row["raw_json"])
                raw.update(source_file=row["source_file"], source_record=int(row["source_record"]), source_header=int(row["source_header"]))
                result[raw["trace_id"]].append(raw)
    return result


class TraceIndex:
    def __init__(self, db_path: Path = DEFAULT_INDEX, trace_root: Path = TRACE_ROOT):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            build_index(self.db_path, trace_root)

    def get_frontend(self, start_ms: int, end_ms: int) -> list[dict]:
        return get_frontend(start_ms, end_ms, self.db_path)

    def get_traces(self, trace_ids: Iterable[str]) -> dict[str, list[dict]]:
        return get_traces(trace_ids, self.db_path)
