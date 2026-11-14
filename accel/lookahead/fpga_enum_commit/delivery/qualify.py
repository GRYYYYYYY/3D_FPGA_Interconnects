"""Summarize final evidence levels without granting a whole-kernel speed claim."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_20261114'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def timing(p):
 lines=p.read_text().splitlines()
 for i,line in enumerate(lines):
  if line.strip().startswith('WNS(ns)'):
   values=lines[i+2].split();assert len(values)==12
   keys=['WNS_ns','TNS_ns','setup_failing_endpoints','setup_total_endpoints','WHS_ns','THS_ns','hold_failing_endpoints','hold_total_endpoints','WPWS_ns','TPWS_ns','pulse_failing_endpoints','pulse_total_endpoints']
   d=dict(zip(keys,[float(v) if j%4<2 else int(v) for j,v in enumerate(values)]))
   d.update({'report':str(p.relative_to(ROOT)),'sha256':sha(p),'setup_hold_pulse_met':all(d[k]>=0 for k in ('WNS_ns','WHS_ns','WPWS_ns'))})
   return d
 raise ValueError(f'No timing summary: {p}')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('front_report',type=Path);ap.add_argument('backend_report',type=Path);a=ap.parse_args()
 model=json.loads((R/'model_final_summary_d.json').read_text());assert model['status']=='COMPLETE_MODEL_CONDITIONAL'
 out={'base':'1e312d6e4ffc5ea96f25c0b97931ad028e710584','front_OOC':timing(a.front_report.resolve()),'backend_OOC':timing(a.backend_report.resolve()),'model_final_summary_sha256':sha(R/'model_final_summary_d.json'),'final_model':'model_native_d','full_samples_passed':80,'small_sample_runs_passed':40,'cases':{},'full_kernel_OOC_started':False,'full_kernel_clock_qualified':False,'full_kernel_resource_fit_qualified':False,'full_global_service_cycle_calibration':False,'simulated_resident_seconds':None,'fpga_seconds':None,'board_measured':False,'decision':'Complete-model conditional performance misses both targets; full-top gate not met. Local mechanism/functional evidence does not grant complete-kernel timing or universal FPGA no-go.','new_GPU_runs':0,'old_model_reruns':0}
 for name,c in model['cases'].items():out['cases'][name]={'cycles':c['sequential_cycles'],'conditional_predicted_seconds':c['conditional_seconds'],'reused_GPU_resident_seconds':c['GPU_target_seconds'],'full_output_sha256':c['full_output_sha256'],'conditional_model_exceeds_target':c['conditional_model_exceeds_target']}
 p=R/'qualification.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
