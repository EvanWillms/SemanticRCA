import csv
import json
from pathlib import Path
import pytest
from experiments.frontend_blind_v1.build_index import build_index, get_frontend, get_traces
from experiments.frontend_blind_v1.retrieval import get_metrics,get_logs
from experiments.frontend_blind_v1.seal import seal_stage


def write(path,fields,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(fields);w.writerows(rows)


def fixture(tmp_path,candidates=('pod-1',),evidence=None):
    root=tmp_path/'telemetry';mf=['timestamp','cmdb_id','kpi_name','value']
    write(root/'2022_03_20/metric/metric_node.csv',mf,[['900','node-1','cpu','1'],['1000','node-1','cpu','3'],['1100','node-1','cpu','5']])
    write(root/'2022_03_20/metric/metric_container.csv',mf,[['900','node-1.pod-1','memory','10'],['950','node-1.pod-1','memory','12'],['1000','node-1.pod-1','memory','30'],['1100','node-1.pod-1','memory','40']])
    write(root/'2022_03_20/metric/metric_service.csv',['service','timestamp','rr','sr','mrt','count'],[['pod-1','900','1','1','2','3'],['pod-1','1000','2','0.5','3','4']])
    write(root/'2022_03_20/log/log_service.csv',['log_id','timestamp','cmdb_id','log_name','value'],[[f'l{i}',str(900+i),'pod-1','app','timeout'] for i in range(300)])
    index=tmp_path/'index.sqlite3';build_index(index,root)
    case=tmp_path/'case';case.mkdir()
    (case/'scope.json').write_text(json.dumps({'row_id':0,'failure_count':1,'query_start':'1970-01-01T00:16:40+00:00','query_end':'1970-01-01T00:20:00+00:00','reference_start':'1970-01-01T00:15:00+00:00'}))
    (case/'index.json').write_text(json.dumps({'index':str(index)}))
    (case/'trace_evidence.json').write_text(json.dumps(evidence or {'traces':[],'component_shortlist':list(candidates)}))
    (case/'trace_only.json').write_text(json.dumps({'row_id':0,'stage':'trace_only','candidates':list(candidates),'incidents':[{'occurrence_time':'','component':'','reason':'','observed_symptom_time':'','confidence':'','evidence_refs':[]}]}))
    return case


def test_index_frontend_half_open_and_full_cross_day_trace(tmp_path):
    root=tmp_path/'telemetry';fields=['timestamp','cmdb_id','span_id','trace_id','duration','type','status_code','operation_name','parent_span']
    write(root/'2022_03_20/trace/trace_span.csv',fields,[['1000','frontend-1','001e2','t1','10','rpc','0','root',''],['1005','other-1','child','t1','5','rpc','0','call','001e2']])
    write(root/'2022_03_21/trace/trace_span.csv',fields,[['1100','other-2','late','t1','4','rpc','0','call','child'],['1200','frontend-1','next','t2','3','rpc','0','root','']])
    p=tmp_path/'index.db';build_index(p,root)
    rows=get_frontend(1000,1200,p)
    assert len(rows)==1 and rows[0]['span_id']=='001e2' and rows[0]['source_record']==2
    assert len(get_traces(['t1'],p)['t1'])==3


def test_pod_mapping_host_mapping_and_service_fields(tmp_path):
    case=fixture(tmp_path);seal_stage(case,'trace_only',source_snapshot={})
    m=get_metrics(case,['pod-1'],sources=['container'])
    assert m['series'][0]['component']=='node-1.pod-1'
    assert m['series'][0]['query']['median']==35
    assert m['explicit_mappings'][0]['kind']=='recorded_dotted_pod'
    n=get_metrics(case,['pod-1'],sources=['node'])
    assert n['series'][0]['query']['median']==4
    assert n['explicit_mappings'][0]['kind']=='recorded_node_pod'
    s=get_metrics(case,['pod-1'],sources=['service'])
    assert {r['kpi_name'] for r in s['series']}=={'rr','sr','mrt','count'}


def test_seal_required_and_mutation_rejected(tmp_path):
    case=fixture(tmp_path)
    with pytest.raises(PermissionError):get_metrics(case,['pod-1'])
    seal_stage(case,'trace_only',source_snapshot={})
    p=case/'trace_only.json';v=json.loads(p.read_text());v['candidates']=['other'];p.write_text(json.dumps(v))
    with pytest.raises(PermissionError):get_metrics(case,['other'])


def test_persistent_budget_and_no_unlinked_expansion(tmp_path):
    case=fixture(tmp_path);seal_stage(case,'trace_only',source_snapshot={})
    with pytest.raises(PermissionError):get_metrics(case,['not-linked'])
    for i in range(20):
        result=get_metrics(case,['pod-1'],sources=['container'])
        assert result['budget_remaining']==19-i
    with pytest.raises(PermissionError):get_metrics(case,['pod-1'],sources=['container'])
    assert len((case/'retrieval.jsonl').read_text().splitlines())==20


def test_rescue_not_permitted_with_trace_candidates(tmp_path):
    case=fixture(tmp_path);seal_stage(case,'trace_only',source_snapshot={})
    with pytest.raises(PermissionError):get_metrics(case,[])


def test_rescue_once_and_provenance(tmp_path):
    case=fixture(tmp_path,candidates=());seal_stage(case,'trace_only',source_snapshot={})
    result=get_metrics(case,[],sources=['node'])
    assert result['global_metric_rescue'] and result['series'][0]['query']['maximum_record']['source_record']==4
    with pytest.raises(PermissionError):get_metrics(case,[])


def test_logs_capped_balanced_and_persistent_budget(tmp_path):
    case=fixture(tmp_path);seal_stage(case,'trace_only',source_snapshot={})
    result=get_logs(case,['pod-1'],contains='timeout')
    assert result['count']==200 and result['available_count']==300 and result['truncated']
    assert {r['window'] for r in result['records']}=={'reference','query'}
    for i in range(9):get_logs(case,['pod-1'],window='query',limit=1)
    with pytest.raises(PermissionError):get_logs(case,['pod-1'])
