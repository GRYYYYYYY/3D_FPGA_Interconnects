#!/usr/bin/env python3
"""Verify terminal complete-core artifacts and consolidate measured batch facts."""
from pathlib import Path
import argparse,collections,csv,hashlib,json
from analyze_full import analyze

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('fixtures',type=Path);a=p.parse_args();terminal=json.loads((a.run/'terminal.json').read_text());assert terminal['status']=='PASS';positive=[];negative=[];history=[]
 for r in terminal['results']:
  assert r['pass'];rd=a.run/(r['case']+'_'+r['negative']+('_stress'if r['stress'] else''));log=(rd/'run.log').read_text();assert'Fatal:'not in log and'ERROR:'not in log
  if r['negative']!='none':
   assert'TEST_PASS complete_core_config_rejected '+r['negative']+' no_physical_requests'in log;negative.append(r['negative']);continue
  cfg=json.loads((a.fixtures/r['case']/'config.json').read_text());cal=analyze(rd);assert cal['status']=='PASS',cal['errors'];(rd/'calibration.json').write_text(json.dumps(cal,indent=2)+'\n');samples=list(cal['samples'].values());assert len(samples)==len(cfg['samples']);assert set(cal['samples'])=={str(i)for i in range(len(cfg['samples']))};assert(rd/'output.bin').read_bytes()==(a.fixtures/r['case']/'validation/output.bin').read_bytes()
  phases=collections.Counter();totals=collections.Counter()
  oldpath=a.fixtures/r['case']/'coverage_sources.json';old=json.loads(oldpath.read_text())['samples']
  for d in samples:
   phases.update(d['phase_cycles']);totals.update({k:d[k]for k in ['cycles','waves','parents','candidates','commits','op_retired','events','stale','physical_requests','physical_responses','recorded']})
   h=old[d['sample']];matched={k:d[k]==h[k]for k in ['waves','parents','candidates','events']};history.append({'case':r['case'],'stress':r['stress'],'sample':d['sample'],'counts_equal':matched,'old_finite_source_sha256':h['source_sha256']})
  assert all(all(x['counts_equal'].values())for x in history),'Native algorithm event counts differ from historic finite model; investigate before asserting match'
  positive.append({'case':r['case'],'stress':r['stress'],'jobs':len(samples),'pairs':r['all_pairs'],'actual_output_sha256':sha(rd/'output.bin'),'totals':dict(totals),'phase_cycles':dict(phases),'initialization_fraction':phases['3']/totals['cycles'],'calibration_sha256':sha(rd/'calibration.json'),'history_manifest_sha256':sha(oldpath)})
 expected=terminal.get('selected_tests',[['native_d3_w8','none',0],['native_d4_w8','none',0],['native_d4_w8','none',1]]+[['native_d3_w8',n,0]for n in ['nodes','cells','costs','jobs','high_address','unaligned','stride','descriptor_end','source','targets','missing_job']])
 assert sorted((r['case'],r['negative'],r['stress'])for r in terminal['results'])==sorted(tuple(t)for t in expected), 'Selected test plan does not match terminal results'
 assert len(positive)==sum(t[1]=='none'for t in expected)and sorted(negative)==sorted(t[1]for t in expected if t[1]!='none')
 out={'status':'PASS','scope':'complete connected production64-bank/64-lane behavioral RTL with native runtime input; no achieved timing claim','binding_sha256':sha(a.run/'binding.json'),'service':terminal.get('service',{'clock_period_ns':'5','memory_latency_requested_ns':'80','memory_issue_requested_ns':'5','scenario':'baseline'}),'config_rejections_reused':terminal.get('config_rejections_reused',False),'positives':positive,'configuration_rejections':negative,'historical_algorithm_counts':history,'limitations':['No hardware execution or post-route timing simulation','Small native graphs do not exhaust8192-member directory or2048 scratch spill slots; separate local capacity evidence is required','Malformed cost-nibble rejection is host admission only','The configured clock period is simulation stimulus and not a timing-closure result']};(a.run/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'positive_batches':len(positive),'config_rejections':len(negative),'cycles':[(r['case'],r['stress'],r['totals']['cycles'])for r in positive]},indent=2))
if __name__=='__main__':main()
