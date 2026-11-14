"""Independent evidence checks; no timing-model execution or old benchmark rerun."""
from pathlib import Path
import csv,json,hashlib,sys
from decimal import Decimal as D
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[3]/'results/fpga_decoupled_front_20261114'
def read(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for run in ['front_b','front_stress_b']:
 t=read(run+'/terminal.json');assert t['all_pass']
 assert len(t['results'])==(51 if run=='front_b' else 6)
 for receipt in t['results']:
  assert receipt['returncode']==0
  command=receipt['command'];rel=Path(command[4]).relative_to(Path(command[0]).parents[1]);x=read(str(rel))
  assert x['all_operand_candidates_and_target_outputs_exact']
  assert x['metadata_requests']==x['parents']
  assert [sum(a) for a in x['traffic_by_kind_port']]==[x[k] for k in ['row_requests','edge_requests','metadata_requests']]
  assert sum(x['lane_emit'])==x['candidates']
  assert all(a+b==x['cycles'] for a,b in zip(x['lane_emit'],x['lane_empty']))
  for hist in x['occupancy_H_E_M_slots_fork_ready_histograms']:assert sum(hist)==x['cycles']
  for group in x['port_queue_flight_credit_return_histograms']:
   for hist in group:assert sum(hist)==x['cycles']
  assert all(a<=b for a,b in zip(x['H_E_M_slots_fork_ready_peaks'],[128,256,128,512,128,128]))
  assert max(i for group in x['port_queue_flight_credit_return_histograms'] for i,v in enumerate(group[2]) if v)<=32
  assert max(i for group in x['port_queue_flight_credit_return_histograms'] for i,v in enumerate(group[3]) if v)<=4
pterm=read('profile_a/terminal.json');assert pterm['all_pass']
for x in pterm['results']:assert x['returncode']==0 and x['output_exact'] and x['output_sha256']==x['expected_output_sha256']
for case,target in [('bnn_export','0.151799969444'),('lstm_s2','0.15949799988888888')]:
 p=read('profile_a/'+case+'/physical_profile.json');q=[sum(a) for a in p['requests_by_kind_port']]
 waves=list(csv.DictReader((R/'profile_a'/case/'address_waves.csv').open()))
 assert sum(int(x['touched_lines']) for x in waves)==q[5]
 assert sum(int(x['changed_lines']) for x in waves)==q[6]
 assert sum(int(k)*v for k,v in p['degree_histogram'].items())==p['candidates']
 assert sum(p['degree_histogram'].values())==p['parents']
 assert p['nonempty_parents']+p['zero_degree_parents']==p['parents']
 assert q[0]==p['parents']+p['row_start_alignment'][3]
 assert q[4]==p['jobs']*((p['nodes']+3)//4)
 # Compute every wave separately; only fence-separated stages may be added.
 lower=D(q[4])/32+D(p['candidates'])/64+sum(D(5)*int(w['touched_lines'])/64-5 for w in waves)
 decision=read('analysis_b/decision.json')['rows'][case]['retained_backend_fenced_bound']
 assert lower==D(decision['sum_cycles'])
 assert (lower>D(target)*200000000)==decision['exceeds_target']
 print(case,'lower_bound_seconds',lower/200000000,'reject',decision['exceeds_target'])
print('PASS: full-profile wave sums, 57 local cases, capacity/time/traffic conservation, frozen output hashes, independently recomputed gate')
