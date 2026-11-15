#!/usr/bin/env python3
"""Compare two immutable complete-core runs; writes only the new run directory."""
from pathlib import Path
import argparse,hashlib,json,re

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(r):return r['case'],r['negative'],r['stress']
def directory(root,r):return root/(r['case']+'_'+r['negative']+('_stress'if r['stress'] else''))
def main():
 p=argparse.ArgumentParser();p.add_argument('old',type=Path);p.add_argument('new',type=Path);p.add_argument('--allow-partial',action='store_true');a=p.parse_args();oldterm=json.loads((a.old/'terminal.json').read_text());assert oldterm['status']=='PASS'
 name='progress.json'if a.allow_partial else'terminal.json';newdoc=json.loads((a.new/name).read_text());newrows=newdoc if a.allow_partial else newdoc['results'];oldrows={key(r):r for r in oldterm['results']}
 if not a.allow_partial:assert newdoc['status']=='PASS'and set(key(r)for r in newrows)==set(oldrows)
 ob=json.loads((a.old/'binding.json').read_text());nb=json.loads((a.new/'binding.json').read_text());assert ob['fixture_manifest_sha256']==nb['fixture_manifest_sha256'];changed=[]
 for n,v in ob['source'].items():
  if v!=nb['source'].get(n):changed.append({'file':n,'old':v,'new':nb['source'].get(n)})
 result=[];differences=[]
 for r in newrows:
  assert r['pass']and key(r)in oldrows;od=directory(a.old,r);nd=directory(a.new,r)
  if a.allow_partial and r['negative']=='none'and('all_jobs'not in r or not(nd/'calibration.json').exists()):continue
  files=['events.csv','samples.csv','phase_cycles.csv','request_kinds.csv']
  if r['negative']=='none':files+=['output.bin']+[f'sample_{q}_actual_beats.hex'for q in range(r['all_jobs'])]
  else:
   marker='TEST_PASS complete_core_config_rejected '+r['negative']+' no_physical_requests'
   assert marker in(od/'run.log').read_text()and marker in(nd/'run.log').read_text()
  entries=[]
  for n in files:
   x,y=sha(od/n),sha(nd/n);same=x==y;entries.append({'file':n,'old_sha256':x,'new_sha256':y,'identical':same})
   if not same:differences.append({'case':r['case'],'negative':r['negative'],'stress':r['stress'],'file':n})
  # Default5ns regression also checks absolute simulated finish time, independently
  # of the cycle CSVs, so clock-generation changes cannot silently pass as5ns.
  ot=re.search(r'\$finish called at time\s*:\s*(\d+) ps', (od/'run.log').read_text());nt=re.search(r'\$finish called at time\s*:\s*(\d+) ps', (nd/'run.log').read_text());assert ot and nt
  time_equal=ot.group(1)==nt.group(1)
  if not time_equal:differences.append({'case':r['case'],'negative':r['negative'],'stress':r['stress'],'file':'absolute_simulation_finish_time'})
  result.append({'case':r['case'],'negative':r['negative'],'stress':r['stress'],'old_finish_ps':ot.group(1),'new_finish_ps':nt.group(1),'finish_time_equal':time_equal,'files':entries})
 status=('PARTIAL_IDENTICAL'if a.allow_partial else'IDENTICAL')if not differences else'DIFFERENT'
 out={'status':status,'scope':'complete native outputs, exact cycle/phase/kind CSVs and accepted logical/physical/retirement/completion event traces; absolute simulated finish time','old_binding_sha256':sha(a.old/'binding.json'),'new_binding_sha256':sha(a.new/'binding.json'),'source_changes':changed,'cases_compared':len(result),'results':result,'differences':differences}
 (a.new/('comparison_partial.json'if a.allow_partial else'comparison_full_a.json')).write_text(json.dumps(out,indent=2)+'\n');print(status,len(result),'cases',differences);assert not differences
if __name__=='__main__':main()
