import sys,struct,json,math,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import probe_io as m
def key(x):return struct.unpack('<I',struct.pack('<f',x))[0]

def run(w,shift):
 stats=[];diff=[0,0]
 for q in range(w.j):
  targets=w.targets(q);output=[None]*w.c
  d=[math.inf]*w.n;c=[math.inf]*w.n;s=w.jobs[q][0];d[s]=0.;c[s]=0.
  buckets={0:{s}} if targets else {};widths=[];raw=eligible=updates=closures=0;settled=set();current=None;bucket_peak=len(buckets);queue_peak=sum(len(v) for v in buckets.values())
  while buckets:
   b=min(buckets);assert current is None or b>=current
   if b!=current:assert not settled;current=b
   active=sorted(u for u in buckets.pop(b) if key(d[u])>>shift==b)
   if active:
    widths.append(len(active));settled.update(active)
   proposal={}
   for u in active:
    for k in range(w.row[u],w.row[u+1]):
     raw+=1;v=w.edges[k][0];a=m.eligibility(w.nodes[u],w.nodes[v])
     if a==0:continue
     if a<0:break
     eligible+=1;dc,cc=w.costs[w.nodes[v][1]];cand=(m.f32(d[u]+dc),m.f32(c[u]+cc))
     old=proposal.get(v,(d[v],c[v]))
     if cand<old:proposal[v]=cand
   for v,pair in proposal.items():
    d[v],c[v]=pair;dest=key(d[v])>>shift;assert dest>=b
    buckets.setdefault(dest,set()).add(v)
   updates+=len(proposal)
   bucket_peak=max(bucket_peak,len(buckets));queue_peak=max(queue_peak,sum(len(v) for v in buckets.values()))
   if b not in buckets:
    closures+=1
    for u in settled:
     cell=w.cells[q*w.n+u]
     if cell>=0 and w.nodes[u][0]==1:
      pair=(d[u],c[u])
      if output[cell] is None or pair<output[cell]:output[cell]=pair
    settled.clear()
    if sum(x is not None for x in output)==len(targets):break
   assert len(widths)<w.n*4
  enc=b''.join(m.MISSING if x is None else struct.pack('<ff',*x) for x in output)
  for cell in range(w.c):
   for f in (0,1):diff[f]+=enc[cell*8+f*4:cell*8+f*4+4]!=w.golden[q][cell*8+f*4:cell*8+f*4+4]
  stats.append(dict(waves=len(widths),closed_buckets=closures,raw_edges=raw,eligible_edges=eligible,updates=updates,widths=widths,active_bucket_peak=bucket_peak,pending_bucket_entries_peak=queue_peak))
 return dict(delay_word_differences=diff[0],congestion_word_differences=diff[1],jobs=stats,raw_edges=sum(x['raw_edges'] for x in stats),eligible_edges=sum(x['eligible_edges'] for x in stats),updates=sum(x['updates'] for x in stats),waves_max=max(x['waves'] for x in stats),closed_buckets_total=sum(x['closed_buckets'] for x in stats),max_frontier=max([a for x in stats for a in x['widths']] or [0]),active_bucket_peak=max(x['active_bucket_peak'] for x in stats),pending_bucket_entries_peak=max(x['pending_bucket_entries_peak'] for x in stats))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description='Small-input functional/work-count probe, not a runtime or QoR benchmark.')
 parser.add_argument('--root',type=Path,required=True)
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();ROOT=args.root.resolve();args.output.parent.mkdir(parents=True,exist_ok=True)
 cases=[('native_d3_w8','round3_20261108T141500Z'),('native_d4_w8','round3_20261108T141500Z'),('native_d5_w8','round4_20261108T182500Z'),('native_d6_w8','round5_20261109T054024Z'),('native_d8_w8','round5_20261109T054024Z'),('native_d6_w8_l1','round5_20261109T054024Z')]
 out=[]
 for case,rd in cases:
  w=m.Workload(ROOT/f'results/lookahead_accel_{rd}/evidence_snapshot/{case}/workload.bin')
  assert all(w.run(q,True)['matches_golden_all_bytes'] for q in range(w.j))
  variants=[]
  for shift in [0,20]:
   z=run(w,shift);z['bucket_key_shift']=shift;variants.append(z)
   print(case,shift,{k:v for k,v in z.items() if k!='jobs'})
  out.append(dict(case=case,N=w.n,E=w.e,J=w.j,C=w.c,sha256=w.sha256,variants=variants))
 fixtures=sorted((ROOT/'results/lookahead_accel_round4_20261108T182500Z/evidence_snapshot/semantic_fixtures').glob('*.bin'))
 cohorts=[]
 for shift in [0,20]:
  fail=[]
  for path in fixtures:
   w=m.Workload(path);z=run(w,shift)
   if z['delay_word_differences'] or z['congestion_word_differences']:fail.append(dict(case=path.stem,delay=z['delay_word_differences'],congestion=z['congestion_word_differences']))
  cohorts.append(dict(bucket_key_shift=shift,fixture_count=len(fixtures),failures=fail))
  print('shift',shift,'fixtures',len(fixtures),'delay_mismatches',sum(x['delay']>0 for x in fail),'congestion_mismatches',sum(x['congestion']>0 for x in fail),'cases',[x['case'] for x in fail])
 args.output.write_text(json.dumps(dict(method='monotone FP32 bit-key buckets; synchronous lexicographic pair min within bucket closure; early target stop only after bucket closure; new semantics',scope='read-only functional/work counting; no timing, HLS, QoR or large graphs; 2 fixed shifts not performance tuned; no globally lexicographic shortest-path optimality claim',source_commit='ab0a4afce89c567cf30f24c8a813d78884872f05',native=out,fixture_cohorts=cohorts),indent=2)+'\n')
