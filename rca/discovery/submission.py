"""Bounded metric retrieval for the unattended submission path.

Avoid preparing a whole-deployment trace index before any evidence is available.
Only dated metric partitions intersecting the query and its 30-minute reference
are read. Samples are compact, capped, and retained when a scan is interrupted.
This is a descriptive fallback, not a validated causal diagnosis.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
import math
from pathlib import Path
import statistics

from rca.discovery.budget import BudgetExceeded
from rca.telemetry.paths import source_path


REFERENCE_SECONDS = 1800
MAX_SAMPLES = 300_000
MAX_SERIES_SAMPLES = 600
FAMILIES = ('metric_node', 'metric_container', 'metric_service', 'metric_runtime', 'metric_mesh')


def discover(dataset: Path, scope: dict, row_id: int, budget=None) -> dict:
    start_dt = datetime.fromisoformat(scope['window_start'])
    end_dt = datetime.fromisoformat(scope['window_end'])
    start, end = start_dt.timestamp(), end_dt.timestamp()
    day = (start_dt - timedelta(seconds=REFERENCE_SECONDS)).date()
    days = []
    while day <= (end_dt - timedelta(microseconds=1)).date():
        days.append(day.strftime('%Y_%m_%d'))
        day += timedelta(days=1)
    grouped, sources, operations = {}, [], []
    selected = 0
    stopped = None
    for family in FAMILIES:
        for day in days:
            relative = f'telemetry/{day}/metric/{family}.csv'
            source = {'path': relative, 'family': family, 'resources': [], 'status': 'not_inspected'}
            resources = set()
            scanned = 0
            try:
                if budget:
                    budget.check()
                path = source_path(dataset, relative)
                if not path.is_file():
                    continue
                sources.append(source)
                with path.open(newline='', encoding='utf-8-sig') as handle:
                    reader = csv.reader(handle)
                    columns = next(reader)
                    required = ('timestamp', 'service', 'rr', 'sr', 'mrt', 'count') if family == 'metric_service' else ('timestamp', 'cmdb_id', 'kpi_name', 'value')
                    if not set(required).issubset(columns) or len(columns) != len(set(columns)):
                        raise ValueError('unsupported metric columns')
                    indices = {name: columns.index(name) for name in required}
                    for record, row in enumerate(reader, 2):
                        scanned += 1
                        if budget and scanned % 4096 == 1:
                            budget.check()
                        if len(row) != len(columns):
                            continue
                        try:
                            timestamp = float(row[indices['timestamp']])
                        except ValueError:
                            continue
                        if not start - REFERENCE_SECONDS <= timestamp < end:
                            continue
                        resource = row[indices['service' if family == 'metric_service' else 'cmdb_id']].strip()
                        if not resource:
                            continue
                        resources.add(resource)
                        values = ((name, row[indices[name]]) for name in ('rr', 'sr', 'mrt', 'count')) if family == 'metric_service' else ((row[indices['kpi_name']], row[indices['value']]),)
                        for kpi, raw in values:
                            try:
                                value = float(raw)
                            except ValueError:
                                continue
                            if not math.isfinite(value):
                                continue
                            key = (family, resource, kpi)
                            samples = grouped.setdefault(key, {})
                            # Exact duplicate timestamps collapse; conflicting values
                            # remain unavailable rather than influencing the median.
                            previous = samples.get(timestamp)
                            if previous is not None:
                                if previous[0] != value:
                                    samples[timestamp] = (None, relative, record)
                                continue
                            if len(samples) >= MAX_SERIES_SAMPLES:
                                stopped = 'sample_limit'
                                continue
                            if selected >= MAX_SAMPLES:
                                raise BudgetExceeded('sample_limit')
                            samples[timestamp] = (value, relative, record)
                            selected += 1
                source['status'] = 'completed'
            except BudgetExceeded as exc:
                stopped = str(exc)
                source['status'] = 'partial'
            except (OSError, ValueError, UnicodeError, csv.Error, StopIteration):
                source['status'] = 'unavailable'
                stopped = stopped or 'source_unavailable_or_invalid'
            finally:
                source['resources'] = sorted(resources)
                if source in sources:
                    operations.append({'operation': 'scoped_metric_scan', 'path': relative,
                                       'status': source['status'], 'scanned_records': scanned})
            if source['status'] == 'partial':
                break
        if sources and sources[-1]['status'] == 'partial':
            break

    candidates = []
    for (family, resource, kpi), samples in grouped.items():
        references = [(t, sample) for t, sample in samples.items() if t < start and sample[0] is not None]
        observed = [(t, sample) for t, sample in samples.items() if t >= start and sample[0] is not None]
        if len(references) < 20 or not observed:
            continue
        median = statistics.median(sample[0] for _, sample in references)
        # One strongest measured departure per series bounds the evidence packet.
        timestamp, sample = max(observed, key=lambda item: (abs(item[1][0] - median), -item[0]))
        difference = sample[0] - median
        if not difference:
            continue
        candidates.append({'family': family, 'resource': resource, 'kpi': kpi,
                           'timestamp': timestamp, 'value': sample[0], 'reference_median': median,
                           'reference_count': len(references), 'reference_seconds': REFERENCE_SECONDS,
                           'reference_observations': [{'timestamp': t, 'value': s[0],
                               'locator': {'path': s[1], 'record': s[2]}} for t, s in sorted(references)],
                           'difference': difference, 'absolute_difference': abs(difference),
                           'locator': {'path': sample[1], 'record': sample[2]},
                           'qualifications': ['raw units; empirical reference is not verified healthy',
                                              'peak departure timestamp is not verified fault onset']})
    candidates.sort(key=lambda item: (-item['absolute_difference'], item['resource'], item['kpi']))
    # Represent distinct resources before spending packet space on repeated KPIs.
    first, remainder, seen = [], [], set()
    for candidate in candidates:
        (remainder if candidate['resource'] in seen else first).append(candidate)
        seen.add(candidate['resource'])
    candidates = (first + remainder)[:24]
    coverage = {'policy': 'scoped_metrics_30min_reference', 'reference_seconds': REFERENCE_SECONDS,
                'selected_samples': selected, 'sources': sources,
                'traces': 'not_inspected', 'logs': 'not_inspected',
                'limitations': 'Raw departures are candidate signals, not causal proof. Missing or capped samples limit comparisons.'}
    findings = {'schema_version': 'discovery-v1', 'row_id': row_id, 'status': 'partial',
                'stop_reason': stopped or 'metrics_only_coverage', 'candidates': candidates,
                'findings': candidates, 'logs': [], 'coverage': coverage,
                'source_snapshot': {'sources': sources}}
    return {'findings': findings, 'operations': operations}
