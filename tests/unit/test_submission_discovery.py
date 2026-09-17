"""Bounded assessment retrieval preserves evidence and source boundaries."""
from pathlib import Path
import tempfile
import unittest

from rca.discovery.budget import BudgetExceeded
from rca.discovery.submission import discover
from scripts.demo_discovery import START, _write_csv


SCOPE = {'deployment': 'cloudbed-8', 'window_start': '2025-06-15T09:00:00+08:00',
         'window_end': '2025-06-15T09:30:00+08:00'}


class SubmissionDiscoveryTests(unittest.TestCase):
    def _source(self, root, extra=()):
        rows = [(START - 1800 + i * 60, 'node-3', 'system.cpu', 10) for i in range(30)]
        rows += [(START + 60, 'node-3', 'system.cpu', 35), *extra]
        _write_csv(root / 'telemetry/2025_06_15/metric/metric_node.csv',
                   ('timestamp', 'cmdb_id', 'kpi_name', 'value'), rows)

    def test_completed_measurements_survive_later_timeout(self):
        class Budget:
            calls = 0

            def check(self):
                self.calls += 1
                if self.calls == 3:
                    raise BudgetExceeded('analysis_time_budget_exhausted')

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._source(root)
            result = discover(root, SCOPE, 19, Budget())['findings']
            self.assertEqual(result['stop_reason'], 'analysis_time_budget_exhausted')
            self.assertEqual(result['candidates'][0]['value'], 35)
            self.assertEqual(result['candidates'][0]['reference_median'], 10)

    def test_conflicting_query_samples_are_not_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._source(root, [(START + 60, 'node-3', 'system.cpu', 999)])
            self.assertEqual(discover(root, SCOPE, 19)['findings']['candidates'], [])

    def test_out_of_scope_dates_and_trace_files_are_not_opened(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._source(root)
            for relative in ('telemetry/2024_06_15/metric/metric_node.csv',
                             'telemetry/2025_06_15/trace/trace_span.csv'):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to('/this-file-must-not-be-opened')
            result = discover(root, SCOPE, 19)['findings']
            self.assertEqual(len(result['candidates']), 1)
            self.assertEqual(len(result['source_snapshot']['sources']), 1)
            self.assertEqual(result['coverage']['traces'], 'not_inspected')
