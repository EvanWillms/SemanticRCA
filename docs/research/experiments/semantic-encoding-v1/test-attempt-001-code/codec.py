"""S01 normalized graph control; no motif discovery or causal interpretation.

The codec cannot read expected facts or source files. Decoding needs the packet
only. Provenance is separately audited by the experiment runner.
"""
import hashlib
import json
from collections import Counter
from itertools import combinations


_REQUIRED_RECORD_FIELDS = frozenset(
    {
        'cmdb_id',
        'duration',
        'operation_name',
        'parent_span',
        'span_id',
        'status_code',
        'timestamp',
        'trace_id',
        'type',
    }
)


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(compact(value)).hexdigest()


def encode(fixture, codebook, policy, source_sha256):
    rows = fixture['records']
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f'S01 record {index} must be an object')
        missing = _REQUIRED_RECORD_FIELDS.difference(row)
        if missing:
            names = ', '.join(sorted(missing))
            raise ValueError(f'S01 record {index} is missing required field(s): {names}')
    identities = [r['span_id'] for r in rows]
    if not rows or len(identities) != len(set(identities)):
        raise ValueError('S01 requires nonempty unique span identities')
    traces = {r['trace_id'] for r in rows}
    if len(traces) != 1:
        raise ValueError('S01 requires one trace')
    if any(r['parent_span'] and r['parent_span'] not in identities for r in rows):
        raise ValueError('S01 requires resolved parents')
    entities = sorted({r['cmdb_id'] for r in rows})
    aliases = {entity: f'e{i}' for i, entity in enumerate(entities)}
    nodes, pointers = [], {}
    for index, row in enumerate(rows):
        raw = row['operation_name']
        symbol = codebook['raw_mappings'].get(raw)
        if symbol is None:
            raise ValueError('Operation outside the frozen S01 dictionary')
        evidence = f'{fixture["fixture"]}:record:{index + 1}'
        nodes.append({'id': row['span_id'], 'op': symbol, 'entity': aliases[row['cmdb_id']],
                      'parent': row['parent_span'] or None,
                      'raw_operation': raw, 'timestamp': row['timestamp'],
                      'duration': row['duration'], 'type': row['type'],
                      'status_code': row['status_code'], 'evidence': evidence})
        pointers[evidence] = {'record_index_1based': index + 1,
                              'trace_id': row['trace_id'], 'span_id': row['span_id'],
                              'row_sha256': digest(row)}
    packet = {'packet_id': fixture['fixture'], 'schema_version': 's01-normalized-v1',
              'codebook': codebook, 'policy': policy,
              'source_sha256': source_sha256, 'trace_id': next(iter(traces)),
              'context': fixture['context'],
              'entities': {alias: entity for entity, alias in aliases.items()},
              'nodes': sorted(nodes, key=lambda n: n['id']),
              'counts': dict(Counter(n['op'] for n in nodes)),
              'quality': {'retrieval': 'complete_authored_fixture',
                          'instrumentation_completeness': 'unknown'},
              'unknowns': {key: 'unknown' for key in policy['unknowns']},
              'provenance_sidecar': f'{fixture["fixture"]}.provenance.json'}
    # Validate that the supported shape really is a rooted tree.
    canonical_structure(decode(packet))
    return packet, {'source_sha256': source_sha256, 'records': pointers}


def decode(packet):
    operations = packet['codebook']['operations']
    nodes = [{'id': n['id'], 'operation': operations[n['op']],
              'parent': n['parent'], 'entity': packet['entities'][n['entity']],
              'parent_resolution': 'root_marker' if n['parent'] is None else 'resolved',
              'raw_operation': n['raw_operation'], 'timestamp': n['timestamp'],
              'duration': n['duration'], 'type': n['type'],
              'status_code': n['status_code'], 'evidence': n['evidence']}
             for n in packet['nodes']]
    counts = dict(Counter(n['operation'] for n in nodes))
    if counts != {operations[k]: v for k, v in packet['counts'].items()}:
        raise ValueError('Packet multiplicities disagree with occurrence membership')
    same, different = [], []
    for a, b in combinations(sorted(nodes, key=lambda n: n['id']), 2):
        (same if a['entity'] == b['entity'] else different).append([a['id'], b['id']])
    return {'nodes': nodes, 'counts': counts,
            'edges': sorted([[n['parent'], n['id']] for n in nodes if n['parent'] is not None]),
            'span_count': len(nodes), 'edge_count': sum(n['parent'] is not None for n in nodes),
            'same_entity_pairs': same, 'different_entity_pairs': different,
            'trace_id': packet['trace_id'], 'context': packet['context'],
            'quality': packet['quality'], 'unknowns': packet['unknowns']}


def canonical_structure(facts):
    """Unordered rooted-tree signature; exact operation/entity colors, no raw IDs."""
    nodes = {n['id']: n for n in facts['nodes']}
    roots = [n['id'] for n in nodes.values() if n['parent'] is None]
    if len(nodes) != len(facts['nodes']) or len(roots) != 1:
        raise ValueError('S01 supports exactly one root and unique nodes')
    children = {key: [] for key in nodes}
    for n in nodes.values():
        if n['parent'] is not None:
            if n['parent'] not in children:
                raise ValueError('Unresolved parent')
            children[n['parent']].append(n['id'])
    seen = set()
    def visit(key):
        if key in seen:
            raise ValueError('Cycle or repeated membership')
        seen.add(key)
        n = nodes[key]
        return [n['operation'], n['entity'], sorted((visit(c) for c in children[key]), key=compact)]
    result = visit(roots[0])
    if len(seen) != len(nodes):
        raise ValueError('Disconnected or cyclic graph')
    return result
