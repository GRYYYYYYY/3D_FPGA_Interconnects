from pathlib import Path
import subprocess,os,json,datetime,hashlib
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'accel/lookahead/fpga_enum_commit/front';R=ROOT/'results/fpga_enum_commit_20261114/front_ooc_e'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 env=dict(os.environ);env['LD_PRELOAD']='/lib/x86_64-linux-gnu/libudev.so.1';cmd=['/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado','-mode','batch','-source',str(S/'complete_reports.tcl'),'-notrace','-log',str(R/'report_recovery.log'),'-journal',str(R/'report_recovery.jou')];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (R/'report_recovery.console.log').open('x') as f:
  p=subprocess.Popen(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT);(R/'report_recovery.running.json').write_text(json.dumps({'pid':p.pid,'command':cmd,'start_utc':start}));rc=p.wait()
 raw=(R/'report_recovery.log').read_text();assert rc==0 and 'FRONT_REPORT_RECOVERY_COMPLETE' in raw
 # Marker-only lines avoid matching Tcl source echo or command text.
 lines=raw.splitlines();a=lines.index('CHECK_TIMING_BEGIN');b=lines.index('CHECK_TIMING_END');(R/'check_timing.rpt').write_text('\n'.join(lines[a+1:b])+'\n')
 original=json.loads((R/'terminal.json').read_text());assert original['returncode']==1 and 'invalid command name "redirect"' in (R/'vivado.log').read_text()
 receipt={'command':cmd,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':rc,'input_route_dcp_sha256':sha(R/'route.dcp'),'script_sha256':sha(S/'complete_reports.tcl'),'environment_override':{'LD_PRELOAD':env['LD_PRELOAD']},'scope':'reports only from already saved actualroutecheckpoint; no reimplementation'};(R/'report_completion.json').write_text(json.dumps(receipt,indent=2))
 combined={'terminal_status':'COMPLETED','returncode':0,'has_completion_marker':True,'original_flow_receipt':'terminal.json','original_flow_returncode':1,'original_failure':'unsupported redirect in report formatting, after routeDCP andmainreports saved','report_recovery_receipt':'report_completion.json','report_recovery_returncode':0,'route_checkpoint_sha256':sha(R/'route.dcp'),'preload_workaround_verified':True,'RTL_or_constraints_changed':False};(R/'final_terminal.json').write_text(json.dumps(combined,indent=2));print('FRONT_REPORTS_RECOVERED_NO_REROUTE')
if __name__=='__main__':main()
