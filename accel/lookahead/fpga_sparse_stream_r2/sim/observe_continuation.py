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
for p in sorted((r/'timing').glob('*/completed_route_rejection_continuation2054.json')):
 v['terminal_route_reviews'].append({'path':str(p.relative_to(r)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'result':read(p)})
v['micro_OOC_terminal']=read(r/'timing/wave_inf_micro_ram_d_5ns/terminal.json')
v['micro_resource_gate']=read(r/'analysis/wave_inf_ram_d_resource_gate.json')
v['GPU_job']='job-7977d112-86f2-42f0-9c4e-6481294f1e30'
v['recovery_terminal']=read(r/'recovery/p8_f0_resume_2108/terminal.json')
v['native_supervisor']=read(r/'supervision/p8_f0_recovered_native_2110b.json')
v['archive_four_routes']=read(out/'verify_four_routes.json')
path=out/('observation_'+tag+'.json')
with path.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
(out/'current_manifest.json').write_text(json.dumps({'observed_at':v['observed_at'],'authoritative_observation':str(path.relative_to(r)),'observation_sha256':hashlib.sha256(path.read_bytes()).hexdigest()},indent=2)+'\n')
print(path)
