#!/usr/bin/env python3
"""Read-only independent receipt/output/capacity audit; never launches a model."""
from pathlib import Path
import argparse,hashlib,json,datetime

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(root,terminal):
 root=Path(root);binding=json.loads((root/'binding.json').read_text());term_path=root/terminal;term=json.loads(term_path.read_text())
 for p,h in binding['source_sha256'].items():assert sha(root/'source'/p)==h,p
 assert sha(root/'bin/model')==binding['binary_sha256']
 gold={};seen=set();checks=[]
 for r in term['results']:
  key=(r['configuration'],r['case'],r['sample'],r['jitter']);assert key not in seen,key;seen.add(key)
  inp=binding['inputs'][r['case']]
  if r['case'] not in gold:
   assert sha(inp['golden'])==inp['golden_sha256'];gold[r['case']]=Path(inp['golden']).read_bytes()
  assert r['returncode']==0 and r['binary_sha256']==binding['binary_sha256']
  assert r['workload_sha256']==inp['workload_sha256'] and r['golden_sha256']==inp['golden_sha256']
  data=Path(r['output_path']).read_bytes();size=inp['cells']*8;start=r['sample']*size
  assert data==gold[r['case']][start:start+size] and len(data)==size,key
  assert hashlib.sha256(data).hexdigest()==r['output_sha256']
  f=json.loads(Path(r['finite_path']).read_text());assert f['configuration']==r['configuration'] and f['sample']==r['sample']
  assert sum(f['phase_cycles'].values())==f['cycles'],key
  assert sum(f['fixed_observer_wall_cycles'][0])==f['phase_cycles']['pop_expand']
  assert sum(f['fixed_observer_wall_cycles'][1])==f['phase_cycles']['finalize']
  assert f['output_ACKs']==(inp['cells']+3)//4
  if 'output_ACK_peak_per_cycle' in f:
   assert 0<=f['output_ACK_peak_per_cycle']<=2
   assert f['output_ACK_rejected_source_cycles']>=0
  traffic=f['traffic'];assert len(traffic)==len(f['memory_kind_names'])==12
  assert all(len(row)==32 for row in traffic)
  counts=dict(zip(f['memory_kind_names'],map(sum,traffic)))
  assert counts['descriptor']==(f['parents'] if r['configuration'] in ('F1','F3') else 0)
  assert counts['meta']==(0 if r['configuration'] in ('F1','F3') else f['parents'])
  assert counts['cost_load']==3
  assert counts['output_write']==f['output_ACKs']
  assert sum(map(sum,traffic))==sum(p['issued'] for p in f['port_stats'])
  for p in f['port_stats']:assert p['issued']==p['returned'] and p['credit_peak']<=32 and p['queue_peak']<=4 and p['return_peak']<=4
  for b in f['bank_stats']:
   assert b['tx_peak']<=8 and b['spill_id_peak']<=2048 and b['input_candidate_peak']<=2 and b['input_op_peak']<=2
   assert all(x<=cap for x,cap in zip(b['fifo_peaks'],[16,16,4,2,16,16]))
  assert max(f['directory_bank_peaks'])<=8192
  groups=f['groups'];lanes=f['lanes_per_group'];caps=[128//groups]*4+[lanes*4,lanes*8]
  hist_totals=set()
  for g in f['group_stats']:
   for h,cap in zip(g['occupancy_histograms'],caps):assert sum(h[cap+1:])==0;hist_totals.add(sum(h))
   for s in g['service_sources']:assert s['accepted']==s['returned'] and s['source_fifo_peak']<=4
  assert len(hist_totals)==1 and next(iter(hist_totals))<=f['cycles']
  if 'output_RAM_admitted' in f:
   assert f['output_RAM_admitted']==f['output_RAM_retired']
   assert f['output_RAM_first']==f['recorded']<=inp['cells']
  if 'emit_population_histogram' in f:
   assert len(f['emit_population_histogram'])==65
   assert sum(i*n for i,n in enumerate(f['emit_population_histogram']))==f['candidates']
  if 'critical_final_bank_observers' in f:
   tails=f['critical_final_bank_observers'];assert len(tails)==f['waves']
   assert sum(sum(x['exclusive_histogram']) for x in tails)==f['phase_cycles']['finalize']
   assert all(0<=x['bank']<64 and len(x['exclusive_histogram'])==8 for x in tails)
  assert f['board_measured'] is False and f['fpga_seconds'] is None
  checks.append({'key':key,'cycles':f['cycles'],'finite_sha256':sha(r['finite_path']),'output_sha256':r['output_sha256']})
 assert len(checks)==term['sample_runs']
 return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_RECEIPTS_OUTPUTS_CAPACITY_CONSERVATION','scope':'read-only existing model artifacts; no new simulation; does not certify full RTL equivalence or timing','root':str(root.resolve()),'terminal':terminal,'terminal_sha256':sha(term_path),'binding_sha256':sha(root/'binding.json'),'sample_runs':len(checks),'source_files':len(binding['source_sha256']),'checks':checks}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('--terminal',default='small_C0F1F2F3_terminal.json');ap.add_argument('--output',required=True);a=ap.parse_args();result=verify(a.root,a.terminal);out=Path(a.output);assert not out.exists(),out;out.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result['sample_runs'],'samples',result['source_files'],'sources')
