from pathlib import Path
import json,math,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114';OUT=R/'front_analysis_a'
def stats(x):
 t=x['cycles'];lanes=x['lane_emit'];mean=sum(lanes)/64;cv=(sum((v-mean)**2 for v in lanes)/64)**.5/mean if mean else 0
 return {'cycles':t,'zero_emit_lanes':sum(v==0 for v in lanes),'lane_work_cv':cv,'lane_emit':lanes,'lane_idle':x['lane_empty'],'lane_allocations':x['lane_allocations'],'lane_occupancy_context_cycles':x['lane_occupancy_context_cycles'],'lane_waiting_for_payload_context_cycles':x.get('lane_waiting_for_payload_context_cycles'),'lane_slot_occupancy_beat_cycles':x.get('lane_slot_occupancy_beat_cycles'),'lane_slot_denied_attempts':x['lane_slot_denied_attempts'],'lane_credit_denied_attempts':x['lane_credit_denied_attempts'],'mean_lane_utilization':sum(lanes)/(64*t),'port_total_requests_per_cycle':sum(map(sum,x['traffic_by_kind_port']))/t,'lane_quarter_mean_utilization':[sum(lanes[i:i+16])/(16*t) for i in [0,16,32,48]],'H_E_M_slots_fork_ready_means':[sum(i*n for i,n in enumerate(a))/t for a in x['occupancy_H_E_M_slots_fork_ready_histograms']],'port_credit_stall_attempts':sum(x['port_credit_stall_attempts']),'port_response_full_port_cycles':sum(x['port_response_full_cycles'])}
def main():
 OUT.mkdir(exist_ok=False);rows=[];counts={}
 for run in ['front_compare_a','front_grouped_a','front_grouped_b','front_independent_a']:
  term=json.loads((R/run/'terminal.json').read_text());assert term['all_pass'];receipts=term.get('receipts',[]);counts[run]=len(receipts)
  for rec in receipts:
   cmd=rec['command'];p=Path(cmd[4]);x=json.loads(p.read_text());case=Path(cmd[2]).parent.name;mode=cmd[6];width=int(cmd[7]);wave=Path(cmd[2]).stem
   assert sum(x['lane_emit'])==x['candidates'];assert all(a+b==x['cycles'] for a,b in zip(x['lane_emit'],x['lane_empty']));assert sum(x['lane_allocations'])<=x['parents'];assert all(sum(h)==x['cycles'] for h in x['occupancy_H_E_M_slots_fork_ready_histograms'])
   if run=='front_independent_a':
    assert 'lane_waiting_for_payload_context_cycles' in x
    assert all(sum(h)==x['cycles'] for h in x['lane_slot_occupancy_histograms'])
   rows.append({'run':run,'case':case,'wave':wave,'mode':mode,'dispatch':width,'trace_sha256':rec['trace_sha256'],'metrics':stats(x)})
  assert len(receipts)==(76 if run=='front_compare_a' else 38)
 pairs=[]
 for run,width in [('front_compare_a',0),('front_compare_a',8),('front_grouped_b',8),('front_independent_a',8)]:
  cases={(x['case'],x['wave']) for x in rows if x['run']==run}
  for case,wave in sorted(cases):
   found={x['mode']:x for x in rows if x['run']==run and x['dispatch']==width and x['case']==case and x['wave']==wave};assert len(found)==2
   a=found['FIRST_FREE']['metrics'];b=found['LANE_RR']['metrics'];pairs.append({'run':run,'dispatch':width,'case':case,'wave':wave,'FIRST_FREE_cycles':a['cycles'],'LANE_RR_cycles':b['cycles'],'elapsed_reduction_fraction':1-b['cycles']/a['cycles'],'firstfree_zero_lanes':a['zero_emit_lanes'],'rr_zero_lanes':b['zero_emit_lanes']})
 value={'all_pass':True,'actual_run_counts':counts,'rows':rows,'pairs':pairs,'final_candidate_policy':'eight independentgroups','front_scope':'valid POP input + ideal candidate sink; completed-header group RTL calibrated separately; whole frontend/kernel qualification false','fpga_seconds':None,'board_measured':False}
 (OUT/'summary.json').write_text(json.dumps(value,indent=2)+'\n')
 print('FRONT_ANALYSIS_PASS',counts)
 for x in pairs:
  if x['run']=='front_independent_a':print(x)
if __name__=='__main__':main()
