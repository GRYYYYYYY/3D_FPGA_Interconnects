#!/usr/bin/env python3
"""Regenerate V2 tables from frozen completed rows; no solver or external data access."""
from pathlib import Path
import json,hashlib,statistics as st,math
P=Path(__file__).resolve().parent;E=P/'evidence/matched_native';T=P/'tables'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for b in read(E/'bindings.json'):assert sha(P/b['snapshot'])==b['sha256'],b['snapshot']
result=read(E/'results.json');rows=read(E/'rows.json');old=read(P/'evidence/holdout_results.json')
assert result['qualified_new_cases'],'V2 needs independently qualified new evidence'
new=[x for x in rows if x['formal'] and x['case'] in result['qualified_new_cases']]
assert len(new)==9*len(result['qualified_new_cases'])
assert len({(x['case'],x['repeat'],x['arm']) for x in new})==len(new)
for x in new:
 assert x['qualified'] and x['qualification_map_equal'] and x['paired_qor_passed'] and x['readback_identity']
 assert x['zero_overuse'] and x['metrics']['full_check'] and x['independent']['metrics']['full_check']
 assert x['affinity']==result['environment']['affinity'] and x['gpu_uuid']==result['environment']['gpu_uuid']
 assert 'R61_CAPTURE' not in x['environment'] and 'R61_VERIFY_CPU' not in x['environment']
prior=[x|dict(arm=x['backend']) for x in old['formal_rows'] if x['case']=='lstm_s2' and x['backend'] in ['stock','pipeline','alt_cuda']]
allrows=new+prior;arms=['stock','pipeline','alt_cuda'];keys=arms+['stock_to_pipeline','pipeline_to_alt_cuda','stock_to_alt_cuda'];pairs=[('stock','pipeline'),('pipeline','alt_cuda'),('stock','alt_cuda')]
for x in result['summary']:
 rs=[r for r in allrows if r['case']==x['case']];by={(r['arm'],r['repeat']):r for r in rs};assert len(rs)==len(by)==9
 for rep in range(3):
  group=[by[a,rep] for a in arms]
  assert len({tuple(sorted((k,v['sha256']) for k,v in r['input_bindings'].items())) for r in group})==1
  for r in group:
   assert r['qualified'] and all(r['metrics'][k]<=1.05*c['metrics'][k] for c in group[:2] for k in ['critical_path_ns','wirelength'])
  s,p,c=[r[x['scope']] for r in group];assert all(math.isfinite(v) and v>0 for v in [s,p,c]);assert math.isclose(s/p*p/c,s/c,rel_tol=1e-12)
 vals={a:[by[a,rep][x['scope']] for rep in range(3)] for a in arms}
 for a,b in pairs:vals[a+'_to_'+b]=[by[a,rep][x['scope']]/by[b,rep][x['scope']] for rep in range(3)]
 for key,v in vals.items():
  assert x[key]['samples']==v
  assert math.isclose(x[key]['mean'],st.mean(v),rel_tol=1e-13)
  assert math.isclose(x[key]['sample_SD'],st.stdev(v),rel_tol=1e-13)
for scope,name in [('Process_wall_s','matched_process'),('E2_s','matched_e2')]:
 lines=[]
 for x in result['summary']:
  if x['scope']!=scope:continue
  cells=[]
  for k in keys:
   v=x[k];digits=2 if k in arms else 3;cells.append(f"${v['mean']:.{digits}f}\\pm{v['sample_SD']:.{digits}f}$")
  lines.append(x['case'].replace('_s2','').upper()+(' (prior)' if not x['new_measurement'] else '')+' & '+' & '.join(cells)+r' \\')
 for x in result['excluded']:lines.append(x['case'].upper()+r' & \multicolumn{6}{l}{NOT MEASURED: qualified paired cohort unavailable} \\')
 (T/(name+'.tex')).write_text('\n'.join(lines)+'\n')
macros=[]
for c in result['qualified_new_cases']:
 for scope,tail in [('Process_wall_s','Proc'),('E2_s','Build')]:
  r=next(x for x in result['summary'] if x['case']==c and x['scope']==scope)
  for base,name in [('pipeline','Pipe'),('stock','Stock')]:
   s=r[base+'_to_alt_cuda'];macros.append('\\newcommand{\\'+c.title()+'New'+name+tail+'}{$'+f"{s['mean']:.3f}\\pm{s['sample_SD']:.3f}"+r'\times$}')
(T/'matched_macros.tex').write_text('\n'.join(macros)+'\n')
lines=[]
for q in result['qualification']:
 vals=[q['case'].replace('_s2','').upper()+(' (prior)' if not q['new_measurement'] else ''),f"{q['N']/1e6:.2f}",f"{q['E']/1e6:.2f}"]
 for key in ['CPD_ns','WL']:
  a=q['alt_cuda_'+key];b=q['stock_'+key];vals.append(f"{100*(a/b-1):+.2f}" if a and b else 'N/A')
 vals.append(str(q['congestion_word_differences']) if q['congestion_word_differences'] is not None else 'N/A');lines.append(' & '.join(vals)+r' \\')
(T/'qualification_compact.tex').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(matched_new_cases=result['qualified_new_cases'],validated_new_formal_rows=len(new),historical_LSTM_rows=len(prior),estimator='direct paired mean and sample SD; no cross-worker denominators')))
