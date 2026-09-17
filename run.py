#!/usr/bin/env python3
"""Official three-flag entrypoint for the offline empty-output harness."""

from __future__ import annotations

import argparse
import importlib
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

# Keep imports of local packages from creating __pycache__ beside the source.
sys.dont_write_bytecode = True

from rca.contracts import Solution
from rca.inputs import InputValidationError, preflight_inputs
from rca.outputs import OutputWriteError, OutputWriter

DEFAULT_AGENT = "agents.heuristic"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the empty-output RCA harness")
    parser.add_argument("--dataset", required=True, help="mounted dataset directory")
    parser.add_argument("--queries", required=True, help="query CSV path")
    parser.add_argument("--out", required=True, help="empty output directory")
    parser.add_argument(
        "--agent",
        default=DEFAULT_AGENT,
        help="optional agent module with solve(instruction, dataset_dir, ctx)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser


def _load_solver(agent_name: str) -> Callable[[str, Path, dict[str, Any]], Solution]:
    try:
        module = importlib.import_module(agent_name)
        solve = getattr(module, "solve")
    except (ImportError, AttributeError) as exc:
        raise RuntimeError("selected agent is unavailable") from exc
    if not callable(solve):
        raise RuntimeError("selected agent does not expose a callable solve")
    return solve


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.resume:
        parser.error("--resume is unsupported by the empty-output harness")

    try:
        bundle = preflight_inputs(args.dataset, args.queries, args.out)
    except InputValidationError as exc:
        print(f"error: input validation failed: {exc}", file=sys.stderr)
        return 2

    try:
        solve = _load_solver(args.agent)
        writer = OutputWriter(bundle.out_dir)
        writer.initialize()
    except (RuntimeError, OutputWriteError):
        print("error: harness could not initialize the selected agent and outputs", file=sys.stderr)
        return 3

    for row in bundle.rows:
        started = time.monotonic()
        try:
            solution = solve(
                row.instruction,
                bundle.dataset_dir,
                {
                    "row_id": row.row_id,
                    "dataset_dir": bundle.dataset_dir,
                    "out_dir": bundle.out_dir,
                },
            )
            if not isinstance(solution, Solution):
                raise TypeError("agent solve did not return a Solution")
            writer.write_case(row, solution, time.monotonic() - started)
        except Exception:
            print(f"error: harness could not persist case {row.row_id}", file=sys.stderr)
            return 3

    print("Harness-only run complete: predictions are intentionally blank; diagnosis is not implemented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["Solution", "main"]
