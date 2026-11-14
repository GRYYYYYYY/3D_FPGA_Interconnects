from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114'
cache={}
def sha(p):
 p=Path(p)
 if p not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8<<20),b''):h.update(b)
  cache[p]=h.hexdigest()
 return cache[p]
report={}
for run,count in [('front_compare_a',76),('front_grouped_a',38),('front_independent_a',38)]:
 d=json.loads((R/run/'terminal.json').read_text());assert d['all_pass'] and d['count']==count;groups={}
 for rec in d['receipts']:
  assert rec['returncode']==0;cmd=rec['command'];assert sha(cmd[0])==rec['binary_sha256'];assert sha(cmd[2])==rec['trace_sha256']
  if 'input_sha256' in rec:assert sha(cmd[1])==rec['input_sha256']
  x=json.loads(Path(cmd[4]).read_text());assert x['all_operand_candidates_and_target_outputs_exact']
  assert sum(x['lane_emit'])==x['candidates']
  assert all(a+b==x['cycles'] for a,b in zip(x['lane_emit'],x['lane_empty']))
  assert all(a<=b for a,b in zip(x['H_E_M_slots_fork_ready_peaks'],[128,256,128,512,128,128,0]))
  assert x['metadata_requests']==x['parents']
  assert [sum(z) for z in x['traffic_by_kind_port']]==[x[k] for k in ['row_requests','edge_requests','metadata_requests']]
  groups.setdefault(rec['trace_sha256'],[]).append(x)
 for group in groups.values():
  assert len({tuple(x[k] for k in ['parents','candidates','target_events','first_seen','row_requests','edge_requests','metadata_requests']) for x in group})==1
 assert len(groups)==19
 if run=='front_compare_a':assert all(c['old_compatibility_exact'] for c in d['comparisons'])
 report[run]={'verified':count,'native_or_contiguous_inputs':len(groups),'paired_work_traffic_output_conserved':True}
print(json.dumps(report,indent=2))
