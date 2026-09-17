#!/usr/bin/env python3
"""Official three-flag entrypoint for assessment predictions and evidence."""

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
# The independently packaged trace domain ships with this offline application.
sys.path.insert(0, str(Path(__file__).resolve().parent / "libraries/trace_semantics/src"))

from rca.contracts import Solution
from rca.discovery.budget import RunBudget
from rca.discovery.context import RunContext
from rca.inputs import InputValidationError, preflight_inputs
from rca.outputs import OutputWriteError, OutputWriter

DEFAULT_AGENT = "agents.routed"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess telemetry and write RCA predictions and evidence")
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

    run_started = time.monotonic()
    discovery_mode = args.agent == "agents.discovery"
    submission_mode = args.agent == "agents.routed"
    result_code = 0
    run_budget = RunBudget()
    run_context = RunContext(bundle.dataset_dir, bundle.out_dir, run_budget) if discovery_mode or submission_mode else None
    if discovery_mode:
        try:
            writer.write_discovery_run("discovery", 0.0, len(bundle.rows), run_context.metadata())
        except Exception:
            print("error: discovery run record could not be initialized", file=sys.stderr)
            return 3
    for index, row in enumerate(bundle.rows):
        started = time.monotonic()
        try:
            solution = solve(
                row.instruction,
                bundle.dataset_dir,
                {
                    "row_id": row.row_id,
                    "dataset_dir": bundle.dataset_dir,
                    "out_dir": bundle.out_dir,
                    "task_index": row.task_index,
                    "budget": run_budget.allocate(len(bundle.rows) - index),
                    "run_context": run_context,
                },
            )
            if not isinstance(solution, Solution):
                raise TypeError("agent solve did not return a Solution")
            writer.write_case(row, solution, time.monotonic() - started)
            if solution.discovery is not None:
                if solution.discovery["findings"]["status"] != "completed":
                    result_code = 1
                writer.write_discovery_run("discovery", time.monotonic() - run_started, len(bundle.rows),
                                           run_context.metadata() if run_context else None)
        except Exception:
            print(f"error: harness could not persist case {row.row_id}", file=sys.stderr)
            return 3

    if discovery_mode:
        print("Discovery run persisted: diagnosis pending; see case findings for completed capability.")
    elif submission_mode:
        print("Submission run complete: predictions and source-backed evidence persisted.")
    else:
        print("Harness-only run complete: predictions are intentionally blank; diagnosis is not implemented.")
    return result_code


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["Solution", "main"]
