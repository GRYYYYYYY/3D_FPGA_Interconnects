import pathlib,json,re
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z/closed_loop';inputs=json.load(open(root/'accel/lookahead/fpga_sim_restart/config/inputs.json'))
rows=[];bounds=[]
for x in inputs[2:]:
 _,n,e,j,k,c,g=x['header'];name='bnn' if x['case']=='bnn_export' else 'lstm';m=json.load(open(r/f'large/{name}_F1_central.json'))
 # All immutable input arrays; no mutable homes/clear traffic moved out of kernel.
 h2d=sum((b+31)//32*32 for b in [8*(n+1),16*n,8*e,8*k,32*j,4*n*j]);d2h=8*j*c;resident=m['cycles']/2e8
 for sid,bw,conversion,launch,post in [('idealized',32e9,0.,0.,0.),('illustrative',16e9,1.,20e-6,.01),('higher_overhead',8e9,2.,100e-6,.05)]:
  terms={'external_conversion_s':conversion,'initial_H2D_s':h2d/bw,'one_time_launch_s':launch,'resident_projected_s':resident,'final_D2H_s':d2h/bw,'external_postprocess_s':post};rows.append({'case':x['case'],'scenario':sid,'parameter_provenance':'assumed illustration; not PCIe/FPGA measurement','real_batch_jobs':j,'reuse_K':1,'H2D_bytes':h2d,'D2H_bytes':d2h,'PCIe_shared_sequential_bytes_per_s':bw,'nonoverlapping_terms':terms,'cold_projected_s':sum(terms.values()),'cold_speedup_claimed':False})
 nonprop=sum(v['reads32B']+v['writes32B'] for a,v in m['traffic'].items() if a!='proposal');bounds.append({'case':x['case'],'source':'actual complete model traffic excluding ALL proposal transactions, including controller proposal scan traffic, for an optimistic bound','nonproposal_controller_transactions':nonprop,'optimistic_controller_transactions_per_cycle':1,'assumed_hz':200000000,'optimistic_lower_bound_s':nonprop/2e8,'interpretation':'applies to this serial scan front end only; changing architecture invalidates this bound'})
def walk(x):
 if isinstance(x,dict):
  if x.get('backend')=='alt_cpu' and 'qualification' in str(x.get('repeat')) and 'live_lines' in x:yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
shares=[]
for fn in ['targeted_optimization_results.json','holdout_results.json']:
 p=root/'results/lookahead_r6_2_20261109T191213Z/evidence_snapshot'/fn
 for x in walk(json.load(open(p))):
  if x.get('case') not in ['bnn','lstm_s2']:continue
  lines='\n'.join(x.get('live_lines',[]));match=re.search(r'\bresident_s=([\d.]+)',lines)
  if not match:continue
  seconds=float(match[1]);e2=x.get('E2_s');process=x.get('Process_wall_s');shares.append({'case':x['case'],'source':str(p.relative_to(root)),'repeat':x['repeat'],'cohort':'historical cold native original ALT CPU qualification, same invocation for numerator/denominator','resident_s':seconds,'E2_s':e2,'Process_wall_s':process,'resident_fraction_of_E2':seconds/e2 if e2 else None,'resident_fraction_of_Process':seconds/process if process else None,'not_FPGA_application_speedup':True})
(r/'cold_call_supplement.json').write_text(json.dumps({'cold_scenarios':rows,'serial_front_end_lower_bounds':bounds,'historical_native_module_share':shares,'observed_win_loss_crossover':'none of five predeclared scenarios wins; even one controller transaction per cycle excluding all proposal work exceeds current ALT CPU batch','scope':'supplement only; main RESIDENT_COMPLETE_BATCH_V2 unchanged'},indent=2)+'\n')
print(json.dumps({'bounds':bounds,'native_shares':shares},indent=2))
