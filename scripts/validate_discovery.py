#!/usr/bin/env python3
"""Validate persisted discovery artifacts without running the interpreter."""
import argparse
import csv
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def reject_constant(value):
        raise ValueError('nonfinite JSON value')
    return json.loads(path.read_text(encoding='utf-8'), parse_constant=reject_constant)


def validate(queries, out, capability):
    with queries.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    ids = [int(row['row_id']) for row in rows]
    require(len(set(ids)) == len(ids), 'duplicate query IDs')
    with (out / 'predictions.csv').open(encoding='utf-8', newline='') as handle:
        predictions = list(csv.DictReader(handle))
    require(predictions == [{'row_id': str(identity), 'prediction': ''} for identity in ids],
            'predictions do not match query IDs and blank discovery answers')
    usage = [json.loads(line) for line in (out / 'usage.jsonl').read_text().splitlines()]
    require([record['row_id'] for record in usage] == ids, 'usage row association mismatch')
    run = read_json(out / 'discovery-run.json')
    require([case['row_id'] for case in run['cases']] == ids, 'run row association mismatch')
    require(run['total_cases'] == len(ids) and run['published_cases'] == len(ids), 'run case count mismatch')
    for row, identity, record, case in zip(rows, ids, usage, run['cases']):
        directory = out / 'cases' / str(identity)
        interpretation = read_json(directory / 'scope.json')
        findings = read_json(directory / 'findings.json')
        require(interpretation['row_id'] == identity == findings['row_id'], 'sidecar row association mismatch')
        instruction = row['instruction']
        require(interpretation['instruction'] == instruction, 'instruction changed')
        require(interpretation['instruction_hash'] == hashlib.sha256(instruction.encode()).hexdigest(), 'instruction hash mismatch')
        require(interpretation['task_index'] == (row.get('task_index') or None), 'task metadata mismatch')
        for support in interpretation['support']:
            if 'start' in support:
                require(0 <= support['start'] < support['end'] <= len(instruction), 'invalid text support range')
                require(instruction[support['start']:support['end']] == support['excerpt'], 'text support mismatch')
            else:
                require(bool(support.get('convention')), 'missing text support or convention')
        scope = interpretation['scope']
        if interpretation['status'] == 'interpreted':
            require(scope is not None and not interpretation['errors'], 'interpreted scope has errors')
            start, end = (datetime.fromisoformat(scope[key]) for key in ('window_start', 'window_end'))
            require(start.utcoffset() == end.utcoffset() == timedelta(hours=8), 'scope is not UTC+08')
            require(end - start == timedelta(minutes=30), 'scope is not thirty minutes')
            require(type(scope['failure_count']) is int and scope['failure_count'] > 0, 'invalid failure count')
            fields = scope['requested_fields']
            require(fields and fields == [field for field in ('datetime', 'component', 'reason') if field in fields], 'invalid projection order')
        else:
            require(interpretation['status'] == 'unsupported' and scope is None and interpretation['errors'], 'invalid unsupported scope')
        require(findings['status'] in ('completed', 'partial', 'unavailable', 'not_run'), 'invalid discovery status')
        require(case['discovery_status'] == findings['status'], 'run/case status mismatch')
        if capability == 'discovery':
            require(findings['status'] == 'completed' and interpretation['status'] == 'interpreted', 'discovery is incomplete')
        for line in (directory / 'operations.jsonl').read_text().splitlines():
            operation = json.loads(line)
            require(operation['question'] and operation['operation'] and operation['policy_id'], 'incomplete operation journal')
            require(math.isfinite(operation['wall_s']) and operation['wall_s'] >= 0, 'invalid operation duration')
        evidence = (out / 'evidence' / f'{identity}.md').read_text()
        require([line for line in evidence.splitlines() if line.startswith('## ')] ==
                ['## Answer', '## Confidence', '## Evidence', '## Ruled out'], 'invalid evidence sections')
        require('Diagnosis pending' in evidence and 'No causal alternatives' in evidence, 'untruthful diagnosis status')
        require(record['models'] == {} and all(type(record[key]) is int and record[key] == 0
                for key in ('calls', 'prompt_tokens', 'completion_tokens')), 'nonzero or invalid model usage')
        require(math.isfinite(record['wall_s']) and record['wall_s'] >= 0, 'invalid case duration')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queries', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--capability', choices=('scope', 'discovery'), default='discovery')
    args = parser.parse_args()
    try:
        validate(args.queries, args.out, args.capability)
    except (OSError, ValueError, KeyError, TypeError, OverflowError):
        print('Discovery artifact validation failed: incomplete or inconsistent artifacts.', file=sys.stderr)
        return 1
    print('Discovery artifact validation passed; this is not official diagnosis or full acceptance validation.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
