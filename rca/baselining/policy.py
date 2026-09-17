"""Frozen membership and query assignment kernels.

All functions here are pure: they read only the supplied observations,
snapshot identity and policy.  Extraction and prepared-source recovery belong
to the caller; a partial recovery receipt is carried through and never turned
into a complete reference population by these kernels.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime
from decimal import Decimal
from dataclasses import replace
import math
from typing import Any

from .contracts import (
    AssignmentBatch,
    BaselinePolicy,
    BaselineSet,
    ChildOccurrence,
    FrozenBaseline,
    MissingContext,
    Observation,
    ObservationBatch,
    ObservationIdentity,
    ReferenceCohort,
    RetrievalReceipt,
    SourceSnapshot,
    StructuralPattern,
    StructuralPopulation,
    QueryAssignment,
    UnresolvedQuery,
    coerce_observation,
    coerce_policy,
    content_id,
)
from .statistics import assess_center_stability, assess_support, compute_statistics


def _anchor_ms(value: float | int | datetime) -> float:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("anchor datetime must have an explicit timezone")
        return value.timestamp() * 1000.0
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("anchor must be finite")
    return result


def _snapshot(value: SourceSnapshot | Mapping[str, Any] | str, deployment: str | None = None) -> SourceSnapshot:
    if isinstance(value, SourceSnapshot):
        return value
    if isinstance(value, str):
        return SourceSnapshot(value, deployment or "")
    if not isinstance(value, Mapping):
        raise TypeError("snapshot must be SourceSnapshot or mapping")
    return SourceSnapshot(
        snapshot_id=str(value.get("snapshot_id", value.get("id", "snapshot"))),
        deployment=str(value.get("deployment", deployment or "")),
        parser_version=str(value.get("parser_version", "unknown")),
        extraction_version=str(value.get("extraction_version", "logical-span-dedup-v1")),
        status=str(value.get("status", "verified")),
        inventory_id=value.get("inventory_id"),
        unavailable_sources=tuple(str(item) for item in value.get("unavailable_sources", ())),
    )


def _materialize(value: ObservationBatch | Iterable[Observation | Mapping[str, Any]]) -> tuple[Observation, ...]:
    if isinstance(value, ObservationBatch):
        return tuple(value.observations)
    return tuple(coerce_observation(item) for item in value)


def _same_semantics(left: Observation, right: Observation) -> bool:
    """Compare duplicate records without source locator/order noise."""

    return (
        left.identity == right.identity
        and left.root_operation == right.root_operation
        and left.root_type == right.root_type
        and left.replica == right.replica
        and left.start_ms == right.start_ms
        and left.end_ms == right.end_ms
        and (
            left.measurement.raw_text, left.measurement.raw_unit,
            left.measurement.normalized_ms, left.measurement.normalization_id,
            left.measurement.available, left.measurement.reasons,
        ) == (
            right.measurement.raw_text, right.measurement.raw_unit,
            right.measurement.normalized_ms, right.measurement.normalization_id,
            right.measurement.available, right.measurement.reasons,
        )
        and left.children == right.children
        and left.structure_state == right.structure_state
        and left.completion_state == right.completion_state
    )


def _deduplicate(observations: Iterable[Observation]) -> tuple[tuple[Observation, ...], dict[str, tuple[str, ...]], set[str]]:
    grouped: dict[str, list[Observation]] = defaultdict(list)
    for observation in observations:
        grouped[observation.observation_id].append(observation)
    deduped: list[Observation] = []
    conflicts: set[str] = set()
    reasons: dict[str, tuple[str, ...]] = {}
    for observation_id, items in grouped.items():
        first = items[0]
        if any(not _same_semantics(first, item) for item in items[1:]):
            conflicts.add(observation_id)
            reasons[observation_id] = ("conflicting_duplicate",)
            # Keep one scoped record in the candidate population so the
            # conflict remains visible.  ``conflicts`` prevents it from
            # entering a member or structural denominator.
            deduped.append(replace(first, duplicate_count=len(items), conflict=True, completion_state="conflict"))
            continue
        locators = tuple(dict.fromkeys((*first.source_locators, *(locator for item in items[1:] for locator in item.source_locators))))
        deduped.append(replace(first, duplicate_count=len(items), source_locators=locators))
        if len(items) > 1:
            reasons[observation_id] = ("duplicate_collapsed",)
    return tuple(deduped), reasons, conflicts


def _completion_reason(observation: Observation, anchor_ms: float) -> str | None:
    endpoint = observation.endpoint_ms
    if observation.completion_state != "resolved" or endpoint is None:
        return "unresolved_completion"
    if endpoint >= anchor_ms:
        return "completion_boundary"
    return None


def _c0_sort_key(value: tuple[str, str]) -> tuple[str, str]:
    return value


def _policy_for_snapshot(policy: BaselinePolicy, snapshot: SourceSnapshot) -> BaselinePolicy:
    if policy.deployment is None:
        return BaselinePolicy(
            policy_id=policy.policy_id, version=policy.version, allowlist=policy.allowlist,
            deployment=snapshot.deployment, context=policy.context, lookback_ms=policy.lookback_ms,
            horizon_ms=policy.horizon_ms, slice_ms=policy.slice_ms, min_count=policy.min_count,
            min_occupied_bins=policy.min_occupied_bins, max_bin_fraction=policy.max_bin_fraction,
            block_ms=policy.block_ms, bootstrap_replicates=policy.bootstrap_replicates,
            bootstrap_seed=policy.bootstrap_seed, stability_width_fraction=policy.stability_width_fraction,
            estimator_id=policy.estimator_id, normalization_id=policy.normalization_id,
            no_fallback=policy.no_fallback,
        )
    if policy.deployment != snapshot.deployment:
        raise ValueError("policy deployment does not match snapshot deployment")
    return policy


def freeze_baselines(
    observation_batch: ObservationBatch | Iterable[Observation | Mapping[str, Any]],
    snapshot: SourceSnapshot | Mapping[str, Any] | str,
    anchor_ms: float | int | datetime,
    policy: BaselinePolicy | str | None = None,
) -> BaselineSet:
    """Freeze C1 duration baselines and C0 structural populations.

    Reference starts use the half-open interval ``[T-lookback, T)``.  Records
    with unresolved or boundary-crossing endpoints are retained only in audit
    exclusions; they never pad support.  Query records are ignored entirely
    so a late context cannot mutate the reference catalog.
    """

    source = _snapshot(snapshot)
    selected_policy = _policy_for_snapshot(coerce_policy(policy), source)
    anchor = _anchor_ms(anchor_ms)
    incoming = _materialize(observation_batch)
    observations, duplicate_reasons, conflicts = _deduplicate(incoming)
    interval_start = anchor - selected_policy.lookback_ms
    deployment = selected_policy.deployment or source.deployment

    # Candidates are scoped by start and deployment.  We keep all candidates
    # for C0/C1 audit denominators, while member selection is stricter.
    candidates = [
        item for item in observations
        if item.identity.snapshot_id == source.snapshot_id
        and item.identity.deployment == deployment
        and item.replica in selected_policy.allowlist
        and interval_start <= item.start_ms < anchor
    ]
    candidate_by_c0: dict[tuple[str, str], list[Observation]] = defaultdict(list)
    candidate_by_c1: dict[Any, list[Observation]] = defaultdict(list)
    for item in candidates:
        candidate_by_c0[item.c0_key].append(item)
        if item.c1_key is not None:
            candidate_by_c1[item.c1_key].append(item)

    eligible_by_c0: dict[tuple[str, str], list[Observation]] = defaultdict(list)
    members_by_c1: dict[Any, list[Observation]] = defaultdict(list)
    exclusions_by_c1: dict[Any, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for item in candidates:
        reasons: list[str] = []
        membership_reasons: list[str] = []
        if item.observation_id in conflicts:
            reasons.append("conflicting_duplicate")
            membership_reasons.append("conflicting_duplicate")
        completion_reason = _completion_reason(item, anchor)
        if completion_reason:
            reasons.append(completion_reason)
            membership_reasons.append(completion_reason)
        # C0 structural populations share only time/completion eligibility.
        # An invalid duration or incompatible unit excludes a C1 duration
        # member but must not erase known/unknown structural evidence.
        if not membership_reasons:
            eligible_by_c0[item.c0_key].append(item)
        if not item.measurement.available or item.measurement.normalized_ms is None:
            reasons.extend(item.measurement.reasons or ("invalid_measurement",))
        if item.measurement.normalization_id != selected_policy.normalization_id:
            reasons.append("unit_incompatible")
        if reasons:
            key = item.c1_key if item.c1_key is not None else ("unknown", item.c0_key)
            exclusions_by_c1[key][item.observation_id].extend(dict.fromkeys(reasons))
            continue
        if item.c1_key is not None:
            members_by_c1[item.c1_key].append(item)

    set_seed = {
        "snapshot_id": source.snapshot_id,
        "deployment": deployment,
        "anchor_ms": anchor,
        "policy": selected_policy.to_dict(),
        "members": {str(key): sorted(item.observation_id for item in values) for key, values in members_by_c1.items()},
    }
    set_id = content_id(set_seed, prefix="baseline-set-")

    structural: list[StructuralPopulation] = []
    for c0_key in sorted(candidate_by_c0, key=_c0_sort_key):
        c0_candidates = candidate_by_c0[c0_key]
        eligible = eligible_by_c0.get(c0_key, [])
        known = [item for item in eligible if item.structure_state == "known"]
        unknown = [item for item in eligible if item.structure_state != "known"]
        by_pattern: dict[Any, list[Observation]] = defaultdict(list)
        for item in known:
            by_pattern[item.c2_key].append(item)
        patterns: list[StructuralPattern] = []
        for c2_key, items in sorted(by_pattern.items(), key=lambda pair: repr(pair[0])):
            pattern_id = content_id((set_id, c0_key, c2_key), prefix="pattern-")
            denominator = len(known)
            patterns.append(StructuralPattern(
                pattern_id=pattern_id, c0_key=c0_key, c2_key=c2_key,
                member_ids=tuple(sorted(item.observation_id for item in items)),
                count=len(items), known_denominator=denominator,
                frequency=len(items) / denominator if denominator else None,
            ))
        population_id = content_id((set_id, c0_key, tuple(sorted(item.observation_id for item in eligible))), prefix="population-")
        structural.append(StructuralPopulation(
            population_id=population_id, set_id=set_id, c0_key=c0_key,
            candidate_ids=tuple(sorted(item.observation_id for item in c0_candidates)),
            eligible_ids=tuple(sorted(item.observation_id for item in eligible)),
            known_structure_count=len(known), unknown_structure_count=len(unknown),
            eligibility_unknown_count=len(c0_candidates) - len(eligible),
            excluded_count=len(c0_candidates) - len(eligible), patterns=tuple(patterns),
        ))

    baselines: list[FrozenBaseline] = []
    cohorts: list[ReferenceCohort] = []
    # Iterate every known C1 candidate, including cohorts whose members all
    # failed completion/measurement checks.  They remain visible as an
    # unavailable catalog outcome instead of disappearing from coverage.
    for c1_key in sorted(candidate_by_c1, key=repr):
        members = tuple(sorted(members_by_c1[c1_key], key=lambda item: (item.start_ms, item.observation_id)))
        candidate_items = candidate_by_c1.get(c1_key, [])
        candidate_ids = tuple(sorted(item.observation_id for item in candidate_items))
        member_ids = tuple(item.observation_id for item in members)
        cohort_id = content_id((set_id, c1_key), prefix="cohort-")
        membership_hash = content_id(member_ids, prefix="membership-")
        stats = compute_statistics(members, anchor_ms=anchor, lookback_ms=selected_policy.lookback_ms, block_ms=selected_policy.block_ms)
        support = assess_support(members, selected_policy)
        receipt_complete = True
        if isinstance(observation_batch, ObservationBatch):
            receipt_complete = observation_batch.selection_receipt.complete and (
                observation_batch.recovery_receipt is None or observation_batch.recovery_receipt.complete
            )
        if source.status != "verified":
            receipt_complete = False
        if not receipt_complete:
            support = replace(
                support,
                status="unavailable",
                reasons=tuple(dict.fromkeys((*support.reasons, "partial_selection" if source.status == "verified" else "incomplete_preparation"))),
            )
        stability = assess_center_stability(members, support, anchor_ms=anchor, policy=selected_policy)
        baseline_id = content_id((set_id, c1_key, membership_hash, selected_policy.estimator_id), prefix="baseline-")
        reasons_by_id: dict[str, tuple[str, ...]] = {}
        for item in candidate_items:
            if item.observation_id not in member_ids:
                values = exclusions_by_c1.get(c1_key, {}).get(item.observation_id)
                if values:
                    reasons_by_id[item.observation_id] = tuple(values)
        qualifications = (
            "health_unverified", "workload_equivalence_unverified", "replica_equivalence_unverified",
            "source_relative_availability", "provisional_units",
        )
        baselines.append(FrozenBaseline(
            baseline_id=baseline_id, cohort_id=cohort_id, set_id=set_id, c1_key=c1_key,
            membership_hash=membership_hash, member_ids=member_ids, statistics=stats,
            support=support, stability=stability, qualifications=qualifications,
            exclusion_reasons=tuple(sorted(reasons_by_id.items())),
            normalization_id=selected_policy.normalization_id,
        ))
        cohorts.append(ReferenceCohort(
            cohort_id=cohort_id, set_id=set_id, c1_key=c1_key,
            candidate_ids=candidate_ids, member_ids=member_ids,
            exclusion_ids=tuple(sorted(reasons_by_id)),
        ))

    receipt = observation_batch.selection_receipt if isinstance(observation_batch, ObservationBatch) else RetrievalReceipt(
        selected_count=len(incoming), resolved_count=len(observations), unresolved_count=len(incoming) - len(observations),
        scanned_records=len(incoming), recovered_records=len(observations), status="complete",
    )
    status_reasons: list[str] = []
    if source.status != "verified":
        status_reasons.append("incomplete_preparation")
    if not receipt.complete:
        status_reasons.append("partial_selection")
    return BaselineSet(
        set_id=set_id, snapshot_id=source.snapshot_id, deployment=deployment,
        anchor_ms=anchor, policy=selected_policy, baselines=tuple(baselines),
        structural_populations=tuple(structural), cohorts=tuple(cohorts),
        selection_receipt=receipt, extraction_version=source.extraction_version,
        status="completed" if not status_reasons else "partial", reasons=tuple(status_reasons),
    )


def assign_queries(
    observations: ObservationBatch | Iterable[Observation | Mapping[str, Any]],
    baseline_set: BaselineSet,
) -> AssignmentBatch:
    """Assign each in-horizon query occurrence to frozen catalog outcomes."""

    materialized = _materialize(observations)
    seen: dict[str, Observation] = {}
    unresolved: list[UnresolvedQuery] = []
    assignments: list[QueryAssignment] = []
    start = baseline_set.anchor_ms
    end = baseline_set.horizon_end_ms
    for item in materialized:
        if item.observation_id in seen:
            if not _same_semantics(seen[item.observation_id], item):
                unresolved.append(UnresolvedQuery(item.observation_id, "conflicting_duplicate", raw_id=item.raw_id))
            else:
                unresolved.append(UnresolvedQuery(item.observation_id, "duplicate_collapsed", raw_id=item.raw_id))
            continue
        seen[item.observation_id] = item
        # The caller may pass one combined recovered batch.  Reference-window
        # records are source material for the frozen set, not unresolved query
        # occurrences, so exclude them from the query denominator.
        if item.start_ms < start:
            continue
        if item.identity.snapshot_id != baseline_set.snapshot_id:
            unresolved.append(UnresolvedQuery(item.observation_id, "snapshot_changed", raw_id=item.raw_id))
            continue
        if item.identity.deployment != baseline_set.deployment or item.replica not in baseline_set.policy.allowlist:
            unresolved.append(UnresolvedQuery(item.observation_id, "out_of_scope", raw_id=item.raw_id))
            continue
        if not start <= item.start_ms < end:
            unresolved.append(UnresolvedQuery(item.observation_id, "outside_horizon", raw_id=item.raw_id))
            continue
        slice_index = int((Decimal(str(item.start_ms)) - Decimal(str(start)))
                          // baseline_set.policy.slice_ms)
        c1 = baseline_set.baseline_for(item.c1_key) if item.c1_key is not None else None
        c0 = baseline_set.population_for(item.c0_key)
        baseline_outcome: FrozenBaseline | MissingContext
        if c1 is None:
            reasons = ("unknown_structure",) if item.c1_key is None else ("missing_context",)
            baseline_outcome = MissingContext(baseline_set.set_id, "C1_duration", item.c1_key, reasons)
        else:
            reasons = list(c1.support.reasons)
            baseline_outcome = c1
        if c0 is None:
            structural_outcome: StructuralPopulation | MissingContext = MissingContext(
                baseline_set.set_id, "C0_structure", item.c0_key, ("missing_context",)
            )
        else:
            structural_outcome = c0
        comparison_reasons: list[str] = []
        if isinstance(baseline_outcome, MissingContext):
            comparison_reasons.extend(baseline_outcome.reasons)
        elif not baseline_outcome.supported:
            comparison_reasons.extend(baseline_outcome.support.reasons)
        if not item.measurement.available or item.measurement.normalized_ms is None:
            comparison_reasons.extend(item.measurement.reasons or ("invalid_measurement",))
        elif item.measurement.normalization_id != baseline_set.policy.normalization_id:
            comparison_reasons.append("unit_incompatible")
        eligible = isinstance(baseline_outcome, FrozenBaseline) and baseline_outcome.supported and not comparison_reasons
        occurrence_id = content_id((baseline_set.set_id, slice_index, item.observation_id), prefix="occurrence-")
        assignments.append(QueryAssignment(
            occurrence_id=occurrence_id, observation_id=item.observation_id,
            set_id=baseline_set.set_id, slice_index=slice_index,
            baseline=baseline_outcome, structural_population=structural_outcome,
            qualification="qualified" if eligible else "unavailable",
            reasons=tuple(dict.fromkeys(comparison_reasons)),
            duration_comparison_eligible=eligible, observation=item,
        ))
    assignments.sort(key=lambda item: (item.slice_index, item.observation_id))
    unresolved.sort(key=lambda item: (item.slice_index if item.slice_index is not None else 999, item.observation_id or ""))
    return AssignmentBatch(tuple(assignments), tuple(unresolved))


def missing_context(baseline_set: BaselineSet, lookup_kind: str, context_key: Any, *reasons: str) -> MissingContext:
    """Small public constructor for consumers that need typed absent outcomes."""

    return MissingContext(baseline_set.set_id, lookup_kind, context_key, tuple(reasons) or ("missing_context",))
