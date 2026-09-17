"""Pure construction of comparative descriptor envelopes."""

from __future__ import annotations

from collections import Counter
import math
import json
from typing import Any, Iterable, Mapping

from .contracts import (
    Availability,
    ComparativeDescriptor,
    ComparisonDefinition,
    DescriptorQualification,
    DurationComparison,
    EvidenceReference,
    FieldResult,
    PatternDifference,
    StructuralComparison,
    content_id,
)


_MISSING = object()


def get(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def first(value: Any, names: Iterable[str], default: Any = None) -> Any:
    for name in names:
        found = get(value, name, _MISSING)
        if found is not _MISSING and found is not None:
            return found
    return default


def _tuple(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    return tuple(value)


def _evidence(value: Any) -> tuple[EvidenceReference, ...]:
    values: list[Any] = []
    direct = first(value, ("evidence", "evidence_refs", "evidence_references"))
    if direct:
        values.extend(_tuple(direct))
    locator = first(value, ("source_locator", "locator"))
    if locator is not None and not direct:
        values.append(locator)
    output: list[EvidenceReference] = []
    for item in values:
        if isinstance(item, EvidenceReference):
            output.append(item)
        elif isinstance(item, Mapping):
            allowed = {key: item[key] for key in EvidenceReference.__dataclass_fields__ if key in item}
            output.append(EvidenceReference(**allowed))
        else:
            output.append(EvidenceReference(locator=item))
    return tuple(output)


def _definition(value: ComparisonDefinition | Mapping[str, Any] | None) -> ComparisonDefinition:
    if value is None:
        return ComparisonDefinition()
    if isinstance(value, ComparisonDefinition):
        return value
    allowed = {key: value[key] for key in ComparisonDefinition.__dataclass_fields__ if key in value}
    return ComparisonDefinition(**allowed)


def _raw_measurement(observation: Any) -> Any:
    return first(observation, ("measurement", "duration", "duration_measurement"), observation)


def _duration_value(observation: Any) -> tuple[float | None, str | None, str | None, Any]:
    measurement = _raw_measurement(observation)
    normalized = first(measurement, ("normalized_ms", "value_ms", "duration_ms"))
    if normalized is None and isinstance(measurement, (int, float)):
        normalized = measurement
    raw_text = first(measurement, ("raw_text", "raw_value", "text"))
    unit = first(measurement, ("unit", "raw_unit", "declared_unit"))
    normalization = first(measurement, ("normalization_id", "normalization", "unit_definition"))
    if normalized is not None:
        try:
            normalized = float(normalized)
        except (TypeError, ValueError):
            normalized = None
    return normalized, unit, normalization, raw_text


def _numeric(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _units_compatible(observation: Any, baseline: Any, measurement: Any) -> bool:
    obs_unit = first(measurement, ("unit", "raw_unit", "declared_unit"))
    stats = first(baseline, ("statistics", "stats"), baseline)
    ref_unit = first(stats, ("unit", "normalized_unit", "declared_unit"))
    def norm(unit: Any) -> str | None:
        if unit is None:
            return None
        text = str(unit).strip().lower().replace("milliseconds", "ms").replace("millisecond", "ms")
        if text in {"ms", "msec", "millis", "milliseconds"}:
            return "ms"
        if text in {"s", "sec", "second", "seconds"}:
            return "s"
        return text
    left, right = norm(obs_unit), norm(ref_unit)
    obs_norm = first(measurement, ("normalization_id", "normalization"))
    ref_norm = first(stats, ("normalization_id", "normalization"))
    if ref_norm is None:
        ref_norm = first(baseline, ("normalization_id", "normalization"))
    if ref_norm is None:
        policy = first(baseline, ("policy",))
        ref_norm = first(policy, ("normalization_id", "normalization"))
    if ref_norm is not None:
        return obs_norm is not None and str(obs_norm) == str(ref_norm)
    # The display unit is the producer's raw unit (the fixture uses us), while
    # the normalized comparison unit is carried by normalization_id.  A
    # declared duration-ms-v1 conversion is therefore compatible with an ms
    # statistic even when the raw display units differ.
    if obs_norm is not None and str(obs_norm) == "duration-ms-v1" and right in {None, "ms"}:
        return True
    if left is not None and right is not None:
        return left == right
    # A producer that has already normalized both values to ms can omit the
    # display unit.  An unknown explicit unit does not qualify.
    if left is None and right is None:
        return True
    if left is None:
        return obs_norm is not None and str(obs_norm) == "duration-ms-v1"
    if right is None:
        return obs_norm is not None and str(obs_norm) == "duration-ms-v1"
    return False


def _support_state(baseline: Any) -> tuple[bool, str]:
    if baseline is None:
        return False, "missing_reference"
    class_name = type(baseline).__name__.lower()
    status = str(first(baseline, ("status", "availability", "comparison_status"), "")).lower()
    if "missingcontext" in class_name or status in {"unavailable", "missing", "unsupported"}:
        reason = first(baseline, ("reason", "reason_code"), "unsupported_reference")
        reasons = get(baseline, "reasons", ())
        if reasons:
            reason = str(tuple(reasons)[0])
        return False, str(reason)
    support = first(baseline, ("support", "support_assessment"))
    if support is not None:
        support_status = str(first(support, ("status", "state"), "")).lower()
        if support_status in {"unavailable", "unsupported", "failed", "missing"}:
            return False, str(first(support, ("reason", "reasons"), "unsupported_reference"))
        available = first(support, ("available", "supported"), None)
        if available is False:
            return False, "unsupported_reference"
    eligible = first(baseline, ("comparison_eligible", "eligible"), None)
    if eligible is False:
        return False, str(first(baseline, ("eligibility_reason", "reason"), "unsupported_reference"))
    return True, ""


def _baseline_stats(baseline: Any) -> Any:
    return first(baseline, ("statistics", "stats"), baseline)


def _baseline_id(baseline: Any) -> str | None:
    value = first(baseline, ("baseline_id", "id", "outcome_id"))
    return str(value) if value is not None else None


def _label_for(excess: float | None) -> FieldResult:
    if excess is None:
        return FieldResult.unavailable("excess_unavailable", definition="ordering-v1")
    if excess > 0:
        label = "above_median"
    elif excess < 0:
        label = "below_median"
    else:
        label = "equal_to_median"
    return FieldResult.available(label, definition="ordering-v1")


def _qualifications(observation: Any, baseline: Any) -> tuple[DescriptorQualification, ...]:
    result: list[DescriptorQualification] = []
    seen: set[tuple[str, str]] = set()
    for source, scope in ((baseline, "baseline"), (observation, "observation")):
        for value in _tuple(first(source, ("qualifications", "qualification"), ())):
            if isinstance(value, DescriptorQualification):
                item = value
            elif isinstance(value, Mapping):
                allowed = {key: value[key] for key in DescriptorQualification.__dataclass_fields__ if key in value}
                item = DescriptorQualification(**allowed)
            else:
                item = DescriptorQualification(code=str(value), scope=scope)
            key = (item.scope, item.code)
            if key not in seen:
                result.append(item)
                seen.add(key)
    support = first(baseline, ("support", "support_assessment"))
    if support is not None:
        code = str(first(support, ("status", "state"), "support_unavailable"))
        key = ("baseline", f"support:{code}")
        if key not in seen:
            result.append(DescriptorQualification(f"support:{code}", scope="baseline", evidence=_evidence(support)))
            seen.add(key)
    stability = first(baseline, ("stability", "center_stability", "stability_assessment"))
    if stability is not None:
        code = str(first(stability, ("state", "status"), "not_assessed"))
        key = ("baseline", f"stability:{code}")
        if key not in seen:
            result.append(DescriptorQualification(f"stability:{code}", scope="baseline", evidence=_evidence(stability)))
    # These statements are deliberate qualifications, never health labels.
    for code in ("health_unverified", "workload_equivalence_unverified", "replica_equivalence_unverified"):
        key = ("assumption", code)
        if key not in seen:
            result.append(DescriptorQualification(code, scope="assumption", unverified=True))
    return tuple(result)


def _pattern_key(value: Any) -> dict[str, int]:
    """Normalize a C1 child multiset into stable string keys and counts."""
    if value is None:
        return {}
    if isinstance(value, Mapping):
        output: Counter[str] = Counter()
        for key, count in value.items():
            if isinstance(key, (tuple, list)):
                key = json.dumps([str(part) for part in key], separators=(",", ":"))
            output[str(key)] += int(count)
        return dict(sorted(output.items()))
    output: Counter[str] = Counter()
    for child in value:
        if isinstance(child, Mapping):
            operation = first(child, ("operation", "name", "raw_operation"), "")
            type_name = first(child, ("type", "raw_type"), "")
            key = json.dumps([str(operation), str(type_name)], separators=(",", ":"))
            count = int(first(child, ("count", "multiplicity"), 1))
        elif hasattr(child, "operation") and hasattr(child, "type"):
            operation = str(getattr(child, "operation"))
            type_name = str(getattr(child, "type"))
            key = json.dumps([operation, type_name], separators=(",", ":"))
            count = int(getattr(child, "count", 1))
        elif isinstance(child, (tuple, list)):
            key = json.dumps([str(part) for part in child[:2]], separators=(",", ":"))
            count = int(child[2]) if len(child) > 2 else 1
        else:
            key, count = str(child), 1
        output[key] += count
    return dict(sorted(output.items()))


def _query_structure(observation: Any) -> tuple[str, dict[str, int]]:
    state = first(observation, ("structure_state", "c1_state", "child_structure_state"))
    raw = first(observation, ("child_pairs", "children", "c1", "child_structure", "c1_key"), _MISSING)
    if state is not None:
        state = str(state).lower()
        if state in {"unknown", "unknown_structure", "unavailable", "excluded"}:
            return "unknown", {}
    if raw is _MISSING or raw is None:
        return "unknown", {}
    return "known", _pattern_key(raw)


def _population_patterns(population: Any) -> tuple[Any, ...]:
    patterns = first(population, ("patterns", "reference_patterns", "structural_patterns"), ())
    if isinstance(patterns, Mapping):
        result: list[Any] = []
        for key, value in patterns.items():
            if isinstance(value, Mapping):
                item = dict(value)
                item.setdefault("pattern_id", key)
                result.append(item)
            else:
                result.append({"pattern_id": key, "members": value})
        return tuple(result)
    return _tuple(patterns)


def _structural(observation: Any, assignment: Any, population: Any) -> StructuralComparison:
    state, query = _query_structure(observation)
    population_id = first(population, ("population_id", "c0_population_id", "id"))
    if population is None:
        unavailable = FieldResult.unavailable("missing_structural_population")
        return StructuralComparison(
            query_state=state,
            c0_population_id=str(population_id) if population_id else None,
            known_reference_count=unavailable,
            unknown_reference_count=unavailable,
            pattern_differences=(),
            matching_pattern_count=unavailable,
            absent_from_reference=unavailable,
            query_pattern=query,
            reasons=("missing_structural_population",),
        )
    known = first(population, ("known_structure_count", "known_count", "known_denominator"), None)
    unknown = first(population, ("unknown_structure_count", "unknown_count"), 0)
    if known is None:
        known = sum(int(first(item, ("count", "frequency_count"), 0)) for item in _population_patterns(population))
    known_num = _numeric(known)
    unknown_num = _numeric(unknown)
    known_field = FieldResult.available(int(known_num)) if known_num is not None and known_num >= 0 else FieldResult.unavailable("known_denominator_unavailable")
    unknown_field = FieldResult.available(int(unknown_num)) if unknown_num is not None and unknown_num >= 0 else FieldResult.unavailable("unknown_count_unavailable")
    if state != "known":
        return StructuralComparison(
            query_state="unknown",
            c0_population_id=str(population_id) if population_id else None,
            known_reference_count=known_field,
            unknown_reference_count=unknown_field,
            pattern_differences=(),
            matching_pattern_count=FieldResult.unavailable("query_structure_unknown"),
            absent_from_reference=FieldResult.unavailable("query_structure_unknown"),
            query_pattern=None,
            reasons=("query_structure_unknown",),
        )
    patterns: list[PatternDifference] = []
    matches = 0
    known_denominator = int(known_num or 0)
    for raw in _population_patterns(population):
        pattern_id = str(first(raw, ("pattern_id", "id"), content_id("pattern", raw)))
        members = first(raw, ("members", "pattern", "child_pairs", "counts", "c2_key"), {})
        reference = _pattern_key(members)
        deltas = {key: query.get(key, 0) - reference.get(key, 0) for key in set(query) | set(reference)}
        deltas = {key: value for key, value in sorted(deltas.items()) if value}
        if not deltas:
            matches += 1
        count = int(first(raw, ("count", "frequency_count", "member_count"), 0) or 0)
        frequency = FieldResult.available(count / known_denominator) if known_denominator > 0 else FieldResult.unavailable("zero_known_denominator")
        additions = {key: value for key, value in deltas.items() if value > 0}
        removals = {key: -value for key, value in deltas.items() if value < 0}
        patterns.append(PatternDifference(
            pattern_id=pattern_id,
            reference_count=count,
            known_denominator=known_denominator,
            frequency=frequency,
            count_deltas=deltas,
            additions=additions,
            removals=removals,
            member_evidence=_evidence(raw),
        ))
    matching = FieldResult.available(matches) if known_denominator > 0 else FieldResult.unavailable("zero_known_denominator")
    absent = FieldResult.available(matches == 0) if known_denominator > 0 else FieldResult.unavailable("zero_known_denominator")
    return StructuralComparison(
        query_state="known",
        c0_population_id=str(population_id) if population_id else None,
        known_reference_count=known_field,
        unknown_reference_count=unknown_field,
        pattern_differences=tuple(patterns),
        matching_pattern_count=matching,
        absent_from_reference=absent,
        query_pattern=query,
    )


def describe(
    observation: Any,
    assignment: Any = None,
    baseline_outcome: Any = None,
    structural_population: Any = None,
    definition: ComparisonDefinition | Mapping[str, Any] | None = None,
    *,
    diagnostics: Iterable[str] | None = None,
) -> ComparativeDescriptor:
    """Construct one complete descriptor without source reads or reselection.

    ``observation``, ``assignment`` and producer values may be frozen dataclass
    instances or mappings.  The assignment is intentionally only consulted for
    identity and references; the function never changes membership.
    """
    definition_obj = _definition(definition)
    if diagnostics is not None:
        definition_obj = ComparisonDefinition(
            definition_id=definition_obj.definition_id,
            version=definition_obj.version,
            measurement_family=definition_obj.measurement_family,
            arithmetic_version=definition_obj.arithmetic_version,
            diagnostics=tuple(diagnostics),
            mad_definition=definition_obj.mad_definition,
            label_version=definition_obj.label_version,
        )
    assignment = assignment or {}
    baseline = baseline_outcome
    if baseline is None:
        baseline = first(assignment, ("baseline", "baseline_outcome", "duration_baseline", "c1_baseline"))
    if structural_population is None:
        structural_population = first(assignment, ("structural_population", "c0_population", "structure"))
    normalized, unit, normalization, raw_text = _duration_value(observation)
    measurement = _raw_measurement(observation)
    observation_evidence = _evidence(measurement) or _evidence(observation)
    # ``unit`` on a FieldResult is the normalized comparison unit.  Preserve
    # the producer's raw unit on the measurement evidence instead of exposing
    # microseconds as if the normalized value were still in microseconds.
    obs_kwargs = {"unit": "ms", "definition": normalization or "duration-normalization-v1", "evidence": observation_evidence, "raw_value": raw_text, "raw_text": str(raw_text) if raw_text is not None else None}
    if normalized is None or not math.isfinite(normalized) or normalized < 0:
        observed_field = FieldResult.unavailable("invalid_measurement", **obs_kwargs)
    else:
        observed_field = FieldResult.available(normalized, **obs_kwargs)
    supported, support_reason = _support_state(baseline)
    stats = _baseline_stats(baseline)
    median = _numeric(first(stats, ("median", "reference_median"), None))
    units_ok = _units_compatible(observation, baseline, measurement)
    baseline_evidence = _evidence(stats) or _evidence(baseline)
    if not supported:
        median_field = FieldResult.unavailable(support_reason, unit="ms", evidence=baseline_evidence)
    elif median is None or median < 0:
        median_field = FieldResult.unavailable("reference_median_unavailable", unit="ms", evidence=baseline_evidence)
    elif not units_ok:
        median_field = FieldResult.unavailable("incompatible_units", unit="ms", evidence=baseline_evidence)
    else:
        median_field = FieldResult.available(median, unit="ms", evidence=baseline_evidence)
    excess: float | None = None
    if observed_field.status == Availability.AVAILABLE.value and median_field.status == Availability.AVAILABLE.value:
        excess = float(observed_field.value) - float(median_field.value)
        excess_field = FieldResult.available(excess, unit="ms", definition=definition_obj.arithmetic_version, evidence=observation_evidence + baseline_evidence)
    else:
        excess_field = FieldResult.unavailable("comparison_unavailable", unit="ms", definition=definition_obj.arithmetic_version, evidence=observation_evidence + baseline_evidence)
    if "ratio" in definition_obj.diagnostics:
        if excess is None:
            ratio_field = FieldResult.unavailable("comparison_unavailable")
        elif median is not None and median <= 0:
            ratio_field = FieldResult.undefined("nonpositive_reference_median", definition="ratio-v1")
        else:
            ratio_field = FieldResult.available(float(observed_field.value) / median, definition="ratio-v1")
    else:
        ratio_field = FieldResult.not_requested()
    raw_mad = _numeric(first(stats, ("raw_mad", "mad", "median_absolute_deviation"), None))
    if "mad" in definition_obj.diagnostics:
        if excess is None:
            mad_field = FieldResult.unavailable("comparison_unavailable", definition=definition_obj.mad_definition)
        elif raw_mad is None or raw_mad <= 0:
            mad_field = FieldResult.undefined("nonpositive_raw_mad", definition=definition_obj.mad_definition)
        else:
            mad_field = FieldResult.available(excess / (1.4826 * raw_mad), definition=definition_obj.mad_definition)
    else:
        mad_field = FieldResult.not_requested()
    raw_mad_field = FieldResult.available(raw_mad, unit="ms", definition="raw-mad-v1") if raw_mad is not None and raw_mad >= 0 else FieldResult.unavailable("raw_mad_unavailable")
    duration = DurationComparison(
        observed=observed_field,
        reference_median=median_field,
        signed_excess=excess_field,
        ratio=ratio_field,
        mad_departure=mad_field,
        ordering=_label_for(excess),
        baseline_id=_baseline_id(baseline),
        raw_mad=raw_mad_field,
    )
    structure = _structural(observation, assignment, structural_population)
    occurrence_id = str(first(assignment, ("occurrence_id", "id"), first(observation, ("occurrence_id",), "occurrence-unknown")))
    observation_id = str(first(assignment, ("observation_id",), first(observation, ("observation_id", "id"), occurrence_id)))
    set_id = first(assignment, ("baseline_set_id", "set_id"), first(baseline, ("set_id", "baseline_set_id")))
    slice_index = first(assignment, ("slice_index", "query_slice"))
    identity = first(observation, ("identity",), None)
    deployment = first(observation, ("deployment", "service"), first(identity, ("deployment",), first(assignment, ("deployment",))))
    trace_id = first(observation, ("trace_id",), first(identity, ("trace_id",), None))
    if trace_id is not None and not isinstance(trace_id, (str, int)):
        trace_id = first(trace_id, ("trace_id", "id"))
    span_id = first(observation, ("root_span_id", "span_id"), first(identity, ("root_span_id",), None))
    qualifications = _qualifications(observation, baseline)
    all_evidence = observation_evidence + baseline_evidence + _evidence(assignment) + _evidence(structural_population)
    identity_payload = {
        "occurrence_id": occurrence_id,
        "observation_id": observation_id,
        "baseline_set_id": set_id,
        "definition": definition_obj,
        "duration": duration,
        "structure": structure,
        "qualifications": qualifications,
        "evidence": all_evidence,
    }
    descriptor_id = content_id("descriptor", identity_payload)
    return ComparativeDescriptor(
        descriptor_id=descriptor_id,
        schema_version="comparative-descriptor-bundle-v1",
        occurrence_id=occurrence_id,
        observation_id=observation_id,
        baseline_set_id=str(set_id) if set_id is not None else None,
        definition=definition_obj,
        duration=duration,
        structure=structure,
        qualifications=qualifications,
        evidence=all_evidence,
        slice_index=int(slice_index) if slice_index is not None else None,
        deployment=str(deployment) if deployment is not None else None,
        trace_id=str(trace_id) if trace_id is not None else None,
        span_id=str(span_id) if span_id is not None else None,
    )


__all__ = ["describe", "get"]
