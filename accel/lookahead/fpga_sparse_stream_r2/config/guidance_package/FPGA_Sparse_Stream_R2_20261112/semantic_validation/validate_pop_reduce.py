#!/usr/bin/env python3
"""Finite algorithm-model differential check; NOT native, RTL, or performance evidence.
Uses destination-node FP32 costs, frozen waves, exact pair order, versioned stale
filtering, and completion only after bucket closure. No VPR eligibility modeling.
"""
import argparse, collections, csv, hashlib, json, random, struct, time
from pathlib import Path

def f32(x): return struct.unpack('<f',struct.pack('<f',x))[0]
def bits(x): return struct.unpack('<I',struct.pack('<f',x))[0]
def pair(x): return tuple(f32(v) for v in x)
def encoded(x): return [0x7fc00000,0x7fc00000] if x is None else [bits(v) for v in x]

def solve(g,shift,mode='closed'):
    n=len(g['cost']); costs=list(map(pair,g['cost'])); src=g.get('source',0)
    labels=[(float('inf'),float('inf'))]*n; prop=labels.copy()
    pending=[None]*n; version=[0]*n; directory={}; output=[None]*g['cells']
    nt=len(set(c for c in g['cell'] if c>=0)); recorded=0; first_seen=set()
    trace=[]; closures=[]; closed=set(); stale=0; events=0
    def observe(u):
        nonlocal recorded,events
        c=g['cell'][u]
        if c<0:return
        if mode=='first_only' and u in first_seen:return
        if mode=='edge_only' and not g['edges'][u]:return
        first_seen.add(u);events+=1; v=labels[u]
        if output[c] is None: output[c]=v;recorded+=1
        elif mode=='component_min': output[c]=tuple(min(x,y) for x,y in zip(v,output[c]))
        else: output[c]=min(v,output[c])
    if not nt:return {'out':list(map(encoded,output)),'trace':trace,'closures':closures,'stale':stale,'events':events}
    labels[src]=prop[src]=(0.0,0.0);pending[src]=0;version[src]=1;directory[0]=[(src,1)]
    while directory:
        if len(trace)>=10000: raise RuntimeError('bounded model wave limit')
        b=min(directory); members=directory.pop(b);active=[]
        for u,v in members:
            if pending[u]!=b or version[u]!=v:stale+=1;continue
            pending[u]=None;active.append(u)
            if mode=='closed':closed.add(u)
            else:observe(u)
        changed=set(); edge_count=0
        for u in active:
            parent=labels[u]
            for v in g['edges'][u]:
                cand=tuple(f32(parent[k]+costs[v][k]) for k in (0,1));edge_count+=1
                if cand<prop[v]:prop[v]=cand;changed.add(v)
        for v in sorted(changed):
            assert prop[v]<labels[v]
            labels[v]=prop[v];key=bits(labels[v][0])>>shift
            assert key>=b,('nonmonotone',key,b)
            if pending[v]!=key:
                version[v]+=1;directory.setdefault(key,[]).append((v,version[v]));pending[v]=key
        trace.append([b,active,edge_count,[[v,encoded(labels[v])] for v in sorted(changed)]])
        if not directory or min(directory)!=b:
            if mode=='closed':
                for u in sorted(closed):observe(u)
                closed.clear()
            closures.append([b,recorded,list(map(encoded,output))])
            if recorded==nt:break
    return {'out':list(map(encoded,output)),'trace':trace,'closures':closures,'stale':stale,'events':events}

def fixture(name,cost,edges,cell,cells=None,source=0):
    return {'name':name,'cost':cost,'edges':edges,'cell':cell,'cells':cells if cells is not None else max(cell,default=-1)+1,'source':source}

def directed():
    return [
      fixture('same_bucket_repeat_delay',[(0,0),(8.5,100),(8,0),(.25,0),(.25,0)],[[1,2],[4],[3],[4],[]],[-1,-1,-1,-1,0]),
      fixture('same_bucket_congestion_only',[(0,0),(8,100),(8,0),(0,0),(0,0)],[[1,2],[4],[3],[4],[]],[-1,-1,-1,-1,0]),
      fixture('whole_pair_same_cell',[(0,0),(8,100),(8.5,0)],[[1,2],[],[]],[-1,0,0]),
      fixture('zero_outdegree_target',[(0,0),(1,2)],[[1],[]],[-1,0]),
      fixture('source_is_target',[(0,0),(1,0)],[[1],[]],[0,-1]),
      fixture('no_targets',[(0,0),(1,0)],[[1],[]],[-1,-1],2),
      fixture('unreachable_target_missing',[(0,0),(1,0),(2,0)],[[1],[],[]],[-1,0,1]),
      fixture('duplicates_zero_cycle',[(0,0),(0,0),(0,0),(1,0)],[[1,1,2],[2,3],[1,3],[]],[-1,0,0,1]),
      fixture('stale_bucket_migration',[(0,0),(8.5,0),(8,0),(.25,0),(.5,0),(0,0)],[[1,2],[4],[3],[4],[],[]],[-1,-1,-1,-1,0,1]),
      fixture('equal_delay_congestion_pairs',[(0,0),(1,3),(1,2),(0,0)],[[1,2],[3],[3],[]],[-1,-1,-1,0]),
    ]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--outdir',default=str(Path(__file__).resolve().parent));args=ap.parse_args();out=Path(args.outdir);out.mkdir(parents=True,exist_ok=True)
    t=time.perf_counter();rng=random.Random(20261112);cases=directed()
    pool=[0,.1,.2,.3,.125,.25,.5,1,2,4,8,8.25,8.5,2**-23,2**20]
    for k in range(80):
        n=rng.randrange(2,25);nc=rng.randrange(1,8)
        costs=[(rng.choice(pool),rng.choice(pool)) for _ in range(n)]
        edges=[[v for v in range(n) if rng.random()<.12] for _ in range(n)]
        if k%5==0:edges[rng.randrange(n)]+=edges[rng.randrange(n)][:2]
        cell=[rng.randrange(nc) if rng.random()<.45 else -1 for _ in range(n)]
        cases.append(fixture('random_%03d'%k,costs,edges,cell,nc,rng.randrange(n)))
    failures=[];checks=[]
    for g in cases:
        for shift in [0,20]:
            try:
                a=solve(g,shift,'closed');b=solve(g,shift,'pop')
                keys=['out','trace','closures','stale'];bad=[key for key in keys if a[key]!=b[key]]
                if bad:failures.append({'case':g,'shift':shift,'differences':bad,'reference':a,'pop':b})
                checks.append({'case':g['name'],'shift':shift,'pass':not bad,'waves':len(a['trace']),'stale':a['stale'],'closed_events':a['events'],'pop_events':b['events']})
            except Exception as exc:failures.append({'case':g,'shift':shift,'exception':repr(exc)})
    mutation_checks=[]
    for name,mode in [('same_bucket_repeat_delay','first_only'),('same_bucket_congestion_only','first_only'),('zero_outdegree_target','edge_only'),('whole_pair_same_cell','component_min')]:
        g=next(g for g in cases if g['name']==name);a=solve(g,20);b=solve(g,20,mode)
        mutation_checks.append({'case':name,'mutation':mode,'detected':a['out']!=b['out'],'reference':a['out'],'mutant':b['out']})
    summary={'scope':'Independent algorithm-model differential validation only; not native, RTL, OOC, physical timing, or FPGA performance evidence','source_commit':'5651a34abb97939bee6402c5af585753ab07f64b','seed':20261112,'directed_graphs':10,'random_graphs':80,'shifts':[0,20],'differential_cases':len(checks),'failures':len(failures),'all_differential_passed':len(checks)==180 and not failures,'mutation_checks':mutation_checks,'all_mutations_detected':all(x['detected'] for x in mutation_checks),'seconds':time.perf_counter()-t,'limitations':['No VPR eligibility, full native graph, hardware finite queues, memory response reordering, numeric rejection, or capacity overflow execution modeled','Shared search/control implementation isolates output transform; independent floating point library/reference not used','Node-cost rounding uses Python float plus explicit float32 round-trip; all generated values finite nonnegative normal or +0'],'failure_archive':'failures.json (retained even when empty)','checks':checks}
    (out/'cases.json').write_text(json.dumps(cases,indent=2)+'\n');(out/'failures.json').write_text(json.dumps(failures,indent=2)+'\n');(out/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='checks'},indent=2))
    return 0 if summary['all_differential_passed'] and summary['all_mutations_detected'] else 1
if __name__=='__main__':raise SystemExit(main())
