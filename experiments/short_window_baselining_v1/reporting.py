"""Create the review tables for a completed short-window matrix.

The runner deliberately emits source-linked, cell-level tables.  This module
is the read-only reporting pass over those tables.  It applies the two
coverage/uncertainty gates to the full 12-anchor population, preserves the
C0/C2 scope rows, and joins interval checks to the comparison identities and
their observed signatures.  It does not choose a global policy; the final
primary and fallback decision remains a parent-review action.

Only the standard library is used.  The implementation streams the large
comparison table and keeps only the bounded observation, uncertainty, and
cell summaries in memory.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping


LOOKBACKS = (5, 10, 15, 30, 60)
MODES = ("C0", "C1", "C2")
REPLICAS = ("same_replica", "pooled")
ANCHORS = tuple(
    f"2022-03-{day:02d}T{hour:02d}:00:00+08:00"
    for day in (20, 21)
    for hour in (1, 5, 9, 13, 17, 21)
)
ANCHOR_COUNT = len(ANCHORS)
MIN_USABLE_BOOTSTRAPS = 190
MAX_MISSING_ANCHORS = 2
RARE_CLASS_QUERY_THRESHOLD = 20
SUPPORTED_STATISTIC = "median_ms_and_signed_absolute_excess_ms"


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return value


def _jsonl(path: Path) -> Iterable[dict]:
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number} is not a JSON object")
            yield value


def _optional_jsonl(path: Path) -> Iterable[dict]:
    if not path.is_file():
        return iter(())
    return _jsonl(path)


def _cell(row: Mapping) -> tuple[str, int, str, str]:
    return (
        str(row.get("anchor_id", "")),
        int(row.get("lookback_minutes", -1)),
        str(row.get("mode", "")),
        str(row.get("replica_policy", "")),
    )


def _identity(row: Mapping) -> tuple[str, str]:
    root = row.get("root_key")
    if isinstance(root, (list, tuple)) and len(root) == 2:
        return str(root[0]), str(root[1])
    return str(row.get("trace_id", "")), str(row.get("span_id", ""))


def _number(value: object) -> float | None:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _json_key(value: object) -> str:
    if isinstance(value, Mapping):
        return json.dumps(dict(value), sort_keys=True, separators=(",", ":"))
    if isinstance(value, (list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def _strata(observation: Mapping) -> tuple[tuple[str, str], ...]:
    signatures = observation.get("signature", {})
    if not isinstance(signatures, Mapping):
        signatures = {}
    # C0 and C2 are the predeclared request classes.  Keep an explicit missing
    # value so malformed records cannot silently disappear from a denominator.
    return tuple((kind, _json_key(signatures.get(kind, "__missing__"))) for kind in ("C0", "C2"))


def _empty_acc() -> dict:
    return {
        "positive_ids": set(),
        "pass_ids": set(),
        "inconclusive_ids": set(),
        "zero_or_missing_ids": set(),
        "comparison_ids": set(),
    }


def _gate3(acc: Mapping) -> tuple[bool, bool, int, int, int]:
    positive = len(acc["positive_ids"])
    passing = len(acc["pass_ids"])
    inconclusive = len(acc["inconclusive_ids"])
    if not positive:
        return False, True, positive, passing, inconclusive
    return passing / positive >= 0.8 and inconclusive == 0, False, positive, passing, inconclusive


def _coverage_summary(rows: list[dict]) -> dict:
    by_policy: dict[tuple[str, str, int], list[dict]] = defaultdict(list)
    for row in rows:
        by_policy[(str(row.get("mode", "")), str(row.get("replica_policy", "")), int(row.get("lookback_minutes", -1)))].append(row)
    result = {}
    for key, policy_rows in by_policy.items():
        present = {str(row.get("anchor_id", "")) for row in policy_rows}
        resolved = sum(int(row.get("query_resolved_count", 0) or 0) for row in policy_rows)
        supported = sum(int(row.get("supported_query_count", 0) or 0) for row in policy_rows)
        anchor_pass = sum(
            1
            for row in policy_rows
            if int(row.get("query_resolved_count", 0) or 0) > 0
            and _number(row.get("request_coverage")) is not None
            and float(row.get("request_coverage")) >= 0.8
        )
        boundary = sum(int(row.get("boundary_excluded_count", 0) or 0) for row in policy_rows)
        raw_refs = sum(int(row.get("reference_raw_count", 0) or 0) for row in policy_rows)
        aging = [item for row in policy_rows for item in (row.get("aging") or []) if isinstance(item, Mapping)]
        aging_pass = sum(1 for item in aging if _number(item.get("request_coverage")) is not None and float(item["request_coverage"]) >= 0.8)
        aging_supported = sum(int(item.get("supported_query_count", 0) or 0) for item in aging)
        unknown_structure = sum(int(row.get("query_unknown_structure_count", 0) or 0) for row in policy_rows)
        unavailable = sum(int(row.get("query_unavailable_duration_count", 0) or 0) for row in policy_rows)
        zero_medians = sum(int(row.get("zero_median_cohort_count", 0) or 0) for row in policy_rows)
        qualifications = sorted({str(value) for row in policy_rows for value in (row.get("qualifications") or [])})
        result[key] = {
            "mode": key[0], "replica_policy": key[1], "lookback_minutes": key[2],
            "anchor_count": len(present), "missing_anchor_count": ANCHOR_COUNT - len(present),
            "resolved_query_count": resolved, "supported_query_count": supported,
            "request_coverage": supported / resolved if resolved else 0.0,
            "anchors_at_least_80pct": anchor_pass,
            "gate_2_coverage": bool(resolved and supported / resolved >= 0.9 and anchor_pass >= ANCHOR_COUNT - MAX_MISSING_ANCHORS),
            "boundary_excluded_count": boundary,
            "boundary_fraction": boundary / raw_refs if raw_refs else None,
            "unknown_structure_count": unknown_structure,
            "unavailable_duration_count": unavailable,
            "zero_median_cohort_count": zero_medians,
            "qualifications": qualifications,
            "aging_slice_count": len(aging), "aging_slices_at_least_80pct": aging_pass,
            "aging_supported_query_count": aging_supported,
        }
    return result


def _load_stratum_rows(independent: Mapping) -> dict[tuple, dict]:
    """Index independent-analysis C0/C2 rows by cell and exact class key."""
    result = {}
    paired = independent.get("paired_sensitivities", {})
    for row in paired.get("stratum_coverage_by_C0_C2_replica", []) if isinstance(paired, Mapping) else []:
        kind = str(row.get("stratum_kind", ""))
        if kind not in {"C0", "C2"}:
            continue
        try:
            key = (_cell(row), kind, str(row.get("stratum_key", "")))
        except (TypeError, ValueError):
            continue
        result[key] = dict(row)
    return result


def _class_coverage_summary(stratum_rows: Mapping[tuple, dict]) -> dict[tuple, dict]:
    by_class: dict[tuple, list[dict]] = defaultdict(list)
    for (cell, kind, stratum_key), row in stratum_rows.items():
        by_class[(cell[2], cell[3], cell[1], kind, stratum_key)].append(row)
    result = {}
    for key, rows in by_class.items():
        anchors = {str(row.get("anchor_id", "")) for row in rows}
        query_count = sum(int(row.get("query_count", 0) or 0) for row in rows)
        resolved = sum(int(row.get("resolved_query_count", 0) or 0) for row in rows)
        supported = sum(int(row.get("supported_query_count", 0) or 0) for row in rows)
        pass_anchors = sum(
            1 for row in rows
            if int(row.get("resolved_query_count", 0) or 0) > 0
            and _number(row.get("request_coverage")) is not None
            and float(row["request_coverage"]) >= 0.8
        )
        result[key] = {
            "mode": key[0], "replica_policy": key[1], "lookback_minutes": key[2],
            "stratum_kind": key[3], "stratum_key": key[4],
            "anchor_count": len(anchors), "missing_anchor_count": ANCHOR_COUNT - len(anchors),
        "observed_class_query_count": query_count,
            "resolved_query_count": resolved, "supported_query_count": supported,
            "rare_class": query_count < RARE_CLASS_QUERY_THRESHOLD,
            "class_request_coverage": supported / query_count if query_count else 0.0,
            "request_coverage": supported / resolved if resolved else 0.0,
            "anchors_at_least_80pct": pass_anchors,
            "gate_2_coverage": bool(resolved and supported / resolved >= 0.9 and pass_anchors >= ANCHOR_COUNT - MAX_MISSING_ANCHORS),
        }
    return result


def _cohort_coverage(artifact_dir: Path, observations: Mapping[tuple[str, str], Mapping]) -> tuple[dict[tuple, dict], dict[tuple, dict]]:
    """Count observed and supported query cohort-anchor incidences.

    Cohort coverage is a separate denominator from request coverage.  The
    set element includes the anchor, so support at one anchor cannot imply
    support at another.  Class incidences use the compact observation index to
    provide the same diagnostic within fixed C0/C2 scopes.
    """
    observed: dict[tuple, set[tuple[str, str]]] = defaultdict(set)
    supported: dict[tuple, set[tuple[str, str]]] = defaultdict(set)
    class_observed: dict[tuple, set[tuple[str, str]]] = defaultdict(set)
    class_supported: dict[tuple, set[tuple[str, str]]] = defaultdict(set)
    membership_path = artifact_dir / "memberships.jsonl"
    if membership_path.is_file():
        for row in _jsonl(membership_path):
            if str(row.get("role", "")) != "query":
                continue
            key = (str(row.get("mode", "")), str(row.get("replica_policy", "")), int(row.get("lookback_minutes", -1)))
            cohort = row.get("cohort_key")
            cohort_text = str(cohort) if cohort is not None else "__UNMATCHED__"
            incidence = (str(row.get("anchor_id", "")), cohort_text)
            observed[key].add(incidence)
            observation = observations.get(_identity(row), {})
            for kind, stratum_key in _strata(observation):
                class_observed[(key[0], key[1], key[2], kind, stratum_key)].add(incidence)
    comparison_path = artifact_dir / "comparisons.jsonl"
    if comparison_path.is_file():
        for row in _jsonl(comparison_path):
            cohort = row.get("cohort_key")
            if cohort is None:
                continue
            key = (str(row.get("mode", "")), str(row.get("replica_policy", "")), int(row.get("lookback_minutes", -1)))
            cohort_text = str(cohort)
            incidence = (str(row.get("anchor_id", "")), cohort_text)
            supported[key].add(incidence)
            observation = observations.get(_identity(row), {})
            for kind, stratum_key in _strata(observation):
                class_supported[(key[0], key[1], key[2], kind, stratum_key)].add(incidence)
    result = {}
    for key in set(observed) | set(supported):
        all_cohorts = observed.get(key, set())
        supported_cohorts = supported.get(key, set())
        result[key] = {
            "all_observed_cohort_count": len(all_cohorts),
            "supported_observed_cohort_count": len(supported_cohorts & all_cohorts),
            "observed_cohort_coverage": len(supported_cohorts & all_cohorts) / len(all_cohorts) if all_cohorts else 0.0,
            "unmatched_observed_cohort_count": sum(1 for _, cohort in all_cohorts if cohort == "__UNMATCHED__"),
        }
    class_result = {}
    for key in set(class_observed) | set(class_supported):
        all_cohorts = class_observed.get(key, set())
        supported_cohorts = class_supported.get(key, set())
        class_result[key] = {
            "all_observed_cohort_count": len(all_cohorts),
            "supported_observed_cohort_count": len(supported_cohorts & all_cohorts),
            "observed_cohort_coverage": len(supported_cohorts & all_cohorts) / len(all_cohorts) if all_cohorts else 0.0,
            "unmatched_observed_cohort_count": sum(1 for _, cohort in all_cohorts if cohort == "__UNMATCHED__"),
        }
    return result, class_result


def _comparison_interval_stats(
    artifact_dir: Path,
    observations: Mapping[tuple[str, str], Mapping],
    uncertainty: Mapping[tuple, Mapping],
    stratum_rows: Mapping[tuple, Mapping],
) -> dict[tuple, dict]:
    """Join each supported comparison to its observed C0/C2 class and cohort.

    Sets are used per cell/class/query identity.  This both protects the
    request-weighted denominator from duplicate lines and makes duplicate
    source rows visible through ``comparison_count``.
    """
    aggregate: dict[tuple, dict] = defaultdict(_empty_acc)
    for row in _optional_jsonl(artifact_dir / "comparisons.jsonl"):
        cell = _cell(row)
        identity = _identity(row)
        identity_text = f"{identity[0]}:{identity[1]}"
        median = _number(row.get("median_ms"))
        if median is None or median <= 0:
            strata = (("ALL", "ALL"),)
            for key in ((cell, "ALL", "ALL"),):
                aggregate[key]["zero_or_missing_ids"].add(identity_text)
                aggregate[key]["comparison_ids"].add(identity_text)
            continue
        summary = uncertainty.get((cell, str(row.get("cohort_key", ""))))
        uncertainty_summary = summary.get("summary", {}).get("reference_uncertainty", {}) if isinstance(summary, Mapping) else {}
        usable = int(uncertainty_summary.get("usable_replicates", 0) or 0)
        width = _number(uncertainty_summary.get("full_width_ms"))
        passes = bool(width is not None and width <= 0.4 * median)
        assessed = usable >= MIN_USABLE_BOOTSTRAPS
        strata = (("ALL", "ALL"),) + _strata(observations.get(identity, {}))
        for kind, stratum_key in strata:
            key = (cell, kind, stratum_key)
            current = aggregate[key]
            current["comparison_ids"].add(identity_text)
            current["positive_ids"].add(identity_text)
            if assessed and passes:
                current["pass_ids"].add(identity_text)
            elif not assessed:
                current["inconclusive_ids"].add(identity_text)
    return aggregate


def _uncertainty_metrics(rows: Iterable[dict]) -> dict[tuple, dict]:
    result: dict[tuple, dict] = defaultdict(lambda: {
        "cohort_count": 0, "positive_median_cohort_count": 0, "zero_median_cohort_count": 0,
        "assessed_cohort_count": 0, "inconclusive_cohort_count": 0,
        "support_50_supported_cohort_count": 0, "support_100_supported_cohort_count": 0,
        "temporal_half_change": [], "lomo_center_count": 0,
    })
    for row in rows:
        key = (str(row.get("mode", "")), str(row.get("replica_policy", "")), int(row.get("lookback_minutes", -1)))
        item = result[key]
        item["cohort_count"] += 1
        summary = row.get("summary", {})
        stats = summary.get("reference_statistics", {}) if isinstance(summary, Mapping) else {}
        median = _number(stats.get("median_ms"))
        if median is not None and median > 0:
            item["positive_median_cohort_count"] += 1
        else:
            item["zero_median_cohort_count"] += 1
        unc = summary.get("reference_uncertainty", {}) if isinstance(summary, Mapping) else {}
        if int(unc.get("usable_replicates", 0) or 0) >= MIN_USABLE_BOOTSTRAPS:
            item["assessed_cohort_count"] += 1
        else:
            item["inconclusive_cohort_count"] += 1
        sensitivity = summary.get("reference_support_sensitivity", {}) if isinstance(summary, Mapping) else {}
        for minimum, field in (("50", "support_50_supported_cohort_count"), ("100", "support_100_supported_cohort_count")):
            if isinstance(sensitivity.get(minimum), Mapping) and sensitivity[minimum].get("supported"):
                item[field] += 1
        change = _number(stats.get("half_change_ms"))
        if change is not None:
            item["temporal_half_change"].append(change)
        lomo = stats.get("leave_one_minute_out", [])
        if isinstance(lomo, list):
            item["lomo_center_count"] += sum(1 for value in lomo if isinstance(value, Mapping) and _number(value.get("center_ms")) is not None)
    for item in result.values():
        changes = item.pop("temporal_half_change")
        item["median_temporal_half_change_ms"] = statistics.median(changes) if changes else None
    return result


def _independent_summary(independent: Mapping, mode: str, lookback: int) -> dict:
    paired = independent.get("paired_sensitivities", {}) if isinstance(independent, Mapping) else {}
    rows = [
        row for row in paired.get("same_vs_pooled_per_query", [])
        if str(row.get("mode", "")) == mode and int(row.get("lookback_minutes", -1)) == lookback
    ] if isinstance(paired, Mapping) else []
    common = [int(row.get("common_supported_count", 0) or 0) for row in rows]
    overlap = [_number(row.get("same_vs_pooled_common_supported_overlap")) for row in rows]
    jaccard = [_number(row.get("same_vs_pooled_common_supported_top5_jaccard")) for row in rows]
    changes = [_number(row.get("median_signed_center_change_ms")) for row in rows]
    return {
        "pair_anchor_count": len(rows),
        "median_common_supported_count": statistics.median(common) if common else None,
        "median_common_top5_overlap": statistics.median(value for value in overlap if value is not None) if any(value is not None for value in overlap) else None,
        "median_common_top5_jaccard": statistics.median(value for value in jaccard if value is not None) if any(value is not None for value in jaccard) else None,
        "median_signed_center_change_ms": statistics.median(value for value in changes if value is not None) if any(value is not None for value in changes) else None,
    }


def _apply_class_selection(rows: list[dict]) -> None:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        if row.get("stratum_kind") in {"C0", "C2"}:
            groups[(row["mode"], row["stratum_kind"], row["stratum_key"])].append(row)
    for group_rows in groups.values():
        passing = [row for row in group_rows if row.get("gate_2_coverage") and row.get("gate_3_interval_pass")]
        if not passing:
            continue
        minimum = min(int(row["lookback_minutes"]) for row in passing)
        at_minimum = [row for row in passing if int(row["lookback_minutes"]) == minimum]
        same = [row for row in at_minimum if row.get("replica_policy") == "same_replica"]
        selected = same or at_minimum
        for row in selected:
            row["shortest_passing_for_class"] = True
            row["class_tie_preference"] = "same_replica" if same else "no_same_replica_candidate_at_minimum"
        for row in group_rows:
            row.setdefault("shortest_passing_for_class", False)
            row.setdefault("class_tie_preference", "same_replica_then_pooled")


def _unavailable_reason(row: Mapping, gate3: bool, inconclusive: bool) -> str:
    reasons = []
    if int(row.get("missing_anchor_count", ANCHOR_COUNT) or 0) > MAX_MISSING_ANCHORS:
        reasons.append("missing_anchor_count_exceeds_2")
    if int(row.get("anchors_at_least_80pct", 0) or 0) < ANCHOR_COUNT - MAX_MISSING_ANCHORS:
        reasons.append("fewer_than_10_anchors_at_80pct")
    coverage = _number(row.get("request_coverage"))
    if coverage is None or coverage < 0.9:
        reasons.append("request_coverage_below_0.90")
    if inconclusive:
        reasons.append("bootstrap_inconclusive_or_no_positive_median")
    elif not gate3:
        reasons.append("interval_width_gate_below_0.80")
    return ";".join(reasons)


def _row_for_policy(
    base: Mapping,
    gate: tuple[bool, bool, int, int, int],
    uncertainty: Mapping,
    independent: Mapping,
    *,
    stratum_kind: str = "ALL",
    stratum_key: str = "ALL",
    class_data: Mapping | None = None,
    cohort_data: Mapping | None = None,
) -> dict:
    gate3, inconclusive_only, positive, passing, inconclusive = gate
    row = dict(base)
    row.update({
        "stratum_kind": stratum_kind, "stratum_key": stratum_key,
        "observed_class_query_count": "", "supported_observed_class_query_count": "",
        "all_observed_cohort_count": "", "supported_observed_cohort_count": "",
        "observed_cohort_coverage": "", "unmatched_observed_cohort_count": "",
        "rare_class": False,
        "metrics_scope": "whole_policy" if stratum_kind == "ALL" else "class_scope_only",
        "supported_statistic": SUPPORTED_STATISTIC,
        "qualifications": json.dumps(list(base.get("qualifications", [])), sort_keys=True),
        "unavailable_reason": "",
        "class_request_coverage": "",
        "gate_3_interval_pass": gate3,
        "gate_3_inconclusive": inconclusive_only or inconclusive > 0,
        "positive_median_query_count": positive,
        "interval_pass_query_count": passing,
        "interval_inconclusive_query_count": inconclusive,
        "gate_1_contract_checks": "pending_external_control_checks",
        "selection_status": "parent_decision_required",
        "status": "preliminary_coverage_uncertainty_pass" if base.get("gate_2_coverage") and gate3 else "unavailable_or_qualified",
    })
    if class_data:
        row.update({
            "observed_class_query_count": class_data.get("observed_class_query_count", 0),
            "supported_observed_class_query_count": class_data.get("supported_query_count", 0),
            "rare_class": bool(class_data.get("rare_class", False)),
            "class_request_coverage": class_data.get("class_request_coverage", 0.0),
            "resolved_query_count": class_data.get("resolved_query_count", 0),
            "supported_query_count": class_data.get("supported_query_count", 0),
            "request_coverage": class_data.get("request_coverage", 0.0),
            "anchor_count": class_data.get("anchor_count", 0),
            "missing_anchor_count": class_data.get("missing_anchor_count", ANCHOR_COUNT),
            "anchors_at_least_80pct": class_data.get("anchors_at_least_80pct", 0),
            "gate_2_coverage": class_data.get("gate_2_coverage", False),
        })
        if cohort_data:
            row.update({
                "all_observed_cohort_count": cohort_data.get("all_observed_cohort_count", 0),
                "supported_observed_cohort_count": cohort_data.get("supported_observed_cohort_count", 0),
                "observed_cohort_coverage": cohort_data.get("observed_cohort_coverage", 0.0),
                "unmatched_observed_cohort_count": cohort_data.get("unmatched_observed_cohort_count", 0),
            })
        row["status"] = "preliminary_coverage_uncertainty_pass" if row["gate_2_coverage"] and gate3 else "unavailable_or_qualified"
        class_qualifications = set(str(value) for value in (base.get("qualifications") or []))
        class_qualifications.update(("class_scope_only", "parent_decision_required"))
        row["qualifications"] = json.dumps(sorted(class_qualifications), sort_keys=True)
        # These metrics are whole-policy diagnostics.  Copying them into a
        # class row would imply a class-specific boundary/temporal result that
        # the artifact does not contain.
        for field in (
            "boundary_excluded_count", "boundary_fraction", "unknown_structure_count",
            "unavailable_duration_count", "zero_median_cohort_count", "reference_cohort_count",
            "positive_median_cohort_count", "assessed_cohort_count", "inconclusive_cohort_count",
            "support_50_supported_cohort_count", "support_100_supported_cohort_count",
            "median_temporal_half_change_ms", "lomo_center_count", "aging_slice_count",
            "aging_slices_at_least_80pct", "aging_supported_query_count", "pooling_pair_anchor_count",
            "pooling_median_common_supported_count", "pooling_median_common_top5_overlap",
            "pooling_median_common_top5_jaccard", "pooling_median_signed_center_change_ms",
        ):
            row[field] = None
    pair = _independent_summary(independent, str(row.get("mode", "")), int(row.get("lookback_minutes", -1)))
    row.update({
        "pooling_pair_anchor_count": pair["pair_anchor_count"],
        "pooling_median_common_supported_count": pair["median_common_supported_count"],
        "pooling_median_common_top5_overlap": pair["median_common_top5_overlap"],
        "pooling_median_common_top5_jaccard": pair["median_common_top5_jaccard"],
        "pooling_median_signed_center_change_ms": pair["median_signed_center_change_ms"],
    })
    row.update({
        "reference_cohort_count": uncertainty.get("cohort_count", 0),
        "positive_median_cohort_count": uncertainty.get("positive_median_cohort_count", 0),
        "zero_median_cohort_count": uncertainty.get("zero_median_cohort_count", 0),
        "assessed_cohort_count": uncertainty.get("assessed_cohort_count", 0),
        "inconclusive_cohort_count": uncertainty.get("inconclusive_cohort_count", 0),
        "support_50_supported_cohort_count": uncertainty.get("support_50_supported_cohort_count", 0),
        "support_100_supported_cohort_count": uncertainty.get("support_100_supported_cohort_count", 0),
        "median_temporal_half_change_ms": uncertainty.get("median_temporal_half_change_ms"),
        "lomo_center_count": uncertainty.get("lomo_center_count", 0),
    })
    if class_data:
        # See the qualification above: whole-policy diagnostics stay null for
        # a C0/C2 scope row even though the shared helper assembled the row.
        for field in (
            "boundary_excluded_count", "boundary_fraction", "unknown_structure_count",
            "unavailable_duration_count", "zero_median_cohort_count", "reference_cohort_count",
            "positive_median_cohort_count", "assessed_cohort_count", "inconclusive_cohort_count",
            "support_50_supported_cohort_count", "support_100_supported_cohort_count",
            "median_temporal_half_change_ms", "lomo_center_count", "aging_slice_count",
            "aging_slices_at_least_80pct", "aging_supported_query_count", "pooling_pair_anchor_count",
            "pooling_median_common_supported_count", "pooling_median_common_top5_overlap",
            "pooling_median_common_top5_jaccard", "pooling_median_signed_center_change_ms",
        ):
            row[field] = None
    if cohort_data:
        row.update(cohort_data)
    row["unavailable_reason"] = _unavailable_reason(row, gate3, bool(row.get("gate_3_inconclusive")))
    return row


CSV_FIELDS = [
    "stratum_kind", "stratum_key", "mode", "replica_policy", "lookback_minutes",
    "status", "selection_status", "anchor_count", "missing_anchor_count", "anchors_at_least_80pct",
    "resolved_query_count", "supported_query_count", "request_coverage",
    "observed_class_query_count", "supported_observed_class_query_count", "class_request_coverage",
    "all_observed_cohort_count", "supported_observed_cohort_count", "observed_cohort_coverage",
    "unmatched_observed_cohort_count", "rare_class", "metrics_scope",
    "gate_2_coverage", "gate_3_interval_pass", "gate_3_inconclusive",
    "positive_median_query_count", "interval_pass_query_count", "interval_inconclusive_query_count",
    "boundary_excluded_count", "boundary_fraction", "unknown_structure_count", "unavailable_duration_count",
    "zero_median_cohort_count", "reference_cohort_count", "assessed_cohort_count", "inconclusive_cohort_count",
    "support_50_supported_cohort_count", "support_100_supported_cohort_count", "median_temporal_half_change_ms", "lomo_center_count",
    "aging_slice_count", "aging_slices_at_least_80pct", "aging_supported_query_count",
    "pooling_pair_anchor_count", "pooling_median_common_supported_count", "pooling_median_common_top5_overlap",
    "pooling_median_common_top5_jaccard", "pooling_median_signed_center_change_ms",
    "shortest_passing_for_class", "class_tie_preference", "gate_1_contract_checks",
    "supported_statistic", "qualifications", "unavailable_reason",
]


def _write_csv(path: Path, rows: Iterable[Mapping]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def _final_selection_state(artifact_dir: Path) -> tuple[bool, dict]:
    """Read the frozen selection and completed controls, if both are present."""
    selection_path = artifact_dir / "selection.json"
    attempt_path = artifact_dir / "controls" / "attempt-3-summary.json"
    real_path = artifact_dir / "controls" / "real-controls-result.json"
    if not selection_path.is_file() or not attempt_path.is_file() or not real_path.is_file():
        return False, {}
    selection = _read_json(selection_path)
    attempt = _read_json(attempt_path)
    real = _read_json(real_path)
    real_controls = real.get("controls", {})
    controls_pass = bool(attempt.get("all_checks_pass") and real_controls.get("all_checks_pass") and not attempt.get("failed_checks") and not real_controls.get("failed_checks"))
    primary = selection.get("primary") if isinstance(selection.get("primary"), Mapping) else {}
    frozen = str(selection.get("selection_status", "")) == "frozen" and bool(primary)
    return bool(frozen and controls_pass), {
        "selection": selection,
        "controls_pass": controls_pass,
        "primary": dict(primary),
    }


def _apply_final_selection_state(rows: list[dict], artifact_dir: Path) -> bool:
    finalized, state = _final_selection_state(artifact_dir)
    if not finalized:
        return False
    primary = state["primary"]
    for row in rows:
        row["gate_1_contract_checks"] = "passed"
        if row.get("stratum_kind") in {"C0", "C2"}:
            row["selection_status"] = "reviewed_scope_map"
            continue
        same_primary = (
            str(row.get("mode")) == str(primary.get("mode"))
            and str(row.get("replica_policy")) == str(primary.get("replica_policy"))
            and int(row.get("lookback_minutes", -1)) == int(primary.get("lookback_minutes", -2))
        )
        passed = bool(row.get("gate_2_coverage") and row.get("gate_3_interval_pass"))
        if same_primary and passed:
            row["selection_status"] = "selected_qualified"
            row["status"] = "selected_qualified"
        elif passed:
            row["selection_status"] = "reviewed_alternative"
            row["status"] = "reviewed_alternative"
        else:
            row["selection_status"] = "reviewed_unavailable"
            row["status"] = "reviewed_unavailable"
    return True


def _report_markdown(rows: list[dict], independent: Mapping, artifact_dir: Path, stratum_count: int, finalized: bool = False) -> str:
    policies = [row for row in rows if row.get("stratum_kind") == "ALL"]
    class_rows = [row for row in rows if row.get("stratum_kind") in {"C0", "C2"}]
    passed = sum(1 for row in policies if row.get("gate_2_coverage") and row.get("gate_3_interval_pass"))
    class_passed = sum(1 for row in class_rows if row.get("shortest_passing_for_class"))
    rare_classes = sum(1 for row in class_rows if row.get("rare_class"))
    boundary_cells = sum(int(row.get("boundary_excluded_count", 0) or 0) for row in policies)
    aging_slices = sum(int(row.get("aging_slice_count", 0) or 0) for row in policies)
    support50 = sum(int(row.get("support_50_supported_cohort_count", 0) or 0) for row in policies)
    support100 = sum(int(row.get("support_100_supported_cohort_count", 0) or 0) for row in policies)
    cohort_coverages = [_number(row.get("observed_cohort_coverage")) for row in policies]
    median_cohort_coverage = statistics.median(value for value in cohort_coverages if value is not None) if any(value is not None for value in cohort_coverages) else None
    context_lines = []
    for mode in MODES:
        subset = [row for row in policies if row.get("mode") == mode]
        if not subset:
            continue
        median_coverage = statistics.median(float(row.get("request_coverage", 0.0) or 0.0) for row in subset)
        context_lines.append(f"| {mode} | {len(subset)} | {sum(bool(row.get('gate_2_coverage')) for row in subset)} | {sum(bool(row.get('gate_3_interval_pass')) for row in subset)} | {median_coverage:.4f} |")
    independent_available = bool(independent)
    reconciliation = independent.get("artifact_reconciliation", {}) if isinstance(independent, Mapping) else {}
    exposure = independent.get("exposure_inventory", {}) if isinstance(independent, Mapping) else {}
    return f"""# Short-window baselining v1 reporting

This report is generated from `{artifact_dir}`. It is a descriptive review of
the frozen matrix and has no access to benchmark labels, answer keys, or
scoring fields. A final primary/fallback policy is intentionally **not** chosen
here; parent review owns that decision after the independent checks.

## Matrix and gates

- Policy rows: **{len(policies)}**; complete policy rows passing Gates 2 and 3: **{passed}**.
- C0/C2 class rows: **{stratum_count}**; class rows with a shortest passing policy: **{class_passed}**.
- Rare class rows (fewer than {RARE_CLASS_QUERY_THRESHOLD} observed requests): **{rare_classes}**.
- The anchor denominator is fixed at **12**. Missing anchors count as failed
  anchors; the coverage gate requires at least 10 of 12 anchors at 80% request
  coverage and aggregate coverage of at least 90%.
- Gate 3 is request-weighted over comparisons whose reference median is
  positive. It requires at least 190 usable bootstrap replicates, width no more
  than 40% of the reference median, and at least 80% passing comparisons.
  Cells with unavailable bootstrap evidence remain inconclusive.

## Context tradeoff

The table is descriptive and leaves context choice to parent review.

| Context | Policy rows | Gate 2 rows | Gate 3 rows | Median request coverage |
|---|---:|---:|---:|---:|
{chr(10).join(context_lines) if context_lines else '| (no rows) | 0 | 0 | 0 | n/a |'}

The C0/C2 rows in `decision-table.csv` report class coverage as supported
observed requests divided by all observed requests, alongside resolved-request
coverage. Their observed-cohort fields count `(anchor, cohort)` incidences;
they are separate from request coverage. For each `(mode, class)` the shortest
passing lookback is marked and same-replica wins only when it ties pooled at
that lookback. These marks are scope guidance, not a global selection.

## Independent sensitivity and audit inputs

- Independent analysis available: **{independent_available}**.
- Coverage/source reconciliation: **{reconciliation.get('all_coverage_cells_present_once', 'unavailable')}**.
- Distinct supplied query windows: **{exposure.get('distinct_query_windows', 'unavailable')}**; expected 57.
- Boundary, 50/100 support sensitivity, temporal halves, leave-one-minute-out
  centers, six aging slices, and same-versus-pooled overlap are carried into
  the policy rows. Pooling values come from `independent-analysis.json` and
  are not recomputed on a different population here.
- Across policy cells, boundary exclusions total **{boundary_cells}**, the
  six-slice aging rows total **{aging_slices}**, and supported-cohort counts
  under minimum support 50 and 100 are **{support50}** and **{support100}**.
- The median policy-level supported/all-observed-cohort coverage is
  **{median_cohort_coverage if median_cohort_coverage is not None else 'unavailable'}**.

## Files

- `decision-table.csv`: complete ALL, C0, and C2 policy scope rows.
- `report.md`: this review narrative.
- `independent-analysis.json`: paired overlap, exposure, and reconciliation
  inputs when available.

The generated matrix report is an intermediate deliverable; the parent owns
the authoritative `final-report.md`. {"The frozen primary is marked selected_qualified after the completed controls; alternatives and class scope rows remain explicitly qualified." if finalized else "Rows remain parent_decision_required until the frozen selection and completed controls are available."}
"""


def generate_report(artifact_dir: Path, output_dir: Path | None = None, independent_path: Path | None = None) -> dict:
    """Generate ``decision-table.csv`` and ``report.md`` from matrix artifacts."""
    artifact_dir = Path(artifact_dir)
    output_dir = Path(output_dir or artifact_dir)
    manifest = _read_json(artifact_dir / "manifest.json") if (artifact_dir / "manifest.json").is_file() else {}
    independent_path = Path(independent_path or artifact_dir / "independent-analysis.json")
    independent = _read_json(independent_path) if independent_path.is_file() else {}

    # Retain only the fields needed for the C0/C2 join.  The raw observations
    # table is source-linked and can exceed a gigabyte; keeping direct-child
    # arrays here would needlessly duplicate that footprint.
    observations = {}
    for row in _optional_jsonl(artifact_dir / "observations.jsonl"):
        observations[_identity(row)] = {
            "signature": row.get("signature", {}),
            "cmdb_id": row.get("cmdb_id"),
        }
    coverage = list(_optional_jsonl(artifact_dir / "coverage.jsonl"))
    uncertainty_rows = list(_optional_jsonl(artifact_dir / "uncertainty.jsonl"))
    uncertainty = {
        (_cell(row), str(row.get("cohort_key", ""))): row
        for row in uncertainty_rows
    }
    base = _coverage_summary(coverage)
    stratum_rows = _load_stratum_rows(independent)
    class_base = _class_coverage_summary(stratum_rows)
    cohort_base, class_cohort_base = _cohort_coverage(artifact_dir, observations)
    interval = _comparison_interval_stats(artifact_dir, observations, uncertainty, stratum_rows)
    uncertainty_summary = _uncertainty_metrics(uncertainty_rows)

    rows: list[dict] = []
    for key, summary in sorted(base.items()):
        interval_acc = interval.get(("__policy__",), {})
        # The actual key is the cell-independent policy tuple.  Aggregate ALL
        # interval sets below instead of using the per-stratum map directly.
        all_acc = _empty_acc()
        for (cell, kind, _), acc in interval.items():
            if kind != "ALL":
                continue
            if (cell[2], cell[3], cell[1]) != key:
                continue
            for field in all_acc:
                all_acc[field].update(acc[field])
        rows.append(_row_for_policy(summary, _gate3(all_acc), uncertainty_summary.get(key, {}), independent, cohort_data=cohort_base.get(key, {})))

    for key, summary in sorted(class_base.items()):
        mode, replica, lookback, kind, stratum_key = key
        all_acc = _empty_acc()
        for (cell, interval_kind, interval_key), acc in interval.items():
            if interval_kind != kind or interval_key != stratum_key:
                continue
            if (cell[2], cell[3], cell[1]) != (mode, replica, lookback):
                continue
            for field in all_acc:
                all_acc[field].update(acc[field])
        row = _row_for_policy(
            base.get((mode, replica, lookback), {
                "mode": mode, "replica_policy": replica, "lookback_minutes": lookback,
                "anchor_count": 0, "missing_anchor_count": ANCHOR_COUNT, "resolved_query_count": 0,
                "supported_query_count": 0, "request_coverage": 0.0, "gate_2_coverage": False,
                "boundary_excluded_count": 0, "boundary_fraction": None, "unknown_structure_count": 0,
                "unavailable_duration_count": 0, "zero_median_cohort_count": 0, "aging_slice_count": 0,
                "aging_slices_at_least_80pct": 0, "aging_supported_query_count": 0,
            }),
            _gate3(all_acc), uncertainty_summary.get((mode, replica, lookback), {}), independent,
            stratum_kind=kind, stratum_key=stratum_key, class_data=summary,
            cohort_data=class_cohort_base.get((mode, replica, lookback, kind, stratum_key), {}),
        )
        rows.append(row)
    _apply_class_selection(rows)
    for row in rows:
        row.setdefault("shortest_passing_for_class", False)
        row.setdefault("class_tie_preference", "same_replica_then_pooled")

    finalized = _apply_final_selection_state(rows, artifact_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    decision_path = output_dir / "decision-table.csv"
    report_path = output_dir / "report.md"
    _write_csv(decision_path, rows)
    report_path.write_text(_report_markdown(rows, independent, artifact_dir, len(rows) - len(base), finalized) + "\n", encoding="utf-8")
    summary = {
        "report_version": "short-window-baselining-v1/reporting-1",
        "artifact_dir": str(artifact_dir), "manifest_status": manifest.get("status"),
        "decision_table": str(decision_path), "report": str(report_path),
        "policy_row_count": len(base), "class_row_count": len(rows) - len(base),
        "selection_status": "selected_qualified" if finalized else "parent_decision_required",
        "final_selection_state_applied": finalized,
        "independent_analysis_available": bool(independent),
    }
    (output_dir / "reporting-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--independent-analysis", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(generate_report(args.artifact_dir, args.output_dir, args.independent_analysis), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
