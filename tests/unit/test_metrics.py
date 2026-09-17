"""Metric retrieval and reference-relative comparison at the public seam."""

from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rca.telemetry.metrics import compare_series, metric_series


UTC8 = timezone(timedelta(hours=8))


def _write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


class MetricSeriesTests(unittest.TestCase):
    def test_reads_all_metric_families_in_scoped_windows_with_provenance(self) -> None:
        start = datetime(2024, 6, 1, 0, 30, tzinfo=UTC8)
        start_s = int(start.timestamp())
        with tempfile.TemporaryDirectory() as temporary:
            dataset = Path(temporary)
            long_header = ["timestamp", "cmdb_id", "kpi_name", "value"]
            for family, resource, kpi in (
                ("metric_container", "pod-1", "cpu"),
                ("metric_node", "node-1", "iowait"),
                ("metric_mesh", "pod-1.destination.api", "bytes"),
                ("metric_runtime", "api.ts:8080", "gc"),
            ):
                _write_csv(
                    dataset / "telemetry" / "2024_06_01" / "metric" / f"{family}.csv",
                    long_header,
                    [[start_s - 300, resource, kpi, 10], [start_s, resource, kpi, 14]],
                )
            _write_csv(
                dataset / "telemetry" / "2024_06_01" / "metric" / "metric_service.csv",
                ["service", "timestamp", "rr", "sr", "mrt", "count"],
                [["api", start_s - 300, 1, 2, 3, 4], ["api", start_s, 5, 6, 7, 8]],
            )
            sources = []
            for path in sorted((dataset / "telemetry" / "2024_06_01" / "metric").glob("*.csv")):
                family = path.stem
                sources.append({"family": family, "path": path.relative_to(dataset).as_posix(), "sha256": "digest"})

            result = metric_series(
                dataset,
                {"deployment": "cloudbed-7", "sources": sources},
                {
                    "deployment": "cloudbed-7",
                    "window_start": start.isoformat(),
                    "window_end": (start + timedelta(minutes=30)).isoformat(),
                },
            )

            self.assertEqual(result["status"], "completed")
            self.assertEqual({item["family"] for item in result["series"]}, {
                "metric_container", "metric_node", "metric_mesh", "metric_runtime", "metric_service",
            })
            service = {(item["resource"], item["kpi"]): item for item in result["series"] if item["family"] == "metric_service"}
            self.assertEqual(set(service), {("api", "rr"), ("api", "sr"), ("api", "mrt"), ("api", "count")})
            self.assertEqual(service[("api", "rr")]["historical5min"][0]["value"], 1.0)
            self.assertEqual(service[("api", "rr")]["query"][0]["value"], 5.0)
            self.assertEqual(service[("api", "rr")]["query"][0]["locator"]["path"],
                             "telemetry/2024_06_01/metric/metric_service.csv")

    def test_deduplicates_identical_samples_and_retains_conflicts(self) -> None:
        start = int(datetime(2024, 6, 1, 0, 30, tzinfo=UTC8).timestamp())
        with tempfile.TemporaryDirectory() as temporary:
            dataset = Path(temporary)
            path = dataset / "telemetry" / "2024_06_01" / "metric" / "metric_node.csv"
            _write_csv(path, ["timestamp", "cmdb_id", "kpi_name", "value"], [
                [start - 60, "node-1", "cpu", 1],
                [start - 60, "node-1", "cpu", 1],
                [start - 60, "node-1", "cpu", 2],
                [start, "node-1", "cpu", 3],
            ])
            result = metric_series(dataset, {
                "deployment": "cloudbed-7",
                "sources": [{"family": "metric_node", "path": path.relative_to(dataset).as_posix(), "sha256": "digest"}],
            }, {"deployment": "cloudbed-7", "window_start": datetime.fromtimestamp(start, UTC8).isoformat(),
               "window_end": datetime.fromtimestamp(start + 1800, UTC8).isoformat()})
            history = result["series"][0]["historical5min"]
            self.assertEqual(len(history), 2)
            self.assertEqual(len(history[0]["provenance"]), 2)
            self.assertTrue(all(item["conflict"] for item in history))

    def test_comparison_uses_median_and_keeps_both_signed_directions(self) -> None:
        history = [
            {"timestamp": i, "value": 10.0, "conflict": False, "locator": {"record": i}, "provenance": []}
            for i in range(20)
        ]
        query = [
            {"timestamp": 100, "value": 13.0, "conflict": False, "locator": {"record": 100}, "provenance": []},
            {"timestamp": 101, "value": 7.0, "conflict": False, "locator": {"record": 101}, "provenance": []},
        ]
        result = compare_series({"status": "completed", "series": [{
            "family": "metric_node", "resource": "node-1", "kpi": "cpu", "unit": "raw/unknown",
            "historical5min": history, "query": query,
        }]})
        self.assertEqual(result["status"], "completed")
        self.assertEqual([finding["signed_difference"] for finding in result["findings"]], [3.0, -3.0])
        self.assertEqual(len(result["candidates"]), 2)


if __name__ == "__main__":
    unittest.main()


class PartialComparisonTests(unittest.TestCase):
    def test_partial_retrieval_cannot_be_reported_as_completed_comparison(self):
        result = compare_series({'status': 'partial', 'series': []})
        self.assertEqual(result['status'], 'partial')
