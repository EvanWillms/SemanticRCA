"""Question-directed log evidence through the public operation seam."""
import csv
from pathlib import Path
import tempfile
import unittest

from rca.telemetry.logs import inspect_logs


class LogInspectionTests(unittest.TestCase):
    def test_returns_only_exact_resource_and_window_with_question_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (root / 'logs.csv').open('w', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(['log_id', 'timestamp', 'cmdb_id', 'log_name', 'value'])
                writer.writerows([['a', 10, 'worker-2', 'app', 'retry'],
                                  ['b', 10, 'worker-20', 'app', 'unrelated'],
                                  ['c', 20, 'worker-2', 'app', 'outside']])
            result = inspect_logs(root, {'sources': [{'family': 'log_service', 'path': 'logs.csv',
                                                      'sha256': 'fixture'}]},
                                  'What was logged on the changed resource?', 'worker-2', 10, 20)
            self.assertEqual(result['status'], 'completed')
            self.assertEqual([row['raw']['log_id'] for row in result['observations']], ['a'])
            self.assertEqual(result['observations'][0]['locator']['record'], 2)
            self.assertEqual(result['resource'], 'worker-2')
            self.assertEqual(result['question'], 'What was logged on the changed resource?')
