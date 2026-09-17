from __future__ import annotations

from copy import deepcopy

from rca_domain.investigation import investigate


def _observation(evidence_id: str) -> dict:
    return {
        "evidence_id": evidence_id,
        "source_snapshot_id": "snapshot-1",
        "deployment": "prod",
        "trace_id": "trace-1",
        "span_id": evidence_id,
        "semantic_operation": "request",
        "recording_component": "frontend-1",
        "raw": {"operation": "GET /cart", "status": "unknown"},
        "locator": {"source": "fixture.json", "record": evidence_id},
        "conflict": False,
    }


def _evidence() -> dict:
    return {
        "schema_version": "rca-evidence-v1",
        "scope": {
            "case_id": "case-1",
            "deployment": "prod",
            "incident_count": 1,
            "projection": ["component", "reason"],
        },
        "revision": 0,
        "observations": {"e1": _observation("e1")},
        "coverage": [],
        "qualifications": [],
        "definitions": [],
    }


def _answer_policy() -> dict:
    return {"components": ["cart-api", "frontend"], "reasons": ["latency", "error"]}


def test_useful_followup_is_merged_and_reassessed_before_sufficient_return():
    calls: list[dict] = []

    def assessor(state: dict) -> dict:
        calls.append(deepcopy(state))
        if len(calls) == 1:
            return {
                "decision": "continue",
                "evidence_revision": 0,
                "incidents": [],
                "gaps": ["cause"],
                "action": {"name": "compare", "arguments": {"metric": "latency"}, "gap": "cause"},
                "rationale": "Compare the competing explanations.",
            }
        return {
            "decision": "complete",
            "evidence_revision": 1,
            "incidents": [{
                "component": "cart-api",
                "reason": "latency",
                "support": ["e2"],
                "explanation": "The comparison supports the cart API explanation.",
            }],
            "gaps": [],
            "rationale": "The requested fields are supported.",
        }

    def compare(arguments: dict, state: dict) -> dict:
        assert arguments == {"metric": "latency"}
        assert state["evidence"]["revision"] == 0
        return {
            "schema_version": "rca-evidence-v1",
            "scope": deepcopy(state["evidence"]["scope"]),
            "revision": 0,
            "observations": {"e2": _observation("e2")},
            "coverage": ["latency-comparison-complete"],
            "qualifications": [],
            "definitions": [],
        }

    result = investigate(_evidence(), assessor, {"compare": compare}, _answer_policy())

    assert result["investigation_stop_reason"] == "evidence_sufficient"
    assert result["execution_status"] == "completed"
    assert result["evidence_adequacy"] == "supported"
    assert result["answer"] == [{"component": "cart-api", "reason": "latency"}]
    assert result["evidence"]["revision"] == 1
    assert list(result["evidence"]["observations"]) == ["e1", "e2"]
    assert len(result["assessments"]) == 2
    assert len(result["operations"]) == 1
    assert result["operations"][0]["status"] == "success"


def test_completion_with_unknown_support_is_rejected_and_reassessed():
    attempts = 0

    def assessor(state: dict) -> dict:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return {
                "decision": "complete",
                "evidence_revision": 0,
                "incidents": [{
                    "component": "cart-api",
                    "reason": "latency",
                    "support": ["invented-evidence"],
                    "explanation": "A plausible but ungrounded explanation.",
                }],
                "gaps": [],
                "rationale": "Initial draft.",
            }
        return {
            "decision": "complete",
            "evidence_revision": 0,
            "incidents": [{
                "component": "cart-api",
                "reason": "latency",
                "support": ["e1"],
                "explanation": "The retained observation supports the explanation.",
            }],
            "gaps": [],
            "rationale": "Corrected draft.",
        }

    result = investigate(_evidence(), assessor, {}, _answer_policy())

    assert attempts == 2
    assert result["investigation_stop_reason"] == "evidence_sufficient"
    assert result["assessments"][0]["accepted"] is False
    assert any(error["code"] == "unknown_support" for error in result["assessments"][0]["gate_errors"])
    assert result["answer"] == [{"component": "cart-api", "reason": "latency"}]


def test_assessment_budget_returns_a_qualified_legal_best_guess():
    def assessor(state: dict) -> dict:
        return {
            "decision": "continue",
            "evidence_revision": state["evidence"]["revision"],
            "incidents": [{
                "component": "cart-api",
                "reason": "latency",
                "support": ["e1"],
                "explanation": "The draft has a plausible supporting observation.",
            }],
            "gaps": ["independent cause confirmation"],
            "action": {"name": "compare", "arguments": {}, "gap": "independent cause confirmation"},
            "rationale": "More evidence would improve the draft.",
        }

    result = investigate(
        _evidence(), assessor, {"compare": lambda arguments, state: state["evidence"]},
        _answer_policy(), {"max_assessments": 1, "max_operations": 3},
    )

    assert result["investigation_stop_reason"] == "budget_exhausted"
    assert result["execution_status"] == "degraded"
    assert result["evidence_adequacy"] == "insufficient"
    assert result["answer"] == [{"component": "cart-api", "reason": "latency"}]
    assert result["incidents"][0]["support"] == ["e1"]
    assert "best_guess" in result["incidents"][0]["qualification"]
    assert result["usage"] == {
        "assessment_attempts": 1,
        "operation_attempts": 0,
        "non_progress_operations": 0,
    }


def test_assessor_failure_is_a_recorded_provider_failure_with_no_operation():
    operation_calls = 0

    def assessor(state: dict) -> dict:
        raise RuntimeError("provider offline")

    def operation(arguments: dict, state: dict) -> dict:
        nonlocal operation_calls
        operation_calls += 1
        return state["evidence"]

    result = investigate(_evidence(), assessor, {"compare": operation}, _answer_policy())

    assert result["investigation_stop_reason"] == "provider_failure"
    assert result["execution_status"] == "degraded"
    assert operation_calls == 0
    assert result["usage"]["assessment_attempts"] == 1
    assert result["operations"] == []
    assert result["assessments"][0]["status"] == "provider_failure"


def test_conflicting_followup_preserves_original_and_incoming_observations():
    assessments = 0

    def assessor(state: dict) -> dict:
        nonlocal assessments
        assessments += 1
        if assessments == 1:
            return {
                "decision": "continue",
                "evidence_revision": 0,
                "incidents": [],
                "gaps": ["conflicting record"],
                "action": {"name": "inspect", "arguments": {}, "gap": "conflicting record"},
                "rationale": "Inspect the conflicting record.",
            }
        return {
            "decision": "blocked",
            "evidence_revision": 1,
            "incidents": [],
            "gaps": ["conflicting record"],
            "rationale": "The conflicting record cannot be resolved by this operation.",
            "stop_reason": "no_useful_action",
        }

    incoming = _observation("e1")
    incoming["raw"] = {"operation": "GET /cart", "status": "changed"}

    def inspect(arguments: dict, state: dict) -> dict:
        return {
            "schema_version": "rca-evidence-v1",
            "scope": deepcopy(state["evidence"]["scope"]),
            "revision": 0,
            "observations": {"e1": incoming},
            "coverage": [],
            "qualifications": [],
            "definitions": [],
        }

    result = investigate(_evidence(), assessor, {"inspect": inspect}, _answer_policy())

    retained = result["evidence"]["observations"]["e1"]
    assert retained["raw"]["status"] == "unknown"
    assert retained["conflict"] is True
    conflicts = [item for item in result["evidence"]["qualifications"] if item.get("code") == "conflicting_observation"]
    assert conflicts and conflicts[0]["incoming_observation"]["raw"]["status"] == "changed"
