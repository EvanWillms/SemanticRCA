"""Streaming recovery of recorded traces across a declared source snapshot."""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from .paths import source_path


def recover_traces(dataset_dir: Path, inventory: dict[str, Any], start: float,
                   end: float, limit: int = 30, check_budget=None,
                   frontend_only: bool = False) -> dict[str, Any]:
    """Select by span start, then recover available records for selected IDs.

    Bounds are epoch seconds; Track 1 span starts are recorded in milliseconds.
    Selection and recovery are separate so unsorted partitions do not lose spans.
    """
    sources = [source for source in inventory['sources'] if source['family'] == 'trace_span']
    selected: dict[str, float] = {}
    scanned = 0
    for source in sources:
        with source_path(dataset_dir, source['path']).open(newline='', encoding='utf-8-sig') as handle:
            for row in csv.DictReader(handle):
                scanned += 1
                if check_budget is not None and scanned % 1024 == 1:
                    check_budget()
                timestamp = float(row['timestamp']) / 1000
                if start <= timestamp < end:
                    if frontend_only and (row['parent_span'] or
                                          not re.fullmatch(r'frontend(?:-\d+)?', row['cmdb_id'])):
                        continue
                    trace_id = row['trace_id']
                    selected[trace_id] = min(timestamp, selected.get(trace_id, timestamp))
    ordered = sorted(selected, key=lambda key: (selected[key], key))
    kept = ordered[:limit]
    traces = {key: {'trace_id': key, 'deployment': inventory['deployment'], 'spans': []}
              for key in kept}
    for source in sources:
        with source_path(dataset_dir, source['path']).open(newline='', encoding='utf-8-sig') as handle:
            for record, row in enumerate(csv.DictReader(handle), start=2):
                scanned += 1
                if check_budget is not None and scanned % 1024 == 1:
                    check_budget()
                if row['trace_id'] in traces:
                    traces[row['trace_id']]['spans'].append({
                        'raw': row,
                        'locator': {'path': source['path'], 'source_digest': source['sha256'],
                                    'record': record},
                    })
    for trace in traces.values():
        trace['spans'].sort(key=lambda span: (float(span['raw']['timestamp']),
                                            span['locator']['path'], span['locator']['record']))
        trace['recorded_recovery'] = 'complete_relative_to_snapshot'
    return {'status': 'partial' if len(ordered) > limit else 'completed',
            'traces': list(traces.values()), 'scanned_records': scanned,
            'selected_count': len(ordered), 'withheld_count': max(0, len(ordered) - limit),
            'stop_reason': 'trace_response_limit' if len(ordered) > limit else None,
            'qualifications': ['Recorded recovery does not establish complete instrumentation.',
                               'Duration units remain provisional.']}


def compare_traces(recovered: dict[str, Any], window_start: float,
                   window_end: float) -> dict[str, Any]:
    """Compare frontend durations and direct-child multiplicity independently."""
    from collections import Counter
    from statistics import median
    import hashlib
    import json
    import math
    import re

    observations = []
    for trace in recovered['traces']:
        # Identical source duplicates do not increase reference support.
        spans = {}
        conflicted = set()
        for span in trace['spans']:
            identity = span['raw']['span_id']
            if identity in spans and spans[identity]['raw'] != span['raw']:
                conflicted.add(identity)
            spans[identity] = span
        roots = [span for span in spans.values()
                 if not span['raw']['parent_span'] and
                 re.fullmatch(r'frontend(?:-\d+)?', span['raw']['cmdb_id'])]
        for root in roots:
            raw = root['raw']
            timestamp = float(raw['timestamp']) / 1000
            duration = float(raw['duration'])
            children = Counter((s['raw']['operation_name'], s['raw']['type'])
                               for s in spans.values() if s['raw']['parent_span'] == raw['span_id'])
            resolved = not conflicted and all(not s['raw']['parent_span'] or
                                              s['raw']['parent_span'] in spans for s in spans.values())
            valid_timing = all(math.isfinite(float(s['raw']['duration'])) and
                               float(s['raw']['duration']) >= 0 for s in spans.values())
            complete_before = valid_timing and all(
                float(s['raw']['timestamp']) / 1000 + float(s['raw']['duration']) / 1_000_000
                < window_start for s in spans.values())
            observations.append({
                'id': f"{trace['deployment']}:{trace['trace_id']}:{raw['span_id']}",
                'resource': raw['cmdb_id'], 'timestamp': timestamp, 'value': duration,
                'context': (raw['operation_name'], raw['type'], tuple(sorted(children))),
                'shape': children, 'resolved': resolved, 'valid_timing': valid_timing,
                'reference_eligible': resolved and complete_before and
                    trace.get('recorded_recovery') == 'complete_relative_to_snapshot',
                'locator': root['locator'],
            })
    references = [obs for obs in observations if window_start - 300 <= obs['timestamp'] < window_start
                  and obs['reference_eligible']]
    findings = []
    qualifications = ['Historical reference health and replica equivalence are unverified.',
                      'Frontend role uses the declared frontend naming convention.',
                      'Raw duration is provisionally interpreted as microseconds for endpoint eligibility.']
    for observation in observations:
        if not window_start <= observation['timestamp'] < window_end:
            continue
        base = {key: observation[key] for key in ('id', 'resource', 'timestamp', 'locator')}
        base['policy_id'] = 'track1-discovery-v1'
        base['qualifications'] = qualifications
        cohort = [ref for ref in references if ref['context'] == observation['context']]
        eligible = len(cohort) >= 20 and observation['resolved'] and observation['valid_timing']
        reference = median(ref['value'] for ref in cohort) if eligible else None
        findings.append({**base, 'channel': 'trace_duration',
                         'value': observation['value'] if math.isfinite(observation['value']) else None,
                         'reference_median': reference, 'reference_count': len(cohort),
                         'reference_ids': [ref['id'] for ref in cohort],
                         'difference': observation['value'] - reference if eligible else None,
                         'eligibility': 'qualified' if eligible else 'unavailable',
                         'reason': None if eligible else 'insufficient_or_unresolved_reference',
                         'unit': 'raw_duration'})
        shapes = {}
        for ref in references:
            if ref['context'][:2] == observation['context'][:2]:
                key = tuple(sorted(ref['shape'].items()))
                shapes.setdefault(key, []).append(ref['id'])
        current = observation['shape']
        matched = tuple(sorted(current.items())) in shapes
        differences = []
        if observation['resolved']:
            for shape, ids in sorted(shapes.items()):
                reference_shape = Counter(dict(shape))
                differences.append({
                    'reference_ids': ids, 'frequency': len(ids),
                    'added': [[*pair, count] for pair, count in sorted((current - reference_shape).items())],
                    'removed': [[*pair, count] for pair, count in sorted((reference_shape - current).items())],
                })
        findings.append({**base, 'channel': 'trace_structure', 'differences': differences,
                         'unmatched': bool(shapes) and not matched and observation['resolved'],
                         'eligibility': 'qualified' if shapes and observation['resolved'] else 'unavailable',
                         'reason': None if shapes and observation['resolved'] else 'unresolved_structure_or_reference'})
    for finding in findings:
        finding['observation_id'] = finding.pop('id')
        finding['id'] = hashlib.sha256(json.dumps(finding, sort_keys=True).encode()).hexdigest()
    candidates = [finding for finding in findings if
                  (finding['channel'] == 'trace_duration' and (finding['difference'] or 0) > 0) or
                  (finding['channel'] == 'trace_structure' and finding['unmatched'])]
    candidates.sort(key=lambda item: (item['channel'], -(item.get('difference') or 0),
                                      item['timestamp'], item['id']))
    return {'findings': findings, 'candidates': candidates,
            'reference_observations': len(references), 'qualifications': qualifications}
