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
from rca.telemetry.trace_index import TraceIndexBudgetExceeded


POLICY_ID = 'track1-discovery-v1'


def discover(dataset: Path, scope: dict[str, Any], row_id: int,
             budget: CaseBudget | None = None, run_context=None) -> dict[str, Any]:
    operations = []
    partial_state: dict[str, Any] = {}
    budget = budget or RunBudget().allocate(1)
    try:
        return _discover(dataset, scope, row_id, budget, operations, run_context, partial_state)
    except (BudgetExceeded, TraceIndexBudgetExceeded, OSError, ValueError) as exc:
        reason = 'analysis_time_budget_exhausted' if isinstance(exc, (BudgetExceeded, TraceIndexBudgetExceeded)) else 'operation_failed'
        findings = partial_state.get('findings')
        if findings is None:
            findings = {'schema_version': 'discovery-v1', 'row_id': row_id,
                        'status': 'partial', 'stop_reason': reason, 'candidates': [],
                        'findings': [], 'logs': [], 'coverage': {'telemetry': 'partial'},
                        'qualifications': ['Interrupted operation results are unavailable; consult the operation journal.']}
        else:
            findings['status'] = 'partial'
            findings['stop_reason'] = reason
            findings.setdefault('qualifications', []).append(
                'Completed observations are retained; interrupted operation results may be unavailable. '
                'Consult the operation journal for the failed stage.')
        return {'findings': findings,
                'operations': operations}


def _discover(dataset, scope, row_id, budget, operations, run_context, partial_state):
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
        except (BudgetExceeded, TraceIndexBudgetExceeded):
            receipt.update(status='budget_exhausted', stop_reason='analysis_time_budget_exhausted')
            raise
        finally:
            receipt['wall_s'] = time.monotonic() - begun

    preparation = None
    if run_context is not None:
        preparation = perform('prepare_sources', 'Which completed source view can this case use?',
                              {'deployment': scope['deployment']},
                              lambda: run_context.prepare(scope['deployment'], budget))
        operations[-1]['preparation_id'] = preparation['preparation_id']
        operations[-1]['reused'] = preparation['reused']
    snapshot = perform('inventory', 'Which supported sources and identities are supplied?',
                       {'deployment': scope['deployment']}, lambda: preparation['snapshot'] if preparation else
                       inventory(dataset, scope['deployment'], check_budget=budget.check))
    source_id = hashlib.sha256(json.dumps(
        {'deployment': scope['deployment'], 'schema_version': snapshot['schema_version'],
         'sources': [(source['path'], source['sha256']) for source in snapshot['sources']]},
        sort_keys=True).encode()).hexdigest()
    for operation in operations:
        operation['source_id'] = source_id
    coverage = {family: {'status': 'not_inspected' if summary['status'] == 'available' else 'unavailable',
                         'reason': 'pending_operation' if summary['status'] == 'available' else summary.get('reason')}
                for family, summary in snapshot['source_families'].items()}
    base = {'schema_version': 'discovery-v1', 'row_id': row_id, 'policy_id': POLICY_ID,
            'source_id': source_id, 'source_snapshot': snapshot, 'coverage': coverage,
            'candidates': [], 'findings': [], 'logs': [], 'relationships': [],
            'recorded_traces': [], 'metric_comparisons': [],
            'trace_coverage': None, 'metric_coverage': None,
            'status': 'partial', 'stop_reason': 'operation_in_progress',
            'qualifications': ['Discovery describes observations and does not establish root cause.']}
    if preparation:
        base.update(preparation_id=preparation['preparation_id'], preparation_reused=preparation['reused'])
    partial_state['findings'] = base
    if not snapshot['sources']:
        return {'findings': {**base, 'status': 'unavailable', 'stop_reason': 'missing_telemetry_sources'},
                'operations': operations}

    trace_result = perform('recover_traces', 'Which frontend-root traces start in the query or reference window?',
                           {'start': start - 300, 'end': end, 'limit': 30, 'frontend_only': True},
                           lambda: recover_traces(dataset, snapshot, start - 300, end,
                                                  check_budget=budget.check, frontend_only=True,
                                                  prepared_view=preparation['view'] if preparation else None))
    base['recorded_traces'] = trace_result['traces']
    base['trace_coverage'] = {key: value for key, value in trace_result.items() if key != 'traces'}
    for family in coverage:
        if family == 'trace_span' and any(source['family'] == family for source in snapshot['sources']):
            coverage[family] = {'status': 'inspected', 'reason': None}
    trace_comparison = perform('compare', 'How do query durations and structures differ from prior observations?',
                               {'channel': 'trace', 'reference_seconds': 300},
                               lambda: compare_traces(trace_result, start, end))
    base['findings'].extend(trace_comparison['findings'])
    base['candidates'].extend(trace_comparison['candidates'])
    from rca.telemetry.metrics import metric_series, compare_series
    metrics = perform('metric_series', 'Which resource measurements occur in the query and reference window?',
                      {'start': start - 300, 'end': end}, lambda: metric_series(dataset, snapshot, scope, check_budget=budget.check))
    base['metric_series'] = metrics['series']
    base['metric_coverage'] = {key: value for key, value in metrics.items() if key != 'series'}
    metric_family_states = (metrics.get('coverage') or {}).get('families', {})
    for family, state in metric_family_states.items():
        if family not in coverage or not isinstance(state, dict):
            continue
        status = state.get('status', 'unavailable')
        reasons = state.get('reasons') or []
        coverage[family] = {
            'status': status,
            'reason': None if status == 'inspected' else '; '.join(str(reason) for reason in reasons) or
                      'metric_source_unavailable',
        }
    metric_comparison = perform('compare', 'Which recorded resource samples differ from their prior median?',
                               {'channel': 'metrics', 'reference_seconds': 300}, lambda: compare_series(metrics))
    base['metric_comparisons'] = metric_comparison['comparisons']
    base['findings'].extend(metric_comparison['findings'])
    base['candidates'].extend(metric_comparison['candidates'])
    del base['metric_series']  # Completed comparisons already retain their source observations.
    base.pop('metric_series', None)
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
