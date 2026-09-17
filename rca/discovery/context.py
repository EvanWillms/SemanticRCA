"""Shared, bounded preparation for one immutable discovery run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .budget import BudgetExceeded, CaseBudget, RunBudget
from rca.telemetry.inventory import inventory
from rca.telemetry.trace_index import (
    PreparedTraceView,
    TraceIndexBudgetExceeded,
    TRACE_EXTRACTION_VERSION,
    TRACE_INDEX_VERSION,
    TRACE_PARSER_VERSION,
    prepare_sources,
)


SHARED_PREPARATION_LIMIT_S = 180.0
RUN_LIMIT_S = 1180


class _PreparationBudget:
    """Expose the common ``check`` protocol to inventory and trace indexing."""

    def __init__(self, run_budget: RunBudget, case_budget: CaseBudget,
                 preparation_wall_s: float, started: float) -> None:
        self._run_budget = run_budget
        self._case_budget = case_budget
        self._preparation_wall_s = preparation_wall_s
        self._started = started

    def check(self) -> None:
        now = self._run_budget.clock()
        if now >= self._run_budget.deadline:
            raise BudgetExceeded("run_time_budget_exhausted")
        if now >= self._case_budget.deadline:
            raise BudgetExceeded("case_time_budget_exhausted")
        elapsed = max(0.0, now - self._started)
        if self._preparation_wall_s + elapsed >= SHARED_PREPARATION_LIMIT_S:
            raise BudgetExceeded("shared_preparation_time_budget_exhausted")


def _stable_id(deployment: str, snapshot: Mapping[str, Any],
               view: PreparedTraceView | None) -> str:
    """Return an identity for the verified preparation inputs and versions."""
    payload = {
        "deployment": deployment,
        "snapshot_id": view.snapshot_id if view is not None else None,
        "sources": [
            {"path": source.get("path"), "sha256": source.get("sha256")}
            for source in (view.sources if view is not None else snapshot.get("sources", []))
        ],
        "inventory_schema_version": snapshot.get("schema_version"),
        "index_version": TRACE_INDEX_VERSION,
        "parser_version": TRACE_PARSER_VERSION,
        "extraction_version": TRACE_EXTRACTION_VERSION,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


class RunContext:
    """Own one run's shared prepared source views and preparation accounting."""

    def __init__(self, dataset: Path, out: Path, run_budget: RunBudget) -> None:
        self.dataset = Path(dataset).resolve(strict=True)
        self.out = Path(out).resolve()
        self.run_budget = run_budget
        self._prepared: dict[str, dict[str, Any]] = {}
        self._ledger: list[dict[str, Any]] = []
        self._preparation_wall_s = 0.0

    @property
    def ledger(self) -> list[dict[str, Any]]:
        """JSON-compatible preparation attempt records."""
        return self._ledger

    @property
    def preparation_wall_s(self) -> float:
        return self._preparation_wall_s

    def prepare(self, deployment: str, case_budget: CaseBudget) -> dict[str, Any]:
        """Inventory and prepare ``deployment`` once, then return its view."""
        deployment = str(deployment)
        cached = self._prepared.get(deployment)
        if cached is not None:
            return {
                "snapshot": cached["snapshot"],
                "view": cached["view"],
                "preparation_id": cached["preparation_id"],
                "reused": True,
            }

        preparation_started = self.run_budget.clock()
        preparation_id = hashlib.sha256(
            json.dumps({"deployment": deployment, "attempt": len(self._ledger) + 1},
                       sort_keys=True).encode("utf-8")
        ).hexdigest()
        attempt: dict[str, Any] = {
            "id": preparation_id,
            "deployment": deployment,
            "status": "failed",
            "wall_s": 0.0,
            "index_path": None,
            "source_id": None,
            "source_digests": [],
            "versions": {},
        }
        budget = _PreparationBudget(self.run_budget, case_budget,
                                    self._preparation_wall_s, preparation_started)
        try:
            budget.check()
            snapshot = inventory(self.dataset, deployment, check_budget=budget.check)
            # Hashing the deployment keeps output names portable and prevents
            # deployment text from becoming a path component.
            deployment_dir = self.out / "prepared" / hashlib.sha256(
                deployment.encode("utf-8")).hexdigest()
            has_trace_source = any(source.get("family") == "trace_span"
                                   for source in snapshot.get("sources", []))
            view = (prepare_sources(self.dataset, snapshot, deployment_dir,
                                    work_budget=budget)
                    if has_trace_source else None)
            budget.check()
            preparation_id = _stable_id(deployment, snapshot, view)
            attempt["id"] = preparation_id
            attempt["status"] = "completed"
            attempt["source_id"] = view.snapshot_id if view is not None else None
            attempt["index_path"] = (
                view.index_path.relative_to(self.out).as_posix()
                if view is not None else None
            )
            attempt["source_digests"] = [
                {"path": source["path"], "sha256": source["sha256"]}
                for source in (view.sources if view is not None else snapshot.get("sources", []))
            ]
            attempt["versions"] = {
                "inventory": snapshot.get("schema_version"),
                "sources": sorted({source.get("schema_version") for source in snapshot.get("sources", [])
                                    if source.get("schema_version") is not None}),
                "index": TRACE_INDEX_VERSION,
                "parser": TRACE_PARSER_VERSION,
                "extraction": TRACE_EXTRACTION_VERSION,
            }
            result = {
                "snapshot": snapshot,
                "view": view,
                "preparation_id": preparation_id,
                "reused": False,
            }
            self._prepared[deployment] = result
            return result
        except (BudgetExceeded, TraceIndexBudgetExceeded) as exc:
            # The trace index translates its own budget exception; inventory
            # uses the common budget callback directly, so normalize both.
            raise TraceIndexBudgetExceeded(str(exc)) from exc
        except Exception:
            raise
        finally:
            elapsed = max(0.0, self.run_budget.clock() - preparation_started)
            attempt["wall_s"] = elapsed
            self._preparation_wall_s += elapsed
            if attempt not in self._ledger:
                self._ledger.append(attempt)

    def metadata(self) -> dict[str, Any]:
        return {
            "shared_preparation_wall_s": self._preparation_wall_s,
            "preparations": self._ledger,
            "budgets": {
                "run_limit_s": RUN_LIMIT_S,
                "shared_preparation_limit_s": SHARED_PREPARATION_LIMIT_S,
            },
        }


__all__ = ["RunContext"]
