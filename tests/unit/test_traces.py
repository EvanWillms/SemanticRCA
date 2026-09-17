"""Recorded recovery and comparison through the trace operation boundary."""
import csv
from pathlib import Path
import tempfile
import unittest

from rca.telemetry.inventory import inventory
from rca.telemetry.trace_index import prepare_sources
from rca.telemetry.traces import recover_traces


class TraceRecoveryTests(unittest.TestCase):
    def test_frontend_root_pagination_is_stable_and_matches_prepared_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            columns = ['timestamp', 'cmdb_id', 'span_id', 'trace_id', 'duration',
                       'type', 'status_code', 'operation_name', 'parent_span']
            rows_by_partition = {'p1': [], 'p2': []}
            roots = [(f'trace-{index:02d}', 1000 + index // 2) for index in range(35)]
            for index, (trace_id, timestamp) in enumerate(reversed(roots)):
                partition = 'p1' if index % 2 else 'p2'
                rows_by_partition[partition].append(
                    [timestamp, 'frontend-7', f'root-{trace_id}', trace_id, 100,
                     'rpc', 0, 'GET /', ''])
                child_partition = 'p2' if partition == 'p1' else 'p1'
                rows_by_partition[child_partition].append(
                    [timestamp + 1, 'worker', f'child-{trace_id}', trace_id, 20,
                     'rpc', 0, 'fetch', f'root-{trace_id}'])
            for partition, rows in rows_by_partition.items():
                source = root / 'telemetry' / partition / 'trace' / 'trace_span.csv'
                source.parent.mkdir(parents=True, exist_ok=True)
                with source.open('w', newline='') as handle:
                    writer = csv.writer(handle)
                    writer.writerow(columns)
                    writer.writerows(rows)

            source_inventory = inventory(root, 'demo')
            prepared = prepare_sources(root, source_inventory, root.parent / 'out')
            expected = [trace_id for trace_id, timestamp in sorted(
                roots, key=lambda item: (item[1], item[0]))]
            pages = [recover_traces(root, source_inventory, 1, 2, frontend_only=True,
                                    limit=30, offset=offset)
                     for offset in (0, 30)]
            prepared_pages = [recover_traces(root, source_inventory, 1, 2,
                                             frontend_only=True, limit=30, offset=offset,
                                             prepared_view=prepared)
                              for offset in (0, 30)]

            self.assertEqual([trace['trace_id'] for trace in pages[0]['traces']], expected[:30])
            self.assertEqual([trace['trace_id'] for trace in pages[1]['traces']], expected[30:])
            self.assertEqual(
                {trace['trace_id'] for page in pages for trace in page['traces']},
                set(expected),
            )
            self.assertEqual(
                set(trace['trace_id'] for trace in pages[0]['traces']).isdisjoint(
                    trace['trace_id'] for trace in pages[1]['traces']),
                True,
            )
            for csv_page, prepared_page in zip(pages, prepared_pages):
                self.assertEqual(csv_page['traces'], prepared_page['traces'])
                for key in ('status', 'selected_count', 'returned_count',
                            'withheld_count', 'next_offset'):
                    self.assertEqual(csv_page[key], prepared_page[key])
            self.assertEqual(pages[0]['status'], 'partial')
            self.assertEqual(pages[0]['returned_count'], 30)
            self.assertEqual(pages[0]['withheld_count'], 5)
            self.assertEqual(pages[0]['next_offset'], 30)
            self.assertEqual(pages[1]['status'], 'completed')
            self.assertEqual(pages[1]['returned_count'], 5)
            self.assertEqual(pages[1]['withheld_count'], 0)
            self.assertIsNone(pages[1]['next_offset'])

    def test_recovery_pagination_requires_integer_offset_and_positive_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'trace.csv'
            columns = ['timestamp', 'cmdb_id', 'span_id', 'trace_id', 'duration',
                       'type', 'status_code', 'operation_name', 'parent_span']
            with source.open('w', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(columns)
                writer.writerow([1000, 'frontend', 'root', 'trace', 100, 'rpc', 0, 'GET /', ''])
            source_inventory = {'deployment': 'demo', 'sources': [
                {'path': 'trace.csv', 'family': 'trace_span', 'sha256': 'fixture'}]}

            with self.assertRaises(ValueError):
                recover_traces(root, source_inventory, 1, 2, offset=-1)
            with self.assertRaises(ValueError):
                recover_traces(root, source_inventory, 1, 2, offset=1.5)
            with self.assertRaises(ValueError):
                recover_traces(root, source_inventory, 1, 2, limit=0)

    def test_prepared_recovery_matches_csv_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'telemetry' / 'p1' / 'trace' / 'trace_span.csv'
            source.parent.mkdir(parents=True)
            columns = ['timestamp', 'cmdb_id', 'span_id', 'trace_id', 'duration',
                       'type', 'status_code', 'operation_name', 'parent_span']
            with source.open('w', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(columns)
                writer.writerows([
                    [1500, 'frontend-7', 'root', 'selected', 100, 'rpc', 0, 'GET /', ''],
                    [2500, 'worker', 'child', 'selected', 20, 'rpc', 0, 'fetch', 'root'],
                    [1500, 'worker', 'ignored', 'other', 1, 'rpc', 0, 'other', ''],
                ])
            source_inventory = inventory(root, 'demo')
            prepared = prepare_sources(root, source_inventory, root.parent / 'out')

            csv_result = recover_traces(root, source_inventory, 1, 2,
                                        frontend_only=True)
            indexed_result = recover_traces(root, source_inventory, 1, 2,
                                            frontend_only=True,
                                            prepared_view=prepared)

            self.assertEqual(indexed_result['status'], csv_result['status'])
            self.assertEqual(indexed_result['selected_count'], csv_result['selected_count'])
            self.assertEqual(indexed_result['withheld_count'], csv_result['withheld_count'])
            self.assertEqual(indexed_result['traces'], csv_result['traces'])
            self.assertEqual(indexed_result['retrieval_backend'], 'prepared_sqlite')
            self.assertEqual(indexed_result['scanned_records'], 3)
            self.assertEqual(set(indexed_result['traces'][0]['spans'][0]['raw']), set(columns))
            self.assertNotIn('header', indexed_result['traces'][0]['spans'][0]['locator'])

    def test_selected_trace_recovers_records_outside_window_and_across_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            columns = ['timestamp', 'cmdb_id', 'span_id', 'trace_id', 'duration',
                       'type', 'status_code', 'operation_name', 'parent_span']
            sources = []
            for name, records in [('first.csv', [
                [1500, 'frontend-7', 'r', 'selected', 100, 'rpc', 0, 'GET /', ''],
                [500, 'worker', 'other', 'unselected', 1, 'rpc', 0, 'other', ''],
            ]), ('second.csv', [
                [2500, 'worker', 'child', 'selected', 20, 'rpc', 0, 'fetch', 'r'],
                [2000, 'frontend-7', 'excluded', 'boundary', 1, 'rpc', 0, 'GET /', ''],
            ])]:
                with (root / name).open('w', newline='') as handle:
                    writer = csv.writer(handle); writer.writerow(columns); writer.writerows(records)
                sources.append({'path': name, 'family': 'trace_span', 'sha256': name})
            result = recover_traces(root, {'deployment': 'renamed', 'sources': sources}, 1, 2)
            self.assertEqual(result['status'], 'completed')
            self.assertEqual([trace['trace_id'] for trace in result['traces']], ['selected'])
            trace = result['traces'][0]
            self.assertEqual({span['raw']['span_id'] for span in trace['spans']}, {'r', 'child'})
            self.assertEqual(trace['spans'][1]['locator']['record'], 2)
            self.assertEqual(trace['spans'][1]['locator']['path'], 'second.csv')

    def test_frontend_only_selection_preserves_frontend_root_after_trace_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            columns = ['timestamp', 'cmdb_id', 'span_id', 'trace_id', 'duration',
                       'type', 'status_code', 'operation_name', 'parent_span']
            rows = [[1100, 'worker', 'root', f'unrelated-{i}', 1, 'rpc', 0, 'other', '']
                    for i in range(31)]
            rows += [[1900, 'frontend-7', 'root', 'frontend-trace', 100, 'rpc', 0, 'GET /', ''],
                     [2500, 'worker', 'child', 'frontend-trace', 20, 'rpc', 0, 'fetch', 'root']]
            source = root / 'trace.csv'
            with source.open('w', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(columns)
                writer.writerows(rows)
            inventory = {'deployment': 'd', 'sources': [
                {'path': 'trace.csv', 'family': 'trace_span', 'sha256': 'trace'}]}

            result = recover_traces(root, inventory, 1, 2, frontend_only=True)

            self.assertEqual([trace['trace_id'] for trace in result['traces']], ['frontend-trace'])
            self.assertEqual({span['raw']['span_id'] for span in result['traces'][0]['spans']},
                             {'root', 'child'})


class TraceComparisonTests(unittest.TestCase):
    def test_duration_and_multiplicity_have_separate_findings(self):
        from rca.telemetry.traces import compare_traces

        def trace(identity, timestamp, duration, children):
            rows = [{'timestamp': str(timestamp), 'cmdb_id': 'frontend-9', 'span_id': 'r',
                     'trace_id': identity, 'duration': str(duration), 'type': 'rpc',
                     'operation_name': 'GET /', 'parent_span': ''}]
            rows += [{'timestamp': str(timestamp), 'cmdb_id': 'worker', 'span_id': f'c{i}',
                      'trace_id': identity, 'duration': '10', 'type': 'rpc',
                      'operation_name': 'fetch', 'parent_span': 'r'} for i in range(children)]
            return {'trace_id': identity, 'deployment': 'd',
                    'recorded_recovery': 'complete_relative_to_snapshot',
                    'spans': [{'raw': row, 'locator': {'path': 'trace.csv', 'record': i + 2,
                                                     'source_digest': 'fixture'}}
                              for i, row in enumerate(rows)]}
        recovered = {'traces': [trace(f'ref{i}', 90000 + i, 100, 1) for i in range(20)] +
                     [trace('query', 100000, 200, 2)], 'status': 'completed'}
        result = compare_traces(recovered, 100, 1900)
        duration = next(item for item in result['candidates'] if item['channel'] == 'trace_duration')
        structure = next(item for item in result['candidates'] if item['channel'] == 'trace_structure')
        self.assertEqual(duration['difference'], 100)
        self.assertEqual(duration['reference_count'], 20)
        self.assertEqual(structure['differences'][0]['added'], [['fetch', 'rpc', 1]])
        self.assertEqual(duration['resource'], 'frontend-9')


class TraceSourceBoundaryTests(unittest.TestCase):
    def test_recovery_rejects_a_source_outside_the_supplied_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset = Path(directory) / 'dataset'
            dataset.mkdir()
            with self.assertRaises(ValueError):
                recover_traces(dataset, {'deployment': 'd', 'sources': [
                    {'family': 'trace_span', 'path': '../outside.csv', 'sha256': 'outside'}]}, 1, 2)
