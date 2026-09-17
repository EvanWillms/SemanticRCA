"""Offline submission seam used by the empty-output milestone."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rca.contracts import Solution


_PLACEHOLDER_EVIDENCE = """## Answer
Diagnosis is not implemented in this harness.

## Confidence
No confidence estimate is available because diagnosis was not attempted.

## Evidence
No telemetry evidence was retrieved or assessed.

## Ruled out
No alternatives were assessed or ruled out.
"""


def solve(
    instruction: str,
    dataset_dir: Path,
    ctx: dict[str, Any],
) -> Solution:
    """Return an honest no-call placeholder for one query.

    The parameters intentionally remain at the public agent seam so a later
    implementation can replace this module without changing ``run.py``.
    """

    del instruction, dataset_dir, ctx
    return Solution(prediction="", evidence=_PLACEHOLDER_EVIDENCE, usage={})
