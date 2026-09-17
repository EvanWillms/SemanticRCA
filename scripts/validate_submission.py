#!/usr/bin/env python3
"""Check submitted artifact structure; this is not the official accuracy scorer."""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rca.contracts import QueryRow
from rca.scope import interpret


def validate(queries, output):
    with queries.open(newline='', encoding='utf-8-sig') as handle:
        rows = list(csv.DictReader(handle))
    with (output / 'predictions.csv').open(newline='', encoding='utf-8') as handle:
        predictions = list(csv.DictReader(handle))
    assert len(predictions) == len(rows), 'wrong prediction count'
    by_id = {row['row_id']: row['prediction'] for row in predictions}
    assert set(by_id) == {row['row_id'] for row in rows}, 'row IDs differ'
    field_names = {'datetime': 'root cause occurrence datetime',
                   'component': 'root cause component', 'reason': 'root cause reason'}
    for row in rows:
        result = interpret(QueryRow(int(row['row_id']), row['instruction'], row.get('task_index')))
        assert result.scope is not None, 'unsupported test query'
        answer = json.loads(by_id[row['row_id']])
        assert list(answer) == [str(i + 1) for i in range(result.scope.failure_count)], 'wrong incident count'
        expected = [field_names[field] for field in result.scope.requested_fields]
        for incident in answer.values():
            assert list(incident) == expected, 'wrong requested fields/order'
            assert all(isinstance(value, str) and value for value in incident.values()), 'empty answer'
        evidence = (output / 'evidence' / f"{row['row_id']}.md").read_text()
        assert [line for line in evidence.splitlines() if line.startswith('## ')] == [
            '## Answer', '## Confidence', '## Evidence', '## Ruled out'], 'wrong evidence sections'
    usage = [json.loads(line) for line in (output / 'usage.jsonl').read_text().splitlines()]
    assert {item['row_id'] for item in usage} == {int(row['row_id']) for row in rows}, 'usage IDs differ'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queries', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    validate(args.queries, args.out)
    print('Submission artifact structure passed; accuracy and benchmark limits are not certified.')
