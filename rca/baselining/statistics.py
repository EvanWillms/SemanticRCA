"""Deterministic support diagnostics and the qualified center estimator."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import math
import random
from typing import Any

from .contracts import (
    BaselinePolicy,
    BaselineStatistics,
    CenterStability,
    Observation,
    SupportAssessment,
    coerce_observation,
)


def _quantile_sorted(values: Sequence[float], probability: float) -> float | None:
    if not values:
        return None
    if not 0 <= probability <= 1:
        raise ValueError("quantile probability must be between 0 and 1")
    ordered = sorted(float(item) for item in values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def quantile(values: Iterable[float], probability: float) -> float | None:
    """Linear-interpolation empirical quantile used by the baseline contract."""

    return _quantile_sorted(tuple(float(value) for value in values), probability)


def median(values: Iterable[float]) -> float | None:
    return quantile(values, 0.5)


def raw_mad(values: Iterable[float]) -> float | None:
    materialized = tuple(float(value) for value in values)
    center = median(materialized)
    if center is None:
        return None
    return median(abs(value - center) for value in materialized)


def _obs(value: Observation | Mapping[str, Any]) -> Observation:
    return coerce_observation(value)


def _valid_observations(observations: Iterable[Observation | Mapping[str, Any]]) -> tuple[Observation, ...]:
    result: list[Observation] = []
    seen: set[str] = set()
    for item in observations:
        observation = _obs(item)
        if observation.observation_id in seen:
            continue
        seen.add(observation.observation_id)
        if observation.measurement.available and observation.measurement.normalized_ms is not None:
            result.append(observation)
    return tuple(result)


def compute_statistics(
    observations: Iterable[Observation | Mapping[str, Any]],
    *,
    anchor_ms: float | None = None,
    lookback_ms: int = 300_000,
    block_ms: int = 60_000,
) -> BaselineStatistics:
    """Compute descriptive fields from already selected observations.

    This function never applies support thresholds.  Unsupported cohorts still
    retain their audit-only statistics, while empty subsets carry ``None``.
    """

    materialized = tuple(_valid_observations(observations))
    ordered = tuple(sorted(materialized, key=lambda item: (item.start_ms, item.observation_id)))
    values = tuple(float(item.measurement.normalized_ms) for item in ordered if item.measurement.normalized_ms is not None)
    starts = tuple(float(item.start_ms) for item in ordered)
    center = median(values)
    q1 = quantile(values, 0.25)
    q3 = quantile(values, 0.75)
    first = starts[0] if starts else None
    last = starts[-1] if starts else None
    largest_gap = max((right - left for left, right in zip(starts, starts[1:])), default=None)
    minute_counts: dict[int, int] = {}
    replica_counts: dict[str, int] = {}
    for item in ordered:
        minute_counts[int(item.start_ms // 60_000)] = minute_counts.get(int(item.start_ms // 60_000), 0) + 1
        replica_counts[item.replica] = replica_counts.get(item.replica, 0) + 1

    if anchor_ms is None:
        midpoint = (first + last) / 2 if first is not None and last is not None else None
    else:
        midpoint = anchor_ms - lookback_ms / 2
    first_half = tuple(value for item, value in zip(ordered, values) if midpoint is None or item.start_ms < midpoint)
    second_half = tuple(value for item, value in zip(ordered, values) if midpoint is not None and item.start_ms >= midpoint)
    if anchor_ms is None:
        # With no declared interval, keep a useful split for callers using this
        # helper directly: the median of each half of observed order.
        pivot = len(values) // 2
        first_half, second_half = values[:pivot], values[pivot:]

    leave_one: list[tuple[int, float | None]] = []
    for minute in sorted(minute_counts):
        subset = tuple(value for item, value in zip(ordered, values) if int(item.start_ms // 60_000) != minute)
        leave_one.append((minute, median(subset)))
    return BaselineStatistics(
        count=len(values), median=center, q1=q1, q3=q3, mad=raw_mad(values),
        first_start_ms=first, last_start_ms=last, largest_gap_ms=largest_gap,
        per_minute=tuple(sorted(minute_counts.items())),
        per_replica=tuple(sorted(replica_counts.items())),
        first_half_median=median(first_half), second_half_median=median(second_half),
        leave_one_minute_out=tuple(leave_one), values=values,
    )


def _starts(observations: Iterable[Observation | Mapping[str, Any] | float | int]) -> tuple[float, ...]:
    result: list[float] = []
    for item in observations:
        if isinstance(item, (int, float)):
            result.append(float(item))
        else:
            result.append(float(_obs(item).start_ms))
    return tuple(result)


def assess_support(
    observations: Iterable[Observation | Mapping[str, Any] | float | int],
    policy: BaselinePolicy | None = None,
) -> SupportAssessment:
    """Apply count, occupied-minute, and concentration rules independently."""

    policy = policy or BaselinePolicy.short_window_c1_pooled_v1()
    starts = _starts(observations)
    bins: dict[int, int] = {}
    for start in starts:
        key = int(start // 60_000)
        bins[key] = bins.get(key, 0) + 1
    n = len(starts)
    occupied = len(bins)
    largest = max(bins.values(), default=0)
    fraction = largest / n if n else None
    reasons: list[str] = []
    if n < policy.min_count:
        reasons.append("minimum_count")
    if occupied < policy.min_occupied_bins:
        reasons.append("occupied_minutes")
    if n and fraction > policy.max_bin_fraction:
        reasons.append("minute_concentration")
    return SupportAssessment(
        status="supported" if not reasons else "unavailable", n=n,
        occupied_bins=occupied, minimum_bins=policy.min_occupied_bins,
        largest_bin_count=largest, largest_bin_fraction=fraction,
        reasons=tuple(reasons), bin_counts=tuple(sorted(bins.items())),
    )


def exact_block_bootstrap(
    blocks: Mapping[int, Sequence[float]],
    *,
    replicate_count: int = 200,
    seed: int = 42,
    relative_width_fraction: float = 0.40,
) -> CenterStability:
    """Resample one-minute interval blocks exactly, retaining empty draws.

    A draw selects the original number of blocks with replacement.  All values
    in each selected block are retained; a draw with no values is recorded as a
    failed replicate rather than silently dropped from the denominator.
    """

    if replicate_count <= 0:
        raise ValueError("replicate_count must be positive")
    keys = tuple(sorted(int(key) for key in blocks))
    if not keys:
        return CenterStability("not_assessed", seed=seed, replicate_count=replicate_count, failed_replicates=replicate_count, reasons=("no_blocks",))
    rng = random.Random(seed)
    draw_indexes: list[tuple[int, ...]] = []
    replicate_medians: list[float | None] = []
    for _ in range(replicate_count):
        draw = tuple(rng.randrange(len(keys)) for _ in range(len(keys)))
        draw_indexes.append(draw)
        sample: list[float] = []
        for index in draw:
            sample.extend(float(value) for value in blocks[keys[index]])
        replicate_medians.append(median(sample))
    usable_values = tuple(value for value in replicate_medians if value is not None)
    usable = len(usable_values)
    failed = replicate_count - usable
    p05 = quantile(usable_values, 0.05)
    p95 = quantile(usable_values, 0.95)
    width = p95 - p05 if p05 is not None and p95 is not None else None
    base = median(value for values in blocks.values() for value in values)
    relative = width / base if width is not None and base is not None and base > 0 else None
    if base is None:
        state = "not_assessed"
        reasons = ("no_usable_values",)
    elif base == 0:
        state = "not_applicable_zero_center"
        reasons = ("zero_center",)
    elif usable < 190:
        state = "inconclusive"
        reasons = ("insufficient_usable_replicates",)
    elif width is not None and width <= relative_width_fraction * base:
        state = "passes_screen"
        reasons = ()
    else:
        state = "fails_screen"
        reasons = ("relative_width",)
    return CenterStability(
        state=state, block_keys=keys, seed=seed, replicate_count=replicate_count,
        usable_replicates=usable, failed_replicates=failed,
        draw_indexes=tuple(draw_indexes), replicate_medians=tuple(replicate_medians),
        p05=p05, p95=p95, full_width=width, relative_width=relative,
        relative_width_available=relative is not None, reasons=reasons,
    )


def assess_center_stability(
    observations: Iterable[Observation | Mapping[str, Any]],
    support: SupportAssessment | None = None,
    *,
    anchor_ms: float,
    policy: BaselinePolicy | None = None,
) -> CenterStability:
    policy = policy or BaselinePolicy.short_window_c1_pooled_v1()
    materialized = _valid_observations(observations)
    support = support or assess_support(materialized, policy)
    if not support.supported:
        return CenterStability("not_assessed", reasons=("unsupported_reference", *support.reasons))
    interval_start = anchor_ms - policy.lookback_ms
    first_block = int(interval_start // policy.block_ms)
    # ``ceil(T / block)-1`` is exact for integer epoch anchors and also works
    # for non-minute-aligned anchors; subtracting a float epsilon can round
    # away at large epoch values and accidentally add a sixth block.
    last_block = math.ceil(anchor_ms / policy.block_ms) - 1
    blocks: dict[int, list[float]] = {key: [] for key in range(first_block, last_block + 1)}
    for item in materialized:
        if interval_start <= item.start_ms < anchor_ms and item.measurement.normalized_ms is not None:
            blocks.setdefault(int(item.start_ms // policy.block_ms), []).append(float(item.measurement.normalized_ms))
    return exact_block_bootstrap(
        blocks, replicate_count=policy.bootstrap_replicates, seed=policy.bootstrap_seed,
        relative_width_fraction=policy.stability_width_fraction,
    )


# Explicit aliases make the estimator name discoverable to adapters and keep
# authored tests readable without introducing a second implementation.
bootstrap_center = exact_block_bootstrap
block_bootstrap = exact_block_bootstrap
support_assessment = assess_support
center_stability = assess_center_stability
