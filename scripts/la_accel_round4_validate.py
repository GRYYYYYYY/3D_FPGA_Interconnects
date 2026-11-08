"""Cross-check final R4 source, timing, exact outputs, counts and evidence hashes."""
import argparse,json,re,struct
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--archive',type=Path);a=p.parse_args();r=a.experiment.resolve();checks=[]
 def check(ok,name):
  if not ok:raise AssertionError(name)
  checks.append(name)
 plan=json.loads((r/'plan.json').read_text())
 for name,digest in plan['protected_untracked'].items():check(sha256(ROOT/name)==digest,'protected '+name)
 d=json.loads((r/'report_final.json').read_text());check(len(d['hardware'])==4,'four fixed hardware controls');check(len(d['software'])==38,'thirty small + eight large software configurations')
 for h in d['hardware']:
  folder=r/('hls_'+h['name']);binding=json.loads((folder/'binding.json').read_text())
  for name,digest in binding['sources'].items():check(sha256(folder/'source_snapshot'/name)==digest,h['name']+' frozen '+name)
  for w in binding['workloads']:check(sha256(Path(w['path']))==w['sha256'],h['name']+' workload '+w['path'])
  check(all(h['phases'][p]=='passed' for p in ['csim','csynth','cosim','impl']),h['name']+' completed tool phases')
  check(h['monitor']['status']=='passed' and h['monitor']['warm_graph_axi_zero'],h['name']+' warm graph AXI absent')
  check(all(h['monitor']['all_output_ports_match'].values()),h['name']+' all output/status traces match')
  check(h['monitor']['cycles']==h['cycles'] and len(h['cycles'])==12,h['name']+' observer does not change cycles')
  t=h['timing_recheck'];check(t['verified_mhz']==125 and min(t['slack_ns'].values())>=0,h['name']+' fixed 125MHz internal STA')
  check(t['constraint_checks']['no_clock']==0 and t['constraint_checks']['unconstrained_internal_endpoints']==0,h['name']+' internal constraint coverage')
  check(sha256(Path(t['original_200mhz_routed_dcp']))==t['original_dcp_sha256'],h['name']+' routed provenance')
  check(sha256(r/('timing125_'+h['name'])/'design_125mhz.dcp')==t['rechecked_dcp_sha256'],h['name']+' rechecked DCP provenance')
  for c,w in zip(h['calls'],binding['workloads']):
   dimensions=w['dimensions'];check(c['warm_output_bytes']==dimensions['j']*(dimensions['c']*8+48),h['name']+' complete map/stats writeout '+c['case'])
   check(abs(c['warm_e1_s']*125e6-c['warm_e1_cycles'])<1e-6,h['name']+' verified clock conversion '+c['case'])
   check(c['first_call_from_device_memory_cycles']>c['warm_e1_cycles'],h['name']+' actual runtime load '+c['case'])
 for w in r.glob('gpu_worker_*'):
  worker=json.loads((w/'worker.json').read_text());rows=json.loads((w/'measurements.json').read_text());done=json.loads((w/'finished.json').read_text());check(done['status']=='passed',w.name+' measured cohort')
  check(len(rows)==done['processes'],w.name+' process count')
  for name in ['cpu4.cpp','cuda4.cu','cuda_kernel4.cuh','reference4.hpp']:
   check(sha256(w/'source/round4'/name)==sha256(ROOT/'accel/lookahead/round4'/name),w.name+' benchmark source '+name)
  for row in rows:
   check(all(m['all_golden_bits_match'] for m in row['measurements']),w.name+' golden '+row['log'])
   check(row['measurements'][0]['phase']=='cold_first_call' and all(m['phase']=='warm' for m in row['measurements'][1:]),w.name+' phase separation '+row['log'])
 trace=json.loads((r/'cross_layer_trace_verified/result.json').read_text())
 for w in trace['workloads']:
  for early in [0,1]:check(sum(v['cross_pushed'] for v in w['observations'] if v['early']==early)>0,'cross-layer traversal '+w['workload']+' '+str(early))
 check('100% tests passed' in (r/'ctest.log').read_text(),'old and new CTest regression')
 for mode in ['full','early']:check('TRANSACTION 2035' in (r/(mode+'_host_semantics.log')).read_text(),mode+' hardware 509 corner/random graphs')
 if a.archive:
  index=json.loads((a.archive/'index.json').read_text())
  for name,entry in index['files'].items():check(sha256(a.archive/name)==entry['sha256'],'archived '+name)
 target=r/('archive_validation.json' if a.archive else 'final_validation.json');check(not target.exists(),'fresh validation receipt')
 result=dict(status='passed',checks=len(checks),names=checks,report_sha256=sha256(r/'report_final.json'))
 target.write_text(json.dumps(result,indent=2)+'\n');print(result['checks'],'checks passed')
if __name__=='__main__':main()
