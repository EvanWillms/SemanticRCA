"""Prepared, snapshot-bound access to trace-span sources.

The baseline producer needs two properties that the legacy trace adapter does
not provide: roots are selected by an explicit allowlist and a selected root's
whole recorded trace is recovered even when its child rows fall outside the
selection window.  This module keeps that boundary small and source-bound.

The SQLite file is a rebuildable accelerator.  The source inventory, digest and
row counts remain part of :class:`PreparedTraceView`, so callers can validate a
snapshot without treating the database as provenance.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

from .paths import source_path


TRACE_FIELDS = (
    "timestamp", "cmdb_id", "span_id", "trace_id", "duration", "type",
    "status_code", "operation_name", "parent_span",
)
TRACE_INDEX_VERSION = "qualified-baseline-trace-index-v1"
TRACE_PARSER_VERSION = "csv-dictreader-v1"
TRACE_EXTRACTION_VERSION = "logical-span-dedup-v1"


class SourceIntegrityError(ValueError):
    """A declared source cannot satisfy its snapshot inventory."""


class TraceIndexBudgetExceeded(RuntimeError):
    """A caller supplied work budget stopped preparation or retrieval."""


def _budget_check(work_budget: Any) -> None:
    """Call the common budget shapes used by the runner and unit fixtures."""
    if work_budget is None:
        return
    checker = getattr(work_budget, "check", None)
    if checker is None and callable(work_budget):
        checker = work_budget
    if checker is not None:
        try:
            checker()
        except TraceIndexBudgetExceeded:
            raise
        except Exception as exc:  # Keep budget exceptions source-local.
            if exc.__class__.__name__ in {"BudgetExceeded", "WorkBudgetExceeded"}:
                raise TraceIndexBudgetExceeded(str(exc)) from exc
            raise


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(path: Path, work_budget: Any = None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            _budget_check(work_budget)
            digest.update(chunk)
    return digest.hexdigest()


def _trace_sources(inventory: Mapping[str, Any]) -> list[dict[str, Any]]:
    sources = inventory.get("sources")
    if sources is None:
        families = inventory.get("source_families", {})
        trace = families.get("trace_span", {}) if isinstance(families, Mapping) else {}
        sources = trace.get("sources", []) if isinstance(trace, Mapping) else []
    result = [dict(source) for source in (sources or [])
              if isinstance(source, Mapping) and source.get("family") == "trace_span"]
    result.sort(key=lambda source: str(source.get("path", "")))
    return result


def _source_record_count(path: Path, work_budget: Any = None) -> tuple[list[str], int]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, strict=True)
            header = next(reader)
            count = 0
            for row in reader:
                _budget_check(work_budget)
                if not row or all(value == "" for value in row):
                    continue
                if len(row) != len(header):
                    raise SourceIntegrityError(f"wrong field count at {path}:{count + 2}")
                count += 1
            return header, count
    except (OSError, UnicodeError, csv.Error, StopIteration) as exc:
        raise SourceIntegrityError(f"cannot read trace source {path}: {exc}") from exc


def _source_manifest(dataset: Path, inventory: Mapping[str, Any], work_budget: Any) -> tuple[list[dict[str, Any]], int]:
    sources = _trace_sources(inventory)
    if not sources:
        raise SourceIntegrityError("inventory contains no trace_span sources")
    entries: list[dict[str, Any]] = []
    total = 0
    for declared in sources:
        relative = str(declared.get("path", ""))
        if not relative:
            raise SourceIntegrityError("trace source has no relative path")
        try:
            path = source_path(dataset, relative)
        except (OSError, ValueError) as exc:
            raise SourceIntegrityError(f"trace source escapes dataset: {relative}") from exc
        if not path.is_file():
            raise SourceIntegrityError(f"trace source is missing: {relative}")
        digest = _sha256(path, work_budget)
        expected_digest = declared.get("sha256")
        if expected_digest and digest != str(expected_digest):
            raise SourceIntegrityError(f"source_changed:{relative}")
        header, count = _source_record_count(path, work_budget)
        expected_count = declared.get("record_count")
        if expected_count is not None and int(expected_count) != count:
            raise SourceIntegrityError(f"source_count_changed:{relative}")
        declared_columns = list(declared.get("columns") or header)
        required = list(declared.get("required_columns") or TRACE_FIELDS)
        if header != declared_columns or any(field not in header for field in required):
            raise SourceIntegrityError(f"invalid_trace_schema:{relative}")
        entries.append({
            "family": "trace_span",
            "path": relative,
            "sha256": digest,
            "columns": header,
            "record_count": count,
        })
        total += count
    return entries, total


def _snapshot_id(deployment: str, sources: Sequence[Mapping[str, Any]]) -> str:
    payload = {
        "deployment": str(deployment),
        "sources": [dict(source) for source in sources],
        "parser_version": TRACE_PARSER_VERSION,
        "extraction_version": TRACE_EXTRACTION_VERSION,
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _row_payload(row: Mapping[str, Any]) -> dict[str, str]:
    return {field: str(row.get(field, "")) for field in TRACE_FIELDS}


def _connect(path: Path, readonly: bool = False) -> sqlite3.Connection:
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    if readonly:
        connection.execute("PRAGMA query_only=ON")
    return connection


def _index_content_hash(connection: sqlite3.Connection) -> str:
    digest = hashlib.sha256()
    for row in connection.execute("SELECT raw_json FROM spans ORDER BY row_id"):
        digest.update(str(row[0]).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE spans(
          row_id INTEGER PRIMARY KEY,
          timestamp_raw TEXT NOT NULL,
          timestamp_ms TEXT NOT NULL,
          cmdb_id TEXT NOT NULL,
          span_id TEXT NOT NULL,
          trace_id TEXT NOT NULL,
          duration_raw TEXT NOT NULL,
          type TEXT NOT NULL,
          status_code TEXT NOT NULL,
          operation_name TEXT NOT NULL,
          parent_span TEXT NOT NULL,
          source_path TEXT NOT NULL,
          source_digest TEXT NOT NULL,
          source_record INTEGER NOT NULL,
          raw_json TEXT NOT NULL
        );
        CREATE INDEX spans_trace ON spans(trace_id);
        CREATE INDEX spans_start ON spans(timestamp_ms);
        CREATE INDEX spans_root ON spans(cmdb_id, parent_span, timestamp_ms);
        """
    )


def _metadata(connection: sqlite3.Connection) -> dict[str, str]:
    return {str(row["key"]): str(row["value"])
            for row in connection.execute("SELECT key,value FROM metadata")}


def _is_reusable(index_path: Path, snapshot_id: str, total_count: int) -> bool:
    if not index_path.is_file():
        return False
    try:
        with closing(_connect(index_path, readonly=True)) as connection:
            metadata = _metadata(connection)
            count = int(connection.execute("SELECT COUNT(*) FROM spans").fetchone()[0])
            content_hash = _index_content_hash(connection)
            return (metadata.get("complete") == "1"
                    and metadata.get("index_version") == TRACE_INDEX_VERSION
                    and metadata.get("snapshot_id") == snapshot_id
                    and count == total_count
                    and metadata.get("row_content_hash") == content_hash)
    except (OSError, sqlite3.Error, ValueError):
        return False


def _build_index(index_path: Path, dataset: Path, sources: Sequence[Mapping[str, Any]],
                 snapshot_id: str, total_count: int, work_budget: Any) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = index_path.with_name(index_path.name + ".building")
    if temporary.exists():
        temporary.unlink()
    connection = _connect(temporary)
    count = 0
    try:
        _create_schema(connection)
        for source in sources:
            path = source_path(dataset, str(source["path"]))
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames != list(source["columns"]):
                    raise SourceIntegrityError(f"source_changed:{source['path']}")
                for record, row in enumerate(reader, start=2):
                    _budget_check(work_budget)
                    if not row or all(value in (None, "") for value in row.values()):
                        continue
                    if None in row.values() or any(row.get(field) is None for field in TRACE_FIELDS):
                        raise SourceIntegrityError(f"invalid_trace_row:{source['path']}:{record}")
                    raw = _row_payload(row)
                    connection.execute(
                        """INSERT INTO spans(
                          timestamp_raw,timestamp_ms,cmdb_id,span_id,trace_id,duration_raw,
                          type,status_code,operation_name,parent_span,source_path,
                          source_digest,source_record,raw_json)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (raw["timestamp"], raw["timestamp"], raw["cmdb_id"], raw["span_id"],
                         raw["trace_id"], raw["duration"], raw["type"], raw["status_code"],
                         raw["operation_name"], raw["parent_span"], source["path"],
                         source["sha256"], record, _canonical(raw)),
                    )
                    count += 1
        if count != total_count:
            raise SourceIntegrityError("source_count_changed_during_index")
        content_hash = _index_content_hash(connection)
        connection.executemany(
            "INSERT INTO metadata(key,value) VALUES(?,?)",
            [("complete", "1"), ("index_version", TRACE_INDEX_VERSION),
             ("parser_version", TRACE_PARSER_VERSION),
             ("extraction_version", TRACE_EXTRACTION_VERSION),
             ("snapshot_id", snapshot_id), ("record_count", str(count)),
             ("row_content_hash", content_hash),
             ("source_inventory", _canonical(list(sources)))],
        )
        connection.commit()
    finally:
        connection.close()
    temporary.replace(index_path)


@dataclass(frozen=True)
class PreparedTraceView(Mapping[str, Any]):
    """Verified source snapshot and read-only prepared trace access."""

    dataset_dir: Path
    output_dir: Path
    index_path: Path
    deployment: str
    snapshot_id: str
    sources: tuple[dict[str, Any], ...]
    record_count: int

    def __getitem__(self, key: str) -> Any:
        snapshot = {
            "snapshot_id": self.snapshot_id,
            "deployment": self.deployment,
            "sources": self.sources,
            "parser_version": TRACE_PARSER_VERSION,
            "extraction_version": TRACE_EXTRACTION_VERSION,
        }
        values = {
            "dataset_dir": self.dataset_dir,
            "output_dir": self.output_dir,
            "index_path": self.index_path,
            "deployment": self.deployment,
            "snapshot_id": self.snapshot_id,
            "sources": self.sources,
            "record_count": self.record_count,
            "source_inventory": self.sources,
            "snapshot": snapshot,
            "status": "verified",
        }
        return values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(("dataset_dir", "output_dir", "index_path", "deployment",
                     "snapshot_id", "sources", "record_count", "source_inventory", "snapshot", "status"))

    def __len__(self) -> int:
        return 10

    def resolve_source(self, locator: Mapping[str, Any]) -> dict[str, str]:
        """Resolve one declared CSV record without permitting path escape."""
        relative = str(locator.get("path", locator.get("source_path", "")))
        record = int(locator.get("record", locator.get("source_record", 0)) or 0)
        digest = str(locator.get("source_digest", locator.get("sha256", "")))
        declared = next((source for source in self.sources if source["path"] == relative), None)
        if declared is None or (digest and digest != declared["sha256"]):
            raise SourceIntegrityError(f"unknown_source_locator:{relative}")
        path = source_path(self.dataset_dir, relative)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for logical_record, row in enumerate(reader, start=2):
                if logical_record != record:
                    continue
                if row is None or None in row.values():
                    break
                return _row_payload(row)
        raise SourceIntegrityError(f"unknown_source_record:{relative}:{record}")

    def verify_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        """Validate a serialized snapshot identity against this prepared view."""
        expected_id = str(snapshot.get("snapshot_id", snapshot.get("id", "")))
        if expected_id != self.snapshot_id:
            raise SourceIntegrityError("source_changed:snapshot_id")
        expected_deployment = str(snapshot.get("deployment", self.deployment))
        if expected_deployment != self.deployment:
            raise SourceIntegrityError("source_changed:deployment")
        declared_sources = snapshot.get("sources")
        if declared_sources is not None and _canonical(list(declared_sources)) != _canonical(list(self.sources)):
            raise SourceIntegrityError("source_changed:inventory")

    def roots(self, start_ms: Any, end_ms: Any,
              components: Sequence[str]) -> list[dict[str, Any]]:
        """Return exact blank-parent roots in the half-open start interval."""
        from decimal import Decimal, InvalidOperation

        lower, upper = Decimal(str(start_ms)), Decimal(str(end_ms))
        allowed = {str(value) for value in components}
        if not allowed:
            return []
        rows: list[dict[str, Any]] = []
        with closing(_connect(self.index_path, readonly=True)) as connection:
            cursor = connection.execute(
                "SELECT * FROM spans WHERE parent_span='' ORDER BY row_id")
            for row in cursor:
                try:
                    timestamp = Decimal(str(row["timestamp_ms"]))
                except InvalidOperation:
                    continue
                if not timestamp.is_finite():
                    continue
                if lower <= timestamp < upper and str(row["cmdb_id"]) in allowed:
                    rows.append(_db_row(row))
        rows.sort(key=lambda row: (
            Decimal(str(row["timestamp"])), str(row["trace_id"]), str(row["span_id"]),
            str(row["source_path"]), int(row["source_record"])))
        return rows

    def all_roots(self, start_ms: Any, end_ms: Any) -> list[dict[str, Any]]:
        from decimal import Decimal, InvalidOperation

        lower, upper = Decimal(str(start_ms)), Decimal(str(end_ms))
        rows: list[dict[str, Any]] = []
        with closing(_connect(self.index_path, readonly=True)) as connection:
            for row in connection.execute("SELECT * FROM spans WHERE parent_span='' ORDER BY row_id"):
                try:
                    timestamp = Decimal(str(row["timestamp_ms"]))
                except InvalidOperation:
                    continue
                if not timestamp.is_finite():
                    continue
                if lower <= timestamp < upper:
                    rows.append(_db_row(row))
        rows.sort(key=lambda row: (Decimal(str(row["timestamp"])), str(row["trace_id"]),
                                   str(row["span_id"]), str(row["source_path"]),
                                   int(row["source_record"])))
        return rows

    def traces(self, trace_ids: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
        ids = list(dict.fromkeys(str(value) for value in trace_ids))
        result: dict[str, list[dict[str, Any]]] = {value: [] for value in ids}
        if not ids:
            return result
        with closing(_connect(self.index_path, readonly=True)) as connection:
            for offset in range(0, len(ids), 500):
                chunk = ids[offset:offset + 500]
                placeholders = ",".join("?" for _ in chunk)
                for row in connection.execute(
                    f"SELECT * FROM spans WHERE trace_id IN ({placeholders}) ORDER BY trace_id,row_id", chunk):
                    result.setdefault(str(row["trace_id"]), []).append(_db_row(row))
        return result

    # These aliases make the typed boundary pleasant for callers that prefer
    # verb-first names while preserving one implementation.
    fetch_roots = roots
    fetch_traces = traces


def _db_row(row: sqlite3.Row) -> dict[str, Any]:
    raw = json.loads(str(row["raw_json"]))
    raw.update({
        "timestamp_raw": str(row["timestamp_raw"]),
        "source_path": str(row["source_path"]),
        "source_digest": str(row["source_digest"]),
        "source_record": int(row["source_record"]),
        "locator": {"path": str(row["source_path"]),
                     "source_digest": str(row["source_digest"]),
                     "record": int(row["source_record"]),
                     "header": 1},
    })
    return raw


def prepare_sources(dataset_dir: Path, inventory: Mapping[str, Any], output_dir: Path,
                    work_budget: Any = None) -> PreparedTraceView:
    """Validate the declared trace sources and return a reusable prepared view.

    Every source path is resolved beneath ``dataset_dir``.  A source digest,
    schema and logical record count must agree with the supplied inventory;
    changed sources therefore create a hard integrity failure instead of a
    stale reusable view.
    """
    dataset = Path(dataset_dir).resolve(strict=True)
    if not dataset.is_dir():
        raise NotADirectoryError(str(dataset_dir))
    if not isinstance(inventory, Mapping):
        raise TypeError("inventory must be a mapping")
    deployment = str(inventory.get("deployment", "")).strip()
    if not deployment:
        raise ValueError("inventory deployment must be a non-empty string")
    output = Path(output_dir).resolve()
    try:
        output.relative_to(dataset)
    except ValueError:
        pass
    else:
        raise ValueError("output_dir must not be inside the read-only dataset")
    sources, total = _source_manifest(dataset, inventory, work_budget)
    snapshot_id = _snapshot_id(deployment, sources)
    index_path = output / "prepared" / "trace.sqlite3"
    if not _is_reusable(index_path, snapshot_id, total):
        _build_index(index_path, dataset, sources, snapshot_id, total, work_budget)
    return PreparedTraceView(dataset, output, index_path, deployment, snapshot_id,
                             tuple(sources), total)


__all__ = [
    "PreparedTraceView", "SourceIntegrityError", "TraceIndexBudgetExceeded",
    "TRACE_EXTRACTION_VERSION", "TRACE_INDEX_VERSION", "TRACE_PARSER_VERSION",
    "prepare_sources",
]
