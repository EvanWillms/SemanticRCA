"""Deterministic preparation through the existing solver seam."""
import json
from pathlib import Path
from typing import Any

from rca.contracts import QueryRow, Solution
from rca.scope import interpret
from rca.discovery.pipeline import discover


def solve(instruction: str, dataset_dir: Path, ctx: dict[str, Any]) -> Solution:
    interpretation = interpret(QueryRow(ctx['row_id'], instruction, ctx.get('task_index'))).to_dict()
    if interpretation['status'] == 'interpreted':
        discovery = discover(dataset_dir, interpretation['scope'], ctx['row_id'], ctx.get('budget'))
    else:
        discovery = {'findings': {
            'schema_version': 'discovery-v1', 'row_id': ctx['row_id'],
            'status': 'not_run', 'stop_reason': 'unsupported_scope',
            'candidates': [], 'findings': [], 'logs': [],
            'coverage': {'telemetry': 'not_inspected'},
        }, 'operations': []}
    findings = discovery['findings']
    evidence = (
        '## Answer\nDiagnosis pending. Predictions are intentionally blank.\n\n'
        '## Confidence\nDiscovery is descriptive; no calibrated diagnosis probability is available.\n\n'
        f"## Evidence\nScope status: {interpretation['status']}.\n"
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
