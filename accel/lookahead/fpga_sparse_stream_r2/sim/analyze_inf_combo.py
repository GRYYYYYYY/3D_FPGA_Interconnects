"""Summarize real RTL handshakes, not full-router calibration or board speed."""
from pathlib import Path
import csv,json,hashlib,sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';rows=[]
for tag in ['inf_combo_rtl_e','inf_combo_rtl_h']:
 d=r/'accumulator'/tag;binding=json.loads((d/'source_binding.json').read_text());receipt=json.loads((d/'receipt.json').read_text());assert receipt['all_pass']
 ooc=json.loads((r/'timing/inf_combo_c_5ns/source_binding.json').read_text())
 assert all(binding['source_sha256'][k]==v for k,v in ooc['source_sha256'].items())
 for case in receipt['results']:
  v=json.loads(case['log']);name=case['case'];n=0;accepted=0;ev=0;requests=[0]*4;responses=[0]*4;peak=0;last_ret=[0,0];first_a=None;last_a=0
  with (d/(name+'_cycles.csv')).open() as f:
   for row in csv.DictReader(f):
    n+=1;cycle=int(row['cycle']);a=int(row['accept']);accepted+=a.bit_count();ev+=int(row['events']).bit_count();peak=max(peak,int(row['credits']))
    if a:first_a=cycle if first_a is None else first_a;last_a=cycle
    for c in range(4):requests[c]+=(int(row['requests'])>>c)&1;responses[c]+=(int(row['responses'])>>c)&1
    last_ret=[int(row['retired0']),int(row['retired1'])]
  assert accepted==v['accepted'] and sum(requests)==v['physical_requests32B'] and peak<=32
  if not v['expected_capacity_rejection']:assert requests==responses
  if 'requests32B_by_client_rw' in v:assert [sum(x) for x in v['requests32B_by_client_rw']]==requests
  rows.append({'case':name,'run':tag,'cycles_including_micro_init_and_drain':n,'candidate_accepts':accepted,'candidate_retire_at_last_sample':last_ret,'accept_rate_over_active_span':accepted/(last_a-first_a+1) if first_a is not None else None,'candidate_rate_over_whole_test':accepted/n,'unique_line_commits':v['unique_commit_events'],'unique_line_commits_per_whole_test_cycle':v['unique_commit_events']/n,'atomic_event_count':ev,'peak_physical_credits':peak,'requests_by_client_scratch0_label0_scratch1_label1':requests,'raw_counts':v,'cycle_log_sha256':hashlib.sha256((d/(name+'_cycles.csv')).read_bytes()).hexdigest()})
value={'scope':'E13 cases plus H concurrent pending-word case, all same RTL as C constrained OOC. Only owner0/two subbanks. External TB labels initialized outside test. Not full batch RTL calibration. Overflow is an expected explicit reject.','cases':rows,'all_pass':True,'fpga_seconds':None,'board_measured':False}
with (r/'inf_followup_5af9908'/sys.argv[1]).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print('RTL cases',len(rows),'all pass')
