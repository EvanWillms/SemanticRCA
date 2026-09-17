"""Controlled interventions for the short-window contract checks.

The checks operate on copied observation mappings.  Every transformed row
retains a source pointer to its original row, and every operation emits a
manifest entry describing the intervention.  These fixtures exercise the
selector/comparator contracts; they are not telemetry evidence or health
certificates.
"""

from __future__ import annotations

import copy
import json
import math
import random
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .contracts import compare_duration, signature_for_root, signature_key, stable_membership_hash, support_diagnostics


CONTROL_CHECK_VERSION = "short-window-baselining-v1/controls-1"
_DURATION_RE = re.compile(r"(?:query_duration_plus_|thin_references_)(\d+)")


def _identity(row: Mapping) -> tuple[str, str]:
    return (str(row.get("trace_id", "")), str(row.get("span_id", "")))


def _source_pointer(row: Mapping) -> dict:
    source = row.get("source") if isinstance(row.get("source"), Mapping) else row
    return {
        "trace_id": str(row.get("trace_id", "")),
        "span_id": str(row.get("span_id", "")),
        "source_file": str(source.get("source_file", row.get("source_file", ""))),
        "source_record": int(source.get("source_record", row.get("source_record", 0)) or 0),
        "source_header": int(source.get("source_header", row.get("source_header", 1)) or 1),
    }


def _role(row: Mapping) -> str:
    return str(row.get("role", row.get("cohort_role", ""))).lower()


def _duration(row: Mapping) -> float | None:
    value = row.get("duration_ms", row.get("observed_ms", row.get("duration")))
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _children(row: Mapping) -> tuple[str, list]:
    if "direct_children" in row:
        return "direct_children", list(row.get("direct_children") or [])
    return "children", list(row.get("children") or [])


def _refresh_signature(row: dict) -> None:
    """Refresh cached C0/C1/C2 fields after a structural intervention."""
    row["signature"] = {
        mode: signature_for_root(row, mode)
        for mode in ("C0", "C1", "C2")
    }


def _clone_records(records: Iterable[Mapping]) -> tuple[list[dict], list[dict]]:
    copied: list[dict] = []
    source_links: list[dict] = []
    for row in records:
        original = copy.deepcopy(dict(row))
        transformed = copy.deepcopy(original)
        transformed["control_source"] = _source_pointer(original)
        transformed["control_original_identity"] = list(_identity(original))
        copied.append(transformed)
        source_links.append({"transformed_identity": list(_identity(transformed)), "original": _source_pointer(original)})
    return copied, source_links


def _selected_indices(rows: Sequence[Mapping], role: str) -> list[int]:
    return [index for index, row in enumerate(rows) if _role(row) == role]


def _duration_shift(rows: list[dict], indices: Iterable[int], factor: float) -> list[dict]:
    changed = []
    for index in indices:
        before = _duration(rows[index])
        if before is None:
            continue
        after = before * factor
        rows[index]["duration_ms"] = after
        rows[index]["control_duration_before_ms"] = before
        rows[index]["control_duration_delta_ms"] = after - before
        changed.append({"index": index, "identity": list(_identity(rows[index])), "before_ms": before, "after_ms": after, "delta_ms": after - before})
    return changed


def apply_intervention(
    records: Iterable[Mapping],
    name: str,
    *,
    seed: int | None = 42,
    fraction: float | None = None,
    target_count: int | None = None,
    factor: float = 2.0,
    target_replica: str | None = None,
) -> dict:
    """Apply one declared intervention to copied observations.

    The returned ``records`` preserve the input cardinality except for
    ``thin_references`` (which intentionally removes only reference rows).
    Query rows remain visible for thinning, and all rows carry
    ``control_source``/``control_original_identity`` pointers.
    """
    records = list(records)
    rows, source_links = _clone_records(records)
    original_hash = stable_membership_hash(rows)
    event: dict = {"version": CONTROL_CHECK_VERSION, "name": str(name), "seed": seed, "fraction": fraction, "target_count": target_count, "factor": factor}
    changed: list[dict] = []

    if name == "reorder_and_rename_ids":
        trace_map: dict[str, str] = {}
        span_map: dict[tuple[str, str], str] = {}
        for index, row in enumerate(rows):
            old_trace, old_span = _identity(row)
            trace_map.setdefault(old_trace, f"control-trace-{len(trace_map) + 1:04d}")
            span_map[(old_trace, old_span)] = f"control-span-{index + 1:06d}"
        # Children may be embedded in a root row instead of appearing as
        # separate observations.  Give those identities the same reversible
        # mapping before mutating any parent or child fields.
        next_span = len(span_map) + 1
        for row in rows:
            old_trace, _ = _identity(row)
            for child in row.get("direct_children", row.get("children", [])) or []:
                if not isinstance(child, dict):
                    continue
                child_trace = str(child.get("trace_id", old_trace))
                if child_trace not in trace_map:
                    trace_map[child_trace] = f"control-trace-{len(trace_map) + 1:04d}"
                child_span = str(child.get("span_id", ""))
                if child_span:
                    span_map.setdefault((child_trace, child_span), f"control-span-{next_span:06d}")
                    next_span += 1
        for row in rows:
            old_trace, old_span = _identity(row)
            row["trace_id"] = trace_map[old_trace]
            row["span_id"] = span_map[(old_trace, old_span)]
            parent = str(row.get("parent_span", ""))
            row["parent_span"] = span_map.get((old_trace, parent), parent) if parent else ""
            if isinstance(row.get("root_key"), (list, tuple)) and len(row["root_key"]) == 2:
                row["root_key"] = [trace_map.get(str(row["root_key"][0]), str(row["root_key"][0])), span_map.get((old_trace, str(row["root_key"][1])), str(row["root_key"][1]))]
            for child in row.get("direct_children", row.get("children", [])) or []:
                if not isinstance(child, dict):
                    continue
                child_trace = str(child.get("trace_id", old_trace))
                child_span = str(child.get("span_id", ""))
                if child_span and (child_trace, child_span) in span_map:
                    child["trace_id"] = trace_map[child_trace]
                    child["span_id"] = span_map[(child_trace, child_span)]
                child_parent = str(child.get("parent_span", ""))
                if child_parent:
                    child["parent_span"] = span_map.get((child_trace, child_parent), child_parent)
        rows.reverse()
        event["trace_id_map"] = trace_map
        event["span_id_map"] = {f"{trace}:{span}": value for (trace, span), value in span_map.items()}
        event["inverse_id_mapping_required"] = True
        changed = [{"kind": "identity", "count": len(rows)}]

    elif name.startswith("query_duration_plus_"):
        match = re.search(r"(25|50|100)", name)
        if not match:
            raise ValueError(f"duration intervention must name 25, 50, or 100 percent: {name}")
        percent = int(match.group(1))
        changed = _duration_shift(rows, _selected_indices(rows, "query"), 1.0 + percent / 100.0)
        event["percent"] = percent

    elif name in {"add_direct_child", "add_novel_direct_child", "remove_direct_child", "change_child_multiplicity_only"}:
        selected = _selected_indices(rows, "query") or list(range(len(rows)))
        for index in selected:
            key, children = _children(rows[index])
            before = copy.deepcopy(children)
            if name in {"add_direct_child", "add_novel_direct_child"}:
                children.append({"operation_name": "control/NovelChild", "type": "synthetic", "control_added": True})
            elif name == "remove_direct_child":
                if children:
                    children.pop()
            elif children:
                children.append(copy.deepcopy(children[0]))
            rows[index][key] = children
            rows[index]["control_children_before"] = before
            rows[index]["control_children_after"] = copy.deepcopy(children)
            changed.append({"index": index, "identity": list(_identity(rows[index])), "before_count": len(before), "after_count": len(children)})

    elif name == "thin_references":
        ref_indices = _selected_indices(rows, "reference")
        if target_count is None:
            match = _DURATION_RE.search(name)
            target_count = int(match.group(1)) if match else len(ref_indices)
        target_count = max(0, int(target_count))
        if target_count >= len(ref_indices):
            chosen = set(ref_indices)
            event["insufficient_original_support"] = target_count > len(ref_indices)
        else:
            rng = random.Random(seed)
            chosen = set(rng.sample(ref_indices, target_count))
            event["insufficient_original_support"] = False
        rows = [row for index, row in enumerate(rows) if _role(row) != "reference" or index in chosen]
        changed = [{"kind": "reference_thinning", "before_count": len(ref_indices), "after_count": len(chosen), "retained_indices": sorted(chosen)}]
        event["target_count"] = target_count

    elif name == "concentrate_references_in_one_minute":
        ref_indices = _selected_indices(rows, "reference")
        stamps = [int(rows[index].get("start_ms", rows[index].get("timestamp_ms", 0))) for index in ref_indices]
        anchor = (min(stamps) // 60_000) * 60_000 if stamps else 0
        for index in ref_indices:
            row = rows[index]
            before = row.get("start_ms", row.get("timestamp_ms"))
            if "start_ms" in row:
                row["start_ms"] = anchor
            if "timestamp_ms" in row:
                row["timestamp_ms"] = anchor
            changed.append({"index": index, "identity": list(_identity(row)), "before_start_ms": before, "after_start_ms": anchor})
        event["target_minute_start_ms"] = anchor

    elif name in {"constant_reference_duration", "zero_reference_duration"}:
        value = 42.0 if name == "constant_reference_duration" else 0.0
        for index in _selected_indices(rows, "reference"):
            before = _duration(rows[index])
            rows[index]["duration_ms"] = value
            rows[index]["control_duration_before_ms"] = before
            changed.append({"index": index, "identity": list(_identity(rows[index])), "before_ms": before, "after_ms": value})
        event["value_ms"] = value

    elif name == "contaminate_reference":
        ref_indices = _selected_indices(rows, "reference")
        fraction = 0.0 if fraction is None else float(fraction)
        if not 0 <= fraction <= 1:
            raise ValueError("contamination fraction must be in [0,1]")
        count = min(len(ref_indices), int(len(ref_indices) * fraction))
        rng = random.Random(seed)
        selected = rng.sample(ref_indices, count)
        changed = _duration_shift(rows, selected, factor)
        event.update({"fraction": fraction, "selected_count": count, "health_certified": False})

    elif name in {"shift_one_replica_query", "shift_all_replica_query"}:
        query_indices = _selected_indices(rows, "query")
        replicas = sorted({str(rows[index].get("cmdb_id", rows[index].get("replica", ""))) for index in query_indices})
        if target_replica is None and replicas:
            target_replica = replicas[0]
        selected = [index for index in query_indices if name == "shift_all_replica_query" or str(rows[index].get("cmdb_id", rows[index].get("replica", ""))) == str(target_replica)]
        changed = _duration_shift(rows, selected, factor)
        event.update({"target_replica": target_replica, "replicas": replicas, "health_certified": False})

    elif name == "remove_children_mark_incomplete":
        for index, row in enumerate(rows):
            if "direct_children" in row:
                row["direct_children"] = None
            elif "children" in row:
                row["children"] = None
            row["structure_status"] = "unknown_structure"
            row["retrieval_unresolved"] = True
            changed.append({"index": index, "identity": list(_identity(row))})

    else:
        raise ValueError(f"unknown controlled intervention: {name}")

    for row in rows:
        _refresh_signature(row)
    # Rebuild links from each retained row.  Positional zipping would assign
    # the wrong provenance after reorder or reference thinning.
    source_links = [
        {"transformed_identity": list(_identity(row)), "original": copy.deepcopy(row.get("control_source", {}))}
        for row in rows
    ]
    event["changed"] = changed
    event["input_count"] = len(records)
    event["output_count"] = len(rows)
    event["input_membership_hash"] = original_hash
    event["output_membership_hash"] = stable_membership_hash(rows)
    event["source_links"] = source_links
    return {"records": rows, "manifest": event, "source_links": source_links}


def evaluate_records(
    records: Iterable[Mapping],
    *,
    mode: str = "C0",
    replica_policy: str | None = None,
    anchor_component: str | None = None,
    allowlist: list[str] | None = None,
    anchor_ms: int | None = None,
    lookback_minutes: int = 10,
    anchor: Mapping | None = None,
) -> dict:
    """Run the matrix runner's connected selector/comparator seam."""
    from .runner import evaluate_policy

    rows = [copy.deepcopy(dict(row)) for row in records]
    if not rows:
        return {"mode": mode, "replica_policy": replica_policy, "input_count": 0, "selected_count": 0, "reference_count": 0, "query_count": 0, "matched_query_count": 0, "unmatched_query_count": 0, "comparisons": [], "membership_hash": stable_membership_hash(rows)}
    for row in rows:
        row.setdefault("identity_resolved", True)
        row.setdefault("root_key", list(_identity(row)))
        row.setdefault("source", _source_pointer(row))
        if not isinstance(row.get("signature"), Mapping):
            row["signature"] = {item: signature_for_root(row, item) for item in ("C0", "C1", "C2")}
    records_by_identity = {_identity(row): row for row in rows}
    allowlist = list(allowlist or sorted({str(row.get("cmdb_id", "")) for row in rows if str(row.get("cmdb_id", ""))}))
    if anchor is None:
        query_stamps = [int(row.get("timestamp_ms", row.get("start_ms", 0))) for row in rows if _role(row) == "query"]
        anchor_ms = int(anchor_ms if anchor_ms is not None else min(query_stamps or [0]))
        anchor = {
            "anchor_id": f"synthetic-{anchor_ms}",
            "epoch_ms": anchor_ms,
            "reference_intervals": {str(minutes): [anchor_ms - minutes * 60_000, anchor_ms] for minutes in (5, 10, 15, 30, 60)},
            "query_slices": [[anchor_ms + offset * 60_000, anchor_ms + (offset + 5) * 60_000] for offset in (0, 5, 10, 15, 20, 25)],
        }
    policy = evaluate_policy(records_by_identity, anchor, lookback_minutes, mode, replica_policy or "pooled", allowlist)
    policy_row = policy["policy"]
    comparisons = list(policy.get("comparisons", []))
    return {
        "mode": mode,
        "replica_policy": replica_policy or "pooled",
        "input_count": len(rows),
        "selected_count": policy_row.get("reference_raw_count", 0) + policy_row.get("query_raw_count", 0),
        "reference_count": policy_row.get("reference_included_count", 0),
        "excluded_reference_count": sum(policy_row.get("reference_excluded_counts", {}).values()),
        "query_count": policy_row.get("query_raw_count", 0),
        "matched_query_count": len(comparisons),
        "unmatched_query_count": max(0, policy_row.get("query_resolved_count", 0) - len(comparisons)) + policy_row.get("query_unknown_identity_count", 0),
        "policy": policy_row,
        "memberships": policy.get("memberships", []),
        "uncertainty": policy.get("uncertainty", []),
        "comparisons": comparisons,
        "membership_hash": stable_membership_hash(rows),
    }


def load_expected_facts(path: Path | None = None) -> dict:
    path = path or Path(__file__).with_name("tests") / "expected_facts.json"
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _restore_renamed_ids(records: Iterable[Mapping], manifest: Mapping) -> list[dict]:
    inverse_traces = {str(new): str(old) for old, new in dict(manifest.get("trace_id_map", {})).items()}
    inverse_spans = {}
    for key, new in dict(manifest.get("span_id_map", {})).items():
        old_trace, old_span = str(key).split(":", 1)
        inverse_spans[(str(new), inverse_traces.get(str(manifest.get("trace_id_map", {}).get(old_trace, "")), old_trace))] = old_span
        inverse_spans[(str(new), "*")] = old_span
    restored = []
    for row in records:
        item = copy.deepcopy(dict(row))
        new_trace = str(item.get("trace_id", ""))
        new_span = str(item.get("span_id", ""))
        item["trace_id"] = inverse_traces.get(new_trace, new_trace)
        item["span_id"] = inverse_spans.get((new_span, new_trace), inverse_spans.get((new_span, "*"), new_span))
        parent = str(item.get("parent_span", ""))
        if parent:
            item["parent_span"] = inverse_spans.get((parent, new_trace), inverse_spans.get((parent, "*"), parent))
        if isinstance(item.get("root_key"), (list, tuple)) and len(item["root_key"]) == 2:
            restored_root_trace = inverse_traces.get(str(item["root_key"][0]), str(item["root_key"][0]))
            restored_root_span = inverse_spans.get((str(item["root_key"][1]), new_trace), inverse_spans.get((str(item["root_key"][1]), "*"), str(item["root_key"][1])))
            item["root_key"] = [restored_root_trace, restored_root_span]
        for child in item.get("direct_children", item.get("children", [])) or []:
            if not isinstance(child, dict):
                continue
            child_new_trace = str(child.get("trace_id", new_trace))
            child_new_span = str(child.get("span_id", ""))
            if child_new_trace:
                child["trace_id"] = inverse_traces.get(child_new_trace, child_new_trace)
            if child_new_span:
                child["span_id"] = inverse_spans.get((child_new_span, child_new_trace), inverse_spans.get((child_new_span, "*"), child_new_span))
            child_parent = str(child.get("parent_span", ""))
            if child_parent:
                child["parent_span"] = inverse_spans.get((child_parent, child_new_trace), inverse_spans.get((child_parent, "*"), child_parent))
            if isinstance(child.get("root_key"), (list, tuple)) and len(child["root_key"]) == 2:
                child["root_key"] = [inverse_traces.get(str(child["root_key"][0]), str(child["root_key"][0])), inverse_spans.get((str(child["root_key"][1]), child_new_trace), inverse_spans.get((str(child["root_key"][1]), "*"), str(child["root_key"][1])))]
        restored.append(item)
    return restored


def _query_ids(records: Iterable[Mapping]) -> set[tuple[str, str]]:
    return {_identity(row) for row in records if _role(row) == "query"}


def _reference_records(records: Iterable[Mapping]) -> list[dict]:
    return [dict(row) for row in records if _role(row) == "reference"]


def _independent_support(rows: Iterable[Mapping], *, mode: str, replica_policy: str, anchor: Mapping | None, lookback_minutes: int) -> dict[str, dict]:
    """Independent count/bin/concentration calculation for control validation."""
    rows = list(rows)
    if anchor is None:
        query_stamps = [int(row.get("timestamp_ms", row.get("start_ms", 0))) for row in rows if _role(row) == "query"]
        anchor_ms = min(query_stamps or [0])
    else:
        anchor_ms = int(anchor["epoch_ms"])
    begin = anchor_ms - int(lookback_minutes) * 60_000
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        if _role(row) != "reference" or not row.get("identity_resolved", True):
            continue
        timestamp = int(row.get("timestamp_ms", row.get("start_ms", -1)))
        endpoint = row.get("max_recorded_end_us")
        if timestamp < begin or timestamp >= anchor_ms or endpoint is None or int(endpoint) >= anchor_ms * 1000:
            continue
        if mode in {"C1", "C2"} and row.get("structure_status") == "unknown_structure":
            continue
        key = signature_key(signature_for_root(row, mode))
        if replica_policy == "same_replica":
            key = f"component={row.get('cmdb_id', '')}\x1f{key}"
        grouped.setdefault(key, []).append(dict(row))
    output = {}
    required = max(3, math.ceil(int(lookback_minutes) / 2))
    for key, values in grouped.items():
        bins = {}
        for row in values:
            minute = int(row.get("timestamp_ms", row.get("start_ms", 0))) // 60_000
            bins[minute] = bins.get(minute, 0) + 1
        n = len(values)
        largest = max(bins.values(), default=0)
        output[key] = {
            "n": n,
            "occupied_minutes": len(bins),
            "required_minutes": required,
            "largest_minute_count": largest,
            "supported": bool(n >= 20 and len(bins) >= required and largest <= n / 2 if n else False),
        }
    return output


def _control_pass(name: str, original: list[dict], transformed: list[dict], baseline: dict, evaluated: dict, manifest: Mapping, target: int | None, *, mode: str = "C0", replica_policy: str = "pooled", anchor: Mapping | None = None, allowlist: list[str] | None = None) -> tuple[bool, dict]:
    """Return an explicit pass/fail and evidence for one intervention cell."""
    details: dict = {"name": name, "target_count": target}
    expected_pass = True
    if name == "reorder_and_rename_ids":
        restored = _restore_renamed_ids(transformed, manifest)
        restored_eval = evaluate_records(restored, mode=mode, replica_policy=replica_policy, anchor=anchor, allowlist=allowlist)
        before_by_id = {_identity(row): row for row in baseline["comparisons"]}
        after_by_id = {_identity(row): row for row in restored_eval["comparisons"]}
        numeric_equal = all(
            key in after_by_id and all(after_by_id[key].get(field) == before.get(field) for field in ("observed_ms", "median_ms", "absolute_excess_ms", "ratio", "standardized_departure"))
            for key, before in before_by_id.items()
        ) and set(before_by_id) == set(after_by_id)
        expected_pass = restored_eval["membership_hash"] == baseline["membership_hash"] and restored_eval["matched_query_count"] == baseline["matched_query_count"] and numeric_equal
        details.update({"restored_membership_equal": restored_eval["membership_hash"] == baseline["membership_hash"], "restored_comparison_count_equal": restored_eval["matched_query_count"] == baseline["matched_query_count"], "restored_numeric_fields_equal": numeric_equal})
    elif name.startswith("query_duration_plus_"):
        percent = int(re.search(r"(25|50|100)", name).group(1))
        before = {(_identity(row)): row for row in baseline["comparisons"]}
        after = {(_identity(row)): row for row in evaluated["comparisons"]}
        before_ids = set(before)
        after_ids = set(after)
        matched_ids_unchanged = before_ids == after_ids
        deltas = [after[key].get("absolute_excess_ms") - before[key].get("absolute_excess_ms") for key in sorted(before_ids & after_ids)]
        expected_deltas = [float(before[key].get("observed_ms")) * percent / 100.0 for key in sorted(before_ids & after_ids) if before[key].get("observed_ms") is not None]
        expected_pass = matched_ids_unchanged and bool(deltas) and len(deltas) == len(expected_deltas) and all(abs(delta - expected) < 1e-9 for delta, expected in zip(deltas, expected_deltas))
        details.update({"matched_ids_unchanged": matched_ids_unchanged, "expected_excess_deltas_ms": expected_deltas, "excess_deltas_ms": deltas})
    elif name in {"add_direct_child", "add_novel_direct_child", "remove_direct_child", "change_child_multiplicity_only"}:
        original_queries = [row for row in original if _role(row) == "query"]
        transformed_queries = [row for row in transformed if _role(row) == "query"]
        c0_before = Counter(signature_key(signature_for_root(row, "C0")) for row in original_queries)
        c0_after = Counter(signature_key(signature_for_root(row, "C0")) for row in transformed_queries)
        c1_before = Counter(signature_key(signature_for_root(row, "C1")) for row in original_queries)
        c1_after = Counter(signature_key(signature_for_root(row, "C1")) for row in transformed_queries)
        c2_before = Counter(signature_key(signature_for_root(row, "C2")) for row in original_queries)
        c2_after = Counter(signature_key(signature_for_root(row, "C2")) for row in transformed_queries)
        c0_preserved = c0_before == c0_after
        c1_changed = c1_before != c1_after
        c2_changed = c2_before != c2_after
        if name == "change_child_multiplicity_only":
            shape_expectation = c1_before == c1_after and c2_changed
            shape_changed = c2_changed
        elif name == "remove_direct_child":
            # Removing one copy always changes C2.  C1 changes only when the
            # removed copy was the last member of its operation/type pair.
            shape_expectation = c2_changed
            shape_changed = c1_changed or c2_changed
        else:
            shape_expectation = c1_changed and c2_changed
            shape_changed = c1_changed or c2_changed
        expected_pass = c0_preserved and shape_expectation and len(transformed) == len(original)
        synthetic_fixture = all(str(row.get("source_file", "")) == "synthetic.csv" for row in original)
        if mode == "C1" and name == "change_child_multiplicity_only":
            before_matches = {_identity(row) for row in baseline["comparisons"]}
            after_matches = {_identity(row) for row in evaluated["comparisons"]}
            c1_match_preserved = before_matches == after_matches
            expected_pass = expected_pass and c1_match_preserved
        else:
            c1_match_preserved = None
        # The synthetic fixture deliberately creates a novel shape with no
        # eligible reference cohort.  Real telemetry can already contain the
        # changed shape, so retain its runner result as evidence rather than
        # imposing the fixture's zero-match expectation on it.
        exact_no_match_expected = synthetic_fixture and (
            mode == "C2" or (mode == "C1" and name != "change_child_multiplicity_only")
        )
        if exact_no_match_expected:
            expected_pass = expected_pass and evaluated["matched_query_count"] == 0
        details.update({"c0_preserved": c0_preserved, "c1_changed": c1_changed, "c2_changed": c2_changed, "shape_changed": shape_changed, "shape_expectation": shape_expectation, "input_output_count_equal": len(transformed) == len(original), "mode": mode, "c1_match_preserved": c1_match_preserved, "exact_no_match_expected": exact_no_match_expected, "unmatched_after_shape_intervention": evaluated["matched_query_count"] == 0 if mode in {"C1", "C2"} else None})
    elif name == "thin_references":
        refs = _reference_records(transformed)
        expected_count = min(target or len(refs), len(_reference_records(original)))
        support = _independent_support(transformed, mode=mode, replica_policy=replica_policy, anchor=anchor, lookback_minutes=10)
        runner_support = {row.get("cohort_key"): row.get("summary", {}).get("reference_support", {}).get("supported") for row in evaluated.get("uncertainty", [])}
        support_agreement = all(key in runner_support and bool(value.get("supported")) == bool(runner_support[key]) for key, value in support.items())
        expected_pass = len(refs) == expected_count and _query_ids(transformed) == _query_ids(original) and support_agreement
        details.update({"reference_count": len(refs), "expected_reference_count": expected_count, "independent_support": support, "runner_support": runner_support, "support_agreement": support_agreement, "query_membership_preserved": _query_ids(transformed) == _query_ids(original)})
    elif name == "concentrate_references_in_one_minute":
        support = support_diagnostics(_reference_records(transformed), 10)
        expected_pass = "minute_concentration" in support["failure_reasons"]
        details["support"] = support
    elif name == "constant_reference_duration":
        comparisons = list(evaluated["comparisons"])
        expected_pass = bool(comparisons) and all(row["mad_ms"] == 0 and row["ratio"] is not None and row["standardized_departure"] is None for row in comparisons)
    elif name == "zero_reference_duration":
        comparisons = list(evaluated["comparisons"])
        expected_pass = bool(comparisons) and all(row["median_ms"] == 0 and row["ratio"] is None and row["absolute_excess_ms"] is not None for row in comparisons)
    elif name == "contaminate_reference":
        original_median = baseline["comparisons"][0].get("median_ms") if baseline["comparisons"] else None
        contaminated_median = evaluated["comparisons"][0].get("median_ms") if evaluated["comparisons"] else None
        original_score = baseline["comparisons"][0].get("standardized_departure") if baseline["comparisons"] else None
        contaminated_score = evaluated["comparisons"][0].get("standardized_departure") if evaluated["comparisons"] else None
        paired = [(before, after) for before, after in zip(baseline["comparisons"], evaluated["comparisons"]) if before.get("trace_id") == after.get("trace_id") and before.get("span_id") == after.get("span_id")]
        positive_excess_reduced = sum(1 for before, after in paired if before.get("absolute_excess_ms") is not None and after.get("absolute_excess_ms") is not None and before["absolute_excess_ms"] > 0 and after["absolute_excess_ms"] < before["absolute_excess_ms"])
        standardized_departure_reduced = sum(1 for before, after in paired if before.get("standardized_departure") is not None and after.get("standardized_departure") is not None and after["standardized_departure"] < before["standardized_departure"])
        expected_pass = bool(manifest.get("changed")) and manifest.get("health_certified") is False
        details.update({
            "baseline_median_ms": original_median,
            "contaminated_median_ms": contaminated_median,
            "center_delta_ms": (contaminated_median - original_median) if original_median is not None and contaminated_median is not None else None,
            "baseline_standardized_departure": original_score,
            "contaminated_standardized_departure": contaminated_score,
            "standardized_departure_delta": (contaminated_score - original_score) if original_score is not None and contaminated_score is not None else None,
            "comparisons_lost": max(0, baseline["matched_query_count"] - evaluated["matched_query_count"]),
            "comparisons_weakened": standardized_departure_reduced,
            "positive_excess_reduced_count": positive_excess_reduced,
            "standardized_departure_reduced_count": standardized_departure_reduced,
            "comparisons_changed_count": sum(1 for before, after in paired if before != after),
        })
    elif name in {"shift_one_replica_query", "shift_all_replica_query"}:
        changed_ids = {tuple(item.get("identity", ())) for item in manifest.get("changed", [])}
        before_by_id = {_identity(row): row for row in baseline["comparisons"]}
        after_by_id = {_identity(row): row for row in evaluated["comparisons"]}
        delta_rows = []
        for item in manifest.get("changed", []):
            key = tuple(item.get("identity", ()))
            if key in before_by_id and key in after_by_id:
                delta_rows.append({"identity": list(key), "observed_delta_ms": after_by_id[key].get("absolute_excess_ms") - before_by_id[key].get("absolute_excess_ms"), "planted_delta_ms": item.get("delta_ms")})
        unchanged = [key for key in before_by_id if key not in changed_ids and key in after_by_id and after_by_id[key].get("absolute_excess_ms") == before_by_id[key].get("absolute_excess_ms")]
        ref_before = {_identity(row): _duration(row) for row in original if _role(row) == "reference"}
        ref_after = {_identity(row): _duration(row) for row in transformed if _role(row) == "reference"}
        references_unchanged = ref_before == ref_after
        expected_pass = bool(changed_ids) and manifest.get("health_certified") is False and _query_ids(transformed) == _query_ids(original) and references_unchanged and bool(delta_rows) and all(abs(float(row["observed_delta_ms"]) - float(row["planted_delta_ms"])) < 1e-9 for row in delta_rows)
        details.update({"shifted_query_count": len(changed_ids), "historical_excess_deltas_ms": delta_rows, "unchanged_query_count": len(unchanged), "references_unchanged": references_unchanged, "pooled_policy_qualification": "preserve_and_report"})
    elif name == "remove_children_mark_incomplete":
        expected_pass = len(transformed) == len(original) and all(row.get("structure_status") == "unknown_structure" for row in transformed)
        if mode in {"C1", "C2"}:
            expected_pass = expected_pass and evaluated["matched_query_count"] == 0
        details["mode"] = mode
    else:
        expected_pass = False
    return bool(expected_pass), details


def run_control_checks(records: Iterable[Mapping], *, expected_path: Path | None = None, anchor: Mapping | None = None, allowlist: list[str] | None = None) -> dict:
    """Run all declared interventions and return machine-readable check rows."""
    original = [copy.deepcopy(dict(row)) for row in records]
    expected = load_expected_facts(expected_path)
    modes = ("C0", "C1", "C2")
    policies = ("same_replica", "pooled")
    baseline_by_cell = {
        (mode, policy): evaluate_records(original, mode=mode, replica_policy=policy, allowlist=allowlist, anchor=anchor)
        for mode in modes
        for policy in policies
    }
    baseline = baseline_by_cell[("C0", "pooled")]
    entries = list(expected.get("intervention_manifest", []))
    rows: list[dict] = []
    for entry in entries:
        name = str(entry["name"])
        # The manifest lists five seeds for thinning; each seed is evaluated
        # against all four predeclared target counts.
        targets = (10, 20, 50, 100) if name == "thin_references" else (None,)
        for target in targets:
            kwargs = {"seed": entry.get("seed", 42)}
            if target is not None:
                kwargs["target_count"] = target
            if entry.get("fraction") is not None:
                kwargs["fraction"] = entry["fraction"]
            result = apply_intervention(original, name, **kwargs)
            transformed = result["records"]
            for mode in modes:
                for policy in policies:
                    baseline_cell = baseline_by_cell[(mode, policy)]
                    evaluated = evaluate_records(transformed, mode=mode, replica_policy=policy, allowlist=allowlist, anchor=anchor)
                    identity_restored = _restore_renamed_ids(transformed, result["manifest"]) if name == "reorder_and_rename_ids" else transformed
                    restored_eval = evaluate_records(identity_restored, mode=mode, replica_policy=policy, allowlist=allowlist, anchor=anchor)
                    membership_equal = baseline_cell["membership_hash"] == restored_eval["membership_hash"]
                    query_preserved = _query_ids(identity_restored) == _query_ids(original)
                    query_count_preserved = restored_eval.get("query_count") == baseline_cell.get("query_count")
                    no_silent_loss = query_preserved and query_count_preserved and (len(transformed) == len(original) or name == "thin_references")
                    passed, pass_details = _control_pass(name, original, transformed, baseline_cell, evaluated, result["manifest"], target, mode=mode, replica_policy=policy, anchor=anchor, allowlist=allowlist)
                    row = {
                        "name": name,
                        "seed": entry.get("seed"),
                        "fraction": entry.get("fraction"),
                        "target_count": target,
                        "mode": mode,
                        "replica_policy": policy,
                        "expected": entry,
                        "manifest": result["manifest"],
                        "baseline": {"membership_hash": baseline_cell["membership_hash"], "matched_query_count": baseline_cell["matched_query_count"]},
                        "evaluated": {"membership_hash": evaluated["membership_hash"], "matched_query_count": evaluated["matched_query_count"]},
                        "membership_equal": membership_equal,
                        "query_membership_preserved": query_preserved,
                        "query_count_preserved": query_count_preserved,
                        "no_silent_loss": no_silent_loss,
                        "health_certified": False,
                        "pass": passed,
                        "pass_details": pass_details,
                    }
                    rows.append(row)
    return {
        "version": CONTROL_CHECK_VERSION,
        "expected_facts_source": str(expected_path or Path(__file__).with_name("tests") / "expected_facts.json"),
        "input_count": len(original),
        "baseline": baseline,
        "checks": rows,
        "zero_silent_losses": all(row["no_silent_loss"] for row in rows),
        "all_membership_preserved": all(row["membership_equal"] for row in rows if row["name"] != "thin_references"),
        "all_checks_pass": all(row["pass"] and row["no_silent_loss"] for row in rows),
        "failed_checks": [row for row in rows if not row["pass"]],
        "health_certification": "never_emitted",
    }
