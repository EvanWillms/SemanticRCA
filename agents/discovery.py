"""Deterministic preparation through the existing solver seam."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from rca.contracts import QueryRow, Solution
from rca.scope import interpret
from rca.discovery.pipeline import discover


def solve(instruction: str, dataset_dir: Path, ctx: dict[str, Any]) -> Solution:
    interpretation = interpret(QueryRow(ctx['row_id'], instruction, ctx.get('task_index'))).to_dict()
    if interpretation['status'] == 'interpreted':
        if ctx.get('submission_metrics'):
            from rca.discovery.submission import discover as discover_submission
            discovery = discover_submission(dataset_dir, interpretation['scope'], ctx['row_id'], ctx.get('budget'))
        else:
            discovery = discover(dataset_dir, interpretation['scope'], ctx['row_id'], ctx.get('budget'),
                                 ctx.get('run_context'))
    else:
        discovery = {'findings': {
            'schema_version': 'discovery-v1', 'row_id': ctx['row_id'],
            'status': 'not_run', 'stop_reason': 'unsupported_scope',
            'candidates': [], 'findings': [], 'logs': [],
            'coverage': {'telemetry': 'not_inspected'},
        }, 'operations': []}
    findings = discovery['findings']
    measured = ''
    if ctx.get('submission_metrics'):
        lines = ['Measured findings (raw units; departures do not establish root cause):']
        for candidate in findings['candidates']:
            when = datetime.fromtimestamp(candidate['timestamp'], timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S UTC+08:00')
            location = candidate['locator']
            lines.append(
                f"- {candidate['resource']} / {candidate['kpi']} at {when}: "
                f"observed {candidate['value']:.6g}, prior 30-minute median "
                f"{candidate['reference_median']:.6g} ({candidate['reference_count']} samples), "
                f"change {candidate['difference']:+.6g}. "
                f"Source: {location['path']}, CSV record {location['record']} (header is record 1)."
            )
        if not findings['candidates']:
            lines.append('No supported metric comparison was available in the inspected scope.')
        lines.append('Traces and logs were not inspected on this bounded assessment path. Peak sample times are not verified fault onset times.')
        measured = '\n'.join(lines) + '\n\n'
    evidence = (
        '## Answer\nDiagnosis pending. Predictions are intentionally blank.\n\n'
        '## Confidence\nDiscovery is descriptive; no calibrated diagnosis probability is available.\n\n'
        f"## Evidence\n{measured}Scope status: {interpretation['status']}.\n"
        f"Scope: {json.dumps(interpretation['scope'], ensure_ascii=False)}\n"
        f"Extraction support: {json.dumps(interpretation['support'], ensure_ascii=False)}\n"
        f"Errors: {json.dumps(interpretation['errors'], ensure_ascii=False)}\n"
        f"Discovery status: {findings['status']}; stop reason: {findings['stop_reason']}.\n"
        f"Coverage: {json.dumps(findings['coverage'], ensure_ascii=False)}\n"
        f"Observed candidates: {json.dumps(findings['candidates'], ensure_ascii=False, allow_nan=False)}\n"
        f"Targeted log observations: {json.dumps(findings['logs'], ensure_ascii=False, allow_nan=False)}\n\n"
        '## Ruled out\nNo causal alternatives were assessed or ruled out.\n'
    )
    return Solution(evidence=evidence, discovery={'interpretation': interpretation, **discovery})
