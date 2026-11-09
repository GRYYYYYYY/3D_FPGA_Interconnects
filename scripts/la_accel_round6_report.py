"""Reduce only completed R6 evidence; never infer missing qualification as a pass."""
import json,sys,statistics,re,hashlib
from collections import defaultdict
from pathlib import Path
from prepare import sha256
from report_native_joint import log_evidence
r=Path(sys.argv[1]);gpu=r/'gpu_worker';finish=json.load(open(gpu/'finished.json'));assert finish['status']=='passed';measure=json.load(open(gpu/'measurements.json'));groups=defaultdict(list)
for row in measure:
 key=(row['case'],row['shift'],row['kind'],row['workers']);warm=[x['E1_s'] for x in row['measurements'] if x['repeat']>0];assert len(warm)==3;groups[key].append(statistics.median(warm))
timing=[]
for (case,shift,kind,workers),values in sorted(groups.items()):
 assert len(values)==3
 timing.append(dict(case=case,shift=shift,kind=kind,workers=workers,process_medians_s=values,median_s=statistics.median(values),min_s=min(values),max_s=max(values)))
matched=[]
for case,shift in sorted(set((x['case'],x['shift']) for x in timing)):
 cpu=min((x for x in timing if x['case']==case and x['shift']==shift and x['kind']=='cpu'),key=lambda x:x['median_s']);cuda=next(x for x in timing if x['case']==case and x['shift']==shift and x['kind']=='cuda');matched.append(dict(case=case,shift=shift,cpu=cpu,cuda=cuda,cpu_over_gpu=cpu['median_s']/cuda['median_s']))
(r/'matched_timing.json').write_text(json.dumps(dict(scope='same worker, full real batch warm E1; median of three process medians, three warm batches each; best tested legal CPU thread count',worker=json.load(open(gpu/'worker.json')),all_configurations=timing,matched=matched),indent=2))
rows=json.load(open(r/'native_live_verified/runs.json'));assert len(rows)==4;native=[]
for case in ['s38417','bnn']:
 pair=[x for x in rows if x['case']==case];a,b=pair
 assert a['arm']=='control' and b['arm']=='alt_s0'
 for x in pair:
  d=r/'native_live_verified'/(case+'_'+x['arm']);ev=log_evidence(d);x['overused_nodes']=ev['last_observed_overused_nodes'];x['native_stage_seconds']=ev['stage_seconds']
  x['independent_pass']=x.get('independent',{}).get('returncode')==0 and x['independent']['metrics']['full_check'] and all(x['metrics'][k]==x['independent']['metrics'][k] for k in ['critical_path_ns','wirelength'])
  x['input_copy_hashes_match']=all(sha256(d/name)==x['input_bindings'][role]['sha256'] for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')])
  x['qualified']=x['returncode']==0 and x['metrics']['routing_success'] and x['metrics']['full_check'] and x['overused_nodes']==0 and x['independent_pass'] and x.get('readback_identity') and x['input_copy_hashes_match'] and x['alt_dispatch_verified']
 da=(r/'native_live_verified'/(case+'_control')/'wire_map.bin').read_bytes();db=(r/'native_live_verified'/(case+'_alt_s0')/'wire_map.bin').read_bytes()
 cp=b['metrics']['critical_path_ns']/a['metrics']['critical_path_ns']-1;wl=b['metrics']['wirelength']/a['metrics']['wirelength']-1
 native.append(dict(case=case,shift=0,qualified_control=a['qualified'],qualified_alt=b['qualified'],cpd_change_fraction=cp,wirelength_change_fraction=wl,native_qor_gate_passed=bool(a['qualified'] and b['qualified'] and cp<=.05 and wl<=.05),decoded_map_differences=json.load(open(r/('native_'+case+'_map_diff.json'))),native_map_bytes_equal=da==db,native_map_changed_bytes=sum(x!=y for x,y in zip(da,db))+abs(len(da)-len(db)),control=a,candidate=b))
(r/'native_qualification.json').write_text(json.dumps(native,indent=2))
profiles=json.load(open(r/'profile_summary.json'));budget=[]
for x in profiles:
 m=next(z for z in matched if (z['case'],z['shift'])==(x['case'],x['shift']));model=x['conditional_screen'];bank=model['bank_service_cycles']/200e6;directory=x['directory_insert_lookups']/200e6
 # One shared directory update/cycle: an explicit optimistic assumption, not implemented RTL.
 lower=max(bank,directory,model['traffic_seconds'][1]);conservative=max(bank*2,directory*2,model['traffic_seconds'][0]);barriers=64*x['wave_count']/200e6
 budget.append(dict(case=x['case'],shift=x['shift'],candidate='8 contexts,16 FP32 lanes,16 label banks,one shared directory update/cycle,external HBM; not synthesized',assumed_hz=200000000,ideal_edge_only_s=x['eligible_edges']/(16*200e6),ideal_edge_only_beats_gpu=x['eligible_edges']/(16*200e6)<m['cuda']['median_s'],lower_bound_before_barriers_s=lower,optimistic_conditional_s=lower+barriers,optimistic_with_25percent_margin_s=(lower+barriers)*1.25,conservative_conditional_s=conservative+barriers,cpu_s=m['cpu']['median_s'],gpu_s=m['cuda']['median_s'],optimistic_with_margin_beats_both=(lower+barriers)*1.25<min(m['cpu']['median_s'],m['cuda']['median_s']),resource_budget_supported=False,limits=model['omitted_costs']))
(r/'hardware_screen.json').write_text(json.dumps(dict(decision='NO_GO_FOR_NEW_HARDWARE_THIS_ROUND',scope='one finite throughput/capacity screen; rejects readiness, not all possible FPGA architectures',reason='BNN shift20 measured CUDA beats even 16-lane200MHz II1 edge-only lower bound; exact shift0 conditional margin does not beat the available coarse CUDA alternative with identical tested BNN output',storage_bn=dict(graph_and_mapping_bytes=next(x for x in profiles if x['case']=='bnn_export')['input_bytes'],eight_context_label_bytes=8*8*4102608,member_capacity_per_context=4*4102608+1,member_storage_8contexts_bytes=8*4*(4*4102608+1)),rows=budget,new_implemented_frequency_hz=None,board_measured=False,fpga_superiority_verified=False),indent=2))
flags=dict(model_schedule_calibrated={'issue_retire_separation':True,'complete_native_cycle_model':False},alternative_contract_defined=True,native_bitwise_equivalent_on_tested_inputs={'six_small_graphs_shift0_shift20':True,'tseng_shift0_shift20':True,'semantic_fixtures_shift0_shift20':False,'BNN_shift0_shift20':False,'native_final_maps':{x['case']:x['native_map_bytes_equal'] for x in native}},same_algorithm_cpu_gpu_verified={'six_small_graphs_and_509_fixtures_shift0_shift20':True,'tseng_and_BNN_complete_batches_shift0_shift20':True},large_3d_complete_batch_verified={'BNN_40_qids_shift0_shift20_cpu_cuda':True},native_qor_gate_passed={x['case']+'_shift0':x['native_qor_gate_passed'] for x in native},native_qor_shift20='not_run',hardware_candidate_budget_supported=False,fpga_superiority_verified=False,new_implemented_frequency_hz=None,board_measured=False)
(r/'report_final.json').write_text(json.dumps(dict(status='completed_algorithm_screen',decision='NO_GO_FOR_NEW_HARDWARE_THIS_ROUND',flags=flags,matched=matched,native=[{k:v for k,v in x.items() if k not in ['control','candidate']} for x in native],hardware=budget,retained_failures=['missing python alias attempt','DLA control600s timeout and dependent cancellation','wrong export-only VPR native attempt: ALT not dispatched; excluded','resource query missing compute-group selector'],limitations=['native is one paired prescreen per circuit, not formal repeated speed statistics','kernel/host phase breakdown not separately instrumented; complete CUDA E1 includes directory scans, barriers, control and output','large path pairing evidence is replayable outputs and algorithm checks; exhaustive immutable path witnesses limited to small corpus','RR parse timer combines filesystem IO and DOM allocation; binary format CPU comparison not measured']),indent=2))
print(json.dumps(dict(matched=matched,native=[{k:v for k,v in x.items() if k not in ['control','candidate']} for x in native],budget=budget),indent=2))
