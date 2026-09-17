"""Small, bounded completion-aware RCA investigation controller.

The controller deliberately works on detached JSON-shaped values.  Evidence is
owned by the controller after entry; injected callbacks only see copies of the
current state and their returned evidence is merged through one validation
boundary.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Callable, Mapping


_DEFAULT_WORK_POLICY = {
    "max_assessments": 4,
    "max_operations": 3,
    "max_non_progress": 2,
}
_DECISIONS = {"complete", "continue", "blocked"}


def _copy(value: Any) -> Any:
    return deepcopy(value)


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, OverflowError):
        return repr(value)


def _error(code: str, detail: Any = None) -> dict[str, Any]:
    result: dict[str, Any] = {"code": code}
    if detail is not None:
        result["detail"] = _copy(detail)
    return result


def _scope(evidence: Mapping[str, Any]) -> Mapping[str, Any]:
    value = evidence.get("scope")
    return value if isinstance(value, Mapping) else {}


def _projection(scope: Mapping[str, Any]) -> list[str]:
    value = scope.get("projection", [])
    return list(value) if isinstance(value, list) else []


def _field_name(name: str) -> str:
    if name in {"occurrence_datetime", "occurrence_time", "time"}:
        return "occurrence_time"
    return name


def _incident_value(incident: Mapping[str, Any], field: str) -> Any:
    if field in incident:
        return incident[field]
    if _field_name(field) == "occurrence_time":
        return incident.get("occurrence_datetime", incident.get("time"))
    return None


def _validate_scope(scope: Any) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not isinstance(scope, Mapping):
        return [_error("invalid_scope")]
    if not isinstance(scope.get("case_id"), str) or not scope["case_id"]:
        errors.append(_error("invalid_case_id"))
    if not isinstance(scope.get("deployment"), str) or not scope["deployment"]:
        errors.append(_error("invalid_deployment"))
    if not isinstance(scope.get("incident_count"), int) or isinstance(scope["incident_count"], bool) or scope["incident_count"] < 1:
        errors.append(_error("invalid_incident_count"))
    projection = scope.get("projection")
    if not isinstance(projection, list) or not projection or any(not isinstance(item, str) for item in projection):
        errors.append(_error("invalid_projection"))
    return errors


def _validate_packet(packet: Any, *, require_scope: bool = True) -> list[dict[str, Any]]:
    if not isinstance(packet, Mapping):
        return [_error("invalid_evidence_packet")]
    errors: list[dict[str, Any]] = []
    if packet.get("schema_version") != "rca-evidence-v1":
        errors.append(_error("unsupported_evidence_schema"))
    if require_scope:
        errors.extend(_validate_scope(packet.get("scope")))
    revision = packet.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        errors.append(_error("invalid_evidence_revision"))
    if not isinstance(packet.get("observations"), Mapping):
        errors.append(_error("invalid_observations"))
    else:
        deployment = packet.get("scope", {}).get("deployment") if isinstance(packet.get("scope"), Mapping) else None
        for key, observation in packet["observations"].items():
            if not isinstance(key, str) or not isinstance(observation, Mapping):
                errors.append(_error("invalid_observation", key))
                continue
            if observation.get("evidence_id") != key:
                errors.append(_error("observation_id_mismatch", key))
            if observation.get("deployment") != deployment:
                errors.append(_error("observation_outside_scope", key))
    for collection_name in ("coverage", "qualifications", "definitions"):
        if not isinstance(packet.get(collection_name), list):
            errors.append(_error(f"invalid_{collection_name}"))
    return errors


def _validate_policy(policy: Any) -> list[dict[str, Any]]:
    if not isinstance(policy, Mapping):
        return [_error("invalid_answer_policy")]
    errors: list[dict[str, Any]] = []
    for name in ("components", "reasons"):
        values = policy.get(name)
        if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
            errors.append(_error(f"invalid_{name}_vocabulary"))
    return errors


def _normalise_work_policy(policy: Any) -> dict[str, Any]:
    result = dict(_DEFAULT_WORK_POLICY)
    if policy is not None:
        if not isinstance(policy, Mapping):
            raise ValueError("work_policy must be a mapping")
        for key, value in policy.items():
            result[key] = _copy(value)
    for name in ("max_assessments", "max_operations", "max_non_progress"):
        if not isinstance(result[name], int) or isinstance(result[name], bool) or result[name] < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    return result


def _observation_lookup(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    observations = packet.get("observations", {})
    if not isinstance(observations, Mapping):
        return result
    for key, observation in observations.items():
        if not isinstance(observation, Mapping):
            continue
        if isinstance(key, str):
            result[key] = observation
        evidence_id = observation.get("evidence_id")
        if isinstance(evidence_id, str):
            result[evidence_id] = observation
    return result


def _normalise_incidents(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            result.append(_copy(dict(item)))
    return result


def _assessment_errors(
    assessment: Any,
    packet: Mapping[str, Any],
    answer_policy: Mapping[str, Any],
    operations: Mapping[str, Callable[..., Any]],
) -> list[dict[str, Any]]:
    if not isinstance(assessment, Mapping):
        return [_error("malformed_assessment")]
    errors: list[dict[str, Any]] = []
    decision = assessment.get("decision")
    if decision not in _DECISIONS:
        errors.append(_error("invalid_decision"))
    if assessment.get("evidence_revision") != packet.get("revision"):
        errors.append(_error("stale_evidence_revision"))
    incidents = assessment.get("incidents")
    if not isinstance(incidents, list):
        errors.append(_error("invalid_incidents"))
        incidents = []
    gaps = assessment.get("gaps")
    if not isinstance(gaps, list) or any(not isinstance(gap, str) or not gap for gap in gaps):
        errors.append(_error("invalid_gaps"))
        gaps = []
    lookup = _observation_lookup(packet)
    scope = _scope(packet)
    requested = _projection(scope)
    for index, incident in enumerate(incidents):
        if not isinstance(incident, Mapping):
            errors.append(_error("invalid_incident", index))
            continue
        support = incident.get("support")
        if support is not None and (not isinstance(support, list) or any(not isinstance(item, str) for item in support)):
            errors.append(_error("invalid_support", index))
            support = []
        if decision == "complete":
            if not isinstance(incident.get("explanation"), str) or not incident["explanation"].strip():
                errors.append(_error("missing_explanation", index))
            if not support:
                errors.append(_error("missing_support", index))
            for evidence_id in support or []:
                observation = lookup.get(evidence_id)
                if observation is None:
                    errors.append(_error("unknown_support", {"incident": index, "evidence_id": evidence_id}))
                elif observation.get("conflict") is True:
                    errors.append(_error("conflicted_support", {"incident": index, "evidence_id": evidence_id}))
            for field in requested:
                value = _incident_value(incident, field)
                if not isinstance(value, str) or not value:
                    errors.append(_error("missing_requested_field", {"incident": index, "field": field}))
                elif _field_name(field) == "component" and value not in answer_policy.get("components", []):
                    errors.append(_error("illegal_component", {"incident": index, "value": value}))
                elif _field_name(field) == "reason" and value not in answer_policy.get("reasons", []):
                    errors.append(_error("illegal_reason", {"incident": index, "value": value}))
    if decision == "complete":
        expected = scope.get("incident_count")
        if len(incidents) != expected:
            errors.append(_error("wrong_incident_count", {"expected": expected, "actual": len(incidents)}))
        if gaps:
            errors.append(_error("unresolved_material_gap", gaps))
    elif decision == "continue":
        action = assessment.get("action")
        if not gaps:
            errors.append(_error("continue_without_gap"))
        if not isinstance(action, Mapping):
            errors.append(_error("continue_without_action"))
        else:
            name = action.get("name")
            if not isinstance(name, str) or name not in operations or not callable(operations[name]):
                errors.append(_error("undeclared_operation", name))
            arguments = action.get("arguments")
            if not isinstance(arguments, Mapping):
                errors.append(_error("invalid_operation_arguments"))
            if not isinstance(action.get("gap"), str) or not action["gap"]:
                errors.append(_error("operation_without_gap"))
            elif action["gap"] not in gaps:
                errors.append(_error("operation_gap_not_declared", action["gap"]))
    elif decision == "blocked" and assessment.get("stop_reason") == "evidence_sufficient":
        errors.append(_error("blocked_cannot_claim_sufficiency"))
    return errors


def _scope_compatible(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    for name in ("case_id", "deployment", "incident_count", "projection"):
        if left.get(name) != right.get(name):
            return False
    for name in ("window_start", "window_end"):
        if (name in left) != (name in right):
            return False
        if name in left and left[name] != right[name]:
            return False
    return True


def _merge_operation_packet(current: Mapping[str, Any], incoming: Any) -> tuple[dict[str, Any], bool, list[dict[str, Any]]]:
    errors = _validate_packet(incoming)
    if errors:
        return _copy(dict(current)), False, errors
    if not _scope_compatible(_scope(current), _scope(incoming)):
        return _copy(dict(current)), False, [_error("incompatible_operation_scope")]
    merged = _copy(dict(current))
    changed = False
    existing = merged["observations"]
    incoming_observations = incoming.get("observations", {})
    if not isinstance(incoming_observations, Mapping):
        return merged, False, [_error("invalid_operation_observations")]
    for key, observation in incoming_observations.items():
        if not isinstance(key, str) or not isinstance(observation, Mapping):
            return _copy(dict(current)), False, [_error("invalid_operation_observation", key)]
        if key not in existing:
            existing[key] = _copy(dict(observation))
            changed = True
        elif _canonical(existing[key]) != _canonical(observation):
            # Preserve the original fact and expose the conflict to later gates.
            existing[key]["conflict"] = True
            changed = True
            merged["qualifications"].append({
                "code": "conflicting_observation",
                "evidence_id": key,
                "incoming_observation": _copy(dict(observation)),
            })
    for collection_name in ("coverage", "qualifications", "definitions"):
        target = merged[collection_name]
        for item in incoming.get(collection_name, []):
            if _canonical(item) not in {_canonical(existing_item) for existing_item in target}:
                target.append(_copy(item))
                if collection_name == "coverage":
                    changed = True
    if changed:
        merged["revision"] = int(current["revision"]) + 1
    else:
        merged["revision"] = int(current["revision"])
    return merged, changed, []


def _state(packet: Mapping[str, Any], feedback: list[Any], assessments: list[Any], operations: list[Any]) -> dict[str, Any]:
    return {
        "evidence": _copy(dict(packet)),
        "feedback": _copy(feedback),
        "assessments": _copy(assessments),
        "operations": _copy(operations),
    }


def _resolved_support(incident: Mapping[str, Any], packet: Mapping[str, Any]) -> list[str]:
    lookup = _observation_lookup(packet)
    result: list[str] = []
    for evidence_id in incident.get("support", []) if isinstance(incident.get("support"), list) else []:
        observation = lookup.get(evidence_id)
        if observation is not None and observation.get("conflict") is not True:
            canonical_id = observation.get("evidence_id", evidence_id)
            if canonical_id not in result:
                result.append(canonical_id)
    return result


def _finalize(
    packet: Mapping[str, Any],
    draft: list[dict[str, Any]],
    answer_policy: Mapping[str, Any],
    stop_reason: str,
    accepted: bool,
    remaining_gaps: list[str],
    unassessed: set[str],
    usage: Mapping[str, Any],
    assessments: list[Any],
    operations: list[Any],
) -> dict[str, Any]:
    scope = _scope(packet)
    requested = _projection(scope)
    count = int(scope.get("incident_count", 0))
    components = list(answer_policy.get("components", []))
    reasons = list(answer_policy.get("reasons", []))
    fallback_time = scope.get("window_start") or scope.get("occurrence_time") or ""
    selections: list[dict[str, Any]] = []
    for source in draft[:count]:
        item: dict[str, Any] = {}
        for field in requested:
            value = _incident_value(source, field)
            canonical_field = _field_name(field)
            if canonical_field == "component" and value not in components:
                value = None
            if canonical_field == "reason" and value not in reasons:
                value = None
            if isinstance(value, str) and value:
                item[canonical_field] = value
        item["support"] = _resolved_support(source, packet)
        item["explanation"] = source.get("explanation", "") if isinstance(source.get("explanation"), str) else ""
        for field in requested:
            canonical_field = _field_name(field)
            if item.get(canonical_field):
                continue
            if canonical_field == "component" and components:
                item[canonical_field] = components[0]
            elif canonical_field == "reason" and reasons:
                item[canonical_field] = reasons[0]
            elif canonical_field == "occurrence_time" and isinstance(fallback_time, str) and fallback_time:
                item[canonical_field] = fallback_time
        selections.append(item)
    while len(selections) < count:
        item: dict[str, Any] = {}
        for field in requested:
            canonical_field = _field_name(field)
            if canonical_field == "component" and components:
                item[canonical_field] = components[0]
            elif canonical_field == "reason" and reasons:
                item[canonical_field] = reasons[0]
            elif canonical_field == "occurrence_time" and isinstance(fallback_time, str) and fallback_time:
                item[canonical_field] = fallback_time
        item["support"] = []
        item["explanation"] = ""
        selections.append(item)
    missing_legal = any(
        not isinstance(item.get(_field_name(field)), str) or not item.get(_field_name(field))
        for item in selections
        for field in requested
    )
    assembly_failure = "no_legal_answer" if missing_legal else None
    if accepted:
        qualifications = [[] for _ in selections]
        adequacy = "supported"
        status = "completed"
    else:
        qualifications = [["best_guess", "insufficient_evidence"] for _ in selections]
        adequacy = "insufficient"
        status = "failed" if assembly_failure else "degraded"
    incidents: list[dict[str, Any]] = []
    answer: list[dict[str, Any]] = []
    for item, item_qualifications in zip(selections, qualifications):
        incident = {key: _copy(value) for key, value in item.items()}
        incident["qualification"] = item_qualifications
        incidents.append(incident)
        answer.append({field: _copy(item.get(_field_name(field))) for field in requested})
    return {
        "answer": answer if not assembly_failure else [],
        "incidents": incidents if not assembly_failure else [],
        "investigation_stop_reason": stop_reason,
        "assembly_failure_reason": assembly_failure,
        "execution_status": status,
        "evidence_adequacy": adequacy,
        "evidence": _copy(dict(packet)),
        "assessments": _copy(assessments),
        "operations": _copy(operations),
        "usage": _copy(dict(usage)),
        "remaining_gaps": _copy(remaining_gaps),
        "unassessed_observation_ids": sorted(unassessed),
        "terminal_event": {"reason": stop_reason},
    }


def investigate(
    evidence: dict[str, Any],
    assessor: Callable[[dict[str, Any]], dict[str, Any]],
    operations: dict[str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]],
    answer_policy: dict[str, Any],
    work_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one bounded investigation and return detached JSON-shaped state."""
    packet = _copy(evidence)
    packet_errors = _validate_packet(packet)
    if packet_errors:
        raise ValueError(f"invalid evidence: {packet_errors}")
    policy = _copy(answer_policy)
    policy_errors = _validate_policy(policy)
    if policy_errors:
        raise ValueError(f"invalid answer policy: {policy_errors}")
    if not callable(assessor) or not isinstance(operations, Mapping):
        raise ValueError("assessor and operations are required callbacks")
    limits = _normalise_work_policy(work_policy)

    feedback: list[dict[str, Any]] = []
    assessment_history: list[dict[str, Any]] = []
    operation_history: list[dict[str, Any]] = []
    retained_draft: list[dict[str, Any]] = []
    remaining_gaps: list[str] = []
    unassessed = set(packet["observations"].keys())
    assessment_attempts = 0
    operation_attempts = 0
    non_progress = 0
    stop_reason: str | None = None
    accepted = False

    while stop_reason is None:
        if assessment_attempts >= limits["max_assessments"]:
            stop_reason = "budget_exhausted"
            break
        assessment_attempts += 1
        try:
            raw_assessment = assessor(_state(packet, feedback, assessment_history, operation_history))
        except Exception as exc:  # injected provider boundary
            assessment_history.append({
                "attempt": assessment_attempts,
                "status": "provider_failure",
                "error": f"{type(exc).__name__}: {exc}",
            })
            stop_reason = "provider_failure"
            break
        assessment = _copy(raw_assessment)
        errors = _assessment_errors(assessment, packet, policy, operations)
        record = {
            "attempt": assessment_attempts,
            "assessment": assessment,
            "accepted": not errors,
            "gate_errors": errors,
        }
        assessment_history.append(record)
        if isinstance(assessment, Mapping):
            retained_draft = _normalise_incidents(assessment.get("incidents"))
            remaining_gaps = [gap for gap in assessment.get("gaps", []) if isinstance(gap, str)] if isinstance(assessment.get("gaps"), list) else []
            if not errors and isinstance(assessment.get("evidence_revision"), int):
                unassessed.clear()
        if errors:
            feedback.append({"assessment_attempt": assessment_attempts, "errors": errors})
            if assessment_attempts >= limits["max_assessments"]:
                stop_reason = "invalid_assessment"
            continue

        decision = assessment["decision"]
        if decision == "complete":
            accepted = True
            stop_reason = "evidence_sufficient"
            break
        if decision == "blocked":
            stop_reason = assessment.get("stop_reason") or "no_useful_action"
            break

        # Continue: one operation, followed by another assessment if capacity remains.
        if operation_attempts >= limits["max_operations"] or assessment_attempts >= limits["max_assessments"]:
            stop_reason = "budget_exhausted"
            break
        action = assessment["action"]
        operation_attempts += 1
        name = action["name"]
        arguments = _copy(dict(action["arguments"]))
        operation_record: dict[str, Any] = {
            "attempt": operation_attempts,
            "name": name,
            "arguments": arguments,
            "gap": action["gap"],
            "revision_before": packet["revision"],
        }
        try:
            returned = operations[name](arguments, _state(packet, feedback, assessment_history, operation_history))
        except Exception as exc:  # injected operation boundary
            operation_record.update({"status": "operation_failure", "error": f"{type(exc).__name__}: {exc}"})
            operation_history.append(operation_record)
            stop_reason = "operation_failure"
            break
        merged, progress, merge_errors = _merge_operation_packet(packet, returned)
        if merge_errors:
            operation_record.update({"status": "rejected", "errors": merge_errors, "progress": False})
            operation_history.append(operation_record)
            feedback.append({"operation_attempt": operation_attempts, "errors": merge_errors})
            non_progress += 1
            if non_progress >= limits["max_non_progress"]:
                stop_reason = "stalled"
                break
            continue
        previous_observation_ids = set(packet["observations"])
        packet = merged
        operation_record.update({
            "status": "success" if progress else "empty",
            "progress": progress,
            "revision_after": packet["revision"],
        })
        operation_history.append(operation_record)
        if progress:
            non_progress = 0
            unassessed.update(set(packet["observations"]) - previous_observation_ids)
        else:
            non_progress += 1
        if non_progress >= limits["max_non_progress"]:
            stop_reason = "stalled"
            break

    usage = {
        "assessment_attempts": assessment_attempts,
        "operation_attempts": operation_attempts,
        "non_progress_operations": non_progress,
    }
    return _finalize(
        packet,
        retained_draft,
        policy,
        stop_reason or "budget_exhausted",
        accepted,
        remaining_gaps,
        unassessed,
        usage,
        assessment_history,
        operation_history,
    )


__all__ = ["investigate"]
