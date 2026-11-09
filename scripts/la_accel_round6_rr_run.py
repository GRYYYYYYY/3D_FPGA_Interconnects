"""Run two bounded attribution diagnostics after native qualification has drained."""
import os,json,sys,subprocess,time,shutil,re
from pathlib import Path
import run_native_flat_baseline as b
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();o=r/'rr_diagnostic';plan=b.read(R/'results/native_flat_baseline_20261105/plan.json');cases=b.read(R/'results/native_flat_baseline_20261105/summary.json')['cases']
def active_native():
 for p in Path('/proc').glob('[0-9]*/cmdline'):
  try:a=p.read_bytes().split(b'\0')
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  if len(a)>2 and a[0]==b'python3' and a[1].endswith(b'la_accel_round6_native.py') and Path(a[2].decode()).resolve()==r/'native_live_verified':return True
 return False
while active_native():time.sleep(5)
# Sequential on this host; GPU worker is a different machine.
rows=[]
for case_name in ['tseng_2d','bnn']:
 case=b.read(cases[case_name]['case']['path']);d=o/case_name;d.mkdir(exist_ok=False)
 for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],d/name)
 cmd=b.cpu_command(str(o/'vpr_rr_diagnostic'),case,d,{'router':'parallel'},8,iterations=1);cmd.remove('--analysis');b.set_option(cmd,'--generate_rr_node_overuse_report','off');b.set_option(cmd,'--write_router_lookahead',d/'wire_map.bin');env=b.environment(plan,'flat',d,False)
 start=time.monotonic()
 with (d/'process.log').open('w') as f:
  try:p=subprocess.run(cmd,cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300);rc=p.returncode
  except subprocess.TimeoutExpired:rc=124
 log=(d/'process.log').read_text(errors='replace');stages=[dict(stage=k,seconds=float(v)) for k,v in re.findall(r'R6_RR_STAGE (\w+) ([\d.]+)',log)];wire=d/'wire_map.bin'
 row=dict(case=case_name,command=cmd,returncode=rc,elapsed_s=time.monotonic()-start,stages=stages,rr_file=case['inputs']['rr_graph'],rr_file_bytes=Path(case['inputs']['rr_graph']['path']).stat().st_size,storage='shared GPFS HDD mount; OS cache not dropped; cache warmth uncontrolled',binary_sha256=sha256(o/'vpr_rr_diagnostic'),map_sha256=sha256(wire) if wire.exists() else None,frozen_map_sha256=cases[case_name]['reference_map']['sha256'],scope='diagnostic one route iteration; not legal full routing or formal timing')
 rows.append(row);(o/'measurements.json').write_text(json.dumps(rows,indent=2));print(row['case'],row['returncode'],row['stages'],flush=True)
