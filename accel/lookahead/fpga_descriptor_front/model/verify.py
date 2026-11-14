"""Independent complete-output, finite-capacity, phase and traffic verification."""
from pathlib import Path
import argparse,json,hashlib,struct,csv

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()

def verify(root):
 root=Path(root);binding=json.loads((root/'binding.json').read_text())
 for name,h in binding['source_sha256'].items():assert sha(root/'source'/name)==h, name
 assert sha(root/'bin/model')==binding['binary_sha256']
 receipts=list((root/'runs').glob('*/*/receipt_[0-9]*.json'));receipts=[p for p in receipts if '_attempt_' not in p.name]
 passed=[]
 for rp in receipts:
  r=json.loads(rp.read_text());assert r['returncode']==0 and r['output_exact'],str(rp)
  assert r['binary_sha256']==binding['binary_sha256'];inp=binding['inputs'][r['case']]
  assert r['workload_sha256']==inp['workload_sha256'] and r['golden_sha256']==inp['golden_sha256']
  assert sha(r['output_path'])==r['output_sha256']
  cells=inp['cells'];q=r['sample'];data=Path(r['output_path']).read_bytes()
  with Path(inp['golden']).open('rb') as f:f.seek(q*cells*8);assert data==f.read(cells*8)
  with Path(inp['workload']).open('rb') as f:_,nodes,edges,jobs,costs,ncells,groups=struct.unpack('<7Q',f.read(56))
  x=json.loads(Path(r['finite_path']).read_text());assert x['sample']==q
  assert sum(x['phase_cycles'].values())==x['cycles']
  assert sum(x['fixed_observer_wall_cycles'][0])==x['phase_cycles']['pop_expand']
  assert sum(x['fixed_observer_wall_cycles'][1])==x['phase_cycles']['finalize']
  assert sum(x['lane_emit'])==x['candidates']
  if 'emit_population_histogram' in x:assert sum(i*n for i,n in enumerate(x['emit_population_histogram']))==x['candidates']
  if 'critical_final_bank_observers' in x:assert sum(sum(c['exclusive_histogram']) for c in x['critical_final_bank_observers'])==x['phase_cycles']['finalize']
  if 'output_ACK_peak_per_cycle' in x:assert x['output_ACK_peak_per_cycle']<=2
  if 'output_RAM_admitted' in x:assert x['output_RAM_admitted']==x['output_RAM_retired'] and x['output_RAM_first']==x['recorded']
  if 'descriptor_slots_peak' in x:assert x['descriptor_slots_peak']<=128 and x['ready_peak']<=128
  traffic=dict(zip(x['memory_kind_names'],map(sum,x['traffic'])))
  assert traffic['init']==(nodes+3)//4
  assert traffic['cost_load']==(costs+3)//4
  assert traffic['output_write']==x['output_ACKs']==(cells+3)//4
  assert traffic['edge']>0 or x['candidates']==0
  if r['configuration'] in ('F1','F3'):assert traffic['descriptor']==x['parents'] and traffic['row']==traffic['meta']==0
  else:assert traffic['descriptor']==0 and traffic['meta']==x['parents'] and x['parents']<=traffic['row']<=2*x['parents']
  assert sum(traffic.values())==sum(p['issued'] for p in x['port_stats'])==sum(p['returned'] for p in x['port_stats'])
  for p in x['port_stats']:assert p['credit_peak']<=32 and p['queue_peak']<=4 and p['return_peak']<=4
  for actual,cap in zip(x['fork_H_E_M_slots_peak'],[128,128,256,128,512]):assert actual<=cap
  assert max(x['directory_bank_peaks'])<=8192
  for b in x['bank_stats']:assert b['tx_peak']<=8 and b['spill_id_peak']<=2048 and b['input_candidate_peak']<=2 and b['input_op_peak']<=2
  for group in x['group_stats']:
   for src in group['service_sources']:assert src['accepted']==src['returned'] and src['source_fifo_peak']<=4
   for hist,cap in zip(group['occupancy_histograms'],[128//x['groups']]*4+[4*x['lanes_per_group'],8*x['lanes_per_group']]):assert sum(hist[cap+1:])==0
  waves=list(csv.DictReader((Path(r['finite_path']).parent/'waves.csv').open()))
  assert len(waves)==x['waves'];assert sum(int(w['candidates']) for w in waves)==x['candidates']
  assert sum(int(w['pop_expand_end'])-int(w['start']) for w in waves)==x['phase_cycles']['pop_expand']
  assert sum(int(w['final_end'])-int(w['pop_expand_end']) for w in waves)==x['phase_cycles']['finalize']
  passed.append({'configuration':r['configuration'],'case':r['case'],'sample':q,'jitter':r['jitter'],'cycles':x['cycles'],'output_sha256':r['output_sha256']})
 result={'verifier_sha256':sha(__file__),'status':'PASS','samples':len(passed),'binary_sha256':binding['binary_sha256'],'results':passed,'complete_kernel_clock_qualified':False,'board_measured':False}
 (root/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('VERIFIED',len(passed),'source-bound complete samples')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');verify(p.parse_args().root)
