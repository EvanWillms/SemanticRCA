"""Evidence grounded GLM router for the official Track 1 interface.

Discovery remains the only reader of the telemetry bundle.  This agent gives a
small, source-linked candidate packet to a cheap model for triage and reserves a
second call for final selection.  Model output is treated as a hypothesis: all
answer fields are checked against discovered identities, timestamps, and the
benchmark's legal reason vocabulary before a new immutable ``Solution`` is
returned.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from rca.contracts import Solution
from rca.discovery.budget import CaseBudget
from rca.model_client import AllModelsUnavailable, ModelClient

from . import discovery as discovery_agent


CHEAP_MODELS = ("zai-org/GLM-4.7-Flash", "zai-org/GLM-5.3-Flash")
STRONG_MODELS = ("zai-org/GLM-5.2", "zai-org/GLM-5.1")
UTC_PLUS_8 = timezone(timedelta(hours=8), name="UTC+08:00")
CASE_SECONDS = 55.0
DISCOVERY_SECONDS = 30.0
MAX_FACTS_CHARS = 20_000

NODE_REASONS = {
    "cpu": "node CPU load",
    "spike": "node CPU spike",
    "memory": "node memory consumption",
    "read": "node disk read I/O consumption",
    "write": "node disk write I/O consumption",
    "space": "node disk space consumption",
}
POD_REASONS = {
    "cpu": "container CPU load",
    "memory": "container memory load",
    "read": "container read I/O load",
    "write": "container write I/O load",
    "latency": "container network latency",
    "loss": "container packet loss",
    "retrans": "container network packet retransmission",
    "corrupt": "container network packet corruption",
    "kill": "container process termination",
}


def _json_object(text: str) -> dict[str, Any]:
    """Decode the first JSON object while tolerating a markdown code fence."""
    match = re.search(r"\{.*\}", text or "", flags=re.S)
    if not match:
        return {}
    try:
        value = json.loads(match.group(0))
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _component(resource: Any, family: Any = "") -> str:
    value = str(resource or "").strip()
    # Container metrics use node.pod identities; the benchmark answer names the
    # pod, whereas node metrics retain the node identity.
    if str(family) == "metric_container" and "." in value:
        return value.split(".", 1)[1]
    return value


def _reason_for(kpi: Any, component: str) -> str:
    key = str(kpi or "").lower()
    table = NODE_REASONS if component.startswith("node-") else POD_REASONS
    if any(token in key for token in ("disk_read", "read_bytes", "diskio_read", "read_io")):
        return table.get("read", next(iter(table.values())))
    if any(token in key for token in ("disk_write", "write_bytes", "diskio_write", "write_io")):
        return table.get("write", next(iter(table.values())))
    if any(token in key for token in ("disk_space", "fs_usage", "disk_usage", "filesystem")):
        return table.get("space", next(iter(table.values())))
    if any(token in key for token in ("memory", "mem_", "pgfault")):
        return table.get("memory", next(iter(table.values())))
    if "cpu" in key:
        return table.get("cpu", next(iter(table.values())))
    if "packet_loss" in key or "drop" in key:
        return table.get("loss", table.get("latency", next(iter(table.values()))))
    if "retrans" in key:
        return table.get("retrans", table.get("latency", next(iter(table.values()))))
    if "corrupt" in key:
        return table.get("corrupt", table.get("latency", next(iter(table.values()))))
    if any(token in key for token in ("latency", "rtt", "delay", "network", "net_", "tcp", "rx", "tx", "receive", "transmit")):
        return table.get("latency", next(iter(table.values())))
    return next(iter(table.values()))


def _datetime(value: Any, *, milliseconds: bool = False) -> str | None:
    try:
        if isinstance(value, (int, float)):
            epoch = float(value) / (1000.0 if milliseconds else 1.0)
            return datetime.fromtimestamp(epoch, UTC_PLUS_8).strftime("%Y-%m-%d %H:%M:%S")
        text = str(value).strip()
        if not text:
            return None
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC_PLUS_8)
        return parsed.astimezone(UTC_PLUS_8).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _findings_payload(sidecar: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    findings = sidecar.get("findings")
    if not isinstance(findings, Mapping):
        return ()
    candidates = findings.get("candidates")
    return tuple(item for item in candidates if isinstance(item, Mapping)) if isinstance(candidates, Sequence) else ()


def _resources(sidecar: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
    findings = sidecar.get("findings")
    snapshot = findings.get("source_snapshot") if isinstance(findings, Mapping) else None
    sources = snapshot.get("sources") if isinstance(snapshot, Mapping) else None
    values: set[tuple[str, str]] = set()
    if isinstance(sources, Sequence):
        for source in sources:
            if not isinstance(source, Mapping):
                continue
            family = str(source.get("family", ""))
            for resource in source.get("resources", ()) if isinstance(source.get("resources", ()), Sequence) else ():
                component = _component(resource, family)
                if component:
                    values.add((component, family))
    return tuple({"component": component, "family": family} for component, family in sorted(values))


def _candidate_records(sidecar: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in _findings_payload(sidecar):
        family = str(item.get("family") or item.get("source_family") or "")
        resource = str(item.get("resource") or "")
        component = _component(resource, family)
        if not component:
            continue
        kpi = str(item.get("kpi") or item.get("operation") or "")
        raw_timestamp = item.get("timestamp")
        # Trace comparison timestamps are seconds after conversion; metric
        # comparison timestamps are epoch seconds as well.
        when = _datetime(raw_timestamp)
        locator = item.get("locator")
        if not isinstance(locator, Mapping):
            observation = item.get("observation")
            locator = observation.get("locator") if isinstance(observation, Mapping) else {}
        score = item.get("absolute_difference", item.get("difference", 0))
        try:
            magnitude = abs(float(score or 0))
        except (TypeError, ValueError):
            magnitude = 0.0
        records.append({
            "component": component,
            "resource": resource,
            "family": family,
            "kpi": kpi,
            "datetime": when,
            "value": item.get("value"),
            "reference": item.get("reference_median"),
            "difference": item.get("difference", item.get("signed_difference")),
            "locator": dict(locator) if isinstance(locator, Mapping) else {},
            "_magnitude": magnitude,
        })
    records.sort(key=lambda item: (-item["_magnitude"], item["component"], item["kpi"], item.get("datetime") or ""))
    # Keep one strongest observation per component before filling the packet;
    # repeated samples otherwise crowd out independent alternatives.
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        if record["component"] not in seen:
            selected.append(record)
            seen.add(record["component"])
        elif len(selected) < 24:
            selected.append(record)
    return selected[:24]


def _public_record(index: int, item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": index,
        "component": item.get("component"),
        "family": item.get("family"),
        "kpi": item.get("kpi"),
        "datetime": item.get("datetime"),
        "value": item.get("value"),
        "reference": item.get("reference"),
        "difference": item.get("difference"),
        "locator": item.get("locator", {}),
        "legal_reasons": sorted(set((NODE_REASONS if str(item.get("component", "")).startswith("node-") else POD_REASONS).values())),
    }


def _facts(records: Sequence[Mapping[str, Any]], resource_records: Sequence[Mapping[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    public = [_public_record(i, item) for i, item in enumerate(records, 1)]
    packet: dict[str, Any] = {"candidates": public, "inventory_resources": list(resource_records)}
    text = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text) <= MAX_FACTS_CHARS:
        return text, public
    # Locator provenance is useful but less important than identities and
    # comparisons when a malformed bundle is unusually verbose.
    for item in public:
        item["locator"] = {}
    packet["candidates"] = public
    text = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text[:MAX_FACTS_CHARS], public


def _scope_start(scope: Mapping[str, Any]) -> str:
    return _datetime(scope.get("window_start")) or "1970-01-01 00:00:00"


def _extract_section(text: str, heading: str, next_heading: str | None = None) -> str:
    marker = heading.lower()
    lower = text.lower()
    start = lower.find(marker)
    if start < 0:
        return ""
    start = start + len(heading)
    end = len(text)
    if next_heading:
        possible = lower.find(next_heading.lower(), start)
        if possible >= 0:
            end = possible
    return text[start:end].strip()


def _format_prediction(answers: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> str:
    output: dict[str, dict[str, str]] = {}
    for index, answer in enumerate(answers, 1):
        item: dict[str, str] = {}
        if "datetime" in fields and answer.get("datetime"):
            item["root cause occurrence datetime"] = str(answer["datetime"])
        if "component" in fields and answer.get("component"):
            item["root cause component"] = str(answer["component"])
        if "reason" in fields and answer.get("reason"):
            item["root cause reason"] = str(answer["reason"])
        output[str(index)] = item
    return json.dumps(output, ensure_ascii=False)


def _typed_unsupported(base: Solution) -> Solution:
    # Keep discovery's typed unsupported result and its truthful explanation;
    # the frozen dataclass is never mutated.
    evidence = base.evidence or (
        "## Answer\nScope unsupported; no answer fields could be established.\n\n"
        "## Confidence\nLow.\n\n## Evidence\nScope interpretation was unsupported.\n\n"
        "## Ruled out\nNo telemetry was inspected.\n"
    )
    return Solution(prediction=base.prediction, evidence=evidence, usage={}, discovery=base.discovery)


def solve(instruction: str, dataset_dir: Path, ctx: dict[str, Any]) -> Solution:
    """Run discovery, route bounded GLM calls, and return a new Solution."""
    started = time.monotonic()
    incoming_budget = ctx.get("budget")
    deadline = started + CASE_SECONDS
    if isinstance(incoming_budget, CaseBudget):
        deadline = min(deadline, incoming_budget.deadline)
    # Give the existing discovery seam a copied context with a short local
    # budget.  This leaves the runner's context and immutable solution intact.
    bounded = dict(ctx)
    bounded["budget"] = CaseBudget(min(deadline, started + DISCOVERY_SECONDS), time.monotonic)
    base = discovery_agent.solve(instruction, dataset_dir, bounded)
    if not isinstance(base, Solution):
        raise TypeError("agents.discovery.solve did not return a Solution")
    sidecar = base.discovery
    interpretation = sidecar.get("interpretation") if isinstance(sidecar, Mapping) else None
    scope = interpretation.get("scope") if isinstance(interpretation, Mapping) else None
    if not isinstance(scope, Mapping) or interpretation.get("status") != "interpreted":
        return _typed_unsupported(base)

    fields = tuple(field for field in ("datetime", "component", "reason") if field in (scope.get("requested_fields") or ()))
    if not fields:
        return _typed_unsupported(base)
    count = max(1, int(scope.get("failure_count") or 1))
    records = _candidate_records(sidecar if isinstance(sidecar, Mapping) else {})
    resources = _resources(sidecar if isinstance(sidecar, Mapping) else {})
    if not records:
        # Inventory is still useful when every comparison was unavailable.  It
        # supplies identities for a deterministic best guess, without inventing
        # an observed anomaly.
        records = [{
            "component": item["component"], "resource": item["component"],
            "family": item["family"], "kpi": "", "datetime": _scope_start(scope),
            "value": None, "reference": None, "difference": None,
            "locator": {}, "_magnitude": 0.0,
        } for item in resources[:24]]
    if not records:
        records = [{"component": "unknown", "family": "", "kpi": "", "datetime": _scope_start(scope), "value": None, "reference": None, "difference": None, "locator": {}}]
    fact_text, public = _facts(records, resources)
    fallback: list[dict[str, str]] = []
    for index in range(count):
        item = records[index % len(records)]
        fallback.append({
            "datetime": item.get("datetime") or _scope_start(scope),
            "component": str(item.get("component") or "unknown"),
            "reason": _reason_for(item.get("kpi"), str(item.get("component") or "")),
        })

    client = ModelClient(deadline=deadline, timeout=min(8.0, max(0.1, deadline - time.monotonic())))
    notes: list[str] = []
    triage: dict[str, Any] = {}
    decision: dict[str, Any] = {}
    try:
        triage = _json_object(client.ask(
            CHEAP_MODELS,
            "Rank the candidate_id values for the stated root-cause question. "
            "Use only the supplied packet and reply JSON only as {\"candidate_ids\":[1,2]}.\n\n"
            + fact_text,
            max_tokens=300,
        ))
    except AllModelsUnavailable:
        notes.append("Cheap triage was unavailable; deterministic candidate order was retained.")
    selected_ids = [int(value) for value in triage.get("candidate_ids", ()) if isinstance(value, (int, float)) and 1 <= int(value) <= len(public)]
    try:
        decision = _json_object(client.ask(
            STRONG_MODELS,
            "Select the root cause from these source-backed candidates. The question asks for "
            f"exactly {count} failure(s) and fields {list(fields)}. Reply JSON only as "
            '{"answers":[{"candidate_id":1,"component":"...","reason":"...","datetime":"YYYY-MM-DD HH:MM:SS"}],'
            '"confidence":"low|medium|high","why":"qualified hypothesis"}. '
            "Use an exact legal reason for that component level and never invent a component, reason, or time.\n\n"
            + fact_text,
            max_tokens=700,
        ))
    except AllModelsUnavailable:
        notes.append("Strong diagnosis models were unavailable; the recorded candidate with the largest departure was retained.")

    legal_components = {str(item.get("component")) for item in records}
    legal_components.update(str(item.get("component")) for item in resources)
    allowed_times = {str(item.get("datetime")) for item in records if item.get("datetime")}
    allowed_times.add(_scope_start(scope))
    model_answers = decision.get("answers") if isinstance(decision.get("answers"), Sequence) else ()
    answers: list[dict[str, str]] = []
    for index in range(count):
        proposed = model_answers[index] if index < len(model_answers) and isinstance(model_answers[index], Mapping) else {}
        candidate_id = proposed.get("candidate_id")
        chosen = None
        if isinstance(candidate_id, (int, float)) and 1 <= int(candidate_id) <= len(records):
            chosen = records[int(candidate_id) - 1]
        if chosen is None:
            component = str(proposed.get("component") or "")
            chosen = next((item for item in records if item.get("component") == component), None)
        if chosen is None:
            chosen = records[index % len(records)]
        component = str(chosen.get("component") or "unknown")
        if str(proposed.get("component") or "") in legal_components:
            component = str(proposed["component"])
        table = NODE_REASONS if component.startswith("node-") else POD_REASONS
        reason = str(proposed.get("reason") or "")
        if reason not in table.values():
            reason = _reason_for(chosen.get("kpi"), component)
        when = _datetime(proposed.get("datetime"))
        if when not in allowed_times:
            when = str(chosen.get("datetime") or _scope_start(scope))
        answers.append({"datetime": when, "component": component, "reason": reason})

    answers.sort(key=lambda item: item["datetime"])
    confidence = str(decision.get("confidence") or "low").lower()
    if confidence not in {"low", "medium", "high"}:
        confidence = "low"
    rationale = re.sub(r"\s+", " ", str(decision.get("why") or "No model rationale was available.")).strip()[:900]
    answer_lines = "\n".join(
        f"{index}. {item.get('component', '')} / {item.get('reason', '')} / {item.get('datetime', '')}"
        for index, item in enumerate(answers, 1)
    )
    raw_evidence = _extract_section(base.evidence, "## Evidence", "## Ruled out")
    if not raw_evidence:
        raw_evidence = "Discovery returned source-linked candidate observations; see the persisted findings sidecar."
    alternatives = ", ".join(dict.fromkeys(str(item.get("component")) for item in records if item.get("component") not in {answer["component"] for answer in answers}))
    ruled_out = (f"No causal alternative was validated. Other observed candidates: {alternatives}."
                 if alternatives else "No causal alternative was validated from the available observations.")
    if notes:
        notes_text = " " + " ".join(notes)
    else:
        notes_text = ""
    evidence = (
        "## Answer\n" + answer_lines + "\n\n"
        "## Confidence\n" + confidence.capitalize() + ". Qualified model hypothesis (not a validated fact): "
        + rationale + notes_text + "\n\n"
        "## Evidence\n" + raw_evidence + "\n\n"
        "## Ruled out\n" + ruled_out + "\n"
    )
    return Solution(
        prediction=_format_prediction(answers, fields),
        evidence=evidence,
        usage=client.usage,
        discovery=None,
    )


__all__ = ["solve"]
