"""Rank frontend latency departures in case 25's prompt window.

Development-only: neither fault component nor fault onset enters the score.
The preceding window is a comparison reference, not verified healthy traffic.
"""
import argparse,csv,collections,json,statistics,pathlib
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=pathlib.Path)
p.add_argument('output',type=pathlib.Path)
args=p.parse_args()
start=1647788400000; stop=start+1800000; baseline_start=start-1800000
out=args.output
out.mkdir(parents=True,exist_ok=True)
rows=[]
with args.source.open(newline='') as f:
 for i,r in enumerate(csv.DictReader(f),2):
  if r['cmdb_id'].startswith('frontend-') and baseline_start-60000<=int(r['timestamp'])<stop+60000:
   rows.append(dict(r,source_record=i))
children=collections.defaultdict(list)
for r in rows: children[(r['trace_id'],r['parent_span'])].append(r)
roots=[]
for r in rows:
 if r['parent_span'] or not baseline_start<=int(r['timestamp'])<stop:continue
 cs=sorted(children[(r['trace_id'],r['span_id'])],key=lambda x:(int(x['timestamp']),x['span_id']))
 # An operation-count signature controls for different recorded request shapes.
 sig=tuple(sorted(collections.Counter(c['operation_name'] for c in cs).items()))
 roots.append(dict(r,signature=sig,children=cs,period='baseline' if int(r['timestamp'])<start else 'query'))
groups=collections.defaultdict(list)
for r in roots:
 if r['period']=='baseline':groups[r['signature']].append(int(r['duration']))
ranked=[];ineligible=[]
for r in roots:
 if r['period']!='query':continue
 b=groups[r['signature']]
 if len(b)<20:ineligible.append(r);continue
 med=statistics.median(b);mad=statistics.median(abs(x-med) for x in b)
 if mad==0 or med==0:ineligible.append(r);continue
 dur=int(r['duration'])
 ranked.append(dict(r,baseline_n=len(b),baseline_median_ms=med/1000,baseline_mad_ms=mad/1000,baseline_max_ms=max(b)/1000,ratio=dur/med,robust_z=(dur-med)/(1.4826*mad),excess_ms=(dur-med)/1000))
ranked.sort(key=lambda r:r['robust_z'],reverse=True)
for i,r in enumerate(ranked,1):r['rank']=i
summary=dict(baseline_roots=sum(r['period']=='baseline' for r in roots),query_roots=sum(r['period']=='query' for r in roots),eligible=len(ranked),ineligible=len(ineligible),signatures=len(set(r['signature'] for r in roots)),ranked=ranked,ineligible_rows=ineligible)
(out/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
print({k:v for k,v in summary.items() if k not in ['ranked','ineligible_rows']})
for r in ranked[:15]:
 print({k:r[k] for k in ['rank','trace_id','timestamp','cmdb_id','duration','baseline_n','baseline_median_ms','baseline_mad_ms','ratio','robust_z','signature']})
 print('children',[(c['operation_name'],round(int(c['duration'])/1000,3)) for c in r['children']])
target=[r for r in ranked if r['trace_id']=='328e653dddef2f29d419a46895d85d12']
print('KNOWN EXAMPLE RANK (looked up after scoring)',[(r['rank'],r['robust_z']) for r in target])
