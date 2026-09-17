from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from rca.telemetry import InventoryBudgetExceeded, inventory


class InventoryHappyPathTests(unittest.TestCase):
    def test_discovers_allowed_sources_schema_units_identities_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = Path(temporary)
            telemetry = dataset / "telemetry" / "2024_06_01"
            rows_by_family = {
                "metric_container": (
                    ["timestamp", "cmdb_id", "kpi_name", "value"],
                    [["1717200000", "checkout-2", "cpu_usage", "0.5"]],
                ),
                "metric_mesh": (
                    ["timestamp", "cmdb_id", "kpi_name", "value"],
                    [["1717200000", "checkout-2.destination.frontend.checkout", "request_count", "3"]],
                ),
                "metric_node": (
                    ["timestamp", "cmdb_id", "kpi_name", "value"],
                    [["1717200000", "node-7", "disk_read", "4"]],
                ),
                "metric_runtime": (
                    ["timestamp", "cmdb_id", "kpi_name", "value"],
                    [["1717200000", "checkout.ts:8080", "gc_pause", "0.1"]],
                ),
                "metric_service": (
                    ["service", "timestamp", "rr", "sr", "mrt", "count"],
                    [["checkout", "1717200000", "0.1", "0.2", "12", "9"]],
                ),
                "log_service": (
                    ["log_id", "timestamp", "cmdb_id", "log_name", "value"],
                    [["log-1", "1717200000", "checkout-2", "request", "ok"]],
                ),
                "log_proxy": (
                    ["log_id", "timestamp", "cmdb_id", "log_name", "value"],
                    [["log-2", "1717200000", "proxy", "route", "ok"]],
                ),
                "trace_span": (
                    [
                        "timestamp",
                        "cmdb_id",
                        "span_id",
                        "trace_id",
                        "duration",
                        "type",
                        "status_code",
                        "operation_name",
                        "parent_span",
                    ],
                    [["1717200000000", "frontend", "span-1", "trace-1", "2.5", "rpc", "0", "GET /", ""]],
                ),
            }
            file_paths: dict[str, Path] = {}
            for family, (header, rows) in rows_by_family.items():
                directory = telemetry / ("trace" if family == "trace_span" else "log" if family.startswith("log_") else "metric")
                directory.mkdir(parents=True, exist_ok=True)
                path = directory / f"{family}.csv"
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.writer(handle, lineterminator="\n")
                    writer.writerow(header)
                    writer.writerows(rows)
                file_paths[family] = path

            # A developer/evaluation artifact is present but outside the allowed source registry.
            (dataset / "dev").mkdir()
            (dataset / "dev" / "query_dev.csv").write_text("scoring_points\nanswer\n", encoding="utf-8")

            result = inventory(dataset, "Cloudbed-7")

            self.assertEqual(result["deployment"], "Cloudbed-7")
            self.assertEqual(result["unavailable_families"], [])
            self.assertEqual({source["family"] for source in result["sources"]}, set(rows_by_family))
            for family, path in file_paths.items():
                source = next(item for item in result["sources"] if item["family"] == family)
                self.assertEqual(source["path"], path.relative_to(dataset).as_posix())
                self.assertEqual(source["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(source["columns"], rows_by_family[family][0])
                self.assertIn("timestamp_unit", source)
                self.assertNotIn("query_dev.csv", source["path"])

            container = next(item for item in result["sources"] if item["family"] == "metric_container")
            self.assertEqual(container["timestamp_unit"], "seconds")
            self.assertEqual(container["raw_units"], {"timestamp": "seconds", "value": "raw/unknown"})
            self.assertEqual(container["resources"], ["checkout-2"])
            self.assertEqual(container["kpis"], ["cpu_usage"])
            self.assertEqual(container["resource_kpis"], [{"resource": "checkout-2", "kpi": "cpu_usage"}])

            service = next(item for item in result["sources"] if item["family"] == "metric_service")
            self.assertEqual(service["resources"], ["checkout"])
            self.assertEqual(service["kpis"], ["count", "mrt", "rr", "sr"])
            self.assertEqual(service["timestamp_unit"], "seconds")

            trace = next(item for item in result["sources"] if item["family"] == "trace_span")
            self.assertEqual(trace["timestamp_unit"], "milliseconds")
            self.assertEqual(trace["raw_units"]["duration"], "raw/unknown")
            self.assertEqual(trace["operations"], ["GET /"])

    def test_budget_check_stops_a_multi_batch_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = Path(temporary)
            path = dataset / "telemetry" / "2024_06_01" / "metric" / "metric_container.csv"
            path.parent.mkdir(parents=True)
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(["timestamp", "cmdb_id", "kpi_name", "value"])
                for index in range(5_000):
                    writer.writerow([str(index), "checkout-2", "cpu_usage", str(index)])

            checks = 0

            def check_budget() -> None:
                nonlocal checks
                checks += 1
                if checks == 3:
                    raise InventoryBudgetExceeded("test budget exhausted")

            with self.assertRaises(InventoryBudgetExceeded):
                inventory(dataset, "cloudbed-7", check_budget=check_budget)
            # One check occurs in hashing and two more at CSV batch boundaries.
            self.assertEqual(checks, 3)


if __name__ == "__main__":
    unittest.main()
