"""Run the declared happy-path discovery operations for an interpreted scope."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from rca.discovery.budget import CaseBudget, BudgetExceeded, RunBudget
from rca.telemetry.inventory import inventory
from rca.telemetry.logs import inspect_logs
from rca.telemetry.traces import recover_traces, compare_traces


POLICY_ID = 'track1-discovery-v1'


def discover(dataset: Path, scope: dict[str, Any], row_id: int,
             budget: CaseBudget | None = None) -> dict[str, Any]:
    operations = []
    budget = budget or RunBudget().allocate(1)
    try:
        return _discover(dataset, scope, row_id, budget, operations)
    except (BudgetExceeded, OSError, ValueError) as exc:
        reason = 'analysis_time_budget_exhausted' if isinstance(exc, BudgetExceeded) else 'operation_failed'
        return {'findings': {'schema_version': 'discovery-v1', 'row_id': row_id,
                            'status': 'partial', 'stop_reason': reason, 'candidates': [],
                            'findings': [], 'logs': [], 'coverage': {'telemetry': 'partial'},
                            'qualifications': ['Interrupted operation results are unavailable; consult the operation journal.']},
                'operations': operations}


def _discover(dataset, scope, row_id, budget, operations):
    source_id = None
    start = datetime.fromisoformat(scope['window_start']).timestamp()
    end = datetime.fromisoformat(scope['window_end']).timestamp()

    def perform(name, question, arguments, action):
        begun = time.monotonic()
        receipt = {
            'id': f'{row_id}:{len(operations)}:{name}', 'stage': 'discovery',
            'operation': name, 'question': question, 'arguments': arguments,
            'policy_id': POLICY_ID, 'source_id': source_id, 'status': 'failed',
            'scanned_records': None, 'withheld_count': None, 'stop_reason': 'operation_failed',
        }
        operations.append(receipt)
        try:
            budget.check()
            result = action()
            receipt.update(status='completed' if result.get('status') == 'complete' else result.get('status', 'completed'),
                           scanned_records=result.get('scanned_records', 0),
                           withheld_count=result.get('withheld_count', 0),
                           stop_reason=result.get('stop_reason'))
            return result
        except BudgetExceeded:
            receipt.update(status='budget_exhausted', stop_reason='analysis_time_budget_exhausted')
            raise
        finally:
            receipt['wall_s'] = time.monotonic() - begun

    snapshot = perform('inventory', 'Which supported sources and identities are supplied?',
                       {'deployment': scope['deployment']}, lambda: inventory(dataset, scope['deployment'], check_budget=budget.check))
    source_id = hashlib.sha256(json.dumps(
        {'deployment': scope['deployment'], 'schema_version': snapshot['schema_version'],
         'sources': [(source['path'], source['sha256']) for source in snapshot['sources']]},
        sort_keys=True).encode()).hexdigest()
    operations[0]['source_id'] = source_id
    coverage = {family: {'status': 'not_inspected' if summary['status'] == 'available' else 'unavailable',
                         'reason': 'pending_operation' if summary['status'] == 'available' else summary.get('reason')}
                for family, summary in snapshot['source_families'].items()}
    base = {'schema_version': 'discovery-v1', 'row_id': row_id, 'policy_id': POLICY_ID,
            'source_id': source_id, 'source_snapshot': snapshot, 'coverage': coverage,
            'candidates': [], 'findings': [], 'logs': [], 'relationships': [],
            'qualifications': ['Discovery describes observations and does not establish root cause.']}
    if not snapshot['sources']:
        return {'findings': {**base, 'status': 'unavailable', 'stop_reason': 'missing_telemetry_sources'},
                'operations': operations}

    trace_result = perform('recover_traces', 'Which frontend-root traces start in the query or reference window?',
                           {'start': start - 300, 'end': end, 'limit': 30, 'frontend_only': True},
                           lambda: recover_traces(dataset, snapshot, start - 300, end,
                                                  check_budget=budget.check, frontend_only=True))
    trace_comparison = perform('compare', 'How do query durations and structures differ from prior observations?',
                               {'channel': 'trace', 'reference_seconds': 300},
                               lambda: compare_traces(trace_result, start, end))
    from rca.telemetry.metrics import metric_series, compare_series
    metrics = perform('metric_series', 'Which resource measurements occur in the query and reference window?',
                      {'start': start - 300, 'end': end}, lambda: metric_series(dataset, snapshot, scope, check_budget=budget.check))
    metric_comparison = perform('compare', 'Which recorded resource samples differ from their prior median?',
                               {'channel': 'metrics', 'reference_seconds': 300}, lambda: compare_series(metrics))
    base['recorded_traces'] = trace_result['traces']
    base['metric_comparisons'] = metric_comparison['comparisons']
    base['findings'] = trace_comparison['findings'] + metric_comparison['findings']
    base['candidates'] = trace_comparison['candidates'] + metric_comparison['candidates']
    # Only describe traces selected by observed departures. This is an evidence
    # selection rule, not an assertion that the trace contains the root cause.
    from trace_semantics import EncodingPolicy, partition_traces, describe
    selected_locators = [finding['locator'] for finding in trace_comparison['candidates']]
    selected_traces = [trace for trace in trace_result['traces'] if any(
        span['locator'] in selected_locators for span in trace['spans'])]
    partition = perform('partition_traces', 'Which selected trace facts can be stated without inferred semantics?',
                        {'trace_ids': [trace['trace_id'] for trace in selected_traces],
                         'timestamp_unit': 'ms', 'duration_unit': None, 'operation_mappings': {}},
                        lambda: partition_traces(selected_traces, EncodingPolicy(
                            version=POLICY_ID, timestamp_unit='ms', duration_unit=None)))
    base['semantic_deferred'] = partition['deferred']
    base['semantic_description'] = perform('describe_traces', 'What recorded facts describe the selected traces?',
                                           {'trace_ids': [trace['trace_id'] for trace in selected_traces]},
                                           lambda: describe(partition))
    base['qualifications'].append('Semantic traces are selected by descriptive departures; fault association is unproven.')
    base['trace_coverage'] = {key: value for key, value in trace_result.items() if key != 'traces'}
    base['metric_coverage'] = {key: value for key, value in metrics.items() if key != 'series'}
    for family in coverage:
        if any(source['family'] == family for source in snapshot['sources']) and not family.startswith('log_'):
            coverage[family] = {'status': 'inspected', 'reason': None}

    # One deterministic corroboration question keeps the first happy path bounded.
    resources = sorted({candidate['resource'] for candidate in base['candidates']})
    log_resources = {resource for source in snapshot['sources'] if source['family'].startswith('log_')
                     for resource in source['resources']}
    target = next((resource for resource in resources if resource in log_resources), None)
    log_result = None
    if target:
        log_result = perform('inspect_logs', 'What was logged on this changed recording resource?',
                             {'resource': target, 'start': start, 'end': end, 'limit': 200},
                             lambda: inspect_logs(dataset, snapshot,
                                 'What was logged on this changed recording resource?', target, start, end, check_budget=budget.check))
        base['logs'] = log_result['observations']
        for family in coverage:
            if family.startswith('log_') and any(source['family'] == family for source in snapshot['sources']):
                coverage[family] = {'status': 'inspected', 'reason': 'exact_resource_targeted_question'}
    else:
        for family in coverage:
            if family.startswith('log_') and coverage[family]['status'] != 'unavailable':
                coverage[family]['reason'] = 'no_exact_candidate_recording_identity'
    partial = bool(snapshot['unavailable_families']) or trace_result['status'] != 'completed' or metrics['status'] != 'completed'
    if log_result and log_result['status'] != 'completed':
        partial = True
    base.update(status='partial' if partial else 'completed',
                stop_reason='incomplete_source_or_operation_coverage' if partial else None)
    return {'findings': base, 'operations': operations}
