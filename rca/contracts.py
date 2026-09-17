"""Small value objects shared by the runner and replaceable agents.

The scope types live here because they are part of the public handoff between
the query interpreter and an agent.  They deliberately contain no I/O or
policy objects; callers can serialize them through :meth:`to_dict` at the
artifact boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class QueryRow:
    """One query in source order, retaining the source ``row_id``."""

    row_id: int
    instruction: str
    task_index: str | None = None


@dataclass(frozen=True)
class ExtractionSupport:
    """Source text supporting one interpreted value.

    ``start`` and ``end`` are Python string offsets, therefore they refer to
    Unicode characters in the original decoded instruction and are half-open.
    A convention can explain values that are derived from the supplied text,
    such as the permitted 23:30-to-midnight rollover.
    """

    field: str
    start: int | None = None
    end: int | None = None
    excerpt: str | None = None
    convention: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {"field": self.field}
        if self.start is not None:
            value["start"] = self.start
        if self.end is not None:
            value["end"] = self.end
        if self.excerpt is not None:
            value["excerpt"] = self.excerpt
        if self.convention is not None:
            value["convention"] = self.convention
        return value


@dataclass(frozen=True)
class InvestigationScope:
    """A validated Track 1 investigation scope."""

    deployment: str
    window_start: datetime
    window_end: datetime
    failure_count: int
    requested_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment": self.deployment,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "failure_count": self.failure_count,
            "requested_fields": list(self.requested_fields),
        }


@dataclass(frozen=True)
class InterpretationResult:
    """Typed result of the pure ``interpret(QueryRow)`` seam."""

    status: str
    parser_version: str
    instruction_hash: str
    instruction: str
    row_id: int
    task_index: str | None
    scope: InvestigationScope | None = None
    errors: tuple[str, ...] = ()
    support: tuple[ExtractionSupport, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "parser_version": self.parser_version,
            "instruction_hash": self.instruction_hash,
            "instruction": self.instruction,
            "row_id": self.row_id,
            "task_index": self.task_index,
            "scope": self.scope.to_dict() if self.scope is not None else None,
            "errors": list(self.errors),
            "support": [item.to_dict() for item in self.support],
        }


@dataclass(frozen=True)
class Solution:
    """Agent result at the public ``solve`` seam.

    The harness uses the empty prediction and evidence supplied by the stub;
    ``usage`` remains a plain mapping so future agents can report their own
    per-model counters without changing this interface.
    """

    prediction: str = ""
    evidence: str = ""
    usage: dict[str, Any] = field(default_factory=dict)
    discovery: dict[str, Any] | None = None
