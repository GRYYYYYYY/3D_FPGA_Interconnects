"""Independent receipt, output, capacity and conservation checks (no model rerun)."""
from pathlib import Path
import csv,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[4]
R=ROOT/'results/fpga_enum_commit_20261114'/(sys.argv[1] if len(sys.argv)>1 else 'model_native_d')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(8<<20),b''):h.update(chunk)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 binding=read(R/'binding.json')
 assert sha(R/'bin/model')==binding['binary_sha256']
 for name,expected in binding['source_sha256'].items():assert sha(R/'source'/name)==expected,name
 report={'run':R.name,'source_closure_verified':True,'binary_verified':True,'input_hash_scope':'frozen run binding; original workload was validated at model preparation, not rehashed here','cases':{}}
 for mode,count in [('small',40),('full',80)]:
  term=read(R/(mode+'_terminal.json'));assert term['all_pass'] and term['sample_runs']==count
  assert len(term['results'])==count
  for rec in term['results']:
   assert rec['returncode']==0 and rec['output_exact']
   assert rec['binary_sha256']==binding['binary_sha256']
   inp=binding['inputs'][rec['case']]
   assert rec['workload_sha256']==inp['workload_sha256'] and rec['golden_sha256']==inp['golden_sha256']
   assert sha(Path(rec['output_path']))==rec['output_sha256']
   d=read(Path(rec['finite_path']));assert d['complete_finite_functional_model'] and d['fpga_seconds'] is None and not d['board_measured']
   assert sum(d['lane_emit'])==d['candidates']
   assert all(v<=c for v,c in zip(d['fork_H_E_M_slots_peak'],[128,128,256,128,512]))
   assert max(d['directory_bank_peaks'])<=8192
   assert len(d['bank_stats'])==64 and len(d['port_stats'])==32
   for b in d['bank_stats']:
    assert b['tx_peak']<=8 and b['spill_id_peak']<=2048
    assert b['commit_admit']==b['commit']
    assert all(v<=c for v,c in zip(b['fifo_peaks'],[16,16,4,2,16,16]))
   for p in d['port_stats']:
    assert p['issued']==p['returned']
    assert p['credit_peak']<=32 and p['queue_peak']<=64 and p['return_peak']<=4
   assert sum(p['issued'] for p in d['port_stats'])==sum(map(sum,d['traffic']))
   assert sum(d['traffic'][3])==d['parents']
   if R.name=='model_native_d':assert sum(d['traffic'][10])==3
   if 'output_ACKs' in d:
    assert d['output_ACKs']==sum(d['traffic'][9])==(inp['cells']+3)//4
    assert d['export_end']-d['export_start']>=(d['output_ACKs']+1)//2
    assert d['output_sample_stride_lines']%32==0
   waves=list(csv.DictReader((Path(rec['finite_path']).parent/'waves.csv').open()))
   assert len(waves)==d['waves']
   assert all(int(x['start'])<=int(x['pop_expand_end'])<=int(x['final_end']) for x in waves)
   assert all(int(a['final_end'])<=int(b['start']) for a,b in zip(waves,waves[1:]))
   assert sum(int(x['candidates']) for x in waves)==d['candidates']
  report[mode]={'verified_sample_runs':count}
 for name,inp in binding['inputs'].items():
  s=read(R/(name+'_summary.json'));assert s['all_pass'] and s['functional_work_counts_match_frozen_profile']
  assert sorted(x['sample'] for x in s['samples'])==list(range(inp['jobs']))
  assert sum(s['per_sample_cycles'])==s['cycles']
  data=b''.join(Path(x['output_path']).read_bytes() for x in sorted(s['samples'],key=lambda x:x['sample']))
  assert hashlib.sha256(data).hexdigest()==inp['golden_sha256']==s['full_output_sha256']
  assert sha(R/(name+'_output.bin'))==inp['golden_sha256']
  report['cases'][name]={'golden_exact':True,'samples':inp['jobs'],'cycles':s['cycles'],'conditional_predicted_seconds':s['conditional_predicted_seconds']}
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
