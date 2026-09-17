#!/usr/bin/env python3
"""Exercise the RCA loop with discovered evidence and explicit scripted decisions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPOSITORY = Path(__file__).resolve().parents[1]
for package in ('trace_semantics', 'rca_domain'):
    sys.path.insert(0, str(REPOSITORY / 'libraries' / package / 'src'))

from rca_domain import from_semantic_traces, investigate
from trace_semantics import EncodingPolicy, encode_traces


def run_demo(findings: dict, interpretation: dict) -> dict:
    """Use the same recorded traces for a controlled two-assessment example.

    The scripted selection of a changed recording component demonstrates answer
    assembly only. It is not an inference of causal responsibility.
    """
    scope = interpretation['scope']
    if scope['requested_fields'] != ['component'] or scope['failure_count'] != 1:
        raise ValueError('scripted demo requires one incident and component-only projection')
    domain_scope = {'case_id': str(findings['row_id']), 'deployment': scope['deployment'],
                    'incident_count': 1, 'projection': ['component']}
    description = findings['semantic_description']
    selected_ids = {trace['trace_id'] for trace in description['traces']}
    references = [trace for trace in findings['recorded_traces'] if trace['trace_id'] not in selected_ids]
    candidates = [item for item in findings['candidates'] if item['channel'] == 'trace_duration']
    if not candidates or not references:
        raise ValueError('scripted demo requires a duration departure and reference traces')
    selected = candidates[0]
    component = selected['resource']

    def packet(value, name):
        return from_semantic_traces([{'packet_id': name, 'source_snapshot_id': findings['source_id'],
                                      'description': value}], domain_scope)

    initial = packet(description, 'discovered-departures')

    def assessor(state):
        common = {'evidence_revision': state['evidence']['revision']}
        if not state['operations']:
            return {**common, 'decision': 'continue', 'incidents': [],
                    'gaps': ['recorded reference traces'],
                    'rationale': 'The scripted demo requests the recorded reference evidence before assembly.',
                    'action': {'name': 'inspect_references', 'arguments': {},
                               'gap': 'recorded reference traces'}}
        support = [identity for identity, observation in state['evidence']['observations'].items()
                   if observation['trace_id'] in selected_ids and observation['locator'] == selected['locator']]
        return {**common, 'decision': 'complete', 'gaps': [],
                'incidents': [{'component': component, 'support': support,
                               'explanation': 'Scripted demo selects the changed recording component; causality is unproven.'}],
                'rationale': 'The authored callback accepts the evidence for workflow demonstration only.'}

    def inspect_references(arguments, state):
        policy = EncodingPolicy(**description['policy'])
        return packet(encode_traces(references, policy), 'recorded-references')

    result = investigate(initial, assessor, {'inspect_references': inspect_references},
                         {'components': [component], 'reasons': []})
    result['demo'] = {'mode': 'scripted_callbacks_on_discovery_artifacts', 'live_llm': False,
                      'real_diagnosis_accuracy_claim': False,
                      'qualification': 'The scripted answer is a changed recording component, not a proven root cause.'}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--findings', required=True, type=Path)
    parser.add_argument('--scope', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    result = run_demo(json.loads(args.findings.read_text()), json.loads(args.scope.read_text()))
    with args.out.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')
    return 0 if result['investigation_stop_reason'] == 'evidence_sufficient' else 1


if __name__ == '__main__':
    raise SystemExit(main())
