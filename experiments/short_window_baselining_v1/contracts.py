"""Small, deterministic contracts shared by the matrix runner and checks.

The functions accept plain mappings so controlled fixtures can exercise the
same semantics without constructing a database.  They intentionally return
JSON-serialisable values; callers may use ``signature_key`` when a compact
hashable cohort key is needed.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import Counter
from typing import Iterable, Mapping, Sequence


MODES = ("C0", "C1", "C2")


def _pair(child: Mapping) -> tuple[str, str]:
    return (str(child.get("operation_name", "")), str(child.get("type", "")))


def signature_for_root(root: Mapping, mode: str = "C0") -> dict:
    """Build a raw operation/type signature from recorded direct children.

    ``unknown_structure`` is explicit.  An empty resolved child list is
    represented as ``empty_recorded_children`` and is never conflated with
    missing retrieval.  Component identity remains in the observation and is
    deliberately outside the signature because replica policy controls it.
    """
    mode = str(mode).upper()
    if mode not in MODES:
        raise ValueError(f"unknown structure mode: {mode}")
    raw_children = root.get("direct_children", root.get("children", []))
    children_unknown = raw_children is None or root.get("retrieval_state") in {"unknown_structure", "incomplete", "unresolved"}
    children = list(raw_children or [])
    state = str(root.get("structure_status", root.get("structure_state", root.get("retrieval_state", "resolved"))))
    if state == "known_empty" or (state == "resolved" and not children and not children_unknown):
        state = "empty_recorded_children"
    elif state not in {"resolved", "empty_recorded_children", "unknown_structure"}:
        state = "unknown_structure"
    if children_unknown or root.get("unknown_structure") or root.get("retrieval_unresolved"):
        state = "unknown_structure"
    pairs = sorted(_pair(child) for child in children)
    result = {
        "mode": mode,
        "root_operation_name": str(root.get("operation_name", "")),
        "root_type": str(root.get("type", "")),
        "structure_state": state,
        "direct_child_set": [[op, typ] for op, typ in sorted(set(pairs))],
        "direct_child_multiset": [[op, typ, count] for (op, typ), count in sorted(Counter(pairs).items())],
    }
    if mode == "C0":
        # C0 is exactly raw root operation + raw type. Structural status is
        # emitted on the observation and structural channel separately.
        return {"mode": mode, "root_operation_name": result["root_operation_name"], "root_type": result["root_type"]}
    elif state == "unknown_structure":
        # Do not accidentally match an unresolved C1/C2 observation to an
        # empty or known structural cohort.
        result["direct_child_set"] = None
        result["direct_child_multiset"] = None
    elif mode == "C1":
        result.pop("direct_child_multiset")
    return result


def signature_key(signature: Mapping) -> str:
    return json.dumps(dict(signature), sort_keys=True, separators=(",", ":"))


def _value(record: Mapping) -> float | None:
    raw = record.get("duration_ms", record.get("observed_ms", record.get("duration")))
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def support_diagnostics(records: Iterable[Mapping], lookback_minutes: int, min_count: int = 20) -> dict:
    """Compute the predeclared count, one-minute-bin and concentration gates."""
    rows = list(records)
    valid = [row for row in rows if _value(row) is not None and row.get("start_ms", row.get("timestamp_ms")) is not None]
    stamps = sorted(int(row.get("start_ms", row.get("timestamp_ms"))) for row in valid)
    # A bin is anchored to the reference interval's absolute minute.  The
    # relative result is deterministic even when callers only provide starts.
    bins = Counter((stamp // 60_000) for stamp in stamps)
    occupied = len(bins)
    largest_count = max(bins.values(), default=0)
    n = len(valid)
    required_bins = max(3, math.ceil(int(lookback_minutes) / 2))
    first = stamps[0] if stamps else None
    last = stamps[-1] if stamps else None
    gaps = [b - a for a, b in zip(stamps, stamps[1:]) if b > a]
    return {
        "n": n,
        "input_records": len(rows),
        "invalid_duration_count": len(rows) - n,
        "occupied_minutes": occupied,
        "required_minutes": required_bins,
        "largest_minute_count": largest_count,
        "largest_minute_fraction": (largest_count / n) if n else None,
        "first_observation_ms": first,
        "last_observation_ms": last,
        "largest_inter_observation_gap_ms": max(gaps, default=None),
        "minimum_count": int(min_count),
        "supported": bool(n >= int(min_count) and occupied >= required_bins and (largest_count <= n / 2 if n else False)),
        "failure_reasons": [
            reason for reason, failed in (
                ("minimum_count", n < int(min_count)),
                ("occupied_minutes", occupied < required_bins),
                ("minute_concentration", bool(n) and largest_count > n / 2),
            ) if failed
        ],
    }


def _quantile(values: Sequence[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * p
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def compare_duration(observed_ms: float | int, reference_durations: Iterable[float | int]) -> dict:
    """Return descriptive median/excess/ratio/MAD fields with explicit nulls."""
    refs = []
    for value in reference_durations:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            refs.append(number)
    try:
        observed = float(observed_ms)
    except (TypeError, ValueError):
        observed = math.nan
    if not refs or not math.isfinite(observed):
        return {"observed_ms": None if not math.isfinite(observed) else observed, "n": len(refs), "median_ms": None, "q1_ms": None, "q3_ms": None, "mad_ms": None, "absolute_excess_ms": None, "ratio": None, "standardized_departure": None, "undefined_reasons": ["empty_reference" if not refs else "invalid_observed"]}
    median = statistics.median(refs)
    mad = statistics.median([abs(value - median) for value in refs])
    excess = observed - median
    undefined = []
    ratio = None
    standardized = None
    if median > 0:
        ratio = observed / median
    else:
        undefined.append("zero_reference_median")
    if mad > 0:
        standardized = excess / (1.4826 * mad)
    else:
        undefined.append("zero_reference_mad")
    return {
        "observed_ms": observed,
        "n": len(refs),
        "median_ms": median,
        "q1_ms": _quantile(refs, 0.25),
        "q3_ms": _quantile(refs, 0.75),
        "mad_ms": mad,
        "absolute_excess_ms": excess,
        "ratio": ratio,
        "standardized_departure": standardized,
        "undefined_reasons": undefined,
    }


def bootstrap_median(ref_records: Iterable[Mapping], seed: int = 42, replicates: int = 200, start_ms: int | None = None, end_ms: int | None = None) -> dict:
    """Resample one-minute blocks and return an exploratory median interval."""
    rows = list(ref_records)
    blocks: dict[int, list[float]] = {}
    for row in rows:
        value = _value(row)
        stamp = row.get("start_ms", row.get("timestamp_ms"))
        if value is None or stamp is None:
            continue
        blocks.setdefault(int(stamp) // 60_000, []).append(value)
    if start_ms is not None and end_ms is not None and int(end_ms) > int(start_ms):
        keys = list(range(int(start_ms) // 60_000, (int(end_ms) - 1) // 60_000 + 1))
    else:
        keys = sorted(blocks)
    rng = random.Random(int(seed))
    medians: list[float] = []
    failed = 0
    for _ in range(int(replicates)):
        if not keys:
            failed += 1
            continue
        sampled = [rng.choice(keys) for _ in keys]
        values = [value for key in sampled if key in blocks for value in blocks[key]]
        if not values:
            failed += 1
            continue
        medians.append(statistics.median(values))
    return {
        "seed": int(seed),
        "replicates": int(replicates),
        "usable_replicates": len(medians),
        "failed_or_empty_replicates": failed,
        "median_ms": statistics.median([_value(row) for row in rows if _value(row) is not None]) if any(_value(row) is not None for row in rows) else None,
        "p05_ms": _quantile(medians, 0.05),
        "p95_ms": _quantile(medians, 0.95),
        "full_width_ms": (_quantile(medians, 0.95) - _quantile(medians, 0.05)) if medians else None,
        "occupied_blocks": len(blocks),
        "sampled_blocks_per_replicate": len(keys),
    }


def stable_membership_hash(records: Iterable[Mapping]) -> str:
    """Hash membership identities only, excluding durations and source order."""
    identities = []
    for row in records:
        identities.append((str(row.get("trace_id", "")), str(row.get("span_id", ""))))
    payload = json.dumps(sorted(set(identities)), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
