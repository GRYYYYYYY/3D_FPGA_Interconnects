"""Verify frozen F receipts/capacities/results independently of the simulator."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[4];R=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results/fpga_enum_commit_20261114'
def mapped(path):
 p=Path(path);parts=p.parts;i=parts.index('fpga_enum_commit_20261114');return R.joinpath(*parts[i+1:])
def main():
 runs={'front_compare_a':76,'front_grouped_a':38,'front_grouped_b':38,'front_independent_a':38};allpairs=0
 for name,total in runs.items():
  t=json.loads((R/name/'terminal.json').read_text());assert t['all_pass'];assert len(t['receipts'])==total;groups={};binary=set()
  for rec in t['receipts']:
   assert rec['returncode']==0;binary.add(rec['binary_sha256']);cmd=rec['command'];p=mapped(cmd[4]);x=json.loads(p.read_text());assert x['all_operand_candidates_and_target_outputs_exact']
   assert sum(x['lane_emit'])==x['candidates'];assert x['metadata_requests']==x['parents']
   assert [sum(q) for q in x['traffic_by_kind_port']]==[x[k] for k in ['row_requests','edge_requests','metadata_requests']]
   assert all(a+b==x['cycles'] for a,b in zip(x['lane_emit'],x['lane_empty']))
   assert all(sum(h)==x['cycles'] for h in x['occupancy_H_E_M_slots_fork_ready_histograms'])
   assert all(a<=b for a,b in zip(x['H_E_M_slots_fork_ready_peaks'],[128,256,128,512,128,128]))
   for port in x['port_queue_flight_credit_return_histograms']:
    for hist,cap in zip(port,[64,32,32,4]):assert sum(hist)==x['cycles'] and not any(hist[cap+1:])
   if 'lane_slot_occupancy_histograms' in x:assert all(sum(h)==x['cycles'] and len(h)==9 for h in x['lane_slot_occupancy_histograms'])
   key=(Path(cmd[2]).parent.name,Path(cmd[2]).stem,cmd[7]);groups.setdefault(key,{})[cmd[6]]=x
  assert len(binary)==1
  for vs in groups.values():
   assert len(vs)==2;a,b=vs['FIRST_FREE'],vs['LANE_RR']
   assert tuple(a[k] for k in ['parents','candidates','target_events','first_seen','traffic_by_kind_port'])==tuple(b[k] for k in ['parents','candidates','target_events','first_seen','traffic_by_kind_port'])
   allpairs+=1
 for name in ['front_rtl_a','front_rtl_b','front_rtl_c','front_rtl_d','front_allocator_rtl_a']:
  x=json.loads((R/name/'calibration.json').read_text());assert x['all_pass']
 assert 'TEST_PASS offset_bounds legal32_max_and_upper32_rejection' in (R/'front_offset_bounds_b/simulate.log').read_text()
 print('FRONT_VERIFY_PASS paired_runs=190 groups=',allpairs,'alllocalcalibrations=5 + explicit32bit-domain test; no timing/fullkernel claim')
if __name__=='__main__':main()
