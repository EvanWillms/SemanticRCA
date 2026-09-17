"""The discovery CLI reaches query traces beyond the first reference page."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.demo_discovery import START, _write_bundle


class DiscoveryPaginationTests(unittest.TestCase):
    def test_query_trace_after_forty_references_produces_a_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, out = root / 'bundle', root / 'out'
            query = _write_bundle(bundle)
            path = bundle / 'telemetry/2025_06_15/trace/trace_span.csv'
            with path.open(newline='') as handle:
                reader = csv.DictReader(handle)
                columns, rows = reader.fieldnames, list(reader)
            for index in range(20):
                rows.append(dict(zip(columns, (
                    (START - 250 + index) * 1000, 'frontend-0', 'root',
                    f'additional-{index:02}', 100, 'rpc', '0', 'GET /', '',
                ))))
            # Later-appended history keeps physical file order unlike time order.
            with path.open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
            completed = subprocess.run([
                sys.executable, 'run.py', '--dataset', str(bundle), '--queries', str(query),
                '--out', str(out), '--agent', 'agents.discovery',
            ], capture_output=True, text=True, timeout=20)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            findings = json.loads((out / 'cases/1/findings.json').read_text())
            duration = next(item for item in findings['candidates'] if item['channel'] == 'trace_duration')
            self.assertEqual(duration['difference'], 200)
            self.assertEqual(duration['reference_count'], 40)
            self.assertEqual(len(findings['recorded_traces']), 41)
            self.assertEqual(findings['trace_coverage']['withheld_count'], 0)
            operations = [json.loads(line) for line in (out / 'cases/1/operations.jsonl').read_text().splitlines()]
            pages = [item for item in operations if item['operation'] == 'recover_traces']
            self.assertEqual([item['arguments']['offset'] for item in pages], [0, 30])
            self.assertEqual([item['returned_count'] for item in pages], [30, 11])
            self.assertEqual([item['next_offset'] for item in pages], [30, None])
            self.assertEqual(len({item['source_id'] for item in pages}), 1)
            self.assertEqual(findings['status'], 'completed')

    def test_later_page_deadline_preserves_completed_query_comparisons(self):
        from datetime import datetime, timedelta, timezone
        from unittest.mock import patch
        from rca.discovery.budget import BudgetExceeded
        from rca.discovery import pipeline
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / 'bundle'
            _write_bundle(bundle)
            path = bundle / 'telemetry/2025_06_15/trace/trace_span.csv'
            with path.open(newline='') as handle:
                reader = csv.DictReader(handle)
                columns, rows = reader.fieldnames, list(reader)
            for index in range(10):
                rows.append({**rows[-1], 'trace_id': f'query-{index:02}',
                             'timestamp': (START + 20 + index) * 1000})
            with path.open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
            start = datetime.fromtimestamp(START, timezone(timedelta(hours=8)))
            scope = {'deployment': 'cloudbed-8', 'window_start': start.isoformat(),
                     'window_end': (start + timedelta(minutes=30)).isoformat()}
            recover = pipeline.recover_traces
            def stop_after_first_page(*args, **kwargs):
                if kwargs.get('offset', 0):
                    raise BudgetExceeded('test page boundary')
                return recover(*args, **kwargs)
            with patch.object(pipeline, 'recover_traces', side_effect=stop_after_first_page):
                result = pipeline.discover(bundle, scope, 7)
            findings = result['findings']
            self.assertEqual(findings['status'], 'partial')
            self.assertEqual(findings['stop_reason'], 'analysis_time_budget_exhausted')
            self.assertEqual(len(findings['recorded_traces']), 30)
            self.assertEqual(findings['trace_coverage']['next_offset'], 30)
            self.assertEqual(findings['trace_coverage']['withheld_count'], 1)
            duration = [item for item in findings['candidates'] if item['channel'] == 'trace_duration']
            self.assertEqual(len(duration), 10)
            self.assertTrue(all(item['difference'] == 200 and item['reference_count'] == 20 for item in duration))
            self.assertEqual(result['operations'][-1]['arguments']['offset'], 30)
            self.assertEqual(result['operations'][-1]['status'], 'budget_exhausted')
