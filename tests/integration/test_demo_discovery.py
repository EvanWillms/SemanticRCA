"""The one-command synthetic discovery demonstration stays reproducible."""

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class DemoDiscoveryTests(unittest.TestCase):
    def test_demo_generates_bundle_runs_discovery_and_writes_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "demo"
            result = subprocess.run(
                [sys.executable, "scripts/demo_discovery.py", "--out", str(root)],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            bundle = root / "bundle"
            results = root / "results"
            query = bundle / "query.csv"
            self.assertTrue(query.is_file())
            with query.open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["row_id"], "1")

            families = {
                "metric_container",
                "metric_mesh",
                "metric_node",
                "metric_runtime",
                "metric_service",
                "log_service",
                "log_proxy",
                "trace_span",
            }
            supplied = {
                path.stem
                for path in (bundle / "telemetry" / "2025_06_15").glob("*/*.csv")
            }
            self.assertEqual(supplied, families)

            with (results / "predictions.csv").open(newline="") as handle:
                self.assertEqual(
                    list(csv.DictReader(handle)),
                    [{"row_id": "1", "prediction": ""}],
                )
            findings = json.loads((results / "cases/1/findings.json").read_text())
            self.assertEqual(findings["status"], "completed")
            self.assertTrue(
                any(
                    finding["channel"] == "trace_duration"
                    and finding["difference"] == 200
                    for finding in findings["candidates"]
                )
            )
            self.assertTrue(
                any(
                    finding["channel"] == "metric"
                    and finding["resource"] == "worker-2"
                    and finding["signed_difference"] == 25
                    for finding in findings["candidates"]
                )
            )
            usage = (results / "usage.jsonl").read_text().strip()
            self.assertEqual(json.loads(usage)["calls"], 0)
            self.assertIn("resource busy", (results / "evidence/1.md").read_text())

            baseline_report = root / "baselines" / "demo.json"
            self.assertTrue(baseline_report.is_file())
            baseline = json.loads(baseline_report.read_text())
            self.assertEqual(baseline["status"], "completed")
            self.assertEqual(len(baseline["baselines"]), 1)
            self.assertEqual(baseline["baselines"][0]["support"], "supported")
            self.assertEqual(baseline["baselines"][0]["member_count"], 20)
            self.assertEqual(len(baseline["descriptors"]), 1)
            self.assertAlmostEqual(
                baseline["descriptors"][0]["duration"]["signed_excess"]["value"],
                0.2,
            )

            investigation = json.loads((root / "investigation.json").read_text())
            self.assertEqual(investigation["investigation_stop_reason"], "evidence_sufficient")
            self.assertEqual(investigation["usage"]["assessment_attempts"], 2)
            self.assertEqual(investigation["usage"]["operation_attempts"], 1)

            summary = (root / "demo.md").read_text()
            self.assertIn("Synthetic fixture", summary)
            self.assertIn("Discovery only", summary)
            self.assertIn("trace_span.csv", summary)
            self.assertIn("metric_container.csv", summary)


if __name__ == "__main__":
    unittest.main()
