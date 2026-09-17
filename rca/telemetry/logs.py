"""Inspect a bounded log response for an explicit resource and question."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .paths import source_path


def inspect_logs(dataset_dir: Path, inventory: dict[str, Any], question: str,
                 resource: str, start: float, end: float, limit: int = 200, check_budget=None) -> dict[str, Any]:
    sources = [source for source in inventory['sources'] if source['family'].startswith('log_')]
    observations = []
    scanned = 0
    matched = 0
    for source in sources:
        with source_path(dataset_dir, source['path']).open(newline='', encoding='utf-8-sig') as handle:
            for record, row in enumerate(csv.DictReader(handle), start=2):
                scanned += 1
                if check_budget is not None and scanned % 1024 == 1:
                    check_budget()
                if row['cmdb_id'] != resource or not start <= float(row['timestamp']) < end:
                    continue
                matched += 1
                observations.append({'raw': row, 'locator': {
                    'path': source['path'], 'source_digest': source['sha256'], 'record': record}})
                observations.sort(key=lambda item: (float(item['raw']['timestamp']),
                                                    item['locator']['path'], item['locator']['record']))
                del observations[limit:]
    return {'status': 'completed' if sources and matched <= limit else 'partial' if sources else 'unavailable',
            'question': question, 'resource': resource, 'observations': observations,
            'scanned_records': scanned, 'returned_count': len(observations),
            'withheld_count': matched - len(observations),
            'stop_reason': 'log_response_limit' if matched > limit else None if sources else 'missing_log_sources',
            'qualifications': ['Exact recording identity only; no causal or request-level link is inferred.']}
