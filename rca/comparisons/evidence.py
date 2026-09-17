"""Restricted semantic evidence validation for descriptor envelopes."""

from __future__ import annotations

from dataclasses import replace
import math
from typing import Any, Mapping

from .contracts import ComparativeDescriptor, EvidenceReference, FieldResult, ValidationResult


def _get(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _value(resolved: Any, selector: str | None = None) -> Any:
    if resolved is None:
        return None
    if selector:
        current = resolved
        for part in selector.replace("/", ".").split("."):
            if not part:
                continue
            current = _get(current, part, None)
        return current
    return _get(resolved, "value", resolved)


def _same_value(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    try:
        return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-12)
    except (TypeError, ValueError):
        return left == right


def _check_field(field: FieldResult, name: str, failures: list[str]) -> None:
    if field.status == "available":
        if field.value is None:
            failures.append(f"{name}:available_without_value")
        if isinstance(field.value, float) and not math.isfinite(field.value):
            failures.append(f"{name}:nonfinite_value")
    elif field.value is not None:
        failures.append(f"{name}:non_null_unavailable_value")
    if field.status in {"undefined", "unavailable"} and not field.reasons:
        failures.append(f"{name}:missing_reason")


def _resolve_reference(reference: EvidenceReference, resolver: Any) -> tuple[Any, str | None]:
    if resolver is None:
        return None, None
    method_name = "resolve_derived" if reference.kind in {"derived", "baseline", "statistic"} else "resolve_source"
    method = getattr(resolver, method_name, None)
    if method is None:
        return None, "resolver_missing_method"
    try:
        return method(reference), None
    except Exception as exc:  # resolvers are a trust boundary; report, don't leak details
        return None, f"resolver_error:{exc.__class__.__name__}"


def _check_reference(reference: EvidenceReference, resolver: Any, failures: list[str], checked: list[str]) -> None:
    key = reference.artifact_id or reference.source_id or str(reference.locator)
    checked.append(str(key))
    resolved, error = _resolve_reference(reference, resolver)
    if resolver is None:
        return
    if error:
        failures.append(f"evidence:{key}:{error}")
        return
    if resolved is None:
        failures.append(f"evidence:{key}:unresolved")
        return
    expected_entity = reference.entity_id
    if expected_entity is not None:
        actual_entity = _get(resolved, "entity_id", _get(resolved, "observation_id", _get(resolved, "baseline_id", None)))
        if actual_entity is not None and str(actual_entity) != str(expected_entity):
            failures.append(f"evidence:{key}:wrong_entity")
    if reference.selector:
        actual_selector = _get(resolved, "selector", _get(resolved, "field", _get(resolved, "statistic", None)))
        # A resolver may already return the selected value without metadata.
        if actual_selector is not None and str(actual_selector) != str(reference.selector):
            failures.append(f"evidence:{key}:wrong_selector")
    if reference.claimed_value is not None:
        actual = _value(resolved, reference.selector)
        if not _same_value(actual, reference.claimed_value):
            failures.append(f"evidence:{key}:claimed_value_mismatch")


def validate_descriptor(
    descriptor: ComparativeDescriptor,
    evidence_resolver: Any = None,
    validation_cache: Any = None,
) -> ValidationResult:
    """Validate arithmetic, availability and exact evidence references.

    This validator checks the descriptor that was constructed; it never
    selects a different baseline or repairs an unavailable field.  A cache is
    a caller-owned mapping and is keyed by immutable evidence identity.
    """
    failures: list[str] = []
    checked: list[str] = []
    duration = descriptor.duration
    for name in ("observed", "reference_median", "signed_excess", "ratio", "mad_departure", "ordering"):
        _check_field(getattr(duration, name), f"duration.{name}", failures)
    observed, median, excess = duration.observed, duration.reference_median, duration.signed_excess
    if excess.status == "available":
        if observed.status != "available" or median.status != "available":
            failures.append("duration:excess_without_operands")
        elif not _same_value(float(observed.value) - float(median.value), excess.value):
            failures.append("duration:excess_arithmetic_mismatch")
    if duration.ratio.status == "available":
        if median.status != "available" or float(median.value) <= 0:
            failures.append("duration:ratio_without_positive_median")
        elif not _same_value(float(observed.value) / float(median.value), duration.ratio.value):
            failures.append("duration:ratio_arithmetic_mismatch")
    if duration.mad_departure.status == "available":
        mad = duration.raw_mad.value if duration.raw_mad and duration.raw_mad.status == "available" else None
        if excess.status != "available" or mad is None or mad <= 0:
            failures.append("duration:mad_without_positive_mad")
        elif not _same_value(float(excess.value) / (1.4826 * float(mad)), duration.mad_departure.value):
            failures.append("duration:mad_arithmetic_mismatch")
    if duration.ordering.status == "available" and excess.status == "available":
        expected = "above_median" if excess.value > 0 else "below_median" if excess.value < 0 else "equal_to_median"
        if duration.ordering.value != expected:
            failures.append("duration:ordering_mismatch")
    structural = descriptor.structure
    if structural.query_state == "known":
        if structural.known_reference_count.status == "available":
            denominator = int(structural.known_reference_count.value)
            for pattern in structural.pattern_differences:
                if pattern.frequency.status == "available":
                    if denominator <= 0 or not _same_value(pattern.reference_count / denominator, pattern.frequency.value):
                        failures.append(f"structure:{pattern.pattern_id}:frequency_mismatch")
    for reference in descriptor.evidence:
        cache_key = (reference.kind, reference.snapshot_id, reference.artifact_id, reference.source_id, str(reference.locator), reference.selector)
        if validation_cache is not None and cache_key in validation_cache:
            cached = validation_cache[cache_key]
            if cached:
                failures.append(str(cached))
            checked.append(str(cache_key))
            continue
        before = len(failures)
        _check_reference(reference, evidence_resolver, failures, checked)
        if validation_cache is not None:
            validation_cache[cache_key] = failures[before] if len(failures) > before else None
    if failures:
        status = "failed"
    else:
        # This module checks arithmetic and pointer-level responses only.  The
        # producer's complete source/member/statistic graph is not yet exposed
        # through the narrow resolver, so no result is promoted to trusted
        # review status here.
        status = "unchecked"
        failures.append("semantic_evidence_validation_deferred")
    return ValidationResult(
        status=status,
        descriptor_id=descriptor.descriptor_id,
        baseline_set_id=descriptor.baseline_set_id,
        checked_evidence=tuple(checked),
        failures=tuple(failures),
        work={"evidence_references": len(descriptor.evidence), "distinct_validations": len(set(checked))},
    )


validate = validate_descriptor


__all__ = ["validate_descriptor", "validate"]
