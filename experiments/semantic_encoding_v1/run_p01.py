"""Immutable, budgeted P01 execution. Prepare/tokenize, execute, and replay score."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from .featherless_p01 import MODEL, credentials, request
from .score_p01 import parse_json, score

ROOT=Path(__file__).resolve().parents[2]
DESIGN=ROOT/'specs/008-featherless-trace-semantics'
RUNS=ROOT/'data/experiments/semantic-encoding-v1/P01'
RATES={'fresh':.15,'cached':.03,'output':.5}
LIMITS={'attempts':18,'input_tokens':8192,'output_tokens':4096,'timeout_seconds':60,'deadline_seconds':1200,'reserve_seconds':30,'cost_usd':1.0}


def now():return datetime.now(timezone.utc).isoformat()
def digest(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def append(path,value):
    with path.open('a') as f:
        f.write(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n');f.flush()
def compact(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)


def create_run_dir(parent,name):
    if not re.fullmatch(r'[A-Za-z0-9_-]+',name):raise ValueError('invalid run id')
    path=parent/name;path.mkdir(parents=True,exist_ok=False);return path


def build_request(prompt,payload):
    return {'model':MODEL,'messages':[{'role':'system','content':prompt},{'role':'user','content':compact(payload)}], 'temperature':0,'reasoning_effort':'low','max_tokens':4096,'stream':False}


def integer(value):return value if type(value) is int and value>=0 else None


def usage_cost(usage,rates=RATES):
    usage=usage if isinstance(usage,dict) else {}
    p=integer(usage.get('prompt_tokens'));o=integer(usage.get('completion_tokens'))
    details=usage.get('prompt_tokens_details')
    nested=integer(details.get('cached_tokens')) if isinstance(details,dict) else None
    top=integer(usage.get('cached_tokens'))
    h=nested if nested is not None else top
    conflict=nested is not None and top is not None and nested!=top
    invalid=conflict or (h is not None and (p is None or h>p))
    if invalid:h=None
    upper=(p*rates['fresh']+o*rates['output'])/1e6 if p is not None and o is not None else None
    estimate=upper-h*(rates['fresh']-rates['cached'])/1e6 if upper is not None and h is not None else None
    return {'input_tokens':p,'output_tokens':o,'cached_input_tokens':h,'invalid_cache_counter':invalid,'uncached_estimate_usd':upper,'estimated_cost_usd':estimate,'observed_charge_usd':None}


def admit(attempts,reserved,elapsed,input_bound,next_cost):
    return attempts<18 and reserved+next_cost<=1.0 and elapsed+60+30<=1200 and input_bound<=8192


def token_count(result):
    body=result.get('json')
    if result.get('status')!=200 or not isinstance(body,dict):return None
    if body.get('model',MODEL)!=MODEL:return None
    if isinstance(body.get('tokens'),list):return len(body['tokens'])
    return integer(body.get('count'))


def prepare(name):
    path=create_run_dir(RUNS,name)
    for folder in ['inputs','sources','code','requests','responses','tokenization']: (path/folder).mkdir()
    m=read(DESIGN/'design-fixtures/p01/evaluation-manifest.json')
    prompt=(DESIGN/'prompts/structural-v1.txt').read_text()
    if digest(prompt.encode())!=m['prompt_sha256']:raise ValueError('prompt hash mismatch')
    (path/'prompt.txt').write_text(prompt)
    for filename,h in m['input_sha256'].items():
        src=DESIGN/'design-fixtures/p01'/filename
        if digest(src.read_bytes())!=h:raise ValueError('input hash mismatch')
        shutil.copyfile(src,path/'inputs'/filename)
    for source,h in m['source_sha256'].items():
        src=ROOT/source
        if digest(src.read_bytes())!=h:raise ValueError('source hash mismatch')
        shutil.copyfile(src,path/'sources'/src.name)
    shutil.copyfile(ROOT/'experiments/semantic_encoding_v1/fixtures/codebook.json',path/'sources/codebook.json')
    for module in ['run_p01.py','score_p01.py','featherless_p01.py','test_p01.py']:
        shutil.copyfile(Path(__file__).parent/module,path/'code'/module)
    catalogue=read(ROOT/'data/experiments/semantic-encoding-v1/P01-preflight-20260917/glm-models.json')
    model=next((v for v in catalogue['glm_models'] if v['id']==MODEL),None)
    if not model or not model.get('available_on_current_plan'):raise ValueError('model unavailable')
    if float(model['pricing']['input'])!=RATES['fresh'] or float(model['pricing']['output'])!=RATES['output']:raise ValueError('model rates changed; refreeze required')
    for trial in m['schedule']:
        body=build_request(prompt,read(path/'inputs'/trial['input']))
        write(path/'requests'/f"{trial['trial']:02d}.json",body)
    write(path/'design-manifest.json',m)
    freeze={'created_at':now(),'checkpoint':'b83e97c','model':MODEL,'model_capability':model,'rates_per_million':RATES,'rate_source':'GET /v1/models and https://featherless.ai/models/zai-org/GLM-5.3-Flash','limits':LIMITS,'file_sha256':{str(p.relative_to(path)):digest(p.read_bytes()) for sub in ['inputs','sources','code','requests'] for p in sorted((path/sub).iterdir())},'prompt_sha256':digest(prompt.encode()),'design_manifest_sha256':digest((path/'design-manifest.json').read_bytes()),'status':'prepared_before_tokenization'}
    write(path/'freeze.json',freeze)
    key,base=credentials(ROOT/'.env')
    counts={};events=[]
    texts={'static_prefix':prompt}
    texts.update({p.name:compact(read(p)) for p in sorted((path/'inputs').glob('*.json'))})
    for label,text in texts.items():
        append(path/'metadata-attempts.jsonl',{'event':'started','label':label,'endpoint':'/tokenize','at':now()})
        result=request(key,base,'/tokenize',{'model':MODEL,'text':text},timeout=30)
        write(path/'tokenization'/f'{label}.json',result)
        count=token_count(result)
        counts[label]=count;events.append({'label':label,'status':result['status'],'tokens':count})
        append(path/'metadata-attempts.jsonl',{'event':'finished','label':label,'status':result['status'],'tokens':count,'at':now()})
        print(json.dumps(events[-1]),flush=True)
        if count is None:break
    complete=len(counts)==7 and all(v is not None for v in counts.values())
    # Text counts exclude chat-template tokens. A 512-token envelope is explicit;
    # actual response usage is independently checked against the 8192-token cap.
    bounds={k:counts['static_prefix']+v+512 for k,v in counts.items() if k!='static_prefix' and complete}
    ready=complete and all(v<=8192 for v in bounds.values())
    write(path/'preflight.json',{'ready':ready,'token_counts':counts,'token_count_scope':'provider tokenizer on exact message content; chat template excluded','chat_template_envelope_tokens':512,'input_admission_bounds':bounds,'metadata_requests':len(events),'inference_attempts':0,'base_url':base,'at':now()})
    print(json.dumps({'run_dir':str(path),'ready':ready,'static_prefix_tokens':counts.get('static_prefix')}),flush=True)
    return path


def verify_freeze(path, check_live_code=True):
    f=read(path/'freeze.json')
    for rel,h in f['file_sha256'].items():
        if digest((path/rel).read_bytes())!=h:raise ValueError('run input/code snapshot changed')
    if digest((path/'prompt.txt').read_bytes())!=f['prompt_sha256']:raise ValueError('prompt changed')
    if digest((path/'design-manifest.json').read_bytes())!=f['design_manifest_sha256']:raise ValueError('manifest changed')
    artifact_manifest=path/'artifact-sha256.json'
    if artifact_manifest.exists():
        for rel,h in read(artifact_manifest).items():
            if digest((path/rel).read_bytes())!=h:raise ValueError('run artifact changed')
    if check_live_code:
        for module in ['run_p01.py','score_p01.py','featherless_p01.py']:
            if digest((Path(__file__).parent/module).read_bytes())!=f['file_sha256']['code/'+module]:raise ValueError('live code changed since freeze')
    return f


def run(path):
    f=verify_freeze(path);pre=read(path/'preflight.json')
    if not pre['ready']:raise ValueError('preflight not ready; no inference admitted')
    with (path/'started.json').open('x') as handle:json.dump({'at':now()},handle)
    key,base=credentials(ROOT/'.env')
    if base!=pre['base_url']:raise ValueError('endpoint changed')
    start=time.monotonic();deadline=start+LIMITS['deadline_seconds'];reserved=0;attempts=0;reason=None
    worst=(8192*RATES['fresh']+4096*RATES['output'])/1e6
    trials=read(path/'design-manifest.json')['schedule']
    for trial in trials:
        number=trial['trial'];bound=pre['input_admission_bounds'][trial['input']]
        if reason or not admit(attempts,reserved,time.monotonic()-start,bound,worst):
            append(path/'attempts.jsonl',dict(trial,event='not_dispatched',reason=reason or 'budget_guard'));continue
        reserved+=worst;attempts+=1
        body=read(path/'requests'/f'{number:02d}.json')
        append(path/'attempts.jsonl',dict(trial,event='dispatched',at=now(),reserved_cost_usd=worst))
        result=request(key,base,'/chat/completions',body,timeout=LIMITS['timeout_seconds'],deadline=deadline)
        write(path/'responses'/f'{number:02d}.json',result)
        j=result.get('json') or {};u=usage_cost(j.get('usage') if isinstance(j,dict) else None)
        append(path/'attempts.jsonl',dict(trial,event='finished',at=now(),http_status=result['status'],error_type=result['error_type'],wall_seconds=result['wall_seconds'],usage=u))
        print(json.dumps({'trial':number,'of':18,'http_status':result['status'],'wall_seconds':round(result['wall_seconds'],2),'usage':u}),flush=True)
        if result['error_type']=='DeadlineExceeded' or time.monotonic() >= deadline:reason='deadline_exceeded'
        elif result['status'] in [400,401,403,404,429] or result['status'] is None:reason='provider_or_transport_failure'
        if u['input_tokens'] is not None and u['input_tokens']>8192:reason='input_cap_exceeded'
        if u['output_tokens'] is not None and u['output_tokens']>4096:reason='output_cap_exceeded'
        # Preserve conservative reservations; do not spend assumed cached discounts.
    write(path/'execution.json',{'completed_at':now(),'attempts':attempts,'reserved_uncached_usd':reserved,'wall_seconds':time.monotonic()-start,'stop_reason':reason})
    return summarize(path)


def summarize(path, report_name='result.json'):
    verify_freeze(path, check_live_code=False)
    rates=read(path/'freeze.json')['rates_per_million']
    m=read(path/'design-manifest.json');results=[]
    book=read(path/'sources/codebook.json')
    for trial in m['schedule']:
        p=path/'responses'/f"{trial['trial']:02d}.json"
        if not p.exists():results.append(dict(trial,passed=False,errors=['not_dispatched_or_interrupted'],usage=usage_cost(None)));continue
        response=read(p);j=response.get('json') if isinstance(response,dict) else None
        errors=[];grading=None
        if not isinstance(response,dict) or response.get('status')!=200 or not isinstance(j,dict):errors.append('provider_response_failure')
        else:
            if j.get('model')!=MODEL:errors.append('returned_model_mismatch')
            try:
                choice=j['choices'][0]
                if not isinstance(choice,dict):raise TypeError('choice must be an object')
                if choice.get('finish_reason')!='stop':errors.append('non_stop_finish')
                message=choice.get('message')
                if not isinstance(message,dict):raise TypeError('message must be an object')
                answer=parse_json(message.get('content'))
                source=read(path/'sources'/(m['source_fixtures'][trial['packet_id']]+'.json'))
                grading=score(answer,trial['packet_id'],source,book)
                errors.extend(grading['errors'])
            except (AttributeError,ValueError,TypeError,KeyError,IndexError):errors.append('invalid_response_json_or_schema')
        u=usage_cost(j.get('usage') if isinstance(j,dict) else None,rates)
        results.append(dict(trial,passed=not errors,errors=errors,grading=grading,usage=u,wall_seconds=response.get('wall_seconds') if isinstance(response,dict) else None,returned_model=j.get('model') if isinstance(j,dict) else None))
    allpass=all(x['passed'] for x in results)
    pre=read(path/'preflight.json');static=pre['token_counts'].get('static_prefix')
    cache_reasons=[]
    if not allpass:cache_reasons.append('P01 fidelity gate did not pass')
    if static is None or static<1000:cache_reasons.append('natural static prefix below approximate 1000-token threshold or unmeasured')
    if not any(x['usage']['cached_input_tokens'] is not None for x in results):cache_reasons.append('provider cache counters absent')
    byformat={}
    for form in ['normalized','symbolic']:
        group=[x for x in results if x['format']==form]
        totals={}
        for field in ['input_tokens','output_tokens','cached_input_tokens','estimated_cost_usd','uncached_estimate_usd']:
            values=[x['usage'][field] for x in group]
            totals[field]=sum(values) if all(v is not None for v in values) else None
        byformat[form]={'passed':sum(x['passed'] for x in group),'trials':len(group),**totals}
    verdict='supported_on_fixture' if allpass else ('falsified' if any(x.get('grading') and not x['grading']['passed'] or 'invalid_response_json_or_schema' in x['errors'] or 'non_stop_finish' in x['errors'] for x in results) else 'inconclusive')
    output={'study':'P01','verdict':verdict,'passed':sum(x['passed'] for x in results),'planned_trials':18,'by_format':byformat,'cache_smoke':{'eligible':not cache_reasons,'skip_reasons':cache_reasons,'calls_executed':0},'static_prefix_tokens':static,'trials':results,'qualification':'Authored synthetic fixtures; agent review, no independent human annotation; no general semantic or diagnostic capability claim.'}
    output['scoring_code_sha256']=digest((Path(__file__).parent/'score_p01.py').read_bytes())
    output['runner_code_sha256']=digest(Path(__file__).read_bytes())
    output['usage_adapter']='nested_or_top_level_cached_tokens.v2'
    target=path/report_name
    if target.exists() and read(target)!=output:raise FileExistsError('refusing to overwrite different derived report')
    if not target.exists():write(target,output)
    print(json.dumps({k:v for k,v in output.items() if k!='trials'}),flush=True)
    return output


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run','score']);parser.add_argument('--run-id',required=True);parser.add_argument('--report-name',default='result-audited.json');args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.run_id):raise ValueError('invalid run id')
    if args.mode=='prepare':prepare(args.run_id)
    elif args.mode=='run':run(RUNS/args.run_id)
    else:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+',args.report_name):raise ValueError('invalid report name')
        summarize(RUNS/args.run_id, args.report_name)

if __name__=='__main__':main()
