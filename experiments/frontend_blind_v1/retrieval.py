"""Bounded label-free metric/log retrieval, authorized by a sealed trace stage."""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
import statistics
import time
from .build_index import DEFAULT_INDEX
from .seal import verify_seal, SealError

METRIC_SOURCES = ('service', 'container', 'runtime', 'node', 'mesh')
LOG_SOURCES = ('service', 'proxy')
MAX_METRIC_CALLS, MAX_LOG_CALLS = 20, 10
MAX_SERIES, MAX_VALUES, MAX_LOG_RECORDS = 50, 120, 200


def _json(path):
    return json.loads(Path(path).read_text())


def _events(case):
    p = case / 'retrieval.jsonl'
    return [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []


def _require_seal(case):
    try:
        verify_seal(case, 'trace_only')
    except (SealError, OSError, ValueError) as exc:
        raise PermissionError('A valid immutable trace-only seal is required') from exc


def _scope(case):
    s = _json(case / 'scope.json')
    def ms(k):
        d = datetime.fromisoformat(s[k])
        if d.tzinfo is None:
            raise ValueError('Scope timestamps require an explicit timezone')
        return int(d.timestamp() * 1000)
    a, b, c = ms('reference_start'), ms('query_start'), ms('query_end')
    if not a < b < c:
        raise ValueError('Reference/query intervals are invalid')
    return {'reference': [a, b], 'query': [b, c]}


def _db(case):
    p = DEFAULT_INDEX
    if (case / 'index.json').exists():
        p = Path(_json(case / 'index.json')['index'])
    elif (case / 'index_path.txt').exists():
        p = Path((case / 'index_path.txt').read_text().strip())
    conn = sqlite3.connect(f'file:{Path(p).resolve()}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _authorize(case, requested, operation):
    _require_seal(case)
    ev = _events(case)
    budget = MAX_METRIC_CALLS if operation == 'get_metrics' else MAX_LOG_CALLS
    used = sum(1 for e in ev if e.get('operation') == operation)
    if used >= budget:
        raise PermissionError(f'{operation} budget exhausted ({budget} structured calls)')
    initial = list(dict.fromkeys(_json(case / 'trace_only.json').get('candidates', [])))
    if len(initial) > 5 or any(not isinstance(x, str) or not x for x in initial):
        raise ValueError('Trace stage must select at most five valid initial components')
    selected = list(dict.fromkeys(requested))
    if any(not isinstance(x, str) or not x for x in selected):
        raise ValueError('Requested components must be nonempty strings')
    evidence = _json(case / 'trace_evidence.json') if (case / 'trace_evidence.json').exists() else {}
    rescue = not selected and operation == 'get_metrics'
    if rescue:
        if initial or evidence.get('component_shortlist'):
            raise PermissionError('Global rescue only permitted when trace discovery has no candidates')
        if any(e.get('global_metric_rescue') for e in ev):
            raise PermissionError('Only one global-metric rescue is permitted')
    elif not selected:
        raise ValueError('Log retrieval requires explicit components')
    linked = set()
    trace_components = set()
    for tr in evidence.get('traces', []):
        spans = tr.get('spans', [])
        by_id = {str(r['span_id']): r for r in spans}
        trace_components.update(r['cmdb_id'] for r in spans)
        for r in spans:
            parent = by_id.get(str(r.get('parent_span', '')))
            if parent and parent['cmdb_id'] != r['cmdb_id']:
                if parent['cmdb_id'] in initial:
                    linked.add(r['cmdb_id'])
                if r['cmdb_id'] in initial:
                    linked.add(parent['cmdb_id'])
    if trace_components and set(initial) - trace_components:
        raise PermissionError('An initial candidate is absent from selected trace evidence')
    # Global rescue may nominate components only from its saved response inventory.
    for e in ev:
        if e.get('global_metric_rescue'):
            linked.update(e.get('returned_components', []))
    expanded = []
    for e in ev:
        expanded = e.get('expanded_components', expanded)
    additions = [x for x in selected if x not in initial and x not in expanded]
    if additions:
        if expanded:
            raise PermissionError('Only one component expansion is permitted')
        if len(additions) > 5 or set(additions) - linked:
            raise PermissionError('Expansion requires up to five explicitly linked or rescue-supported components')
        expanded = additions
    return initial, expanded, selected, rescue, used, budget


def _mapping(conn, source, components):
    identities = [r[0] for r in conn.execute('SELECT DISTINCT identity FROM metric_rows WHERE source=?', (source,))]
    # The documented container source identity is <node>.<pod>; this is a
    # recorded mapping, not an inference from similar component names.
    containers = [r[0] for r in conn.execute("SELECT DISTINCT identity FROM metric_rows WHERE source='container'")]
    host_pairs = [(x.split('.', 1)[0], x.split('.', 1)[1], x) for x in containers if '.' in x]
    resolved, mappings = [], []
    for identity in identities:
        for component in components:
            exact = identity == component
            dotted = '.' in identity and identity.split('.', 1)[1] == component
            host = source == 'node' and any(n == identity and p == component for n,p,_ in host_pairs)
            if exact or dotted or host:
                if identity not in resolved:
                    resolved.append(identity)
                mappings.append({'requested_component': component, 'source_identity': identity,
                                 'kind': 'exact' if exact else 'recorded_node_pod' if host else 'recorded_dotted_pod',
                                 'mapping_identity': next((raw for n,p,raw in host_pairs if n==identity and p==component), None) if host else identity})
    return resolved, mappings


def _number(value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _sample(rows, limit):
    if len(rows) <= limit:
        return rows
    ids = {0, len(rows)-1}
    vals = [(_number(r['value']), i) for i,r in enumerate(rows)]
    valid = [(v,i) for v,i in vals if v is not None]
    if valid:
        ids.update([min(valid)[1], max(valid)[1]])
    for i in range(limit):
        if len(ids) >= limit:
            break
        ids.add(round(i*(len(rows)-1)/(limit-1)))
    return [rows[i] for i in sorted(ids)[:limit]]


def _stats(rows, bounds):
    valid = [(r, _number(r['value'])) for r in rows]
    valid = [(r,v) for r,v in valid if v is not None]
    vals = [v for _,v in valid]
    med = statistics.median(vals) if vals else None
    mad = statistics.median(abs(v-med) for v in vals) if vals else None
    stamps = sorted({r['timestamp_ms'] for r in rows})
    gaps = [b-a for a,b in zip(stamps,stamps[1:]) if b>a]
    cadence = statistics.median(gaps) if gaps else None
    n_expected = (bounds[1]-bounds[0])/cadence if cadence else None
    bins = []
    for i in range(12):
        lo = bounds[0]+i*(bounds[1]-bounds[0])//12
        hi = bounds[0]+(i+1)*(bounds[1]-bounds[0])//12
        vs = [v for r,v in valid if lo<=r['timestamp_ms']<hi]
        bins.append({'start_ms':lo,'end_ms':hi,'count':len(vs),'median':statistics.median(vs) if vs else None,
                     'min':min(vs) if vs else None,'max':max(vs) if vs else None})
    return {'count':len(vals),'raw_count':len(rows),'median':med,'mad':mad,'zero_mad':mad==0 if mad is not None else False,
            'range':{'min':min(vals) if vals else None,'max':max(vals) if vals else None},
            'minimum_record': min(valid,key=lambda rv:rv[1])[0] if valid else None,
            'maximum_record': max(valid,key=lambda rv:rv[1])[0] if valid else None,
            'values':_sample(rows,60),'time_pattern':bins,
            'cadence_coverage':{'median_cadence_ms':cadence,'observed_points':len(stamps),
                'observed_start_ms':stamps[0] if stamps else None,'observed_end_ms':stamps[-1] if stamps else None,
                'coverage_ratio':min(1,len(stamps)/n_expected) if n_expected else None}}


def _record(row, raw, value, kpi):
    return {'timestamp_ms':int(row['timestamp_ms']),'value':value,'kpi_name':kpi,
            'source_file':row['source_file'],'source_record':int(row['source_record']),'source_header':1,
            'source_identity':row['identity'],'raw':raw}


def _save(case, result, event):
    events = _events(case)
    path = case / f'retrieval_{len(events)+1:02d}_{event["operation"]}.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    event = {'ts':datetime.now(timezone.utc).isoformat(),'response_file':path.name,**event}
    with (case/'retrieval.jsonl').open('a') as f:
        f.write(json.dumps(event)+'\n')
    result['response_file'] = str(path)
    return result


def get_metrics(case_dir, components, sources=None, *, kpis=None):
    """One bounded structured call; optional exact KPI selection within budget."""
    case = Path(case_dir)
    initial, expanded, selected, rescue, used, budget = _authorize(case,components,'get_metrics')
    windows = _scope(case)
    sources = list(dict.fromkeys(str(s).removeprefix('metric_') for s in (sources or METRIC_SOURCES)))
    if set(sources)-set(METRIC_SOURCES):
        raise ValueError('Unknown metric source')
    started=time.perf_counter(); series=[]; mappings=[]; inventory=[]
    conn=_db(case)
    try:
        for source in sources:
            identities, mapping = _mapping(conn,source,selected) if not rescue else ([],[])
            mappings.extend(mapping)
            sql='SELECT * FROM metric_rows WHERE source=? AND timestamp_ms>=? AND timestamp_ms<?'
            params=[source,windows['reference'][0],windows['query'][1]]
            if not rescue:
                if not identities:
                    continue
                sql += ' AND identity IN ('+','.join('?' for _ in identities)+')';params+=identities
            sql+=' ORDER BY identity,kpi_name,timestamp_ms,source_file,source_record'
            groups=defaultdict(list)
            for row in conn.execute(sql,params):
                raw=json.loads(row['raw_json'])
                fields=('rr','sr','mrt','count') if source=='service' else (str(raw.get('kpi_name','')),)
                for kpi in fields:
                    if kpis is not None and kpi not in kpis:
                        continue
                    value=raw.get(kpi) if source=='service' else raw.get('value')
                    groups[(row['identity'],kpi)].append(_record(row,raw,value,kpi))
            for (identity,kpi), rows in groups.items():
                q=[r for r in rows if windows['query'][0]<=r['timestamp_ms']<windows['query'][1]]
                b=[r for r in rows if windows['reference'][0]<=r['timestamp_ms']<windows['reference'][1]]
                qs,bs=_stats(q,windows['query']),_stats(b,windows['reference'])
                signed = (qs['median']-bs['median'])/(1.4826*bs['mad']) if qs['median'] is not None and bs['median'] is not None and bs['mad'] and bs['mad']>0 else None
                extreme=max(abs(qs['range'][k]-bs['median']) for k in ('min','max'))/(1.4826*bs['mad']) if qs['count'] and bs['count'] and bs['mad'] and bs['mad']>0 else None
                series.append({'component':identity,'source':source,'kpi_name':kpi,'query':qs,'reference':bs,
                    'signed_median_departure':signed,'max_absolute_departure':extreme,
                    'zero_mad':{'reference':bs['zero_mad'],'query':qs['zero_mad']},
                    'units':'not declared in CSV; preserve raw values and KPI name',
                    'timestamp_unit':'raw epoch seconds; output timestamp_ms converts explicitly',
                    'counter_uncertainty':{'status':'unknown','reason':'No counter/gauge schema; raw values, no inferred rate'}})
                inventory.append({'source':source,'component':identity,'kpi_name':kpi})
    finally:conn.close()
    # Round-robin identities prevents one component consuming the response cap.
    buckets=defaultdict(list)
    for s in series:buckets[s['component']].append(s)
    for values in buckets.values():values.sort(key=lambda s:(-(s['max_absolute_departure'] or 0),s['source'],s['kpi_name']))
    chosen=[]
    for i in range(max((len(v) for v in buckets.values()),default=0)):
        for identity in sorted(buckets):
            if i<len(buckets[identity]) and len(chosen)<MAX_SERIES:chosen.append(buckets[identity][i])
    result={'windows':windows,'components':{'initial':initial,'expanded':expanded,'selected':selected},'sources':sources,
        'series':chosen,'available_series':inventory[:200],'available_series_count':len(series),
        'series_truncated':len(series)>len(chosen),'available_series_truncated':len(inventory)>200,
        'explicit_mappings':mappings,'call_count':1,'calls_used_before':used,'budget_remaining':budget-used-1,
        'global_metric_rescue':rescue,'elapsed_seconds':time.perf_counter()-started,
        'sampling_policy':'component round robin; descending reference-scaled extreme departure within component; zero/unknown MAD has no numeric score',
        'limits':{'max_calls':budget,'max_series':50,'max_values_total_per_series':120}}
    return _save(case,result,{'operation':'get_metrics','components':selected,'initial_components':initial,
        'expanded_components':expanded,'sources':sources,'kpis':kpis,'call_count':1,'series_count':len(chosen),
        'global_metric_rescue':rescue,'returned_components':sorted({s['component'] for s in chosen}),
        'elapsed_seconds':result['elapsed_seconds']})


def get_logs(case_dir, components, limit=200, contains=None, *, window='both', sources=None):
    """Bounded logs with explicit period selection; deterministic balanced caps."""
    case=Path(case_dir)
    initial,expanded,selected,_,used,budget=_authorize(case,components,'get_logs')
    windows=_scope(case)
    if window not in ('both','query','reference'):raise ValueError('Invalid window')
    periods=('query','reference') if window=='both' else (window,)
    sources=list(sources or LOG_SOURCES)
    if set(sources)-set(LOG_SOURCES):raise ValueError('Invalid log source')
    limit=min(MAX_LOG_RECORDS,max(1,int(limit)));conn=_db(case);buckets={};count=0
    started=time.perf_counter()
    try:
        for source in sources:
            for period in periods:
                a,b=windows[period]
                sql='SELECT * FROM log_rows WHERE source=? AND timestamp_ms>=? AND timestamp_ms<? AND identity IN ('+','.join('?' for _ in selected)+')'
                params=[source,a,b,*selected]
                if contains:
                    sql+=' AND instr(lower(raw_json),lower(?))>0';params.append(str(contains))
                sql+=' ORDER BY timestamp_ms,log_id,source_file,source_record'
                rows=[]
                for r in conn.execute(sql,params):
                    raw=json.loads(r['raw_json'])
                    rows.append({'window':period,'source':source,'timestamp_ms':int(r['timestamp_ms']),**raw,
                                 'source_file':r['source_file'],'source_record':int(r['source_record']),'source_header':1})
                count+=len(rows)
                buckets[(period,source)]=rows
    finally:conn.close()
    quotas={k:min(len(v),limit//max(1,len(buckets))) for k,v in buckets.items()}
    remaining=limit-sum(quotas.values())
    for k in sorted(buckets):
        extra=min(remaining,len(buckets[k])-quotas[k]);quotas[k]+=extra;remaining-=extra
    chosen=[]
    for k,rows in buckets.items():
        n=quotas[k]
        if n==0:continue
        indexes=list(range(len(rows))) if len(rows)<=n else sorted({round(i*(len(rows)-1)/max(1,n-1)) for i in range(n)})
        chosen.extend(rows[i] for i in indexes)
    chosen.sort(key=lambda r:(r['timestamp_ms'],r.get('log_id',''),r['source']))
    result={'windows':windows,'components':{'initial':initial,'expanded':expanded,'selected':selected},'contains':contains,
            'records':chosen[:limit],'count':min(len(chosen),limit),'available_count':count,'truncated':count>limit,
            'call_count':1,'budget_remaining':budget-used-1,'elapsed_seconds':time.perf_counter()-started,
            'sampling_policy':'balanced requested periods/sources, evenly spaced matching records ordered by timestamp',
            'limits':{'max_calls':budget,'max_records':limit}}
    return _save(case,result,{'operation':'get_logs','components':selected,'initial_components':initial,
        'expanded_components':expanded,'contains':contains,'window':window,'sources':sources,'call_count':1,
        'record_count':result['count'],'available_count':count,'truncated':result['truncated'],'elapsed_seconds':result['elapsed_seconds']})
