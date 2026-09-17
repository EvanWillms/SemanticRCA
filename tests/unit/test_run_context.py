from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from rca.discovery.budget import RunBudget
from rca.discovery.context import RunContext


TRACE_HEADER = [
    "timestamp", "cmdb_id", "span_id", "trace_id", "duration", "type",
    "status_code", "operation_name", "parent_span",
]


class RunContextTests(unittest.TestCase):
    def test_prepare_reuses_one_verified_view_and_ledger_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = root / "dataset"
            source = dataset / "telemetry" / "p1" / "trace" / "trace_span.csv"
            source.parent.mkdir(parents=True)
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(TRACE_HEADER)
                writer.writerow(["1000", "frontend", "span-1", "trace-1", "1", "http", "200", "GET /", ""])

            out = root / "out"
            run_budget = RunBudget()
            context = RunContext(dataset, out, run_budget)
            first = context.prepare("demo", run_budget.allocate(1))
            second = context.prepare("demo", run_budget.allocate(1))

            self.assertIs(first["view"], second["view"])
            self.assertFalse(first["reused"])
            self.assertTrue(second["reused"])
            self.assertEqual(first["preparation_id"], second["preparation_id"])
            self.assertEqual(len(context.ledger), 1)
            self.assertEqual(context.ledger[0]["status"], "completed")
            self.assertEqual(context.ledger[0]["source_id"], first["view"].snapshot_id)
            index_path = first["view"].index_path
            self.assertTrue(index_path.is_relative_to(context.out))
            self.assertTrue(index_path.is_file())
            with source.open(newline="", encoding="utf-8") as handle:
                self.assertEqual(sum(1 for _ in csv.DictReader(handle)), 1)
            self.assertEqual(context.metadata()["budgets"]["shared_preparation_limit_s"], 180)


if __name__ == "__main__":
    unittest.main()
