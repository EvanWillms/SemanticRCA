"""Independent source-record scorer for P01; no model or network access."""
import json
from collections import Counter

UNKNOWN_KEYS={'status_interpretation','business_outcome','interaction_role','backend_target','instrumentation_completeness'}


def json_equal(left, right):
    """Compare JSON values without Python's bool/int equality coercion."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return (left.keys() == right.keys()
                and all(json_equal(left[key], right[key]) for key in left))
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def parse_json(text):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate key')
            result[key]=value
        return result
    return json.loads(text, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite number')))


def score(answer, packet_id, source, book):
    errors=[]
    required={'schema_version','packet_id','trace_id','context','entities','occurrences','unknowns'}
    if not isinstance(answer,dict) or set(answer)!=required:
        return {'passed':False,'errors':['schema_fields']}
    if answer['schema_version']!='p01.v1' or answer['packet_id']!=packet_id: errors.append('schema_or_packet_identity')
    records=source['records']
    entities={f'e{i}':e for i,e in enumerate(sorted({r['cmdb_id'] for r in records}))}
    if answer['trace_id']!=records[0]['trace_id']:errors.append('trace_identity')
    if answer['entities']!=entities:errors.append('entity_dictionary')
    if not json_equal(answer['context'],source['context']):errors.append('context')
    if answer['unknowns']!={k:'unknown' for k in UNKNOWN_KEYS}:errors.append('unknowns_or_unsupported_promotion')
    actual=answer['occurrences']
    if not isinstance(actual,list) or any(not isinstance(row,list) or len(row)!=10 for row in actual):
        return {'passed':False,'errors':errors+['occurrence_schema']}
    expected=[]
    aliases={v:k for k,v in entities.items()}
    for i,row in enumerate(records,1):
        expected.append([row['span_id'],book['raw_mappings'][row['operation_name']],aliases[row['cmdb_id']],row['parent_span'] or None,row['operation_name'],row['timestamp'],row['duration'],row['type'],row['status_code'],f'{packet_id}:record:{i}'])
    serialize=lambda row:json.dumps(row,ensure_ascii=False,separators=(',',':'))
    ac=Counter(map(serialize,actual));ec=Counter(map(serialize,expected))
    if ac!=ec:errors.append('raw_structure_or_evidence_mismatch')
    return {'passed':not errors,'errors':errors,'expected_occurrences':len(expected),'actual_occurrences':len(actual),'missing_occurrences':list((ec-ac).elements()),'unexpected_occurrences':list((ac-ec).elements())}
