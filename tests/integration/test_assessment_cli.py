"""Exercise the exact judging CLI with minute-cadence telemetry and no provider."""
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.demo_discovery import START, _write_csv
from scripts.validate_submission import validate


class AssessmentCLITests(unittest.TestCase):
    def test_default_cli_persists_measured_findings_without_models(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, output = root / 'bundle', root / 'out'
            query = bundle / 'query.csv'
            instruction = ('The system cloudbed-8 experienced one failure on June 15, 2025, '
                           'from 09:00 to 09:30. Please identify the root cause occurrence datetime, '
                           'root cause component and root cause reason.')
            datetime_only = instruction.replace('datetime, root cause component and root cause reason', 'datetime')
            _write_csv(query, ('row_id', 'instruction'), [(17, instruction), (93, datetime_only)])
            source = bundle / 'telemetry/2025_06_15/metric/metric_container.csv'
            rows = [(START - 1800 + i * 60, 'node-3.worker-2', 'container_cpu_usage', 10) for i in range(30)]
            rows += [(START + 60, 'node-3.worker-2', 'container_cpu_usage', 35)]
            _write_csv(source, ('timestamp', 'cmdb_id', 'kpi_name', 'value'), rows)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            env.pop('FEATHERLESS_API_KEY', None)
            result = subprocess.run([sys.executable, 'run.py', '--dataset', str(bundle),
                                     '--queries', str(query), '--out', str(output)],
                                    env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            validate(query, output)
            with (output / 'predictions.csv').open() as handle:
                predictions = list(csv.DictReader(handle))
            for row in predictions:
                answer = json.loads(row['prediction'])['1']
                self.assertTrue(all(value == "I don't know" for value in answer.values()))
                evidence = (output / 'evidence' / f"{row['row_id']}.md").read_text()
                self.assertIn('metric_container.csv', evidence)
                self.assertIn('35', evidence)
                self.assertIn('10', evidence)
                self.assertIn('Low.', evidence)
                self.assertNotIn('Observed candidates: []', evidence)
                line = next(line for line in evidence.splitlines() if line.startswith('Observed candidates: '))
                findings = json.loads(line.removeprefix('Observed candidates: '))
                self.assertEqual(findings[0]['resource'], 'node-3.worker-2')
                self.assertEqual(findings[0]['timestamp'], START + 60)
                self.assertEqual(findings[0]['value'], 35)
                self.assertEqual(findings[0]['reference_median'], 10)
                self.assertEqual(findings[0]['reference_count'], 30)
