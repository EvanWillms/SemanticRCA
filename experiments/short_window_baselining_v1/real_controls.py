"""Select a frozen real-observation control case without using outcome labels.

The selector is deliberately event-time and structure based.  It chooses the
earliest protocol anchor, a C2 cohort with the declared count/bin/concentration
support across at least two frontend replicas, and query roots in the anchor's
primary interval with the same C2 signature.  Duration values are carried
through as observations; they are never used to choose the cohort.

This module is an execution entry point.  Importing it does not read the
dataset or run controls.  ``run_real_controls`` writes a frozen selection
manifest before invoking the shared controlled-check runner.
"""

from __future__ import annotations

import copy
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping

from .contracts import signature_key, stable_membership_hash, support_diagnostics
from .controlled_checks import run_control_checks
from .index import (
    DEFAULT_ARTIFACT_ROOT,
    DEFAULT_INDEX,
    DEFAULT_TRACE_ROOT,
    build_index,
    discover_frontend_components,
    source_inventory,
    validate_index,
    open_index,
)
from .runner import anchor_specs, collect_observations


REAL_CONTROLS_VERSION = "short-window-baselining-v1/real-controls-1"
REFERENCE_LOOKBACK_MINUTES = 10
PRIMARY_QUERY_MINUTES = 5


def _identity(row: Mapping) -> tuple[str, str]:
    return (str(row.get("trace_id", "")), str(row.get("span_id", "")))


def _timestamp_ms(row: Mapping) -> int:
    return int(row.get("timestamp_ms", row.get("start_ms", -1)))


def _source(row: Mapping) -> dict:
    value = row.get("source")
    if isinstance(value, Mapping):
        return {
            "source_file": str(value.get("source_file", row.get("source_file", ""))),
            "source_record": int(value.get("source_record", row.get("source_record", 0)) or 0),
            "source_header": int(value.get("source_header", row.get("source_header", 1)) or 1),
        }
    return {
        "source_file": str(row.get("source_file", "")),
        "source_record": int(row.get("source_record", 0) or 0),
        "source_header": int(row.get("source_header", 1) or 1),
    }


def _c2_key(row: Mapping) -> str:
    signature = row.get("signature", {}).get("C2")
    if not isinstance(signature, Mapping):
        return ""
    return signature_key(signature)


def _reference_candidate(row: Mapping, anchor_ms: int, start_ms: int) -> bool:
    if not row.get("identity_resolved", False):
        return False
    if row.get("structure_status") == "unknown_structure":
        return False
    timestamp = _timestamp_ms(row)
    if timestamp < start_ms or timestamp >= anchor_ms:
        return False
    endpoint = row.get("max_recorded_end_us")
    return endpoint is not None and int(endpoint) < anchor_ms * 1000


def _query_candidate(row: Mapping, anchor_ms: int, end_ms: int) -> bool:
    return bool(row.get("identity_resolved", False)) and anchor_ms <= _timestamp_ms(row) < end_ms


def _selection_manifest(
    records: Iterable[Mapping],
    *,
    anchor: Mapping,
    allowlist: list[str],
    selected_c2_key: str,
    support: Mapping,
    reference_rows: list[Mapping],
    query_rows: list[Mapping],
    source_validation: Mapping,
) -> dict:
    rows = list(reference_rows) + list(query_rows)
    return {
        "version": REAL_CONTROLS_VERSION,
    "selection_basis": {
        "anchor_order": "earliest protocol anchor",
        "cohort_tie_break": "largest eligible reference count, then lexical C2 signature key",
            "reference_interval": [anchor["epoch_ms"] - REFERENCE_LOOKBACK_MINUTES * 60_000, anchor["epoch_ms"]],
            "query_interval": [anchor["epoch_ms"], anchor["epoch_ms"] + PRIMARY_QUERY_MINUTES * 60_000],
            "signature_mode": "C2",
            "minimum_reference_count": 20,
            "minimum_occupied_minutes": 5,
            "maximum_minute_fraction": 0.5,
            "minimum_replica_count": 2,
            "duration_used_for_selection": False,
            "labels_or_health_fields_used": False,
            "duration_intervention_endpoint_membership": "frozen_to_original_max_recorded_end_us; controls override duration_ms only",
        },
        "anchor": dict(anchor),
        "component_allowlist": list(allowlist),
        "index_validation": dict(source_validation),
        "selected_c2_key": selected_c2_key,
        "reference_support": dict(support),
        "reference_count": len(reference_rows),
        "reference_replica_counts": dict(Counter(str(row.get("cmdb_id", "")) for row in reference_rows)),
        "query_count": len(query_rows),
        "source_files": sorted({_source(row)["source_file"] for row in rows}),
        "input_membership_hash": stable_membership_hash(rows),
        "rows": [
            {
                "identity": list(_identity(row)),
                "role": str(row.get("role", "")),
                "cmdb_id": str(row.get("cmdb_id", "")),
                "timestamp_ms": _timestamp_ms(row),
                "source": _source(row),
            }
            for row in rows
        ],
    }


def select_real_case(records: Mapping[tuple[str, str], Mapping], anchor: Mapping | None = None, allowlist: list[str] | None = None) -> dict:
    """Select the deterministic earliest-anchor C2 case or report unavailable.

    The returned rows are copied and assigned ``reference``/``query`` roles
    strictly from the frozen event-time intervals.  No duration or outcome
    field participates in selection.
    """
    anchor = dict(anchor or anchor_specs()[0])
    allowlist = list(allowlist or sorted({str(row.get("cmdb_id", "")) for row in records.values()}))
    anchor_ms = int(anchor["epoch_ms"])
    reference_start_ms = anchor_ms - REFERENCE_LOOKBACK_MINUTES * 60_000
    query_end_ms = anchor_ms + PRIMARY_QUERY_MINUTES * 60_000
    candidates: dict[str, list[dict]] = defaultdict(list)
    for row in records.values():
        if str(row.get("cmdb_id", "")) not in set(allowlist):
            continue
        if _reference_candidate(row, anchor_ms, reference_start_ms):
            key = _c2_key(row)
            if key:
                candidates[key].append(copy.deepcopy(dict(row)))
    eligible: list[tuple[str, list[dict], dict]] = []
    for key, rows in candidates.items():
        support = support_diagnostics(rows, REFERENCE_LOOKBACK_MINUTES)
        replicas = {str(row.get("cmdb_id", "")) for row in rows}
        if support["supported"] and len(replicas) >= 2:
            eligible.append((key, rows, {**support, "replica_count": len(replicas)}))
    if not eligible:
        return {
            "status": "unavailable",
            "reason": "no_known_c2_cohort_with_declared_support_across_two_replicas",
            "anchor": anchor,
            "component_allowlist": allowlist,
            "reference_interval": [reference_start_ms, anchor_ms],
            "query_interval": [anchor_ms, query_end_ms],
            "candidate_cohort_count": len(candidates),
            "eligible_cohort_count": 0,
            "records": [],
            "manifest": None,
        }
    selected_key, reference_rows, support = sorted(eligible, key=lambda item: (-len(item[1]), item[0]))[0]
    query_rows = []
    for row in records.values():
        if str(row.get("cmdb_id", "")) not in set(allowlist):
            continue
        if _query_candidate(row, anchor_ms, query_end_ms) and _c2_key(row) == selected_key:
            query_rows.append(copy.deepcopy(dict(row)))
    query_rows.sort(key=lambda row: (_timestamp_ms(row), _identity(row), _source(row)["source_file"], _source(row)["source_record"]))
    if not query_rows:
        return {
            "status": "unavailable",
            "reason": "selected_c2_cohort_has_no_matching_primary_queries",
            "anchor": anchor,
            "component_allowlist": allowlist,
            "selected_c2_key": selected_key,
            "reference_interval": [reference_start_ms, anchor_ms],
            "query_interval": [anchor_ms, query_end_ms],
            "reference_count": len(reference_rows),
            "reference_support": support,
            "records": [],
            "manifest": None,
        }
    selected_rows = []
    for row in reference_rows:
        row["role"] = "reference"
        selected_rows.append(row)
    for row in query_rows:
        row["role"] = "query"
        selected_rows.append(row)
    return {
        "status": "available",
        "reason": None,
        "anchor": anchor,
        "component_allowlist": allowlist,
        "selected_c2_key": selected_key,
        "reference_interval": [reference_start_ms, anchor_ms],
        "query_interval": [anchor_ms, query_end_ms],
        "reference_count": len(reference_rows),
        "query_count": len(query_rows),
        "reference_support": support,
        "records": selected_rows,
    }


def run_real_controls(
    *,
    output_dir: Path = DEFAULT_ARTIFACT_ROOT / "controls",
    trace_root: Path = DEFAULT_TRACE_ROOT,
    index_path: Path = DEFAULT_INDEX,
    expected_path: Path | None = None,
) -> dict:
    """Collect, freeze, and run controls for the selected real-observation case."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index_summary = build_index(index_path, trace_root)
    validation = validate_index(index_path, trace_root)
    if not validation.get("valid"):
        raise RuntimeError(f"trace index failed validation: {validation}")
    anchors = anchor_specs()
    anchor = anchors[0]
    conn = open_index(index_path)
    try:
        allowlist = discover_frontend_components(conn)
    finally:
        conn.close()
    records, collection_cost = collect_observations(index_path, allowlist, [anchor])
    selection = select_real_case(records, anchor=anchor, allowlist=allowlist)
    selection["collection_cost"] = collection_cost
    selection["index_summary"] = index_summary
    selection["source_inventory"] = source_inventory(trace_root)
    if selection["status"] != "available":
        result = {"version": REAL_CONTROLS_VERSION, "status": "unavailable", "selection": selection, "controls": None}
        (output_dir / "real-controls-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result
    source_manifest = _selection_manifest(
        selection["records"],
        anchor=anchor,
        allowlist=allowlist,
        selected_c2_key=selection["selected_c2_key"],
        support=selection["reference_support"],
        reference_rows=[row for row in selection["records"] if row["role"] == "reference"],
        query_rows=[row for row in selection["records"] if row["role"] == "query"],
        source_validation=validation,
    )
    (output_dir / "real-controls-input-manifest.json").write_text(json.dumps(source_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    controls = run_control_checks(selection["records"], expected_path=expected_path, anchor=anchor, allowlist=allowlist)
    reference_count = int(selection["reference_count"])
    unavailable_targets = [target for target in (10, 20, 50, 100) if target > reference_count]
    for row in controls["checks"]:
        if row["name"] == "thin_references" and row.get("target_count") in unavailable_targets:
            row["availability"] = "unavailable_original_support"
        else:
            row["availability"] = "available"
    controls["unavailable_thinning_targets"] = unavailable_targets
    controls["available_check_rows"] = sum(1 for row in controls["checks"] if row["availability"] == "available")
    controls["real_control_status"] = "qualified_unavailable_thinning_targets" if unavailable_targets else "completed"
    result = {"version": REAL_CONTROLS_VERSION, "status": "completed", "selection": selection, "input_manifest": source_manifest, "controls": controls}
    (output_dir / "real-controls-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    raise SystemExit("Import run_real_controls from this module; execute only after review.")
