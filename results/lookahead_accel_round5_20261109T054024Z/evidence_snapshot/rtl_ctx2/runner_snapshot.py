"""Isolated bounded RTL probe reusing an already synthesized frozen design."""
import argparse,json,os,shutil,subprocess,time
from pathlib import Path
from prepare import sha256
from la_accel_hls5 import HLS
p=argparse.ArgumentParser();p.add_argument('--hls',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();h=a.hls.resolve();o=a.output.resolve();assert json.loads((h/'csynth.json').read_text())['status']=='passed';o.mkdir(exist_ok=False)
shutil.copytree(h/'project',o/'project',ignore=shutil.ignore_patterns('sim','impl','csim','*.log','*.jou'));shutil.copytree(h/'source_snapshot',o/'source_snapshot')
b=json.loads((h/'binding.json').read_text());b['source_binding_sha256']=sha256(h/'binding.json');b['source_hls']=str(h);b['workloads']=b['workloads'][:1];b['scope']='Complete 3x3 native batch; three compute calls and load-only; all capacities and synthesized RTL unchanged.';(o/'binding.json').write_text(json.dumps(b,indent=2)+'\n')
for n in ['csim.json','csynth.json']:shutil.copy2(h/n,o/n)
files={str(f.relative_to(h/'project/solution/syn')):sha256(f) for f in (h/'project/solution/syn').rglob('*') if f.is_file()};assert all(sha256(o/'project/solution/syn'/f)==v for f,v in files.items());(o/'synth_reuse.json').write_text(json.dumps(dict(evidence='measured',files=files),indent=2))
tcl=f'open_project project\nopen_solution solution\ncosim_design -rtl verilog -tool xsim -trace_level none -argv [list {{{b["workloads"][0]["path"]}}}]\nexit\n';(o/'probe.tcl').write_text(tcl);shutil.copy2(__file__,o/'runner_snapshot.py');env=os.environ.copy();env.pop('DEBUG',None);env['LD_PRELOAD']='/lib/x86_64-linux-gnu/libudev.so.1';start=time.monotonic();cmd=[str(HLS),'-f',str(o/'probe.tcl')]
with (o/'cosim.log').open('w') as f:run=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT)
text=(o/'cosim.log').read_text();passed=not run.returncode and 'C/RTL co-simulation finished: PASS' in text and 'ERROR:' not in text;(o/'cosim.json').write_text(json.dumps(dict(status='passed' if passed else 'failed',returncode=run.returncode,command=cmd,host_elapsed_s=time.monotonic()-start,not_fpga_runtime=True,binding_sha256=sha256(o/'binding.json'),log_sha256=sha256(o/'cosim.log')),indent=2));print('passed' if passed else 'failed');raise SystemExit(not passed)
