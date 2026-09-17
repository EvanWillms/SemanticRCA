"""Scoped retrieval and descriptive comparison of Track 1 metric samples.

The metric files have two deliberately small adapters: four long-format
families and one wide service family.  Retrieval keeps source rows intact and
adds a locator to every observation.  Comparison is a separate public seam so
that callers can retain the complete retrieved series before applying any
packet/display limit.
"""

from __future__ import annotations

import csv
import hashlib
import math
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .paths import source_path
from typing import Any, Callable


LONG_FAMILIES = (
    "metric_container",
    "metric_node",
    "metric_mesh",
    "metric_runtime",
)
METRIC_FAMILIES = LONG_FAMILIES + ("metric_service",)
SERVICE_KPIS = ("rr", "sr", "mrt", "count")
_LONG_COLUMNS = ("timestamp", "cmdb_id", "kpi_name", "value")
_SERVICE_COLUMNS = ("service", "timestamp", "rr", "sr", "mrt", "count")
_UTC8 = timezone(timedelta(hours=8))


def _iso_epoch(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def _float_value(raw: Any) -> tuple[float | None, str | None]:
    text = "" if raw is None else str(raw).strip()
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None, "malformed_value"
    if not math.isfinite(value):
        return None, "nonfinite_value"
    return value, None


def _sample_value_key(sample: Mapping[str, Any]) -> tuple[str, Any]:
    value = sample.get("value")
    if value is None:
        return ("raw", sample.get("raw_value"))
    return ("number", float(value))


def _locator(source: Mapping[str, Any], record: int) -> dict[str, Any]:
    path = str(source["path"])
    digest = source["sha256"]
    return {
        "path": path,
        "source_digest": digest,
        "sha256": digest,
        "record": record,
    }


def _sample(
    source: Mapping[str, Any],
    row: Mapping[str, str],
    record: int,
    timestamp: float,
    raw_value: Any,
    value: float | None,
    qualification: str | None,
    kpi: str,
) -> dict[str, Any]:
    location = _locator(source, record)
    sample: dict[str, Any] = {
        "timestamp": timestamp,
        "timestamp_raw": row.get("timestamp"),
        "value": value,
        "raw_value": raw_value,
        "kpi": kpi,
        "raw": dict(row),
        "locator": location,
        "provenance": [dict(location)],
        "valid": value is not None,
        "conflict": False,
    }
    if qualification is not None:
        sample["qualification"] = qualification
    return sample


def _deduplicate(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse identical logical observations while retaining all locators."""

    by_value: dict[tuple[float, tuple[str, Any]], dict[str, Any]] = {}
    by_timestamp: dict[float, list[dict[str, Any]]] = defaultdict(list)
    for sample in samples:
        timestamp = float(sample["timestamp"])
        key = (timestamp, _sample_value_key(sample))
        existing = by_value.get(key)
        if existing is None:
            by_value[key] = sample
            by_timestamp[timestamp].append(sample)
        else:
            existing["provenance"].extend(sample["provenance"])
            # Keep the first source row as the stable primary locator and
            # preserve all source rows in provenance.
    for timestamp, values in by_timestamp.items():
        if len(values) > 1:
            conflict_id = hashlib.sha256(
                f"{timestamp}|{[(item.get('raw_value'), item.get('locator')) for item in values]}".encode()
            ).hexdigest()
            for sample in values:
                sample["conflict"] = True
                sample["conflict_group"] = conflict_id
                sample.setdefault("qualifications", []).append("conflicting_values_at_timestamp")
    return sorted(
        by_value.values(),
        key=lambda item: (
            float(item["timestamp"]),
            str(item["locator"].get("path", "")),
            int(item["locator"].get("record", 0)),
            repr(item.get("raw_value")),
        ),
    )


def _new_result(start: float, end: float) -> dict[str, Any]:
    return {
        "status": "completed",
        "series": [],
        "scanned_records": 0,
        "selected_count": 0,
        "withheld_count": 0,
        "stop_reason": None,
        "coverage": {
            "query": {
                "start": start,
                "end": end,
                "start_iso": _iso_epoch(start),
                "end_iso": _iso_epoch(end),
            },
            "historical5min": {
                "start": start - 300.0,
                "end": start,
                "start_iso": _iso_epoch(start - 300.0),
                "end_iso": _iso_epoch(start),
            },
            "families": {},
            "sample_counts": {"historical5min": 0, "query": 0},
        },
        "qualifications": [
            "Metric timestamps are interpreted as epoch seconds per the Track 1 schema.",
            "Metric values retain raw/unknown unit semantics.",
        ],
    }


def metric_series(
    dataset_dir: Path,
    inventory: Mapping[str, Any],
    scope: Mapping[str, Any],
    check_budget: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Return every metric series in the five-minute history and query window.

    ``inventory`` is the result of :func:`rca.telemetry.inventory.inventory`.
    Sources are selected only from its dataset-relative ``sources`` entries;
    no manifest, query, answer, or developer file is consulted.  The operation
    keeps all query samples and performs no display sampling.
    """

    start_raw = scope["window_start"]
    end_raw = scope["window_end"]
    deployment = scope["deployment"]
    try:
        start = datetime.fromisoformat(start_raw).timestamp()
        end = datetime.fromisoformat(end_raw).timestamp()
    except (TypeError, ValueError, OverflowError) as exc:
        return {
            "status": "unavailable",
            "series": [],
            "scanned_records": 0,
            "selected_count": 0,
            "withheld_count": 0,
            "stop_reason": "invalid_scope",
            "reason": str(exc),
            "coverage": {"families": {}},
            "qualifications": [],
        }
    if end <= start:
        result = _new_result(start, end)
        result.update({"status": "unavailable", "stop_reason": "invalid_scope", "reason": "window_end must be after window_start"})
        return result

    result = _new_result(start, end)
    inventory_deployment = inventory.get("deployment") if isinstance(inventory, Mapping) else None
    if deployment is not None and inventory_deployment is not None and str(deployment).lower() != str(inventory_deployment).lower():
        result.update({"status": "unavailable", "stop_reason": "deployment_mismatch", "reason": "scope deployment is absent from this inventory"})
        return result

    source_entries = [
        source for source in inventory.get("sources", ())
        if isinstance(source, Mapping) and str(source.get("family", "")) in METRIC_FAMILIES
    ]
    source_entries.sort(key=lambda source: (str(source.get("family", "")), str(source.get("path", ""))))
    if not source_entries:
        result.update({"status": "unavailable", "stop_reason": "metric_source_unavailable", "reason": "no metric source supplied"})
        result["coverage"]["families"] = {family: {"status": "unavailable", "reason": "no source supplied"} for family in METRIC_FAMILIES}
        return result

    grouped: dict[tuple[str, str, str, str], dict[str, list[dict[str, Any]]]] = {}
    family_states: dict[str, dict[str, Any]] = {
        family: {"status": "unavailable", "paths": [], "scanned_records": 0, "sample_counts": {"historical5min": 0, "query": 0}}
        for family in METRIC_FAMILIES
    }
    invalid_sources = 0
    usable_sources = 0
    for source in source_entries:
        family = str(source["family"])
        state = family_states[family]
        relative = str(source["path"])
        state["paths"].append(relative)
        try:
            path = source_path(Path(dataset_dir), relative)
            handle = path.open("r", encoding="utf-8-sig", newline="")
        except (OSError, ValueError) as exc:
            invalid_sources += 1
            state.setdefault("reasons", []).append(f"source_unavailable: {exc}")
            continue
        expected = _LONG_COLUMNS if family in LONG_FAMILIES else _SERVICE_COLUMNS
        try:
            with handle:
                reader = csv.DictReader(handle)
                columns = list(reader.fieldnames or [])
                missing = [column for column in expected if column not in columns]
                if missing:
                    invalid_sources += 1
                    state.setdefault("reasons", []).append("missing_columns: " + ", ".join(missing))
                    continue
                usable_sources += 1
                state["status"] = "inspected"
                for record, row in enumerate(reader, start=2):
                    if check_budget is not None and (record - 2) % 4096 == 0:
                        check_budget()
                    result["scanned_records"] += 1
                    state["scanned_records"] += 1
                    timestamp_text = row.get("timestamp", "")
                    try:
                        timestamp = float(timestamp_text)
                    except (TypeError, ValueError):
                        state.setdefault("reasons", []).append(f"record_{record}: malformed_timestamp")
                        continue
                    if not math.isfinite(timestamp):
                        state.setdefault("reasons", []).append(f"record_{record}: nonfinite_timestamp")
                        continue
                    if start - 300.0 <= timestamp < start:
                        window_name = "historical5min"
                    elif start <= timestamp < end:
                        window_name = "query"
                    else:
                        continue
                    if family in LONG_FAMILIES:
                        resource = str(row.get("cmdb_id", "")).strip()
                        kpi_values = ((str(row.get("kpi_name", "")).strip(), row.get("value", "")),)
                    else:
                        resource = str(row.get("service", "")).strip()
                        kpi_values = tuple((kpi, row.get(kpi, "")) for kpi in SERVICE_KPIS)
                    if not resource:
                        state.setdefault("reasons", []).append(f"record_{record}: missing_resource")
                        continue
                    for kpi, raw_value in kpi_values:
                        if not kpi:
                            continue
                        value, qualification = _float_value(raw_value)
                        unit = str((source.get("raw_units") or source.get("units") or {}).get(
                            "value" if family in LONG_FAMILIES else kpi,
                            "raw/unknown",
                        ))
                        key = (family, resource, kpi, unit)
                        grouped.setdefault(key, {"historical5min": [], "query": []})[window_name].append(
                            _sample(source, row, record, timestamp, raw_value, value, qualification, kpi)
                        )
                        state["sample_counts"][window_name] += 1
                        result["coverage"]["sample_counts"][window_name] += 1
        except (OSError, UnicodeError, csv.Error) as exc:
            invalid_sources += 1
            state.setdefault("reasons", []).append(f"source_failed: {exc}")

    for family, state in family_states.items():
        if state["status"] == "unavailable" and not state.get("reasons"):
            state["reasons"] = ["no source supplied"]
        result["coverage"]["families"][family] = state

    for (family, resource, kpi, unit), windows in sorted(grouped.items()):
        historical = _deduplicate(windows["historical5min"])
        query = _deduplicate(windows["query"])
        sources = sorted({sample["locator"]["path"] for sample in (*historical, *query)})
        qualifications = ["unit_unknown_raw"]
        if any(sample.get("qualification") for sample in (*historical, *query)):
            qualifications.append("malformed_or_nonfinite_values_retained_as_unavailable")
        if any(sample.get("conflict") for sample in (*historical, *query)):
            qualifications.append("conflicting_values_at_same_timestamp_excluded_from_comparison")
        result["series"].append({
            "family": family,
            "source_family": family,
            "resource": resource,
            "kpi": kpi,
            "unit": unit,
            "conversion": "identity",
            "historical5min": historical,
            "query": query,
            "samples": [*historical, *query],
            "provenance": {"sources": sources, "deployment": deployment or inventory_deployment},
            "qualifications": qualifications,
        })
    result["selected_count"] = len(result["series"])
    if invalid_sources and usable_sources:
        result["status"] = "partial"
        result["stop_reason"] = "source_unavailable_or_invalid"
    elif invalid_sources and not usable_sources:
        result["status"] = "unavailable"
        result["stop_reason"] = "metric_source_unavailable"
    elif not result["series"]:
        result["status"] = "completed"
        result["stop_reason"] = "valid_empty_selection"
    return result


def _series_samples(series: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    if key == "historical5min":
        names = ("historical5min", "historical_samples", "history", "reference")
    else:
        names = ("query", "query_samples", "observations")
    for name in names:
        value = series.get(name)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [item for item in value if isinstance(item, Mapping)]
    return []


def _series_id(series: Mapping[str, Any]) -> str:
    return "|".join(str(series.get(key, "")) for key in ("family", "resource", "kpi", "unit"))


def _finding_id(series_id: str, sample: Mapping[str, Any]) -> str:
    locator = sample.get("locator", {})
    text = f"{series_id}|{sample.get('timestamp')}|{locator.get('path')}|{locator.get('record')}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _observation_id(series_id: str, sample: Mapping[str, Any]) -> str:
    locator = sample.get("locator", {})
    text = f"{series_id}|{sample.get('timestamp')}|{locator.get('path')}|{locator.get('record')}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compare_series(series_result: Mapping[str, Any]) -> dict[str, Any]:
    """Compare every query sample with its series' historical median.

    At least twenty valid, nonconflicting reference samples are required.
    Unknown units remain qualified raw comparisons.  Every finite query
    difference is retained, including zero; candidates contain only nonzero
    signed differences and therefore preserve both directions.
    """

    series = series_result["series"]
    input_status = series_result["status"]
    comparisons: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for raw_series in series:
        if not isinstance(raw_series, Mapping):
            continue
        sid = _series_id(raw_series)
        references = [sample for sample in _series_samples(raw_series, "historical5min")
                      if sample.get("valid", sample.get("value") is not None) and not sample.get("conflict")
                      and isinstance(sample.get("value"), (int, float)) and math.isfinite(float(sample["value"]))]
        queries = _series_samples(raw_series, "query")
        reference_ids = [_observation_id(sid, sample) for sample in references]
        reference_observations = [
            {
                "id": _observation_id(sid, sample),
                "timestamp": sample.get("timestamp"),
                "value": sample.get("value"),
                "locator": sample.get("locator"),
                "provenance": sample.get("provenance", []),
            }
            for sample in references
        ]
        base = {
            "series_id": sid,
            "family": raw_series.get("family", raw_series.get("source_family")),
            "resource": raw_series.get("resource"),
            "kpi": raw_series.get("kpi"),
            "unit": raw_series.get("unit", "raw/unknown"),
            "reference_count": len(references),
            "reference_ids": reference_ids,
            "reference_observations": reference_observations,
            "query_count": len(queries),
        }
        if len(references) < 20:
            comparison_findings: list[dict[str, Any]] = []
            for sample in sorted(queries, key=lambda item: (
                float(item.get("timestamp", 0.0)),
                str((item.get("locator") or {}).get("path", "")),
                int((item.get("locator") or {}).get("record", 0)),
            )):
                unavailable = {
                    **base,
                    "finding_id": _finding_id(sid, sample),
                    "id": _finding_id(sid, sample),
                    "observation_id": _observation_id(sid, sample),
                    "channel": "metric",
                    "timestamp": sample.get("timestamp"),
                    "status": "unavailable",
                    "eligibility": "unavailable",
                    "reason": "insufficient_reference_samples",
                    "observation": sample,
                    "value": sample.get("value"),
                    "raw_value": sample.get("raw_value"),
                    "reference_median": None,
                    "signed_difference": None,
                    "difference": None,
                    "absolute_difference": None,
                    "provenance": sample.get("provenance", []),
                }
                comparison_findings.append(unavailable)
                findings.append(unavailable)
            if not comparison_findings:
                unavailable = {
                    **base,
                    "finding_id": hashlib.sha256(f"{sid}|insufficient_reference_samples".encode("utf-8")).hexdigest(),
                    "id": hashlib.sha256(f"{sid}|insufficient_reference_samples".encode("utf-8")).hexdigest(),
                    "observation_id": None,
                    "channel": "metric",
                    "timestamp": None,
                    "status": "unavailable",
                    "eligibility": "unavailable",
                    "reason": "insufficient_reference_samples",
                    "observation": None,
                    "value": None,
                    "raw_value": None,
                    "reference_median": None,
                    "signed_difference": None,
                    "difference": None,
                    "absolute_difference": None,
                    "provenance": [],
                }
                comparison_findings.append(unavailable)
                findings.append(unavailable)
            comparison = {
                **base,
                "status": "unavailable",
                "eligibility": "unavailable",
                "reason": "insufficient_reference_samples",
                "reference_median": None,
                "findings": comparison_findings,
            }
            comparisons.append(comparison)
            continue
        median = float(statistics.median(float(sample["value"]) for sample in references))
        comparison_findings: list[dict[str, Any]] = []
        for sample in sorted(queries, key=lambda item: (
            float(item.get("timestamp", 0.0)),
            str((item.get("locator") or {}).get("path", "")),
            int((item.get("locator") or {}).get("record", 0)),
        )):
            value = sample.get("value")
            valid = sample.get("valid", value is not None)
            if not valid or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or sample.get("conflict"):
                finding = {
                    **base,
                    "finding_id": _finding_id(sid, sample),
                    "id": _finding_id(sid, sample),
                    "observation_id": _observation_id(sid, sample),
                    "channel": "metric",
                    "timestamp": sample.get("timestamp"),
                    "status": "unavailable",
                    "eligibility": "unavailable",
                    "reason": "conflicting_or_nonfinite_query_sample",
                    "observation": sample,
                    "value": None,
                    "raw_value": sample.get("raw_value"),
                    "reference_median": median,
                    "signed_difference": None,
                    "difference": None,
                    "absolute_difference": None,
                    "provenance": sample.get("provenance", []),
                }
            else:
                difference = float(value) - median
                direction = "positive" if difference > 0 else "negative" if difference < 0 else "zero"
                finding = {
                    **base,
                    "finding_id": _finding_id(sid, sample),
                    "id": _finding_id(sid, sample),
                    "observation_id": _observation_id(sid, sample),
                    "channel": "metric",
                    "timestamp": sample.get("timestamp"),
                    "status": "qualified",
                    "eligibility": "qualified",
                    "reason": "raw_unknown_unit" if str(raw_series.get("unit", "raw/unknown")) in {"raw/unknown", "unknown", ""} else None,
                    "observation": sample,
                    "value": float(value),
                    "raw_value": float(value),
                    "reference_median": median,
                    "signed_difference": difference,
                    "difference": difference,
                    "absolute_difference": abs(difference),
                    "direction": direction,
                    "provenance": sample.get("provenance", []),
                    "qualifications": ["reference_is_empirical_median", "unit_unknown_raw"],
                }
                if difference != 0.0:
                    candidates.append({
                        **finding,
                        "channel": "metric",
                        "candidate_priority": abs(difference),
                    })
            comparison_findings.append(finding)
            findings.append(finding)
        comparison = {
            **base,
            "status": "qualified",
            "eligibility": "qualified",
            "reference_median": median,
            "findings": comparison_findings,
            "qualifications": ["at least 20 valid nonconflicting historical samples", "raw/unknown unit"],
        }
        comparisons.append(comparison)
    candidates.sort(key=lambda finding: (
        str(finding.get("family", "")),
        str(finding.get("resource", "")),
        str(finding.get("kpi", "")),
        str(finding.get("unit", "")),
        -float(finding.get("absolute_difference", 0.0)),
        float((finding.get("observation") or {}).get("timestamp", 0.0)),
        str(((finding.get("observation") or {}).get("locator") or {}).get("path", "")),
        int(((finding.get("observation") or {}).get("locator") or {}).get("record", 0)),
    ))
    status = input_status if input_status in ("partial", "unavailable") else "completed"
    return {
        "status": status,
        "comparisons": comparisons,
        "findings": findings,
        "candidates": candidates,
        "candidate_count": len(candidates),
        "qualifications": [
            "Comparison uses all inspected query samples before any display reduction.",
            "No rates, standardized scores, or failure-count pruning are applied.",
        ],
    }


__all__ = ["compare_series", "metric_series"]
