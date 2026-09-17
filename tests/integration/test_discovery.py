"""Discovery behavior through the supported CLI and persisted artifacts."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class DiscoveryCLITests(unittest.TestCase):
    def test_scope_is_persisted_when_telemetry_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / 'data'
            dataset.mkdir()
            queries = dataset / 'query.csv'
            instruction = ('On June 15, 2025, between 09:00 and 09:30, the system '
                           'cloudbed-8 experienced one failure. Please identify the '
                           'root cause component.')
            with queries.open('w', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(['row_id', 'task_index', 'instruction'])
                writer.writerow([42, 'task_3', instruction])
            output = root / 'out'
            result = subprocess.run(
                [sys.executable, 'run.py', '--dataset', str(dataset), '--queries',
                 str(queries), '--out', str(output), '--agent', 'agents.discovery'],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            scope = json.loads((output / 'cases/42/scope.json').read_text())
            self.assertEqual(scope['status'], 'interpreted')
            self.assertEqual(scope['scope']['deployment'], 'cloudbed-8')
            self.assertEqual(scope['scope']['requested_fields'], ['component'])
            findings = json.loads((output / 'cases/42/findings.json').read_text())
            self.assertEqual(findings['status'], 'unavailable')
            self.assertEqual(findings['stop_reason'], 'missing_telemetry_sources')
            self.assertEqual(json.loads((output / 'cases/42/operations.jsonl').read_text())['operation'], 'inventory')
            with (output / 'predictions.csv').open() as handle:
                self.assertEqual(list(csv.DictReader(handle)), [{'row_id': '42', 'prediction': ''}])
            self.assertEqual(json.loads((output / 'usage.jsonl').read_text())['calls'], 0)
            self.assertIn('unavailable', (output / 'evidence/42.md').read_text())
            run = json.loads((output / 'discovery-run.json').read_text())
            self.assertEqual(run['capability'], 'discovery')
            self.assertEqual(run['cases'][0]['row_id'], 42)

    def test_cli_persists_trace_and_independent_metric_candidates(self):
        from datetime import datetime
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / 'data'; dataset.mkdir()
            start = int(datetime.fromisoformat('2025-06-15T09:00:00+08:00').timestamp())
            partition = dataset / 'telemetry/2025_06_15'

            def source(family, columns, rows):
                modality = family.split('_')[0]
                path = partition / modality / (family + '.csv')
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('w', newline='') as handle:
                    writer = csv.writer(handle); writer.writerow(columns); writer.writerows(rows)

            trace_rows = []
            for i in range(21):
                timestamp = (start - 100 + i if i < 20 else start + 10) * 1000
                trace_rows.append([timestamp, 'frontend-9', 'root', f't{i}', 100 if i < 20 else 300,
                                   'rpc', '0', 'GET /', ''])
            source('trace_span', ['timestamp', 'cmdb_id', 'span_id', 'trace_id', 'duration',
                                 'type', 'status_code', 'operation_name', 'parent_span'], trace_rows)
            samples = [[start - 100 + i, 'worker-2', 'cpu', 10] for i in range(20)]
            samples.append([start + 10, 'worker-2', 'cpu', 35])
            for family in ('metric_container', 'metric_node', 'metric_mesh', 'metric_runtime'):
                source(family, ['timestamp', 'cmdb_id', 'kpi_name', 'value'], samples)
            source('metric_service', ['service', 'timestamp', 'rr', 'sr', 'mrt', 'count'],
                   [['worker', start - 100 + i, 1, 1, 10, 5] for i in range(20)] +
                   [['worker', start + 10, 1, 1, 10, 5]])
            for family in ('log_service', 'log_proxy'):
                source(family, ['log_id', 'timestamp', 'cmdb_id', 'log_name', 'value'],
                       [['log1', start + 10, 'worker-2', 'app', 'resource busy']])
            queries = dataset / 'query.csv'
            with queries.open('w', newline='') as handle:
                writer = csv.writer(handle); writer.writerow(['row_id', 'instruction'])
                writer.writerow([9, 'The system cloudbed-8 experienced one failure on June 15, 2025, '
                                    'from 09:00 to 09:30. Please identify the root cause component.'])
            out = root / 'out'
            run = subprocess.run([sys.executable, 'run.py', '--dataset', str(dataset),
                                  '--queries', str(queries), '--out', str(out), '--agent', 'agents.discovery'],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            findings = json.loads((out / 'cases/9/findings.json').read_text())
            self.assertEqual(findings['status'], 'completed')
            self.assertEqual(findings['semantic_description']['schema_version'], 'trace-description-v1')
            self.assertEqual(len(findings['semantic_description']['traces']), 1)
            candidates = findings['candidates']
            self.assertTrue(any(c['channel'] == 'trace_duration' and c['difference'] == 200 for c in candidates))
            self.assertTrue(any(c['channel'] == 'metric' and c['resource'] == 'worker-2' and c['signed_difference'] == 25 for c in candidates))
            self.assertGreater(len(candidates), 1)  # Count is independent of the one-failure prompt.
            operations = [json.loads(line) for line in (out / 'cases/9/operations.jsonl').read_text().splitlines()]
            self.assertTrue({'inventory', 'recover_traces', 'metric_series', 'compare', 'inspect_logs'} <=
                            {operation['operation'] for operation in operations})
            self.assertIn('resource busy', (out / 'evidence/9.md').read_text())
            validation = subprocess.run(
                [sys.executable, 'scripts/validate_discovery.py', '--queries', str(queries),
                 '--out', str(out), '--capability', 'discovery'], capture_output=True, text=True)
            self.assertEqual(validation.returncode, 0, validation.stderr)
            investigation_path = root / 'investigation.json'
            loop = subprocess.run([sys.executable, 'scripts/demo_investigation.py',
                                   '--findings', str(out / 'cases/9/findings.json'),
                                   '--scope', str(out / 'cases/9/scope.json'),
                                   '--out', str(investigation_path)], capture_output=True, text=True)
            self.assertEqual(loop.returncode, 0, loop.stderr)
            investigation = json.loads(investigation_path.read_text())
            self.assertEqual(investigation['investigation_stop_reason'], 'evidence_sufficient')
            self.assertEqual(investigation['answer'], [{'component': 'frontend-9'}])
            self.assertEqual(investigation['usage']['assessment_attempts'], 2)
            self.assertEqual(investigation['usage']['operation_attempts'], 1)
            self.assertFalse(investigation['demo']['real_diagnosis_accuracy_claim'])
