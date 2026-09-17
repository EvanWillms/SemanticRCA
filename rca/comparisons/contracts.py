"""Typed values for reference-relative comparative descriptors.

The comparison package deliberately has no dependency on the baseline
producer's implementation.  Values at this boundary are immutable and can
therefore be passed by a producer implemented with either dataclasses or
portable JSON mappings.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence


class Availability(str, Enum):
    AVAILABLE = "available"
    NOT_REQUESTED = "not_requested"
    UNDEFINED = "undefined"
    UNAVAILABLE = "unavailable"


def _json_value(value: Any) -> Any:
    """Turn a domain value into deterministic, finite JSON-compatible data."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: _json_value(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _json_value(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list, set, frozenset)):
        values = [_json_value(v) for v in value]
        if isinstance(value, (set, frozenset)):
            return sorted(values, key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
        return values
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite values are not valid descriptor content")
        return value
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_value(value.to_dict())
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_json_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def content_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:24]}"


@dataclass(frozen=True)
class EvidenceReference:
    """A portable pointer to a source record or a derived baseline value."""

    kind: str = "source"
    snapshot_id: str | None = None
    artifact_id: str | None = None
    source_id: str | None = None
    locator: Any = None
    entity_id: str | None = None
    selector: str | None = None
    definition_id: str | None = None
    claimed_value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True)
class FieldResult:
    """A value and its independent availability state."""

    status: str
    value: Any = None
    unit: str | None = None
    definition: str | None = None
    reasons: tuple[str, ...] = ()
    evidence: tuple[EvidenceReference, ...] = ()
    raw_value: Any = None
    raw_text: str | None = None

    def __post_init__(self) -> None:
        status = self.status.value if isinstance(self.status, Availability) else self.status
        if status not in {state.value for state in Availability}:
            raise ValueError(f"unknown field availability: {status}")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "reasons", tuple(self.reasons))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        if status != Availability.AVAILABLE.value and self.value is not None:
            raise ValueError(f"{status} fields must have null value")
        if status == Availability.AVAILABLE.value and self.value is None:
            raise ValueError("available fields must carry a value")
        if status == Availability.AVAILABLE.value and isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError("available numeric fields must be finite")

    @classmethod
    def available(cls, value: Any, **kwargs: Any) -> "FieldResult":
        return cls(Availability.AVAILABLE.value, value=value, **kwargs)

    @classmethod
    def not_requested(cls, reason: str = "diagnostic_not_requested", **kwargs: Any) -> "FieldResult":
        return cls(Availability.NOT_REQUESTED.value, reasons=(reason,), **kwargs)

    @classmethod
    def undefined(cls, reason: str, **kwargs: Any) -> "FieldResult":
        return cls(Availability.UNDEFINED.value, reasons=(reason,), **kwargs)

    @classmethod
    def unavailable(cls, reason: str, **kwargs: Any) -> "FieldResult":
        return cls(Availability.UNAVAILABLE.value, reasons=(reason,), **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True)
class ComparisonDefinition:
    definition_id: str = "frontend-comparison-v1"
    version: str = "1"
    measurement_family: str = "frontend_root_duration"
    arithmetic_version: str = "duration-excess-v1"
    diagnostics: tuple[str, ...] = ()
    mad_definition: str = "(x-median)/(1.4826*raw_mad)"
    label_version: str = "ordering-v1"

    def __post_init__(self) -> None:
        allowed = {"ratio", "mad"}
        unknown = set(self.diagnostics) - allowed
        if unknown:
            raise ValueError(f"unknown diagnostics: {sorted(unknown)}")
        object.__setattr__(self, "diagnostics", tuple(sorted(set(self.diagnostics))))

    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True)
class DescriptorQualification:
    code: str
    scope: str = "comparison"
    evidence: tuple[EvidenceReference, ...] = ()
    unverified: bool = False
    detail: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))

    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True)
class DurationComparison:
    observed: FieldResult
    reference_median: FieldResult
    signed_excess: FieldResult
    ratio: FieldResult
    mad_departure: FieldResult
    ordering: FieldResult
    baseline_id: str | None = None
    raw_mad: FieldResult | None = None

    @property
    def observed_ms(self) -> FieldResult:
        return self.observed

    @property
    def reference_median_ms(self) -> FieldResult:
        return self.reference_median

    @property
    def signed_excess_ms(self) -> FieldResult:
        return self.signed_excess

    @property
    def standardized_departure(self) -> FieldResult:
        return self.mad_departure

    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True)
class PatternDifference:
    pattern_id: str
    reference_count: int
    known_denominator: int
    frequency: FieldResult
    count_deltas: Mapping[str, int]
    additions: Mapping[str, int]
    removals: Mapping[str, int]
    member_evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "count_deltas", MappingProxyType(dict(sorted(self.count_deltas.items()))))
        object.__setattr__(self, "additions", MappingProxyType(dict(sorted(self.additions.items()))))
        object.__setattr__(self, "removals", MappingProxyType(dict(sorted(self.removals.items()))))
        object.__setattr__(self, "member_evidence", tuple(self.member_evidence))

    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True)
class StructuralComparison:
    query_state: str
    c0_population_id: str | None
    known_reference_count: FieldResult
    unknown_reference_count: FieldResult
    pattern_differences: tuple[PatternDifference, ...]
    matching_pattern_count: FieldResult
    absent_from_reference: FieldResult
    query_pattern: Mapping[str, int] | None = None
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "pattern_differences", tuple(self.pattern_differences))
        if self.query_pattern is not None:
            object.__setattr__(self, "query_pattern", MappingProxyType(dict(sorted(self.query_pattern.items()))))
        object.__setattr__(self, "reasons", tuple(self.reasons))

    @property
    def patterns(self) -> tuple[PatternDifference, ...]:
        return self.pattern_differences

    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True)
class ComparativeDescriptor:
    descriptor_id: str
    schema_version: str
    occurrence_id: str
    observation_id: str
    baseline_set_id: str | None
    definition: ComparisonDefinition
    duration: DurationComparison
    structure: StructuralComparison
    qualifications: tuple[DescriptorQualification, ...] = ()
    evidence: tuple[EvidenceReference, ...] = ()
    slice_index: int | None = None
    deployment: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    validation_status: str = "constructed"
    validation_errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "qualifications", tuple(self.qualifications))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "validation_errors", tuple(self.validation_errors))

    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True)
class ReviewView:
    view_id: str
    version: str
    baseline_set_id: str | None
    slice_index: int | None
    descriptor_ids: tuple[str, ...]
    sort_definition: str
    total_rankable: int
    full_population_count: int
    descriptors: tuple[ComparativeDescriptor, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "descriptor_ids", tuple(self.descriptor_ids))
        object.__setattr__(self, "descriptors", tuple(self.descriptors))

    def to_dict(self) -> dict[str, Any]:
        data = _json_value(self)
        # A view is a compact index; full descriptors remain in descriptors.jsonl.
        data.pop("descriptors", None)
        return data

    @property
    def ordered_descriptor_ids(self) -> tuple[str, ...]:
        return self.descriptor_ids


@dataclass(frozen=True)
class DescriptorCoverage:
    assignment_count: int
    descriptor_count: int
    unique_observation_count: int
    occurrence_count: int
    field_states: Mapping[str, Mapping[str, int]]
    structural_known_count: int
    structural_unknown_count: int
    slice_counts: Mapping[str, int]
    repeated_observation_count: int = 0
    unprocessed_count: int = 0
    inspection_status: str = "complete"
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "field_states", MappingProxyType({str(k): MappingProxyType(dict(v)) for k, v in self.field_states.items()}))
        object.__setattr__(self, "slice_counts", MappingProxyType(dict(self.slice_counts)))
        object.__setattr__(self, "reasons", tuple(self.reasons))

    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


@dataclass(frozen=True)
class ValidationResult:
    status: str
    descriptor_id: str
    baseline_set_id: str | None
    checked_evidence: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()
    work: Mapping[str, int] = None  # type: ignore[assignment]
    validator_version: str = "descriptor-validator-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "checked_evidence", tuple(self.checked_evidence))
        object.__setattr__(self, "failures", tuple(self.failures))
        object.__setattr__(self, "work", MappingProxyType(dict(self.work or {})))

    def to_dict(self) -> dict[str, Any]:
        return _json_value(self)


def field_from_dict(data: Mapping[str, Any] | FieldResult) -> FieldResult:
    if isinstance(data, FieldResult):
        return data
    evidence = tuple(EvidenceReference(**ref) if isinstance(ref, Mapping) else ref for ref in data.get("evidence", ()))
    return FieldResult(
        status=data.get("status", Availability.UNAVAILABLE.value),
        value=data.get("value"),
        unit=data.get("unit"),
        definition=data.get("definition"),
        reasons=tuple(data.get("reasons", ())),
        evidence=evidence,
        raw_value=data.get("raw_value"),
        raw_text=data.get("raw_text"),
    )


# Naming aliases used by adapters that describe the state dimension rather
# than the value envelope.
FieldAvailability = Availability
FieldOutcome = FieldResult
