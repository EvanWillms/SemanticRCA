from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from rca.baselining.observations import collect_requests
from rca.telemetry.inventory import inventory
from rca.telemetry.trace_index import SourceIntegrityError, prepare_sources


HEADER = [
    "timestamp", "cmdb_id", "span_id", "trace_id", "duration", "type",
    "status_code", "operation_name", "parent_span",
]


def _row(timestamp: str, component: str, span: str, trace: str, duration: str,
         parent: str = "", operation: str = "GET /", typ: str = "http") -> list[str]:
    return [timestamp, component, span, trace, duration, typ, "0", operation, parent]


class BaselineSourceBoundaryTests(unittest.TestCase):
    def test_prepare_and_collect_select_allowlisted_roots_and_recover_full_trace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = Path(temporary) / "dataset"
            source = dataset / "telemetry" / "p1" / "trace" / "trace_span.csv"
            source.parent.mkdir(parents=True)
            rows = [
                _row("900", "frontend-0", "r", "reference", "5000"),
                # This child starts beyond the query horizon; complete trace
                # recovery must still retain it once the root is selected.
                _row("2500", "worker", "c", "reference", "1000", "r", "fetch", "rpc"),
                _row("1000", "frontend-1", "q", "query", "2000"),
                _row("1001", "worker", "qc", "query", "1000", "q", "fetch", "rpc"),
                _row("950", "frontend-9", "outside", "outside", "1000"),
            ]
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(HEADER)
                writer.writerows(rows)
            source_inventory = inventory(dataset, "demo")
            view = prepare_sources(dataset, source_inventory, Path(temporary) / "out")
            batch = collect_requests(view, "demo", 1000, {
                "allowlist": ["frontend-0", "frontend-1", "frontend-2"],
                "lookback_ms": 300, "horizon_ms": 1800, "slice_ms": 300,
            })

            self.assertEqual(view["record_count"], 5)
            self.assertEqual(len(batch.observations), 2)
            reference = next(item for item in batch.observations if item.identity.trace_id == "reference")
            self.assertEqual(reference.endpoint_ms, Decimal("2501"))
            self.assertEqual(len(reference.children), 1)
            self.assertEqual(batch.recovery_receipt.recovered_records, 4)
            self.assertEqual(batch.unresolved[0]["reasons"], ["out_of_scope"])

    def test_endpoint_equal_anchor_is_not_reference_eligible_and_duplicate_spans_collapse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = Path(temporary) / "dataset"
            source = dataset / "telemetry" / "p1" / "trace" / "trace_span.csv"
            source.parent.mkdir(parents=True)
            root = _row("900", "frontend-0", "r", "t", "5000")
            child = _row("995", "worker", "c", "t", "5000", "r", "fetch", "rpc")
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(HEADER)
                writer.writerows([root, child, child])
            view = prepare_sources(dataset, inventory(dataset, "demo"), Path(temporary) / "out")
            batch = collect_requests(view, "demo", 1000, {"allowlist": ["frontend-0"]})
            observation = batch.observations[0]
            self.assertEqual(observation.endpoint_ms, Decimal("1000"))
            self.assertEqual(observation.completion_state, "resolved")
            self.assertEqual(observation.children[0].count, 1)

    def test_changed_source_is_rejected_against_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = Path(temporary) / "dataset"
            source = dataset / "telemetry" / "p1" / "trace" / "trace_span.csv"
            source.parent.mkdir(parents=True)
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(HEADER)
                writer.writerow(_row("900", "frontend-0", "r", "t", "1"))
            declared = inventory(dataset, "demo")
            source.write_text(source.read_text(encoding="utf-8").replace(",1,http,0,GET /,", ",2,http,0,GET /,"), encoding="utf-8")
            with self.assertRaises(SourceIntegrityError):
                prepare_sources(dataset, declared, Path(temporary) / "out")


if __name__ == "__main__":
    unittest.main()
