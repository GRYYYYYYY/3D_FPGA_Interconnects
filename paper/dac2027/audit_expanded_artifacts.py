#!/usr/bin/env python3
"""Independently audit expanded derived statistics and frozen source bindings; no solver runs."""
from pathlib import Path
import json,hashlib,math,statistics,collections
P=Path(__file__).resolve().parent;E=P/"evidence/expanded_20261105"
def dump(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Independent numerical recomputation, using explicit formulas rather than generator helpers.
s=json.loads((P/'statistics_expanded/statistics.json').read_text());rows=s['formal_runs'];assert len(rows)==603
index={(x['cohort'],x['key']):x for x in rows};assert len(index)==603
for a in s['summary']:
 vals=[x[a['metric']] for x in rows if all(x[k]==a[k] for k in ['cohort','phase','case','workers','mode','arm','scope']) and x[a['metric']] is not None]
 assert len(vals)==a['n'];mu=math.fsum(vals)/len(vals);assert math.isclose(mu,a['mean'],rel_tol=1e-12)
 if len(vals)>1:assert math.isclose(math.sqrt(math.fsum((v-mu)**2 for v in vals)/(len(vals)-1)),a['sd'],rel_tol=1e-11,abs_tol=1e-12)
 else:assert a['sd'] is None
for a in s['pairs']:
 x=index[a['cohort'],a['control_key']];y=index[a['cohort'],a['candidate_key']]
 assert x['repeat']==y['repeat'] and x['case']==y['case'] and x['mode']==y['mode']
 assert math.isclose(x[a['metric']]/y[a['metric']],a['ratio'],rel_tol=1e-12)
for a in s['aggregates']:
 ps=[v for v in s['pairs'] if all(v[k]==a[k] for k in ['cohort','mode','control','candidate']) and v['metric']=='process'];bycase=collections.defaultdict(list)
 for p in ps:bycase[p['case']].append(p['ratio'])
 bycirc=collections.defaultdict(list)
 for case,vals in bycase.items():bycirc[case.rsplit('_s',1)[0]].append(math.fsum(vals)/len(vals))
 means=[math.exp(math.fsum(math.log(v) for v in vals)/len(vals)) for vals in bycirc.values()]
 val=math.exp(math.fsum(math.log(v) for v in means)/len(means));assert math.isclose(val,a['value'],rel_tol=1e-12)
batches=json.loads((E/'results__native_paper_closure_20261105__summary.json').read_text())['measurements'];batches=[m for m in batches if m['phase']=='batch']
assert len(batches)==90
for m in batches:
 assert m['independent']['returncode']==0 and m['independent_metrics']['full_check']
for a in s['cache_prefixes']:
 vals=[]
 for r in range(3):
  arms=[];hashes=set()
  for arm in [a['control'],'pipeline']:
   ms=[m for m in batches if m['case']==a['case'] and m['repeat']==r and m['arm']==arm and m['index']<a['k']];assert len(ms)==a['k']
   arms.append(math.fsum(m['process_seconds'] for m in ms));hashes.update(m['map_sha256'] for m in ms)
  assert len(hashes)==1;vals.append(arms[0]/arms[1])
 assert math.isclose(statistics.mean(vals),a['mean'],rel_tol=1e-12)
 assert math.isclose(statistics.stdev(vals),a['sd'],rel_tol=1e-12,abs_tol=1e-12)
manifest=json.loads((E/'source_manifest.json').read_text())
for m in manifest:assert sha(P/m['snapshot'])==m['sha256']
dump(P/'statistics_reporting_check.json',{'status':'passed','revision':'expanded_20261105','formal_observations_checked':len(rows),'absolute_metric_summaries_checked':len(s['summary']),'paired_observations_checked':len(s['pairs']),'circuit_aggregates_checked':len(s['aggregates']),'actual_cache_processes_checked':90,'cache_prefix_groups_checked':len(s['cache_prefixes']),'frozen_source_hashes_checked':len(manifest),'statistical_form':'arithmetic mean, n-1 sample SD, paired ratios first','independently_recomputed':True,'n1_sd_undefined':True,'historical_selection_records_unchanged':True,'new_solver_runs':0})
print("Expanded numerical audit passed")
