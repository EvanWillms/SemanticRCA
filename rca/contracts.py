"""Small value objects shared by the runner and replaceable agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class QueryRow:
    """One query in source order, retaining the source ``row_id``."""

    row_id: int
    instruction: str


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
