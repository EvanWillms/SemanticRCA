"""Pure interpretation of the bounded Track 1 query grammar.

This module intentionally has no dataset, environment, clock, network or model
dependency.  The parser emits a typed unsupported result whenever one of the
scope dimensions cannot be established without guessing.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import hashlib
import re
from typing import Iterable

from .contracts import (
    ExtractionSupport,
    InterpretationResult,
    InvestigationScope,
    QueryRow,
)


PARSER_VERSION = "scope-v1"
UTC_PLUS_8 = timezone(timedelta(hours=8), name="UTC+08:00")

_MONTH = (
    "January|February|March|April|May|June|July|August|September|October|"
    "November|December"
)
_DATE = rf"(?:{_MONTH})\s+\d{{1,2}}(?:st|nd|rd|th)?\s*,?\s*\d{{4}}"
_CLOCK = r"\d{1,2}:\d{2}"
_IDENTIFIER = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"

_WINDOW_RE = re.compile(
    rf"""\b(?:
        (?:within|during)\s+(?:the\s+)?(?:specified\s+)?
            (?:time\s+(?:range|period)|timeframe)\s+of
      | between\s+(?:the\s+)?time\s+range\s+of
      | (?:time\s+range|time\s+period)\s+of
      | on
    )\s+(?P<date_start>{_DATE})\s*,?\s*
    (?:from|between)\s+(?P<time_start>{_CLOCK})\s+
    (?:to|and)\s+
    (?:(?P<date_end>{_DATE})\s*,?\s*(?:at\s+)?)?
    (?P<time_end>{_CLOCK})""",
    re.IGNORECASE | re.VERBOSE,
)
_DATE_RE = re.compile(rf"\b{_DATE}\b", re.IGNORECASE)
_CLOCK_RE = re.compile(rf"\b{_CLOCK}\b")
_TIMEZONE_RE = re.compile(
    r"\b(?:utc|gmt|pst|pdt|est|edt|cst|cdt|mst|mdt|cet|eet|timezone|time\s+zone)\b",
    re.IGNORECASE,
)

_SYSTEM_ID_RE = re.compile(
    rf"\b(?:cloud\s+service\s+)?system\s*,?\s*(?P<id>{_IDENTIFIER})\b",
    re.IGNORECASE,
)
_ID_SYSTEM_RE = re.compile(rf"\b(?P<id>{_IDENTIFIER})\s+system\b", re.IGNORECASE)
_DIRECT_ID_RE = re.compile(
    rf"\b(?P<id>{_IDENTIFIER})\s+(?:has\s+|may\s+have\s+)?(?:experienced|encountered)\b",
    re.IGNORECASE,
)
_DEPLOYMENT_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "cloud",
    "encountered",
    "experienced",
    "failure",
    "has",
    "have",
    "is",
    "may",
    "one",
    "service",
    "system",
    "the",
    "two",
}

_COUNT_TOKEN = r"(?:a\s+single|a|an|one|single|two|[1-9][0-9]*)"
_OCCURRENCE_COUNT_RE = re.compile(
    rf"\b(?:experienced|encountered)\s+(?P<count>{_COUNT_TOKEN})\s+failures?\b",
    re.IGNORECASE,
)
_REPEATED_COUNT_RE = re.compile(
    rf"\b(?:there\s+(?:is|was)|confirmed\s+there\s+was)\s+"
    rf"(?P<count>{_COUNT_TOKEN})\s+(?:known\s+)?failures?\b",
    re.IGNORECASE,
)
_INVALID_COUNT_RE = re.compile(
    r"\b(?:experienced|encountered)\s+(?P<count>[A-Za-z0-9]+)\s+failures?\b|"
    r"\b(?:there\s+(?:is|was)|confirmed\s+there\s+was)\s+"
    r"(?P<repeated>[A-Za-z0-9]+)\s+(?:known\s+)?failures?\b",
    re.IGNORECASE,
)

_REQUEST_RE = re.compile(
    r"""\b(?:
        please\s+(?:identify|determine|pinpoint|investigate(?:\s+to\s+determine)?)
      | your\s+task\s+is\s+to\s+(?:identify|determine)
      | you\s+are\s+tasked\s+with\s+(?:identifying|to\s+identify|to\s+determine)
      | you\s+are\s+required\s+to\s+(?:identify|determine)
      | you\s+need\s+to\s+(?:identify|determine)(?:\s+and\s+(?:identify|determine))?
      | identify|determine|pinpoint
    )\b""",
    re.IGNORECASE | re.VERBOSE,
)

# Long aliases precede their short fallback so provenance is useful to a
# reviewer while remaining tolerant of the observed wording variants.
_DATETIME_ALIASES = (
    re.compile(r"\b(?:root\s+cause\s+)?occurrence\s+(?:datetime|date\s+and\s+time|time)\b", re.I),
    re.compile(r"\b(?:root\s+cause\s+)?(?:date\s+and\s+time|datetime)\b", re.I),
    re.compile(r"\b(?:exact|precise)\s+times?\b", re.I),
    re.compile(r"\b(?:exact|precise)\s+time\s+(?:of|when|at)\b", re.I),
    re.compile(r"\btime\s+(?:of|when|at\s+which)\s+(?:the\s+)?root\s+cause\b", re.I),
    re.compile(r"\boccurrence\s+time\b", re.I),
)
_COMPONENT_ALIASES = (
    re.compile(r"\b(?:root\s+cause|affected|specific|particular|exact)\s+components?\b", re.I),
    re.compile(r"\bcomponents?\s+(?:responsible|affected|involved)\b", re.I),
    re.compile(r"\bcomponents?\s+that\s+(?:triggered|caused)\b", re.I),
    re.compile(r"\bcomponents?\b", re.I),
)
_REASON_ALIASES = (
    re.compile(r"\b(?:root\s+cause|underlying)\s+reasons?\b", re.I),
    re.compile(r"\breasons?\s+(?:behind|for|of)\s+(?:this|these|the|a|an)\s+[^,.!?]+", re.I),
    re.compile(r"\breasons?\b", re.I),
)
_FIELD_ALIASES = {
    "datetime": _DATETIME_ALIASES,
    "component": _COMPONENT_ALIASES,
    "reason": _REASON_ALIASES,
}
_TASK_FIELDS = {
    "task_1": ("datetime",),
    "task_2": ("reason",),
    "task_3": ("component",),
    "task_4": ("datetime", "reason"),
    "task_5": ("datetime", "component"),
    "task_6": ("component", "reason"),
    "task_7": ("datetime", "component", "reason"),
}
_CANONICAL_ORDER = ("datetime", "component", "reason")


def _hash(instruction: str) -> str:
    return hashlib.sha256(instruction.encode("utf-8")).hexdigest()


def _support(
    instruction: str,
    field: str,
    start: int,
    end: int,
    *,
    convention: str | None = None,
) -> ExtractionSupport:
    return ExtractionSupport(
        field=field,
        start=start,
        end=end,
        excerpt=instruction[start:end],
        convention=convention,
    )


def _unique_support(items: Iterable[ExtractionSupport]) -> tuple[ExtractionSupport, ...]:
    seen: set[tuple[object, ...]] = set()
    result: list[ExtractionSupport] = []
    for item in items:
        key = (item.field, item.start, item.end, item.excerpt, item.convention)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return tuple(result)


def _date(value: str) -> date:
    cleaned = re.sub(r"(?i)(\d{1,2})(?:st|nd|rd|th)", r"\1", value)
    cleaned = re.sub(r"\s+", " ", cleaned.strip())
    match = re.fullmatch(r"(?i)([a-z]+) (\d{1,2})\s*,?\s*(\d{4})", cleaned)
    if not match:
        raise ValueError("invalid English date")
    months = {name.lower(): number for number, name in enumerate(
        ("January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"), start=1
    )}
    try:
        return date(int(match.group(3)), months[match.group(1).lower()], int(match.group(2)))
    except (KeyError, ValueError) as exc:
        raise ValueError("invalid English date") from exc


def _clock(value: str) -> time:
    hour, minute = (int(part) for part in value.split(":"))
    if hour > 23 or minute > 59:
        raise ValueError("clock out of range")
    return time(hour, minute)


def _count(value: str) -> int:
    token = re.sub(r"\s+", " ", value.lower().strip())
    if token in {"a", "a single", "an", "one", "single"}:
        return 1
    if token == "two":
        return 2
    return int(token, 10)


def _result(
    query: QueryRow,
    *,
    scope: InvestigationScope | None,
    errors: Iterable[str],
    support: Iterable[ExtractionSupport],
) -> InterpretationResult:
    unique_errors = tuple(dict.fromkeys(errors))
    return InterpretationResult(
        status="interpreted" if scope is not None and not unique_errors else "unsupported",
        parser_version=PARSER_VERSION,
        instruction_hash=_hash(query.instruction),
        instruction=query.instruction,
        row_id=query.row_id,
        task_index=query.task_index.strip() if isinstance(query.task_index, str) and query.task_index.strip() else None,
        scope=scope if not unique_errors else None,
        errors=unique_errors,
        support=_unique_support(support),
    )


def _deployment(instruction: str) -> tuple[str | None, list[ExtractionSupport], list[str]]:
    found: list[tuple[str, int, int]] = []
    for pattern in (_SYSTEM_ID_RE, _ID_SYSTEM_RE, _DIRECT_ID_RE):
        for match in pattern.finditer(instruction):
            value = match.group("id")
            if value.lower() in _DEPLOYMENT_STOPWORDS:
                continue
            if pattern is _ID_SYSTEM_RE and not any(
                character.isdigit() or character in "-_." for character in value
            ):
                # The compact ``<identifier> system`` form is accepted for
                # ordinary names at sentence start or after ``the``.  This
                # keeps prose such as ``is ... within the system`` from
                # turning the word before ``system`` into a deployment.
                prefix = instruction[max(0, match.start("id") - 4) : match.start("id")].lower()
                if match.start("id") and prefix != "the ":
                    continue
            found.append((value.lower(), match.start("id"), match.end("id")))
    canonical = {item[0] for item in found}
    if not canonical:
        return None, [], ["missing_deployment"]
    if len(canonical) > 1:
        supports = [_support(instruction, "deployment", start, end) for _, start, end in found]
        return None, supports, ["conflicting_deployment"]
    value = next(iter(canonical))
    supports = [
        _support(instruction, "deployment", start, end)
        for candidate, start, end in found
        if candidate == value
    ]
    return value, supports, []


def _window(
    instruction: str,
) -> tuple[datetime | None, datetime | None, list[ExtractionSupport], list[str]]:
    matches = list(_WINDOW_RE.finditer(instruction))
    if len(matches) > 1:
        supports = [_support(instruction, "window", match.start(), match.end()) for match in matches]
        return None, None, supports, ["conflicting_window"]
    if not matches:
        # A date and clock-looking value in a scope marker indicates malformed
        # bounds; a wholly absent window is a distinct diagnostic.
        has_date_and_clock = bool(_DATE_RE.search(instruction)) and bool(_CLOCK_RE.search(instruction))
        return None, None, [], ["invalid_window" if has_date_and_clock else "missing_window"]

    match = matches[0]
    try:
        start_date = _date(match.group("date_start"))
        start_time = _clock(match.group("time_start"))
        end_date_text = match.group("date_end")
        end_date = _date(end_date_text) if end_date_text else start_date
        end_time = _clock(match.group("time_end"))
        start = datetime.combine(start_date, start_time, tzinfo=UTC_PLUS_8)
        end = datetime.combine(end_date, end_time, tzinfo=UTC_PLUS_8)
    except (TypeError, ValueError):
        return None, None, [_support(instruction, "window", match.start(), match.end())], ["invalid_window"]

    convention: str | None = None
    if end_date_text is None and end <= start:
        if start_time == time(23, 30) and end_time == time(0, 0):
            end += timedelta(days=1)
            convention = "cross_midnight_23:30_to_00:00"
        else:
            return None, None, [_support(instruction, "window", match.start(), match.end())], ["invalid_window"]
    if end - start != timedelta(minutes=30):
        return None, None, [_support(instruction, "window", match.start(), match.end())], ["invalid_window"]

    date_start = match.start("date_start")
    time_start = match.end("time_start")
    date_end = match.start("date_end") if end_date_text else match.start("time_end")
    supports = [
        _support(instruction, "window_start", date_start, time_start),
        _support(
            instruction,
            "window_end",
            date_end,
            match.end("time_end"),
            convention=(convention or ("end_date_inherits_start_date" if end_date_text is None else None)),
        ),
    ]
    return start, end, supports, []


def _requested_fields(
    instruction: str,
) -> tuple[tuple[str, ...], list[ExtractionSupport], list[str]]:
    requests = []
    for match in _REQUEST_RE.finditer(instruction):
        end = re.search(r"[.!?](?:\s|$)", instruction[match.start() :])
        clause_end = match.start() + end.start() if end else len(instruction)
        requests.append((match.start(), clause_end))
    if not requests:
        return (), [], ["missing_requested_fields"]

    projections: list[tuple[str, ...]] = []
    supports: list[ExtractionSupport] = []
    for clause_start, clause_end in requests:
        clause = instruction[clause_start:clause_end]
        clause_supports: list[ExtractionSupport] = []
        fields: list[str] = []
        for field in _CANONICAL_ORDER:
            for alias in _FIELD_ALIASES[field]:
                matches = list(alias.finditer(clause))
                if matches:
                    fields.append(field)
                    clause_supports.extend(
                        _support(instruction, field, clause_start + item.start(), clause_start + item.end())
                        for item in matches
                    )
                    break
        ordered = tuple(field for field in _CANONICAL_ORDER if field in fields)
        if not ordered:
            return (), supports, ["unsupported_request"]
        projections.append(ordered)
        supports.extend(clause_supports)

    distinct = {projection for projection in projections}
    if len(distinct) > 1:
        return (), supports, ["conflicting_requested_fields"]
    return next(iter(distinct)), supports, []


def _failure_count(
    instruction: str,
) -> tuple[int | None, list[ExtractionSupport], list[str]]:
    matches = list(_OCCURRENCE_COUNT_RE.finditer(instruction))
    matches.extend(_REPEATED_COUNT_RE.finditer(instruction))
    values: list[tuple[int, re.Match[str]]] = []
    for match in matches:
        try:
            values.append((_count(match.group("count")), match))
        except (TypeError, ValueError):
            pass
    if not values:
        if _INVALID_COUNT_RE.search(instruction):
            return None, [], ["invalid_failure_count"]
        return None, [], ["missing_failure_count"]
    distinct = {value for value, _ in values}
    supports = [
        _support(instruction, "failure_count", match.start("count"), match.end("count"))
        for _, match in values
    ]
    if any(value <= 0 for value, _ in values):
        return None, supports, ["invalid_failure_count"]
    if len(distinct) > 1:
        return None, supports, ["conflicting_failure_count"]
    return next(iter(distinct)), supports, []


def interpret(query: QueryRow) -> InterpretationResult:
    """Interpret one query row without consulting external state."""

    if not isinstance(query, QueryRow):
        raise TypeError("interpret expects a QueryRow")
    if not isinstance(query.instruction, str):
        raise TypeError("QueryRow.instruction must be a string")

    if not query.instruction.strip():
        return _result(query, scope=None, errors=("empty_instruction",), support=())

    support: list[ExtractionSupport] = []
    errors: list[str] = []
    if _TIMEZONE_RE.search(query.instruction):
        errors.append("unsupported_instruction")

    deployment, deployment_support, deployment_errors = _deployment(query.instruction)
    support.extend(deployment_support)
    errors.extend(deployment_errors)

    window_start, window_end, window_support, window_errors = _window(query.instruction)
    support.extend(window_support)
    errors.extend(window_errors)

    failure_count, count_support, count_errors = _failure_count(query.instruction)
    support.extend(count_support)
    errors.extend(count_errors)

    requested_fields, request_support, request_errors = _requested_fields(query.instruction)
    support.extend(request_support)
    errors.extend(request_errors)

    task_index = query.task_index.strip() if isinstance(query.task_index, str) else query.task_index
    if task_index:
        if task_index not in _TASK_FIELDS:
            errors.append("unsupported_task_index")
        elif requested_fields and tuple(requested_fields) != _TASK_FIELDS[task_index]:
            errors.append("task_index_mismatch")

    scope: InvestigationScope | None = None
    if not errors and deployment and window_start and window_end and failure_count and requested_fields:
        scope = InvestigationScope(
            deployment=deployment,
            window_start=window_start,
            window_end=window_end,
            failure_count=failure_count,
            requested_fields=requested_fields,
        )
    return _result(query, scope=scope, errors=errors, support=support)


__all__ = ["PARSER_VERSION", "UTC_PLUS_8", "interpret"]
