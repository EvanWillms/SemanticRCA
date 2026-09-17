"""Read-only review and coverage projections over complete descriptors."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from .contracts import ComparativeDescriptor, DescriptorCoverage, ReviewView, content_id


def review_view(
    descriptors: Iterable[ComparativeDescriptor],
    baseline_set_id: str | None = None,
    slice_index: int | None = None,
    *,
    max_items: int = 5,
) -> ReviewView:
    """Return a deterministic compact view without dropping full outcomes.

    Ranking uses the unrounded signed excess in milliseconds.  Descriptors
    whose validation failed are rejected because a compact view must never
    turn failed evidence into trusted review material; freshly constructed
    descriptors are accepted for pure local workflows and can be revalidated
    before publication.
    """
    all_items = list(descriptors)
    scoped = [
        item for item in all_items
        if (baseline_set_id is None or item.baseline_set_id == baseline_set_id)
        and (slice_index is None or item.slice_index == slice_index)
    ]
    if not scoped:
        scope_set = baseline_set_id
    else:
        scope_set = baseline_set_id if baseline_set_id is not None else scoped[0].baseline_set_id
    definitions = {item.definition.to_dict().__repr__() for item in scoped}
    if len(definitions) > 1:
        raise ValueError("review view cannot mix comparison definitions")
    baseline_scopes = {item.baseline_set_id for item in scoped}
    if len(baseline_scopes) > 1:
        raise ValueError("review view cannot mix baseline sets")
    units = {
        (item.duration.observed.unit, item.duration.reference_median.unit)
        for item in scoped
        if item.duration.observed.status == "available" and item.duration.reference_median.status == "available"
    }
    if len(units) > 1:
        raise ValueError("review view cannot mix normalized units")
    candidates: list[ComparativeDescriptor] = []
    for item in scoped:
        if item.validation_status != "valid":
            raise ValueError(f"descriptor {item.descriptor_id} has not passed semantic validation")
        field = item.duration.signed_excess
        if field.status == "available" and isinstance(field.value, (int, float)) and field.value > 0:
            candidates.append(item)
    candidates.sort(key=lambda item: (
        -float(item.duration.signed_excess.value),
        item.deployment or "",
        item.trace_id or "",
        item.span_id or "",
        item.descriptor_id,
    ))
    limit = max(0, min(int(max_items), 5))
    selected = tuple(candidates[:limit])
    view_id = content_id("review", {
        "baseline_set_id": scope_set,
        "slice_index": slice_index,
        "descriptor_ids": tuple(item.descriptor_id for item in selected),
        "sort": "signed_excess_desc,deployment,trace_id,span_id,descriptor_id",
    })
    return ReviewView(
        view_id=view_id,
        version="review-view-v1",
        baseline_set_id=scope_set,
        slice_index=slice_index,
        descriptor_ids=tuple(item.descriptor_id for item in selected),
        sort_definition="signed_excess_desc,deployment,trace_id,span_id,descriptor_id",
        total_rankable=len(candidates),
        full_population_count=len(scoped),
        descriptors=selected,
    )


def _field_states(descriptors: list[ComparativeDescriptor]) -> dict[str, dict[str, int]]:
    names = {
        "observed": lambda item: item.duration.observed.status,
        "reference_median": lambda item: item.duration.reference_median.status,
        "signed_excess": lambda item: item.duration.signed_excess.status,
        "ratio": lambda item: item.duration.ratio.status,
        "mad_departure": lambda item: item.duration.mad_departure.status,
        "ordering": lambda item: item.duration.ordering.status,
    }
    output: dict[str, dict[str, int]] = {}
    for name, getter in names.items():
        counts = Counter(getter(item) for item in descriptors)
        output[name] = dict(sorted(counts.items()))
    return output


def summarize_occurrences(
    descriptors: Iterable[ComparativeDescriptor],
    assignment_index: Any = None,
    inspection_receipt: Any = None,
) -> DescriptorCoverage:
    """Reconcile descriptor, occurrence and structural denominators."""
    items = list(descriptors)
    observations = [item.observation_id for item in items]
    counts = Counter(observations)
    structure_known = sum(item.structure.query_state == "known" for item in items)
    structure_unknown = sum(item.structure.query_state != "known" for item in items)
    slices = Counter(str(item.slice_index) for item in items if item.slice_index is not None)
    expected_assignments = len(items)
    expected_occurrences: set[str] | None = None
    unprocessed = 0
    receipt_status = "complete"
    reasons: list[str] = []
    if inspection_receipt is not None:
        unprocessed = int(getattr(inspection_receipt, "unprocessed_count", getattr(inspection_receipt, "withheld_count", 0)) or 0)
        receipt_status = str(getattr(inspection_receipt, "status", getattr(inspection_receipt, "inspection_status", "complete")))
        reasons.extend(str(value) for value in (getattr(inspection_receipt, "reasons", ()) or ()))
    if assignment_index is not None and not isinstance(assignment_index, Mapping):
        assignments = getattr(assignment_index, "assignments", None)
        if assignments is not None:
            expected_assignments = len(assignments)
            expected_occurrences = {str(getattr(item, "occurrence_id", "")) for item in assignments}
        unresolved = getattr(assignment_index, "unresolved", ()) or ()
        unprocessed = max(unprocessed, len(unresolved))
        if getattr(assignment_index, "status", "complete") in {"partial", "incomplete"}:
            receipt_status = "partial"
    if isinstance(assignment_index, Mapping):
        expected_assignments = int(assignment_index.get("assignment_count", assignment_index.get("resolved_count", len(items))) or 0)
        expected_occurrences = {str(value) for value in assignment_index.get("occurrence_ids", ())}
        unprocessed = max(unprocessed, int(assignment_index.get("unprocessed_count", 0) or 0))
        if assignment_index.get("status") in {"partial", "incomplete"}:
            receipt_status = "partial"
    if expected_occurrences is not None:
        missing = expected_occurrences - {item.occurrence_id for item in items}
        unprocessed = max(unprocessed, len(missing))
    if expected_assignments != len(items):
        unprocessed = max(unprocessed, expected_assignments - len(items))
    if unprocessed:
        receipt_status = "partial"
        if "unprocessed_assignments" not in reasons:
            reasons.append("unprocessed_assignments")
    return DescriptorCoverage(
        assignment_count=expected_assignments,
        descriptor_count=len(items),
        unique_observation_count=len(set(observations)),
        occurrence_count=len(items),
        field_states=_field_states(items),
        structural_known_count=structure_known,
        structural_unknown_count=structure_unknown,
        slice_counts=dict(slices),
        repeated_observation_count=sum(count - 1 for count in counts.values() if count > 1),
        unprocessed_count=unprocessed,
        inspection_status=receipt_status,
        reasons=tuple(reasons),
    )


summarize = summarize_occurrences


__all__ = ["review_view", "summarize_occurrences", "summarize"]
