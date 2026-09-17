"""Run S01 once into a new immutable-by-convention directory (stdlib only)."""
import argparse
import hashlib
import json
import platform
import shutil
from collections.abc import Mapping
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from .codec import canonical_structure, compact, decode, digest, encode

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / 'fixtures'
EXPECTED_QUALITY = {
    'retrieval': 'complete_authored_fixture',
    'instrumentation_completeness': 'unknown',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def compare(facts, expected):
    actual_nodes = sorted([[n['id'], n['operation'], n['parent'], n['entity']] for n in facts['nodes']])
    wanted_nodes = sorted(expected['nodes'])
    same = sorted(sorted(pair) for pair in expected['same_entity_pairs'])
    all_pairs = combinations(sorted(n[0] for n in expected['nodes']), 2)
    different = [list(pair) for pair in all_pairs if list(pair) not in same]
    checks = {
        'nodes': (actual_nodes, wanted_nodes),
        'edges': (facts['edges'], sorted([[n[2], n[0]] for n in expected['nodes'] if n[2] is not None])),
        'counts': (facts['counts'], expected['counts']),
        'span_count': (facts['span_count'], expected['span_count']),
        'edge_count': (facts['edge_count'], expected['edge_count']),
        'same_entity_pairs': (facts['same_entity_pairs'], same),
        'different_entity_pairs': (facts['different_entity_pairs'], different),
        'distinct_pair_count': (len(facts['different_entity_pairs']), expected['distinct_pairs']),
    }
    return {key: {'passed': a == e, 'actual': a, 'expected': e} for key, (a, e) in checks.items()}


def quality_checks(facts):
    """Check the small quality/root contract that is independent of raw rows."""
    nodes = facts.get('nodes', [])
    roots = [n for n in nodes if n.get('parent') is None]
    root_actual = [[n.get('id'), n.get('parent_resolution')] for n in roots]
    root_expected = [[roots[0].get('id'), 'root_marker']] if len(roots) == 1 else []
    root_passed = len(roots) == 1 and roots[0].get('parent_resolution') == 'root_marker'

    parent_actual = sorted(
        [[n.get('id'), n.get('parent'), n.get('parent_resolution')]
         for n in nodes if n.get('parent') is not None]
    )
    parent_expected = sorted(
        [[n.get('id'), n.get('parent'), 'resolved']
         for n in nodes if n.get('parent') is not None]
    )
    parent_passed = all(n.get('parent_resolution') == 'resolved' for n in nodes if n.get('parent') is not None)
    return {
        'quality': {
            'passed': facts.get('quality') == EXPECTED_QUALITY,
            'actual': facts.get('quality'),
            'expected': EXPECTED_QUALITY,
        },
        'root_marker': {
            'passed': root_passed,
            'actual': root_actual,
            'expected': root_expected,
        },
        'resolved_parents': {
            'passed': parent_passed,
            'actual': parent_actual,
            'expected': parent_expected,
        },
    }


def provenance_audit(fixture, packet, sidecar, facts, source_hash):
    differences = []
    packet_source = packet.get('source_sha256') if isinstance(packet, Mapping) else None
    sidecar_source = sidecar.get('source_sha256') if isinstance(sidecar, Mapping) else None
    if packet_source != source_hash or sidecar_source != source_hash:
        differences.append('source hash')
    records = sidecar.get('records') if isinstance(sidecar, Mapping) else None
    if not isinstance(records, Mapping):
        records = {}
        differences.append('sidecar records')
    if len(records) != len(fixture['records']):
        differences.append('sidecar record count')
    visited = []
    for n in facts.get('nodes', []):
        evidence = n.get('evidence', '<missing-evidence>')
        pointer = records.get(evidence)
        if not isinstance(pointer, Mapping):
            differences.append(evidence + ':pointer')
            continue
        raw_index = pointer.get('record_index_1based')
        if (not isinstance(raw_index, int) or isinstance(raw_index, bool)
                or not 1 <= raw_index <= len(fixture['records'])):
            differences.append(evidence + ':index')
            continue
        index = raw_index - 1
        visited.append(index)
        row = fixture['records'][index]
        recovered = {'timestamp': n['timestamp'], 'cmdb_id': n['entity'], 'span_id': n['id'],
                     'trace_id': facts['trace_id'], 'duration': n['duration'], 'type': n['type'],
                     'status_code': n['status_code'], 'operation_name': n['raw_operation'],
                     'parent_span': n['parent'] or ''}
        if recovered != row or digest(row) != pointer.get('row_sha256'):
            differences.append(evidence)
        if pointer.get('trace_id') != row['trace_id'] or pointer.get('span_id') != row['span_id']:
            differences.append(evidence + ':identity')
    if sorted(visited) != list(range(len(fixture['records']))):
        differences.append('source membership')
    if facts.get('context') != fixture['context']:
        differences.append('context')
    return {'passed': not differences, 'differences': differences,
            'audited_records': len(visited), 'kind': 'synthetic_source_verification'}


def create_run_dir(run_id):
    """Create one run directory without ever replacing an earlier attempt."""
    out = ROOT / 'data/experiments/semantic-encoding-v1/S01' / run_id
    out.mkdir(parents=True, exist_ok=False)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    if not args.run_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.run_id):
        parser.error('run-id must be a simple directory name')
    freeze = read(FIXTURES / 'freeze.json')
    for filename, wanted in freeze['sha256'].items():
        if sha(ROOT / filename) != wanted:
            raise ValueError('Frozen input changed: ' + filename)
    review = ROOT / 'docs/research/experiments/semantic-encoding-v1/pre-execution-review.md'
    if not review.exists():
        raise ValueError('Pre-execution review must be retained before running')
    out = create_run_dir(args.run_id)
    shutil.copytree(FIXTURES, out / 'inputs')
    shutil.copy2(FIXTURES / 'expected-facts.json', out / 'expected-facts.json')
    code_dir = out / 'code'
    code_dir.mkdir()
    for f in Path(__file__).parent.glob('*.py'):
        shutil.copy2(f, code_dir / f.name)
    expected = read(out / 'expected-facts.json')
    codebook, policy = read(FIXTURES / 'codebook.json'), read(FIXTURES / 'policy.json')
    all_facts, diffs, sizes, errors = {}, {}, {}, {}
    for name in ['T0', 'T1', 'T2']:
        fixture = read(FIXTURES / (name + '.json'))
        try:
            source_hash = sha(FIXTURES / (name + '.json'))
            packet, sidecar = encode(fixture, codebook, policy, source_hash)
            # Serialization boundary: retained facts decoded solely from the packet.
            packet_bytes = compact(packet)
            (out / (name + '.packet.json')).write_bytes(packet_bytes)
            provenance_path = out / (name + '.provenance.json')
            write(provenance_path, sidecar)
            persisted_sidecar = read(provenance_path)
            facts = decode(json.loads(packet_bytes))
            write(out / (name + '.decoded.json'), facts)
            structure = canonical_structure(facts)
            write(out / (name + '.structure.json'), structure)
            all_facts[name] = facts
            unknowns = {k: 'unknown' for k in policy['unknowns']}
            diffs[name] = {
                'facts': compare(facts, expected['fixtures'][name]),
                'provenance': provenance_audit(fixture, packet, persisted_sidecar, facts, source_hash),
                'unknowns': {
                    'passed': facts.get('unknowns') == unknowns,
                    'actual': facts.get('unknowns'),
                    'expected': unknowns,
                },
                'quality': quality_checks(facts),
                'provenance_path': {
                    'passed': packet.get('provenance_sidecar') == provenance_path.name,
                    'actual': packet.get('provenance_sidecar'),
                    'expected': provenance_path.name,
                },
            }
            sizes[name] = {
                'compact_source_fixture_bytes': len(compact(fixture)),
                'packet_bytes_cold_including_dictionary_and_policy': len(packet_bytes),
                'compact_provenance_bytes': len(compact(sidecar)),
                'retained_provenance_file_bytes': (out / (name + '.provenance.json')).stat().st_size,
                'dictionary_bytes_included_in_packet': len(compact(codebook)),
            }
        except Exception as error:
            # Preserve an honest result artifact when an encoder/decoder boundary
            # rejects a fixture. The run remains immutable and is never replaced.
            errors[name] = f'{type(error).__name__}: {error}'
            diffs[name] = {'error': errors[name]}

    contrasts = {}
    added_nodes, added_edges = [], []
    if all(name in all_facts for name in ['T0', 'T1', 'T2']):
        f0, f1, f2 = (all_facts[k] for k in ['T0', 'T1', 'T2'])
        n0 = {n['id']: n for n in f0['nodes']}
        n2 = {n['id']: n for n in f2['nodes']}
        # Ignore only source pointer changes when checking preservation of T0 in T2.
        semantic = lambda n: {k: v for k, v in n.items() if k != 'evidence'}
        added = [n for key, n in n2.items() if key not in n0]
        added_nodes = sorted([[n['id'], n['operation'], n['parent'], n['entity']] for n in added])
        added_edges = sorted([e for e in f2['edges'] if e not in f0['edges']])
        contrasts = {
            'T0_T1_equivalent': canonical_structure(f0) == canonical_structure(f1),
            'T0_T2_distinct': canonical_structure(f0) != canonical_structure(f2),
            'exact_added_node': added_nodes == [expected['contrasts']['added_node']],
            'exact_added_edge': added_edges == [expected['contrasts']['added_edge']],
            'existing_facts_unchanged': all(k in n2 and semantic(v) == semantic(n2[k]) for k, v in n0.items()),
            'count_deltas': (f2['span_count'] - f0['span_count'], f2['edge_count'] - f0['edge_count'], f2['counts']['catalog.get_product'] - f0['counts']['catalog.get_product']) == (1, 1, 1),
            'constant_labeler_rejected': not all(c['passed'] for c in compare(f0, expected['fixtures']['T2']).values()),
        }
    else:
        reason = 'not evaluated because fixture processing failed'
        contrasts = {key: False for key in (
            'T0_T1_equivalent', 'T0_T2_distinct', 'exact_added_node',
            'exact_added_edge', 'existing_facts_unchanged', 'count_deltas',
            'constant_labeler_rejected')}
    diffs['contrasts'] = {k: {'passed': v} for k, v in contrasts.items()}
    diffs['observed_delta'] = {'added_nodes': added_nodes, 'added_edges': added_edges}
    failures = []
    observed_failures = []
    for name in ['T0', 'T1', 'T2']:
        if name in errors:
            failures.append(f'{name}.execution')
            continue
        fixture_failures = [
            *[f'{name}.{k}' for k, v in diffs[name]['facts'].items() if not v['passed']],
            *[f'{name}.{k}' for k in ['provenance', 'provenance_path', 'unknowns'] if not diffs[name][k]['passed']],
            *[f'{name}.quality.{k}' for k, v in diffs[name]['quality'].items() if not v['passed']],
        ]
        failures.extend(fixture_failures)
        observed_failures.extend(fixture_failures)
    if not errors:
        contrast_failures = ['contrast.' + k for k, v in contrasts.items() if not v]
        failures.extend(contrast_failures)
        observed_failures.extend(contrast_failures)
    decision = 'falsified' if observed_failures else ('inconclusive' if errors else 'supported_on_fixture')
    diffs['decision'] = decision
    diffs['first_differing_fact'] = failures[0] if failures else None
    write(out / 'fact-diff.json', diffs)
    write(out / 'sizes.json', sizes)
    sources = [
        ROOT / 'docs/research/reliability-taxonomy-review.v1/07-incremental-experiments-handoff.v1.md',
        ROOT / 'specs/001-candidate-recall-experiment/plan.md',
        ROOT / 'specs/001-candidate-recall-experiment/contracts/semantic-evidence.md',
        ROOT / 'docs/research/track-1-trace-audit.md',
        ROOT / 'docs/research/reliability-taxonomy-review.v1/04-candidate-synthesis.v1.md',
        Path('/Users/nonadmin/Development/mantisgrid-hackathon/hackathon-2026-official/track-1/docs/data.md'),
        ROOT / 'experiments/semantic_encoding_v1/README.md',
        review,
    ]
    review_dir = ROOT / 'docs/research/experiments/semantic-encoding-v1'
    if review_dir.is_dir():
        sources.extend(sorted(path for path in review_dir.rglob('*') if path.is_file()))
    sources = list(dict.fromkeys(path for path in sources if path.is_file()))
    code_files = sorted(Path(__file__).parent.glob('*.py'))
    code_files.append(Path(__file__).parent / 'README.md')
    manifest = {'slice': 'S01', 'run_id': args.run_id, 'created_at': datetime.now(timezone.utc).isoformat(),
                'decision': decision, 'python': platform.python_version(), 'model_calls': 0,
                'annotation': 'provisional fidelity against authored expectations with separate agent review; no independent human validation',
                'freeze': freeze, 'source_sha256': {str(f): sha(f) for f in sources},
                'code_sha256': {str(f.relative_to(ROOT)): sha(f) for f in code_files},
                'stop': 'S01 only; S02 not started'}
    completed = [name for name in ['T0', 'T1', 'T2'] if name in all_facts]
    if errors:
        processing_summary = (
            'Decoded fact sheets were available for ' + (', '.join(completed) if completed else 'none')
            + '. Fixture processing errors were recorded for: '
            + ', '.join(f'{name} ({message})' for name, message in errors.items()) + '.'
        )
    else:
        processing_summary = 'All three decoded fact sheets were checked against expectations frozen before implementation.'
    if completed:
        observed_summary = '; '.join(
            f'{name}: {all_facts[name]["span_count"]} spans, '
            f'{all_facts[name]["edge_count"]} edges, '
            f'catalog.get_product={all_facts[name]["counts"].get("catalog.get_product", 0)}'
            for name in completed
        )
        pair_summary = ', '.join(
            str(len(all_facts[name]['different_entity_pairs'])) for name in completed
        )
    else:
        observed_summary = 'none'
        pair_summary = 'none'
    if 'constant_labeler_rejected' in contrasts:
        constant_summary = 'passed' if contrasts['constant_labeler_rejected'] else 'failed'
    else:
        constant_summary = 'not evaluated'
    text = f'''# S01 result — {decision}

Run: `{args.run_id}`. First differing fact: `{diffs['first_differing_fact']}`.

The hypothesis was that incidental trace/span identifier renaming and source-order
shuffling preserve operation/entity-colored parent structure, while one added
catalog child remains visible. T1 changes only IDs/order; T2 adds one catalog#1
occurrence under the original root. Operations, existing measurements, context,
entity names and existing parent references are held fixed modulo T1 ID renaming.

{processing_summary}
Source pointers and all nine raw fields were audited separately for each completed
fixture. The full decoded facts, available packets, provenance, tree signatures,
and exact comparisons are alongside this report. Observed decoded structure:
{observed_summary}. Different-entity pair counts, in T0/T1/T2 order where
available: {pair_summary}. Constant-output control: {constant_summary}.

Decision: **{decision}**. This is provisional fidelity against authored synthetic
expectations, separately reviewed by an agent. It is not independent human
validation, general graph validation, or evidence of real-telemetry fidelity.
No status semantics, success, backend targets or causal labels are inferred.
No motifs, model calls or real telemetry were used.

| Fixture | Compact source fixture bytes | Cold packet bytes | Compact provenance bytes |
|---|---:|---:|---:|
'''
    for name, size in sizes.items():
        text += f"| {name} | {size['compact_source_fixture_bytes']} | {size['packet_bytes_cold_including_dictionary_and_policy']} | {size['compact_provenance_bytes']} |\n"
    text += '''
Sizes are UTF-8 bytes, not estimated model tokens. Packets include the dictionary,
policy, context and reference metadata; provenance storage is separate. This is
the compact normalized graph control, not a symbolic/pattern compression trial.
The source fixture is not a matched-fidelity compression baseline. No compression
or model-cost benefit is claimed.

Next smallest experiment, if scheduled separately: S02's one indexed real trace,
with its full expected fact sheet independently reviewed before encoding. Stop
here as required by the handoff and A1 plan. If any check failed, repair that first.
'''
    (out / 'result.md').write_text(text)
    manifest['output_sha256'] = {str(f.relative_to(out)): sha(f) for f in out.rglob('*') if f.is_file()}
    write(out / 'manifest.json', manifest)
    print(json.dumps({'run_dir': str(out), 'decision': decision, 'first_differing_fact': diffs['first_differing_fact']}))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
