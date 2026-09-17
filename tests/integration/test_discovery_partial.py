"""Discovery retains completed evidence when a later operation fails."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.demo_discovery import DEPLOYMENT, START, _write_bundle


TRACE_SEMANTICS = Path(__file__).parents[2] / "libraries" / "trace_semantics" / "src"
if str(TRACE_SEMANTICS) not in sys.path:
    sys.path.insert(0, str(TRACE_SEMANTICS))

from rca.discovery import pipeline
from rca.discovery.budget import BudgetExceeded


class DiscoveryPartialTests(unittest.TestCase):
    def _scope(self):
        start = datetime.fromtimestamp(START, timezone(timedelta(hours=8)))
        return {
            "deployment": DEPLOYMENT,
            "window_start": start.isoformat(),
            "window_end": (start + timedelta(minutes=30)).isoformat(),
            "failure_count": 1,
            "requested_fields": ["component"],
        }

    def test_late_log_failure_keeps_prior_findings_and_journals_failure(self):
        for failure, reason, status in (
            (ValueError("log failed"), "operation_failed", "failed"),
            (BudgetExceeded("time limit"), "analysis_time_budget_exhausted", "budget_exhausted"),
        ):
            with self.subTest(failure=type(failure).__name__), tempfile.TemporaryDirectory() as directory:
                bundle = Path(directory) / "bundle"
                _write_bundle(bundle)
                with patch.object(pipeline, "inspect_logs", side_effect=failure):
                    result = pipeline.discover(bundle, self._scope(), row_id=1)
                findings = result["findings"]
                self.assertEqual(findings["status"], "partial")
                self.assertEqual(findings["stop_reason"], reason)
                self.assertTrue(findings["source_id"])
                self.assertTrue(findings["source_snapshot"]["sources"])
                self.assertTrue(findings["recorded_traces"])
                self.assertTrue(any(item["channel"] == "trace_duration" and item["difference"] == 200
                                    for item in findings["findings"]))
                self.assertTrue(any(item["channel"] == "metric" and item.get("signed_difference") == 25
                                    for item in findings["findings"]))
                self.assertNotIn("metric_series", findings)
                failed = result["operations"][-1]
                self.assertEqual(failed["operation"], "inspect_logs")
                self.assertEqual(failed["status"], status)
                self.assertEqual(failed["stop_reason"], reason)
                self.assertEqual(failed["source_id"], findings["source_id"])

    def test_metric_comparison_failure_keeps_recovered_trace_and_metric_series(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "bundle"
            _write_bundle(bundle)

            with patch("rca.telemetry.metrics.compare_series", side_effect=ValueError("compare failed")):
                result = pipeline.discover(bundle, self._scope(), row_id=1)

            findings = result["findings"]
            self.assertEqual(findings["status"], "partial")
            self.assertEqual(findings["stop_reason"], "operation_failed")
            self.assertTrue(findings["recorded_traces"])
            self.assertTrue(findings["findings"])
            self.assertTrue(any(item["channel"] == "trace_duration" for item in findings["findings"]))
            self.assertTrue(findings["metric_series"])
            self.assertEqual(result["operations"][-1]["operation"], "compare")
            self.assertEqual(result["operations"][-1]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
