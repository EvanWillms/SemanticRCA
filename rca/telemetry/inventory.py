"""Read-only inventory of the supplied Track 1 telemetry sources."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final


INVENTORY_SCHEMA_VERSION: Final = "track1-inventory-v1"
SOURCE_SCHEMA_VERSION: Final = "track1-source-schema-v1"
_HASH_CHUNK_SIZE: Final = 1024 * 1024
_CSV_BATCH_SIZE: Final = 4096


class InventoryBudgetExceeded(RuntimeError):
    """The caller's optional budget check stopped an inventory scan."""


@dataclass(frozen=True)
class _Family:
    name: str
    directory: str
    filename: str
    columns: tuple[str, ...]
    timestamp_unit: str
    raw_units: tuple[tuple[str, str], ...]
    kind: str


_LONG_COLUMNS = ("timestamp", "cmdb_id", "kpi_name", "value")
_LONG_UNITS = (("timestamp", "seconds"), ("value", "raw/unknown"))
_LOG_COLUMNS = ("log_id", "timestamp", "cmdb_id", "log_name", "value")
_LOG_UNITS = (("timestamp", "seconds"), ("value", "raw/unknown"))
_SERVICE_COLUMNS = ("service", "timestamp", "rr", "sr", "mrt", "count")
_SERVICE_UNITS = (
    ("timestamp", "seconds"),
    ("rr", "raw/unknown"),
    ("sr", "raw/unknown"),
    ("mrt", "raw/unknown"),
    ("count", "raw/unknown"),
)
_TRACE_COLUMNS = (
    "timestamp", "cmdb_id", "span_id", "trace_id", "duration", "type",
    "status_code", "operation_name", "parent_span",
)
_TRACE_UNITS = (("timestamp", "milliseconds"), ("duration", "raw/unknown"))

_SPECS: tuple[_Family, ...] = tuple(
    _Family(name, "metric", f"{name}.csv", _LONG_COLUMNS, "seconds", _LONG_UNITS, "long")
    for name in ("metric_container", "metric_mesh", "metric_node", "metric_runtime")
) + (
    _Family("metric_service", "metric", "metric_service.csv", _SERVICE_COLUMNS, "seconds", _SERVICE_UNITS, "service"),
    _Family("log_service", "log", "log_service.csv", _LOG_COLUMNS, "seconds", _LOG_UNITS, "log"),
    _Family("log_proxy", "log", "log_proxy.csv", _LOG_COLUMNS, "seconds", _LOG_UNITS, "log"),
    _Family("trace_span", "trace", "trace_span.csv", _TRACE_COLUMNS, "milliseconds", _TRACE_UNITS, "trace"),
)
ALLOWED_SOURCE_FAMILIES: Final[tuple[str, ...]] = tuple(spec.name for spec in _SPECS)


def _check_budget(check_budget: Callable[[], None] | None) -> None:
    if check_budget is None:
        return
    check_budget()


def _sha256(path: Path, check_budget: Callable[[], None] | None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(_HASH_CHUNK_SIZE)
            if not chunk:
                return digest.hexdigest()
            _check_budget(check_budget)
            digest.update(chunk)


def _relative_source(path: Path, dataset: Path) -> str:
    # The caller constructs ``path`` beneath ``dataset``.  Resolve once here
    # to reject a symlink that would read outside the supplied bundle.
    path.resolve(strict=True).relative_to(dataset.resolve(strict=True))
    return path.relative_to(dataset).as_posix()


def _new_identity() -> dict[str, set[Any]]:
    return {
        "resources": set(),
        "kpis": set(),
        "resource_kpis": set(),
        "operations": set(),
        "types": set(),
        "status_codes": set(),
    }


def _add_identity(spec: _Family, index: dict[str, int], row: list[str], identity: dict[str, set[Any]]) -> None:
    if spec.kind == "long":
        resource, kpi = row[index["cmdb_id"]].strip(), row[index["kpi_name"]].strip()
        if resource and kpi:
            identity["resources"].add(resource)
            identity["kpis"].add(kpi)
            identity["resource_kpis"].add((resource, kpi))
    elif spec.kind == "service":
        resource = row[index["service"]].strip()
        if resource:
            identity["resources"].add(resource)
            for kpi in ("rr", "sr", "mrt", "count"):
                identity["kpis"].add(kpi)
                identity["resource_kpis"].add((resource, kpi))
    elif spec.kind == "log":
        resource, kpi = row[index["cmdb_id"]].strip(), row[index["log_name"]].strip()
        if resource:
            identity["resources"].add(resource)
        if kpi:
            identity["kpis"].add(kpi)
        if resource and kpi:
            identity["resource_kpis"].add((resource, kpi))
    else:
        resource = row[index["cmdb_id"]].strip()
        operation = row[index["operation_name"]].strip()
        if resource:
            identity["resources"].add(resource)
        if operation:
            identity["operations"].add(operation)
            identity["kpis"].add(operation)
        if resource and operation:
            identity["resource_kpis"].add((resource, operation))
        span_type, status = row[index["type"]].strip(), row[index["status_code"]].strip()
        if span_type:
            identity["types"].add(span_type)
        if status:
            identity["status_codes"].add(status)


def _pairs(identity: dict[str, set[Any]]) -> list[dict[str, str]]:
    return [{"resource": resource, "kpi": kpi} for resource, kpi in sorted(identity["resource_kpis"])]


def _read_source(path: Path, dataset: Path, spec: _Family, check_budget: Callable[[], None] | None) -> dict[str, Any]:
    relative_path = _relative_source(path, dataset)
    digest = _sha256(path, check_budget)
    identity = _new_identity()
    record_count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        try:
            columns = next(reader)
        except StopIteration as exc:
            raise ValueError("source CSV has no header") from exc
        if len(columns) != len(set(columns)):
            raise ValueError("source CSV has duplicate columns")
        missing = sorted(set(spec.columns).difference(columns))
        if missing:
            raise ValueError("source CSV is missing required columns: " + ", ".join(missing))
        index = {name: columns.index(name) for name in spec.columns}
        for row in reader:
            if len(row) != len(columns):
                raise ValueError("source CSV row has the wrong number of columns")
            record_count += 1
            _add_identity(spec, index, row, identity)
            if record_count % _CSV_BATCH_SIZE == 0:
                _check_budget(check_budget)
        if record_count % _CSV_BATCH_SIZE:
            _check_budget(check_budget)

    raw_units = dict(spec.raw_units)
    return {
        "family": spec.name,
        "path": relative_path,
        "sha256": digest,
        "partition": path.parent.parent.name,
        "schema_version": SOURCE_SCHEMA_VERSION,
        "schema_status": "valid",
        "columns": columns,
        "required_columns": list(spec.columns),
        "timestamp_unit": spec.timestamp_unit,
        "raw_units": raw_units,
        "record_count": record_count,
        "resources": sorted(identity["resources"]),
        "kpis": sorted(identity["kpis"]),
        "resource_kpis": _pairs(identity),
        "operations": sorted(identity["operations"]),
        "types": sorted(identity["types"]),
        "status_codes": sorted(identity["status_codes"]),
    }


def _empty_family(spec: _Family) -> dict[str, Any]:
    return {
        "family": spec.name,
        "status": "unavailable",
        "sources": [],
        "columns": list(spec.columns),
        "required_columns": list(spec.columns),
        "timestamp_unit": spec.timestamp_unit,
        "raw_units": dict(spec.raw_units),
        "record_count": 0,
        "resources": [],
        "kpis": [],
        "resource_kpis": [],
        "operations": [],
        "types": [],
        "status_codes": [],
        "reason": "no source file supplied",
    }


def _family_summary(spec: _Family, sources: list[dict[str, Any]]) -> dict[str, Any]:
    first = sources[0]
    pairs = {(pair["resource"], pair["kpi"]) for source in sources for pair in source["resource_kpis"]}
    return {
        "family": spec.name,
        "status": "available",
        "sources": [source["path"] for source in sources],
        "columns": first["columns"],
        "required_columns": list(spec.columns),
        "timestamp_unit": spec.timestamp_unit,
        "raw_units": dict(first["raw_units"]),
        "record_count": sum(source["record_count"] for source in sources),
        "resources": sorted({value for source in sources for value in source["resources"]}),
        "kpis": sorted({value for source in sources for value in source["kpis"]}),
        "resource_kpis": [{"resource": resource, "kpi": kpi} for resource, kpi in sorted(pairs)],
        "operations": sorted({value for source in sources for value in source["operations"]}),
        "types": sorted({value for source in sources for value in source["types"]}),
        "status_codes": sorted({value for source in sources for value in source["status_codes"]}),
    }


def inventory(
    dataset_dir: Path,
    deployment: str,
    check_budget: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Discover and validate allowed Track 1 CSV sources under ``dataset_dir``.

    Source reads are streamed row by row; ``check_budget`` is called after
    each fixed-size hash chunk and CSV batch.  It may raise to stop work; the
    partial receipt is never returned as complete.
    """

    dataset = Path(dataset_dir).resolve(strict=True)
    if not dataset.is_dir():
        raise NotADirectoryError(str(dataset_dir))
    if not isinstance(deployment, str) or not deployment.strip():
        raise ValueError("deployment must be a non-empty string")

    telemetry = dataset / "telemetry"
    partitions = sorted(
        (path for path in telemetry.iterdir() if path.is_dir() and not path.name.startswith(".")),
        key=lambda path: path.name,
    ) if telemetry.is_dir() else []
    found: dict[str, list[dict[str, Any]]] = {spec.name: [] for spec in _SPECS}
    rejected: list[dict[str, Any]] = []
    for partition in partitions:
        for spec in _SPECS:
            path = partition / spec.directory / spec.filename
            if not path.is_file():
                continue
            try:
                found[spec.name].append(_read_source(path, dataset, spec, check_budget))
            except InventoryBudgetExceeded:
                raise
            except (OSError, UnicodeError, csv.Error, ValueError) as exc:
                entry: dict[str, Any] = {
                    "family": spec.name,
                    "path": path.relative_to(dataset).as_posix(),
                    "schema_status": "invalid",
                    "reason": str(exc),
                }
                try:
                    _relative_source(path, dataset)
                    entry["sha256"] = _sha256(path, None)
                except (OSError, ValueError):
                    pass
                rejected.append(entry)

    families: dict[str, dict[str, Any]] = {}
    unavailable: list[str] = []
    for spec in _SPECS:
        if found[spec.name]:
            families[spec.name] = _family_summary(spec, found[spec.name])
        else:
            summary = _empty_family(spec)
            invalid = [entry for entry in rejected if entry["family"] == spec.name]
            if invalid:
                summary["status"] = "invalid"
                summary["reason"] = "source schema validation failed"
                summary["rejected_sources"] = invalid
            families[spec.name] = summary
            unavailable.append(spec.name)
    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "deployment": deployment,
        "source_families": families,
        "sources": [source for spec in _SPECS for source in found[spec.name]],
        "unavailable_families": unavailable,
        "rejected_sources": rejected,
        "status": "complete" if not unavailable else "partial",
    }


__all__ = [
    "ALLOWED_SOURCE_FAMILIES",
    "INVENTORY_SCHEMA_VERSION",
    "InventoryBudgetExceeded",
    "inventory",
]
