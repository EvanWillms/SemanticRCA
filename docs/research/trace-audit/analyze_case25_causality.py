"""Reproduce the gold-guided case-25 latency attribution; duration units are provisional.

Two full-file scans: select checkout requests, then recover their complete recorded
traces. This is a development diagnostic, not a blind diagnosis or causal estimator.
"""
import argparse,csv,json,collections,pathlib
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('source',type=pathlib.Path)
parser.add_argument('output',type=pathlib.Path)
args=parser.parse_args()
src=args.source
out=args.output
out.mkdir(parents=True,exist_ok=True)
onset=1647788966000
selected={}
with src.open(newline='') as f:
 for i,r in enumerate(csv.DictReader(f),2):
  if r['cmdb_id']=='checkoutservice-2' and r['operation_name']=='hipstershop.CheckoutService/PlaceOrder' and onset-300000<=int(r['timestamp'])<onset+300000:
   selected[r['trace_id']]=dict(r,source_record=i)
print('selected',len(selected),flush=True)
traces=collections.defaultdict(list)
with src.open(newline='') as f:
 for i,r in enumerate(csv.DictReader(f),2):
  if r['trace_id'] in selected: traces[r['trace_id']].append(dict(r,source_record=i))
print('extracted',sum(map(len,traces.values())),flush=True)
result=[]
for tid,rows in traces.items():
 byid={r['span_id']:r for r in rows}; children=collections.defaultdict(list)
 assert len(byid)==len(rows), 'Duplicate span IDs within selected trace'
 assert sum(not r['parent_span'] for r in rows)==1, 'Expected one recorded root'
 for r in rows:
  seen=set(); current=r
  while current['parent_span']:
   assert current['span_id'] not in seen, 'Parent cycle'
   seen.add(current['span_id'])
   assert current['parent_span'] in byid, 'Orphan parent'
   current=byid[current['parent_span']]
 for r in rows: children[r['parent_span']].append(r)
 checkout=selected[tid]; caller=byid[checkout['parent_span']]; root=caller
 while root['parent_span']: root=byid[root['parent_span']]
 start=lambda r:int(r['timestamp'])*1000
 dur=lambda r:int(r['duration'])
 end=lambda r:start(r)+dur(r)
 calls=sorted(children[checkout['span_id']],key=start)
 details=[]; intervals=[]
 for c in calls:
  receivers=[r for r in children[c['span_id']] if r['cmdb_id']!=c['cmdb_id']]
  details.append(dict(operation=c['operation_name'],span_id=c['span_id'],source_record=c['source_record'],offset_ms=(start(c)-start(root))/1000,duration_ms=dur(c)/1000,receivers=[dict(component=r['cmdb_id'],span_id=r['span_id'],source_record=r['source_record'],duration_ms=dur(r)/1000,start_gap_ms=(start(r)-start(c))/1000,client_minus_receiver_ms=(dur(c)-dur(r))/1000) for r in receivers]))
  intervals.append((max(start(c),start(checkout)),min(end(c),end(checkout))))
 union=0; cursor=start(checkout); gaps=[]
 for a,b in sorted(intervals):
  if b<=a:continue
  if a>cursor:gaps.append(dict(offset_ms=(cursor-start(root))/1000,duration_ms=(a-cursor)/1000))
  union+=max(0,b-max(a,cursor));cursor=max(cursor,b)
 if cursor<end(checkout):gaps.append(dict(offset_ms=(cursor-start(root))/1000,duration_ms=(end(checkout)-cursor)/1000))
 result.append(dict(trace_id=tid,period='before' if int(checkout['timestamp'])<onset else 'after',timestamp=int(checkout['timestamp']),span_count=len(rows),duplicate_ids=len(rows)-len(byid),orphan_count=sum(bool(r['parent_span']) and r['parent_span'] not in byid for r in rows),root=dict(root),caller=dict(caller),checkout=dict(checkout),root_ms=dur(root)/1000,caller_ms=dur(caller)/1000,checkout_ms=dur(checkout)/1000,root_minus_caller_ms=(dur(root)-dur(caller))/1000,checkout_children_union_ms=union/1000,checkout_uncovered_ms=(dur(checkout)-union)/1000,uncovered_gaps=gaps,calls=details))
result.sort(key=lambda r:r['timestamp'])
(out/'extracted_traces.json').write_text(json.dumps(dict(traces),indent=2)+'\n')
(out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for r in result:
 print(r['trace_id'],r['period'],'root',r['root_ms'],'caller',r['caller_ms'],'checkout',r['checkout_ms'],'other frontend',r['root_minus_caller_ms'],'uncovered',r['checkout_uncovered_ms'])
 for c in r['calls']:
  print(' ',c['operation'].split('.')[-1],c['duration_ms'],'recv',[(s['component'],s['duration_ms'],s['start_gap_ms']) for s in c['receivers']])
 print(' gaps',r['uncovered_gaps'])
