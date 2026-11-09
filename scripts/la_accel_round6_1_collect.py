"""Collect final R6.1 evidence; refuses to turn unfinished experiments into success."""
import json,sys,statistics as st,hashlib,re,struct
from pathlib import Path
from report_native_joint import log_evidence
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();g=r/'gpu_worker';e=r/'evidence_snapshot';e.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text())
def write(name,x): (e/name).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def E1(x):return x.get('E1_s',x.get('resident_s'))
assert read(g/'finished.json')['status']=='passed'
rows=read(g/'measurements.json');assert len(rows)==87
extra=read(g/'native/representation_control.json')
for x in extra:x['workers']=0
allrows=rows+extra;groups={}
for x in allrows:groups.setdefault((x['case'],x['kind'],x['workers']),[]).append(x)
summary=[]
for (case,kind,workers),xs in sorted(groups.items()):
 assert len(xs)==3 and all(len(x['measurements'])==4 for x in xs)
 process=[st.median(E1(y) for y in x['measurements'][1:]) for x in xs]
 summary.append(dict(case=case,kind=kind,workers=workers,process_warm_medians_s=process,warm_median_s=st.median(process),warm_range_s=[min(process),max(process)],fresh_first_call_median_s=st.median(E1(x['measurements'][0]) for x in xs),load_median_s=st.median(x['measurements'][0].get('load_s',0) for x in xs),prepare_median_s=st.median(x['measurements'][0].get('prepare_s',0) for x in xs),conversion_median_s=st.median(x['measurements'][0].get('conversion_s',0) for x in xs)))
write('matched_software.json',dict(protocol='3 independent processes x (first call +3 warm complete batches); median of process warm medians; sequential same worker; first/load/prepare are separate columns, not E2',rows=allrows,summary=summary))
worker=read(g/'worker.json');inputs=[dict(case=c,**read(g/(c+'_preflight.json'))) for c in ['tseng_export','bnn_export']]
write('baseline_inventory.json',dict(base_commit='480ba6d5cc2b9d73696a44315777c0e658d8a7b4',worker=worker,inputs=inputs,implementations={k:dict(source=s,algorithm=a,representation=rep,native_qualification='separate; no inheritance') for k,s,a,rep in [('strict','round6_1/strict61.cpp + frozen round4/reference4.hpp','STRICT full flood','original'),('early','same wrapper + frozen round4/reference4.hpp','MAP_EQ_EARLY_STOP','original'),('alt_original','round6_1/cpu61.cpp','ALT_BUCKET_FP32_V1 shift20','original'),('alt_compact','round6_1/cpu61.cpp','ALT_BUCKET_FP32_V1 shift20','COMPACT_RRG_V1'),('alt_direct','round6_1/cpu61.cpp','ALT_BUCKET_FP32_V1 shift20 direct directory','COMPACT_RRG_V1'),('gpu_basic','unchanged round6/cuda6.cu','ALT_BUCKET_FP32_V1 shift20','original'),('gpu_compact','round6_1/cuda61.cu','ALT_BUCKET_FP32_V1 shift20','COMPACT_RRG_V1'),('gpu_original_refactor','round6_1/cuda61.cu','ALT_BUCKET_FP32_V1 shift20','original') ]},strict_admission='N<2^23, E<UINT32_MAX, original FP32 bound; GEMM excluded; no relaxation',scope_version='R6_1_NATIVE_BUILD_V1',native_scope=read(r/'native_build/binding.json'),cache_state='filesystem cache not flushed, warm resident batch explicit; no graph-reuse throughput claim'))
native=read(g/'native/rows.json');formal=[x for x in native if not x['qualification_diagnostic']];assert len(formal)==24
for x in formal:
 log=(g/'native'/f"{x['case']}_{x['backend']}_{x['repeat']}"/'process.log').read_text(errors='replace');x['inherited_RRG_no_fanin_diagnostics']=log.count('has no fanin')
 x['timing_components']={k:float(v) for k,v in re.findall(r'(conversion_s|prepare_s|resident_s|readback_s|release_s|service_s|merge_s|total_s)=([0-9.eE+-]+)',' '.join(x['live_lines']))}
 x['outside_LA_LIVE_within_E2_s']=x['E2_s']-x['timing_components']['total_s'] if 'total_s' in x['timing_components'] else None
 x['residual_scope_note']='remaining native builder work outside LA_LIVE; not an isolated interpolation measurement'
native_summary=[]
for case in ['s38417','bnn']:
 for arm in ['stock','optimized','alt_cpu','alt_cuda']:
  xs=[x for x in formal if x['case']==case and x['backend']==arm];assert len(xs)==3
  native_summary.append(dict(case=case,backend=arm,representation='original',shift=20 if arm.startswith('alt') else None,E1_wall_median_s=st.median(x['E1_wall_s'] for x in xs) if arm.startswith('alt') else None,E2_median_s=st.median(x['E2_s'] for x in xs),Process_median_s=st.median(x['Process_wall_s'] for x in xs),CPD_ns=[x['metrics']['critical_path_ns'] for x in xs],wirelength=[x['metrics']['wirelength'] for x in xs],iterations=[x['metrics']['iterations'] for x in xs],qor_passed=all(x['paired_qor_passed'] for x in xs),scope_version='R6_1_NATIVE_BUILD_V1',E2_timer_precision_s=xs[0]['E2_precision_s']))
write('native_e2.json',dict(rows=formal,summary=native_summary,parent_child='Process contains native E2. E2 contains conversion, prepare/service, E1, merge/interpolation and remaining native lookahead. LA_LIVE.total_s is a subset. CUDA resident/readback are children of direct E1. No median sums.',qualification_capture_in_formal=False,RR_load='outside E2, inside Process',stock_timer_precision_s=.01))
a2=read(r/'native_cpu_qualification_b/runs.json');identities=read(r/'native_cpu_identity.json');diff=read(r/'native_cpu_map_diff.json');qrecords=[]
source_inputs={}
for x in a2:
 for role,binding in x['input_bindings'].items():
  path=binding['path']
  if path not in source_inputs:
   actual=sha(path);assert actual==binding['sha256'],'native source input changed'
   source_inputs[path]=dict(role=role,sha256=actual,expected=binding['sha256'],verified=True)
write('native_source_input_hash_check.json',source_inputs)
for x in formal:
 arm='alt_s20' if x['backend'].startswith('alt') else 'control';expected=next(z for z in a2 if z['case']==x['case'] and z['arm']==arm)['map_sha256'];assert x['map_sha256']==expected,'formal map differs from qualification/control'
for case in ['s38417','bnn']:
 control=next(x for x in a2 if x['case']==case and x['arm']=='control')
 for shift in [0,20]:
  x=dict(next(x for x in a2 if x['case']==case and x['arm']==f'alt_s{shift}'));x['zero_overuse']=log_evidence(r/'native_cpu_qualification_b'/f'{case}_alt_s{shift}')['last_observed_overused_nodes']==0;ok=bool(x['zero_overuse'] and x['returncode']==0 and x['metrics']['full_check'] and x['independent']['metrics']['full_check'] and x['alt_dispatch_verified'] and x['readback_identity'] and x['metrics']['critical_path_ns']<=1.05*control['metrics']['critical_path_ns'] and x['metrics']['wirelength']<=1.05*control['metrics']['wirelength'])
  qrecords.append(dict(case=case,backend='cpu',shift=shift,representation='original',qualification='pass' if ok else 'fail',evidence=x,final_map_differences=next(z for z in diff if z['case']==case and z['pair']==f'alt_s{shift}_vs_control')))
 x=next(x for x in native if x['case']==case and x['qualification_diagnostic']);cap=Path(x['native_capture']['path']);h=struct.unpack('<7Q',cap.open('rb').read(56));cut=cap.stat().st_size-h[3]*h[5]*8;dig=hashlib.sha256()
 with cap.open('rb') as f:
  remain=cut
  while remain:b=f.read(min(remain,8*1024*1024));dig.update(b);remain-=len(b)
  outsha=hashlib.sha256(f.read()).hexdigest()
 cpu=next(z for z in identities if z['case']==case)['actual_inputs'][1];same=dig.hexdigest()==cpu['input_prefix_sha256'] and outsha==cpu['output_sha256'];assert same
 qrecords.append(dict(case=case,backend='cuda',shift=20,representation='original',qualification='pass' if x['qualified'] and same and all(z['paired_qor_passed'] for z in formal if z['case']==case and z['backend']=='alt_cuda') else 'fail',live_same_input_pair_verified=same,input_prefix_sha256=dig.hexdigest(),output_sha256=outsha,evidence=x,final_map_differences=next(z for z in diff if z['case']==case and z['pair']=='alt_s20_vs_control')))
 for backend in ['cpu','cuda','cpu_direct']:qrecords.append(dict(case=case,backend=backend,shift=20,representation='compact',qualification='not_run',reason='offline representation validated; native path remains original'))
write('native_qualification.json',dict(records=qrecords,bnn_offline_native_identity=read(r/'bnn_export_native_identity.json'),cpu_input_identities=identities,map_differences=diff,STRICT_equivalent=False,historical_counterexamples='preserved unchanged in R6 evidence; offline BNN sample congestion differences133798 are not native map24434'))
write('phase_profile.json',dict(measurements=read(g/'phase_profile.json'),uninstrumented_fresh_diagnostic_controls=read(g/'native/phase_controls.json'),overhead_interpretation='observed fresh-call differences include event synchronization and run/clock variation; not a pure isolated instrumentation cost',interpretation='CUDA event interval per named stage; stage sync changes schedule; host completion wait separately measured; any interval containing launch/memset gaps is not pure kernel time; no profiled number in formal speed table',profiler_replay=False))
cache=read(r/'cache_screen/finished.json')
if not cache.get('functional_full_batch_replay_complete'):
 observed='\n'.join(p.read_text(errors='replace') for p in (r/'cache_screen').glob('*_full.log'))
 if 'finite chunk pool overflow' in observed or '"status":1' in observed or '"whole_pair_home_equal":false' in observed:
  cache=dict(cache,raw_runner_status=cache['status'],status='NO_GO',classification='observed finite-capacity or whole-pair functional failure')
gate=read(r/'cache_screen/necessary_gate.json');selection=read(r/'cache_screen/selection.json') if (r/'cache_screen/selection.json').exists() else None
full=read(r/'cache_screen/full_transactions.json') if (r/'cache_screen/full_transactions.json').exists() else []
final_target=min(x['warm_median_s'] for x in summary if x['case']=='bnn_export')
gate['pre_representation_isolation_target_s']=gate['updated_best_E1_s'];gate['final_all_controls_best_E1_s']=final_target
gate['final_sensitivity']=[dict(lanes=l,reference_frequency_hz=f,ideal_edge_only_s=1286937147/(l*f),required_utilization_for20percent_margin=1286937147/(l*f*final_target*.8)) for l in [16,32,64] for f in [125000000,200000000]]
capacity=selection['chosen'] if selection else None
ledger=dict(contexts=8,owner_banks_per_qid=64,shared_headers_bytes=4096*8*16,leaf_bitmap_bytes=4096,top_bitmap_bytes=64,member_pool_bytes=524288*8*4,sparse_chunk_metadata_bytes=16384*8*32,cache_entries_per_bank=capacity,cache_entry_budget_bytes=24,all_cache_entries_bytes=capacity*64*8*24 if capacity else None,replicated_cost_table_bytes=10*8*64*8,other_FIFOs_and_ports='unknown; not included',physical_fit='unknown; logical storage only')
for inp in inputs:
 if inp['case']=='bnn_export':
  h=inp['header'];N,E,J,K,C=h[1:6];ledger['bnn_external_layout_sensitivity']=dict(compact_graph_bytes=inp['compact_graph_bytes'],eight_qid_label_proposal_pending_seen_flags_bytes=N*8*25,all40_cell_mapping_bytes=N*J*4,all40_output_bytes=J*C*8,meaning='possible layout ledger, not complete timed-model implementation; mapping paging/seen traffic and reset service unmodeled')

transactions=[]
for row in full:
 xs=row['rows'];keys=['events','fp32_additions','cache_hits','cache_misses','evictions','dirty_pair_writebacks','member_enqueue','pending_writes','chunk_publish','empty_to_nonempty','min_selection'];total={k:sum(x[k] for x in xs) for k in keys};total.update(case=row['case'],qid_count=len(xs),max_chunk_pool=max(x['chunk_pool_peak'] for x in xs),max_member_peak=max(x['member_peak'] for x in xs),whole_pair_home_equal=all(x['whole_pair_home_equal'] for x in xs));total['hit_rate']=total['cache_hits']/total['events'];total['proposal_read_bytes_channels']=[sum(x['proposal_read_bytes_channels'][i] for x in xs) for i in range(32)];total['proposal_write_bytes_channels']=[sum(x['proposal_write_bytes_channels'][i] for x in xs) for i in range(32)];transactions.append(total)
unknown=['per_owner_member_high_watermark_and_partition_capacity','physical_issue_retire_timestamps','per_qid_concurrent_wave_closure_completion_timestamps','complete_label_proposal_pending_seen_transactions','actual_burst_distribution','outstanding_requests','RAW_forwarding_latency','cycle_bank_conflicts','FIFO_occupancy_overflow_backpressure','reset_output_drain_nonoverlap_time','achieved_frequency','random_RMW_effective_bandwidth','ports_and_physical_capacity']
write('transaction_model.json',dict(status=cache['status'],functional_full_batch_replay_complete=cache.get('functional_full_batch_replay_complete',False),finite_full_batch_model_complete=False,gate=gate,capacity_ledger=ledger,selection=selection,full_raw=full,summary=transactions,unknown={k:None for k in unknown},transaction_assumption='32B diagnostic granule,32 striped channels; software LRU/CSR candidate order; not measured HBM traffic',issued_retired='functional eligible candidates and two FP32 additions each only; no physical issue/retirement or timing claim',pending='set writes only; pending clears/seen/label traffic omitted',window_equality='sample-mode whole_pair_home_equal true is bypass/not_checked; only full-mode equality is asserted',histogram='distinct reuse distance only bounded windows; full zeros mean uncollected'))
flags=[]
for case in ['tseng_export','bnn_export']:
 for backend,repr_ in [('strict_cpu','original'),('early_cpu','original'),('alt_cpu','original'),('alt_cpu','compact'),('direct_cpu','compact'),('basic_cuda','original'),('cuda','compact'),('cuda_refactor','original')]:flags.append(dict(case=case,backend=backend,shift=20 if 'strict' not in backend and 'early' not in backend else None,representation=repr_,same_worker_measured='pass',strict_cpu_same_worker_measured='pass' if backend=='strict_cpu' else 'not_applicable',early_cpu_same_worker_measured='pass' if backend=='early_cpu' else 'not_applicable',compact_cpu_cuda_matched_measured='pass' if repr_=='compact' and backend in ['alt_cpu','cuda'] else 'not_applicable',direct_directory_contract_verified='pass' if backend=='direct_cpu' else 'not_applicable',native_qualified='not_run',compact_same_contract_verified='pass' if repr_=='compact' else 'not_applicable'))
for case in ['tseng_export','bnn_export']:
 for backend,repr_,status in [('cpu','original','pass'),('cpu','compact','pass'),('cuda','original','pass'),('cuda','compact','not_run')]:flags.append(dict(case=case,backend=backend,shift=0,representation=repr_,full_input_functional_validation=status,formal_warm_matrix_measured='not_run',native_qualified='not_run',compact_same_contract_verified=status if repr_=='compact' else 'not_applicable'))
for x in qrecords:flags.append({k:x[k] for k in ['case','backend','shift','representation']}|dict(native_qualified=x['qualification'],shift20_native_cuda_qualified=x['qualification'] if x['backend']=='cuda' and x['shift']==20 else 'not_applicable',shift20_native_cpu_qualified=x['qualification'] if x['shift']==20 and x['backend']=='cpu' else 'not_applicable',shift20_native_cuda_live_verified=x['qualification'] if x['backend']=='cuda' and x['representation']=='original' else 'not_run',native_E2_measured='pass' if x['representation']=='original' and x['shift']==20 else 'not_run'))
for case in ['tseng_export','bnn_export']:flags.append(dict(case=case,backend='finite_cache_candidate',shift=20,representation='compact',functional_full_batch_replay='pass' if any(x['case']==case and x['whole_pair_home_equal'] for x in transactions) else 'not_run',finite_full_batch_model_complete='unknown',memory_service_parameters_supported='unknown',resource_capacity_supported='unknown',eligible_for_service_prototype='fail',fpga_superiority_verified=False,board_measured=False))
write('decision.json',dict(status=cache['status'],software_closure='pass' if all(x.get('qualification')!='fail' for x in qrecords) and all(x['paired_qor_passed'] for x in formal) else 'fail',case_backend_shift_representation=flags,native_E2_scope_version='R6_1_NATIVE_BUILD_V1',finite_full_batch_model_complete=False,memory_service_parameters_supported='unknown',resource_capacity_supported='unknown',resource_capacity_reason='logical cache/chunk/member counts tested, physical ports/FIFOs/external service not established',eligible_for_service_prototype=False,fpga_superiority_verified=False,board_measured=False,reason='complete functional replay is not a finite timed architecture; unsupported random RMW service and achieved frequency prevent20percent margin claim',stop='close R6.1; do not start HLS/RTL/OOC or another candidate; preserve software results',minimum_missing_evidence=unknown))
write('functional_summary.json',dict(cases=[dict(case=x['case'],backend='cpu',shift=x['shift'],representation=x['representation'],status='pass' if x['equal'] else 'fail') for x in read(r/'validation/result.json')]+[dict(case=x['case'],backend='cuda',shift=x['shift'],representation='compact',status='pass' if x['pass_'] else 'fail') for x in read(g/'functional.json')],cpu_configurations=len(read(r/'validation/result.json')),cuda_configurations=len(read(g/'functional.json')),cpu_compact_lifecycle=read(r/'compact_errors/result.json'),cpu_direct_lifecycle=[dict(x,representation='direct' if x.get('shift')==20 else 'compact') for x in read(r/'direct_errors/result.json')],cuda_lifecycle=read(g/'native/cuda_errors.json'),field_admission=read(r/'compact_field_admission.json')))
print(json.dumps(dict(software=summary,native=native_summary,cache=transactions,decision=read(e/'decision.json')['status']),indent=2))
