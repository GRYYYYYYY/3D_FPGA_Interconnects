from run_profile import *
from decimal import Decimal,getcontext
import csv,re,shutil
getcontext().prec=40

def main():
 out=R/'analysis_a';out.mkdir(exist_ok=False)
 pterm=json.loads((R/'profile_a/terminal.json').read_text());aterm=json.loads((R/'front_a/terminal.json').read_text());sterm=json.loads((R/'front_stress_a/terminal.json').read_text());assert all(x['all_pass'] for x in [pterm,aterm,sterm])
 sim=R/'enum_rtl_a/project/enum_witness.sim/sim_1/behav/xsim'
 for name in ['simulate.log','compile.log','elaborate.log']:
  raw=(sim/name).read_text();assert 'FATAL' not in raw.upper() and 'ERROR:' not in raw.upper();shutil.copy2(sim/name,out/('enum_'+name))
 log=(sim/'simulate.log').read_text();assert 'TEST_PASS two_waves=2 lines=128 consecutive_enumeration_II=5' in log
 records=[tuple(map(int,x)) for x in re.findall(r'ENUM cycle=(\d+) wave=(\d+) line=(\d+)',log)];assert len(records)==128
 for wave in [0,1]:
  c=[x[0] for x in records if x[1]==wave];assert len(c)==64 and all(b-a==5 for a,b in zip(c,c[1:]))
 rows={};comparisons=[]
 for case,target in [('bnn_export','0.151799969444'),('lstm_s2','0.15949799988888888')]:
  d=json.loads((R/'profile_a'/case/'physical_profile.json').read_text());summary=json.loads((R/'profile_a'/case/'summary.json').read_text());q=[sum(x) for x in d['requests_by_kind_port']];n=d['candidates'];plus=d['nonempty_parents'];waves=summary['waves'];f=Decimal(200000000);budget=Decimal(target)*f
  assert sum(int(k)*v for k,v in d['degree_histogram'].items())==n and sum(d['degree_histogram'].values())==d['parents']
  assert d['zero_degree_parents']==d['degree_histogram']['0']
  independent={'edge_D1':Decimal(16)*q[1]/256,'edge_D2':Decimal(16)*q[1]/512,'E_first_read_residence':(Decimal(16)*plus+n-plus)/256,'pair_lanes':Decimal(n)/64,'header_MSHR_256':Decimal(16)*q[0]/256,'metadata_MSHR_128':Decimal(16)*q[2]/128,'port_all_profiled_requests':Decimal(max(map(sum,zip(*d['requests_by_kind_port']))))}
  # Retained FSM proof: five clocks per resident entry; nonresident spill enumeration
  # starts after resident drain and has a serial >=16-cycle scratch read per line.
  # Hence final >=5*(R_b+S_b)-5 per bank. At least one bank has >=U/64 lines.
  final=Decimal(5)*q[5]/64-5*waves
  init=Decimal(q[4])/32;compute=Decimal(n)/64;total=init+compute+final
  rows[case]={'profile_sha256':sha(R/'profile_a'/case/'physical_profile.json'),'scope':'necessary bounds only; no FPGA prediction','candidate_config':{'H':128,'E':256,'L':64,'D':[1,2],'slots':512,'M':128,'fork':128,'ready':128,'pending_K':8,'scratch_inflight_per_subbank':1,'ports':32,'credit_per_port':32,'request_fifo_per_port':64,'response_buffer_per_port':4,'output_banks':8,'output_entries_per_bank':4096,'latency_ns':80,'gap_ns':5,'assumed_frequency_hz':200000000},'counts':d,'independent_frontend_and_port_bounds_cycles':{k:str(v) for k,v in independent.items()},'frontend_not_rejected':max(independent.values())<budget,'retained_backend_fenced_bound':{'canonical_init_cycles':str(init),'pair_compute_cycles':str(compute),'finalize_enumeration_cycles':str(final),'unique_touched_lines_all_waves':q[5],'boundary_discount_cycles':5*waves,'sum_cycles':str(total),'lower_bound_seconds':str(total/f),'GPU_target_seconds':target,'budget_cycles':str(budget),'exceeds_target':total>budget,'proof_assumptions':['64 subbanks retain inf_flat_bank ENUM_READ/META/SELECT/PAYLOAD/SEND, minimum five-cycle resident enumeration interval.','Scratch enumerates nonresident spilled IDs only after core_done (resident fragment drain). One scratch command waits >=16-cycle read per nonresident line.','Resident/spilled intersection commits once; R+S equals unique touched lines, independent of replacement order. No spill-count reuse.','Full wave fence separates all pair computation from canonical finalize; next-wave computation starts after finalize.','Single canonical backing is initialized in each of 40 samples; init cannot overlap live prior-sample canonical state.','64 physical pair lanes at II=1 and 200 MHz; ideal distribution, no added pipeline/routing cost.','Five cycles per wave are subtracted to allow a free first enumeration boundary.','No edge cache, cross-wave asynchronous updates, changed accumulator enumeration FSM or higher clock is included.']},'fpga_seconds':None,'board_measured':False}
  for trace in sorted((R/'front_a'/case).glob('wave_*.bin')):
   vs={v:json.loads((trace.parent/(trace.stem+'_'+v+'.json')).read_text()) for v in 'ABC'}
   for v,x in vs.items():
    assert x['all_operand_candidates_and_target_outputs_exact']
    assert all(a<=b for a,b in zip(x['H_E_M_slots_fork_ready_peaks'],[128,256,128,512,128,128,0]))
   assert len({(x['parents'],x['candidates'],x['target_events'],x['first_seen']) for x in vs.values()})==1
   comparisons.append({'case':case,'trace_sha256':sha(trace),'wave':trace.stem,'A_B_C_cycles':[vs[v]['cycles'] for v in 'ABC'],'B_over_A':vs['B']['cycles']/vs['A']['cycles'],'C_over_B':vs['C']['cycles']/vs['B']['cycles'],'reports':{v:str((trace.parent/(trace.stem+'_'+v+'.json')).relative_to(ROOT)) for v in 'ABC'}})
 assert rows['bnn_export']['retained_backend_fenced_bound']['exceeds_target']
 value={'status':'NO_GO_CONFIGURATION','scope':'200MHz frontend A/B/C with retained five-cycle accumulator enumeration and full per-sample canonical init; BNN rejected, LSTM not rejected by this bound','stages':{'0':'complete physical profile and necessary bounds','1':'51 frozen native-wave plus 6 contiguous-native alignment/jitter comparisons passed; local scope only','2':'new frontend RTL/OOC not entered after retained-backend bound rejection; existing enumeration RTL witness passed','3':'not entered; no complete new finite architecture model','4':'not entered; no complete-kernel timing qualification'},'rows':rows,'comparisons':comparisons,'new_frontend_RTL_qualified':False,'complete_kernel_clock_qualified':False,'fpga_seconds':None,'board_measured':False}
 (out/'decision.json').write_text(json.dumps(value,indent=2)+'\n')
 print(json.dumps({k:v['retained_backend_fenced_bound'] for k,v in rows.items()},indent=2))
if __name__=='__main__':main()
