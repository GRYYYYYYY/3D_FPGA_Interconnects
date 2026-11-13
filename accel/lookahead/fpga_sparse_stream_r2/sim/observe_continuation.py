"""Append an authoritative timestamped observation; old running receipts stay immutable."""
from pathlib import Path
import datetime,json,subprocess,sys,hashlib
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';out=r/'continuation_82860ce';tag=sys.argv[1]
def read(p):return json.loads(p.read_text()) if p.exists() else None
def proc(pid):
 p=Path('/proc')/str(pid)
 try:return {'pid':pid,'alive':True,'start_ticks':p.joinpath('stat').read_text().split()[21],'command':p.joinpath('cmdline').read_bytes().replace(b'\0',b' ').decode(),'cwd':str(p.joinpath('cwd').resolve())}
 except FileNotFoundError:return {'pid':pid,'alive':False}
v={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'review_base':'82860ced203bde54f1fa267446b3d0edc521a293','HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip(),'review_is_ancestor':subprocess.run(['git','merge-base','--is-ancestor','82860ced203bde54f1fa267446b3d0edc521a293','HEAD'],cwd=root).returncode==0,'processes':[],'terminal_route_reviews':[],'fpga_seconds':None,'board_measured':False,'legacy_state_notice':'Historical pending_commands/active_vivado_sessions/branch_pushed and interrupted running receipts are not live state. Use this timestamp plus process identity and terminal evidence.'}
for p in sorted(out.glob('*launch*.json')):
 x=read(p)
 if x.get('pid'):
  observed=proc(x['pid']);expected=x.get('command',[])
  observed['launch_command_matches']=bool(observed['alive'] and expected and all(str(arg) in observed.get('command','') for arg in expected[1:]))
  v['processes'].append({'launch':str(p.relative_to(r)),**observed})
v['original_P8_F0_ooc']=proc(1125009)
v['original_P8_F0_ooc']['variant']='many32_p8_f0_router_context_10ns_a'
for p in sorted((r/'timing').glob('*/completed_route_rejection_*.json')):
 v['terminal_route_reviews'].append({'path':str(p.relative_to(r)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'result':read(p)})
v['micro_OOC_terminal']=read(r/'timing/wave_inf_micro_ram_d_5ns/terminal.json')
v['micro_OOC_recovery2_terminal']=read(r/'timing/wave_inf_micro_ram_d_5ns_recovery2/terminal.json')
v['micro_OOC_review']=read(r/'timing/wave_inf_micro_ram_d_5ns_recovery2/review.json')
v['micro_OOC_recovery1_terminal']=read(r/'timing/wave_inf_micro_ram_d_5ns_recovery1/terminal.json')
v['original_OOC_MCP_last_snapshot']=read(r/'inf_followup_5af9908/original_OOC_terminal_input_v2.json') or read(out/'original_ooc_MCP_2156.json')
v['original_P8_F0_ooc']['execution_state']='completed_failed' if (r/'timing/many32_p8_f0_router_context_10ns_a/completed_route_rejection_followup_2246.json').exists() else 'see_MCP_observation'
v['original_OOC_MCP_snapshot_notice']='The MCP result has its own observation time and must not be refreshed from parent PID alone.'
v['micro_resource_gate']=read(r/'analysis/wave_inf_ram_d_resource_gate.json')
software=read(root/'accel/lookahead/fpga_sparse_stream_r2/config/current_software_run.json')
v['software_run_config']=software
v['GPU_job']=software['job_id'] if software else None
watch=r/'supervision'/software['watch_tag'] if software else r/'supervision/private_inf_gpu_watch'
gpu_observations=sorted(watch.glob('observation_*.json'),key=lambda p:int(p.stem.rsplit('_',1)[1]))
v['GPU_last_status_change']=read(gpu_observations[-1]) if gpu_observations else None
v['GPU_watch_terminal']=read(watch/'terminal.json')
v['targeted_INF_micro_OOC']=read(r/'timing/inf_combo_c_5ns/review.json')
v['targeted_INF_finite_budget']=read(r/'inf_followup_5af9908/finite_budget_v2.json')
v['software_finalizers']=[{'path':str(p.relative_to(r)),'receipt':read(p)} for p in sorted((r/'supervision').glob('software_finalize_*/*.json')) if p.name in ['started.json','terminal.json','failed_preserved.json']]
v['native_finalizers']=[{'path':str(p.relative_to(r)), 'receipt':read(p)} for p in sorted((r/'supervision').glob('finalize_recovered_native_*/*.json')) if p.name in ['started.json','terminal.json','failed_preserved.json']]
v['recovery_terminal']=read(r/'recovery/p8_f0_resume_2108/terminal.json')
v['native_supervisor']=read(r/'supervision/p8_f0_recovered_native_2110b.json')
v['archive_four_routes']=read(out/'verify_four_routes.json')
path=out/('observation_'+tag+'.json')
with path.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
(out/'current_manifest.json').write_text(json.dumps({'observed_at':v['observed_at'],'authoritative_observation':str(path.relative_to(r)),'observation_sha256':hashlib.sha256(path.read_bytes()).hexdigest()},indent=2)+'\n')
print(path)
