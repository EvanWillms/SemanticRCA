"""Immutable values at the qualified-baseline domain boundary.

The producer and its storage adapters deliberately meet through these values.
The classes in this module contain no file or database access.  Collections are
tuples (and mapping fields are represented as sorted tuples) so a completed
baseline cannot be changed by a caller after it has been published.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence


def _finite_nonnegative(value: float | int | None) -> float | None:
    if value is None:
        return None
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("measurement must be finite and non-negative")
    return result


def _freeze_map(value: Mapping[str, Any] | Iterable[tuple[str, Any]] | None) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        value = value.items()
    return tuple(sorted((str(key), item) for key, item in value))


def _as_json(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {str(key): _as_json(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        # Epoch endpoints from the trace index are Decimal so exact boundary
        # decisions survive identity hashing and can still be canonicalized.
        return str(value)
    if isinstance(value, (tuple, list)):
        return [_as_json(item) for item in value]
    return value


def content_id(value: Any, *, prefix: str = "") -> str:
    """Return a stable SHA-256 identity for a JSON-compatible value."""

    encoded = json.dumps(_as_json(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return prefix + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class SourceLocator:
    """A resolver-independent pointer into one declared source."""

    snapshot_id: str
    source_id: str
    representation: str = "csv"
    record: str | int | None = None
    field: str | None = None
    selector: str | None = None

    def __post_init__(self) -> None:
        if not self.snapshot_id or not self.source_id:
            raise ValueError("source locator requires snapshot_id and source_id")
        if self.representation not in {"csv", "json", "sqlite", "memory"}:
            raise ValueError("unsupported source representation")

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "snapshot_id": self.snapshot_id,
            "source_id": self.source_id,
            "representation": self.representation,
        }
        if self.record is not None:
            value["record"] = self.record
        if self.field is not None:
            value["field"] = self.field
        if self.selector is not None:
            value["selector"] = self.selector
        return value


@dataclass(frozen=True)
class SourceSnapshot:
    """Identity of the complete, verified input inventory."""

    snapshot_id: str
    deployment: str
    sources: tuple[SourceLocator, ...] = ()
    parser_version: str = "unknown"
    extraction_version: str = "logical-span-dedup-v1"
    status: str = "verified"
    inventory_id: str | None = None
    unavailable_sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"discovered", "preparing", "verified", "partial", "failed"}:
            raise ValueError("invalid source snapshot status")
        if self.status == "verified" and self.unavailable_sources:
            raise ValueError("a verified snapshot cannot have unavailable sources")

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "deployment": self.deployment,
            "sources": [item.to_dict() for item in self.sources],
            "parser_version": self.parser_version,
            "extraction_version": self.extraction_version,
            "status": self.status,
            "inventory_id": self.inventory_id,
            "unavailable_sources": list(self.unavailable_sources),
        }


@dataclass(frozen=True)
class ObservationIdentity:
    snapshot_id: str
    deployment: str
    trace_id: str
    root_span_id: str

    @property
    def observation_id(self) -> str:
        return content_id((self.snapshot_id, self.deployment, self.trace_id, self.root_span_id))

    def to_dict(self) -> dict[str, str]:
        return {
            "snapshot_id": self.snapshot_id,
            "deployment": self.deployment,
            "trace_id": self.trace_id,
            "root_span_id": self.root_span_id,
            "observation_id": self.observation_id,
        }


@dataclass(frozen=True)
class Measurement:
    """Original duration evidence and its normalized millisecond value."""

    raw_text: str
    raw_unit: str = "ms"
    normalized_ms: float | None = None
    normalization_id: str = "duration-ms-v1"
    available: bool = True
    reasons: tuple[str, ...] = ()
    locator: SourceLocator | None = None

    def __post_init__(self) -> None:
        value = _finite_nonnegative(self.normalized_ms)
        if self.available and value is None:
            raise ValueError("available measurement requires normalized_ms")
        if not self.available and value is not None:
            raise ValueError("unavailable measurement cannot carry normalized_ms")

    @classmethod
    def from_value(
        cls,
        value: float | int | str | None,
        *,
        raw_unit: str = "ms",
        normalization_id: str = "duration-ms-v1",
        locator: SourceLocator | None = None,
    ) -> "Measurement":
        raw_text = "" if value is None else str(value)
        try:
            normalized = _finite_nonnegative(float(value))
        except (TypeError, ValueError):
            return cls(raw_text, raw_unit, None, normalization_id, False, ("invalid_measurement",), locator)
        return cls(raw_text, raw_unit, normalized, normalization_id, True, (), locator)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "raw_unit": self.raw_unit,
            "normalized_ms": self.normalized_ms,
            "normalization_id": self.normalization_id,
            "available": self.available,
            "reasons": list(self.reasons),
            "locator": self.locator.to_dict() if self.locator else None,
        }


@dataclass(frozen=True, order=True)
class OperationType:
    operation: str
    type: str

    def to_list(self) -> list[str]:
        return [self.operation, self.type]


@dataclass(frozen=True)
class ChildOccurrence:
    operation: str
    type: str
    count: int = 1
    end_ms: float | None = None

    def __post_init__(self) -> None:
        if self.count <= 0:
            raise ValueError("child count must be positive")
        if self.end_ms is not None:
            _finite_nonnegative(self.end_ms)

    @property
    def pair(self) -> OperationType:
        return OperationType(self.operation, self.type)


@dataclass(frozen=True)
class Observation:
    """A recovered frontend root and the structural evidence around it.

    ``role`` is advisory (``reference``, ``query`` or ``candidate``); kernels
    determine role from the anchor so a mislabeled record cannot enter a
    frozen catalog.  ``structure_state='unknown'`` is deliberately different
    from a known empty ``children`` tuple.
    """

    identity: ObservationIdentity
    root_operation: str
    root_type: str
    replica: str
    start_ms: float
    end_ms: float | None
    measurement: Measurement
    children: tuple[ChildOccurrence, ...] = ()
    structure_state: str = "known"
    role: str | None = None
    source_locators: tuple[SourceLocator, ...] = ()
    completion_state: str = "resolved"
    raw_id: str | None = None

    def __post_init__(self) -> None:
        _finite_nonnegative(self.start_ms)
        if self.end_ms is not None:
            _finite_nonnegative(self.end_ms)
        if self.structure_state not in {"known", "unknown"}:
            raise ValueError("structure_state must be known or unknown")
        if self.completion_state not in {"resolved", "unknown", "conflict", "excluded"}:
            raise ValueError("invalid completion state")
        if self.end_ms is None and self.completion_state == "resolved":
            object.__setattr__(self, "completion_state", "unknown")

    @property
    def observation_id(self) -> str:
        return self.identity.observation_id

    @property
    def c0_key(self) -> tuple[str, str]:
        return (self.root_operation, self.root_type)

    @property
    def c1_key(self) -> tuple[tuple[str, str], tuple[tuple[str, str], ...]] | None:
        if self.structure_state != "known":
            return None
        pairs = tuple(sorted({(child.operation, child.type) for child in self.children}))
        return (self.c0_key, pairs)

    @property
    def c2_key(self) -> tuple[tuple[str, str, int], ...] | None:
        if self.structure_state != "known":
            return None
        counts: dict[tuple[str, str], int] = {}
        for child in self.children:
            key = (child.operation, child.type)
            counts[key] = counts.get(key, 0) + child.count
        return tuple((operation, typ, count) for (operation, typ), count in sorted(counts.items()))

    @property
    def endpoint_ms(self) -> float | None:
        endpoints = [child.end_ms for child in self.children if child.end_ms is not None]
        if self.end_ms is not None:
            endpoints.append(self.end_ms)
        return max(endpoints) if endpoints else self.end_ms

    @property
    def complete(self) -> bool:
        return self.completion_state == "resolved" and self.endpoint_ms is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "identity": self.identity.to_dict(),
            "root_operation": self.root_operation,
            "root_type": self.root_type,
            "replica": self.replica,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "measurement": self.measurement.to_dict(),
            "children": [{"operation": c.operation, "type": c.type, "count": c.count, "end_ms": c.end_ms} for c in self.children],
            "structure_state": self.structure_state,
            "role": self.role,
            "completion_state": self.completion_state,
            "source_locators": [item.to_dict() for item in self.source_locators],
            "raw_id": self.raw_id,
        }


RecordedRequest = Observation


@dataclass(frozen=True)
class RetrievalReceipt:
    inventory_id: str | None = None
    selected_count: int = 0
    resolved_count: int = 0
    unresolved_count: int = 0
    scanned_records: int = 0
    recovered_records: int = 0
    missing_sources: tuple[str, ...] = ()
    cursors: tuple[tuple[str, str], ...] = ()
    completed_batches: int = 0
    status: str = "complete"
    reason: str | None = None
    timings: tuple[tuple[str, float], ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"complete", "partial", "failed", "not_available"}:
            raise ValueError("invalid retrieval receipt status")
        for name in ("selected_count", "resolved_count", "unresolved_count", "scanned_records", "recovered_records", "completed_batches"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")

    @property
    def complete(self) -> bool:
        return self.status == "complete" and not self.missing_sources


@dataclass(frozen=True)
class ObservationBatch:
    observations: tuple[Observation, ...] = ()
    selection_receipt: RetrievalReceipt = field(default_factory=RetrievalReceipt)
    recovery_receipt: RetrievalReceipt | None = None
    unresolved: tuple[Any, ...] = ()
    extraction_version: str = "logical-span-dedup-v1"

    def __iter__(self):
        return iter(self.observations)


@dataclass(frozen=True)
class BaselinePolicy:
    policy_id: str = "short-window-c1-pooled-v1"
    version: str = "1"
    allowlist: tuple[str, ...] = ("frontend-0", "frontend-1", "frontend-2")
    deployment: str | None = None
    context: str = "C1"
    lookback_ms: int = 300_000
    horizon_ms: int = 1_800_000
    slice_ms: int = 300_000
    min_count: int = 20
    min_occupied_bins: int = 3
    max_bin_fraction: float = 0.5
    block_ms: int = 60_000
    bootstrap_replicates: int = 200
    bootstrap_seed: int = 42
    stability_width_fraction: float = 0.40
    estimator_id: str = "median-linear-quantile-v1"
    normalization_id: str = "duration-ms-v1"
    no_fallback: bool = True

    def __post_init__(self) -> None:
        if not self.policy_id or self.context != "C1":
            raise ValueError("initial baseline policy requires C1 and a policy id")
        if not self.allowlist:
            raise ValueError("frontend allowlist cannot be empty")
        if min(self.lookback_ms, self.horizon_ms, self.slice_ms, self.block_ms) <= 0:
            raise ValueError("policy windows must be positive")
        if self.horizon_ms % self.slice_ms:
            raise ValueError("horizon must contain whole query slices")
        if self.min_count <= 0 or self.min_occupied_bins <= 0 or self.bootstrap_replicates <= 0:
            raise ValueError("support and bootstrap counts must be positive")
        if not 0 < self.max_bin_fraction <= 1 or not 0 < self.stability_width_fraction:
            raise ValueError("policy fractions are out of range")

    @classmethod
    def short_window_c1_pooled_v1(cls) -> "BaselinePolicy":
        return cls()

    @property
    def slice_count(self) -> int:
        return self.horizon_ms // self.slice_ms

    @property
    def frontend_allowlist(self) -> tuple[str, ...]:
        return self.allowlist

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id, "version": self.version, "allowlist": list(self.allowlist),
            "deployment": self.deployment, "context": self.context, "lookback_ms": self.lookback_ms,
            "horizon_ms": self.horizon_ms, "slice_ms": self.slice_ms, "min_count": self.min_count,
            "min_occupied_bins": self.min_occupied_bins, "max_bin_fraction": self.max_bin_fraction,
            "block_ms": self.block_ms, "bootstrap_replicates": self.bootstrap_replicates,
            "bootstrap_seed": self.bootstrap_seed, "stability_width_fraction": self.stability_width_fraction,
            "estimator_id": self.estimator_id, "normalization_id": self.normalization_id,
            "no_fallback": self.no_fallback,
        }


@dataclass(frozen=True)
class SupportAssessment:
    status: str
    n: int
    occupied_bins: int
    minimum_bins: int
    largest_bin_count: int
    largest_bin_fraction: float | None
    reasons: tuple[str, ...] = ()
    bin_counts: tuple[tuple[int, int], ...] = ()

    @property
    def supported(self) -> bool:
        return self.status == "supported"


@dataclass(frozen=True)
class CenterStability:
    state: str
    block_keys: tuple[int, ...] = ()
    seed: int | None = None
    replicate_count: int = 0
    usable_replicates: int = 0
    failed_replicates: int = 0
    draw_indexes: tuple[tuple[int, ...], ...] = ()
    replicate_medians: tuple[float | None, ...] = ()
    p05: float | None = None
    p95: float | None = None
    full_width: float | None = None
    relative_width: float | None = None
    relative_width_available: bool = False
    reasons: tuple[str, ...] = ()

    @property
    def passes(self) -> bool:
        return self.state == "passes_screen"


@dataclass(frozen=True)
class BaselineStatistics:
    count: int
    median: float | None
    q1: float | None
    q3: float | None
    mad: float | None
    first_start_ms: float | None = None
    last_start_ms: float | None = None
    largest_gap_ms: float | None = None
    per_minute: tuple[tuple[int, int], ...] = ()
    per_replica: tuple[tuple[str, int], ...] = ()
    first_half_median: float | None = None
    second_half_median: float | None = None
    leave_one_minute_out: tuple[tuple[int, float | None], ...] = ()
    values: tuple[float, ...] = ()


@dataclass(frozen=True)
class StructuralPattern:
    pattern_id: str
    c0_key: tuple[str, str]
    c2_key: tuple[tuple[str, str, int], ...]
    member_ids: tuple[str, ...]
    count: int
    known_denominator: int
    frequency: float | None


@dataclass(frozen=True)
class StructuralPopulation:
    population_id: str
    set_id: str
    c0_key: tuple[str, str]
    candidate_ids: tuple[str, ...] = ()
    eligible_ids: tuple[str, ...] = ()
    known_structure_count: int = 0
    unknown_structure_count: int = 0
    eligibility_unknown_count: int = 0
    excluded_count: int = 0
    patterns: tuple[StructuralPattern, ...] = ()

    @property
    def known_denominator(self) -> int:
        return self.known_structure_count


@dataclass(frozen=True)
class ReferenceCohort:
    cohort_id: str
    set_id: str
    c1_key: Any
    candidate_ids: tuple[str, ...]
    member_ids: tuple[str, ...]
    exclusion_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FrozenBaseline:
    baseline_id: str
    cohort_id: str
    set_id: str
    c1_key: Any
    membership_hash: str
    member_ids: tuple[str, ...]
    statistics: BaselineStatistics
    support: SupportAssessment
    stability: CenterStability
    qualifications: tuple[str, ...] = ()
    exclusion_reasons: tuple[tuple[str, tuple[str, ...]], ...] = ()
    normalization_id: str = "duration-ms-v1"

    @property
    def supported(self) -> bool:
        return self.support.supported

    @property
    def median(self) -> float | None:
        return self.statistics.median


@dataclass(frozen=True)
class MissingContext:
    set_id: str
    lookup_kind: str
    context_key: Any
    reasons: tuple[str, ...] = ("missing_context",)
    outcome_id: str = ""
    unavailable: bool = True

    def __post_init__(self) -> None:
        if self.lookup_kind not in {"C1_duration", "C0_structure"}:
            raise ValueError("invalid missing-context lookup kind")
        if not self.outcome_id:
            object.__setattr__(self, "outcome_id", content_id((self.set_id, self.lookup_kind, self.context_key, self.reasons), prefix="missing-"))


@dataclass(frozen=True)
class UnresolvedQuery:
    observation_id: str | None
    reason: str
    slice_index: int | None = None
    raw_id: str | None = None


@dataclass(frozen=True)
class QueryAssignment:
    occurrence_id: str
    observation_id: str
    set_id: str
    slice_index: int
    baseline: FrozenBaseline | MissingContext
    structural_population: StructuralPopulation | MissingContext
    qualification: str
    reasons: tuple[str, ...] = ()
    duration_comparison_eligible: bool = False
    observation: Observation | None = None


@dataclass(frozen=True)
class AssignmentBatch:
    assignments: tuple[QueryAssignment, ...] = ()
    unresolved: tuple[UnresolvedQuery, ...] = ()

    @property
    def resolved_count(self) -> int:
        return len(self.assignments)


@dataclass(frozen=True)
class BaselineSet:
    set_id: str
    snapshot_id: str
    deployment: str
    anchor_ms: float
    policy: BaselinePolicy
    baselines: tuple[FrozenBaseline, ...] = ()
    structural_populations: tuple[StructuralPopulation, ...] = ()
    cohorts: tuple[ReferenceCohort, ...] = ()
    selection_receipt: RetrievalReceipt = field(default_factory=RetrievalReceipt)
    extraction_version: str = "logical-span-dedup-v1"
    status: str = "completed"
    reasons: tuple[str, ...] = ()

    def baseline_for(self, c1_key: Any) -> FrozenBaseline | None:
        return next((item for item in self.baselines if item.c1_key == c1_key), None)

    def population_for(self, c0_key: tuple[str, str]) -> StructuralPopulation | None:
        return next((item for item in self.structural_populations if item.c0_key == c0_key), None)

    @property
    def horizon_end_ms(self) -> float:
        return self.anchor_ms + self.policy.horizon_ms


@dataclass(frozen=True)
class CoverageStatement:
    resolved_queries: int
    supported_assignments: int
    unavailable_assignments: int
    unresolved_queries: int
    denominator: int
    ratio: float | None
    reason: str | None = None


def _coerce_child(value: Any) -> ChildOccurrence:
    if isinstance(value, ChildOccurrence):
        return value
    if isinstance(value, Mapping):
        return ChildOccurrence(str(value.get("operation", value.get("operation_name", ""))), str(value.get("type", "")), int(value.get("count", 1)), value.get("end_ms", value.get("end")))
    if isinstance(value, Sequence) and len(value) >= 2:
        return ChildOccurrence(str(value[0]), str(value[1]), int(value[2]) if len(value) > 2 else 1)
    raise TypeError("child must be ChildOccurrence or a mapping/sequence")


def coerce_observation(value: Observation | Mapping[str, Any]) -> Observation:
    """Coerce the small mapping shape used by extraction adapters and fixtures."""

    if isinstance(value, Observation):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("observation must be Observation or mapping")
    identity_value = value.get("identity")
    if isinstance(identity_value, ObservationIdentity):
        identity = identity_value
    else:
        identity = ObservationIdentity(
            str(value.get("snapshot_id", value.get("source_snapshot_id", "snapshot"))),
            str(value.get("deployment", "")),
            str(value.get("trace_id", value.get("trace", value.get("id", "")))),
            str(value.get("root_span_id", value.get("span_id", value.get("root_id", value.get("id", ""))))),
        )
    measurement_value = value.get("measurement")
    if isinstance(measurement_value, Measurement):
        measurement = measurement_value
    elif isinstance(measurement_value, Mapping):
        measurement = Measurement(
            str(measurement_value.get("raw_text", measurement_value.get("raw", value.get("duration", "")))),
            str(measurement_value.get("raw_unit", measurement_value.get("unit", "ms"))),
            measurement_value.get("normalized_ms", measurement_value.get("duration_ms", value.get("duration_ms", value.get("duration")))),
            str(measurement_value.get("normalization_id", "duration-ms-v1")),
            bool(measurement_value.get("available", True)),
            tuple(str(item) for item in measurement_value.get("reasons", ())),
            measurement_value.get("locator"),
        )
    else:
        measurement = Measurement.from_value(value.get("duration_ms", value.get("duration")), raw_unit=str(value.get("unit", "ms")))
    children = tuple(_coerce_child(item) for item in value.get("children", value.get("child_occurrences", ())))
    return Observation(
        identity=identity,
        root_operation=str(value.get("root_operation", value.get("operation_name", value.get("operation", "")))),
        root_type=str(value.get("root_type", value.get("type", ""))),
        replica=str(value.get("replica", value.get("component", value.get("cmdb_id", "")))),
        start_ms=float(value.get("start_ms", value.get("timestamp", value.get("start", 0)))),
        end_ms=None if value.get("end_ms", value.get("end")) is None else float(value.get("end_ms", value.get("end"))),
        measurement=measurement,
        children=children,
        structure_state=str(value.get("structure_state", "unknown" if value.get("children_unknown") else "known")),
        role=value.get("role"),
        source_locators=tuple(item for item in value.get("source_locators", ()) if isinstance(item, SourceLocator)),
        completion_state=str(value.get("completion_state", "resolved" if value.get("end_ms", value.get("end")) is not None else "unknown")),
        raw_id=None if value.get("raw_id") is None else str(value.get("raw_id")),
    )


def coerce_policy(value: BaselinePolicy | str | None) -> BaselinePolicy:
    if value is None:
        return BaselinePolicy.short_window_c1_pooled_v1()
    if isinstance(value, BaselinePolicy):
        return value
    if isinstance(value, str):
        if value != "short-window-c1-pooled-v1":
            raise ValueError(f"unknown baseline policy: {value}")
        return BaselinePolicy.short_window_c1_pooled_v1()
    raise TypeError("policy must be BaselinePolicy, policy id, or None")
