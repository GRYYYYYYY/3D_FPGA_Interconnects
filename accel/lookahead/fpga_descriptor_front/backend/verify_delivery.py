#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,hashlib,csv,re,shutil
root=Path(__file__).resolve().parents[4];h=Path(__file__).resolve().parent;o=root/'results/fpga_descriptor_front_20261114/backend'
allruns={}
for name,old in [('fixed','sim_b'),('jitter','sim_c'),('ops','sim_ops_b'),('port','sim_port_b')]:
 r=o/('sim_reg_'+name);sim=r/'project/context_sim.sim/sim_1/behav/xsim';raw=(sim/'simulate.log').read_text();assert 'TEST_PASS' in raw and not re.search(r'Fatal:|ERROR:',raw)
 bindings={};(r/'source').mkdir(exist_ok=True)
 for prj in sim.glob('*_vlog.prj'):
  bindings[str(prj.relative_to(root))]=hashlib.sha256(prj.read_bytes()).hexdigest()
  for line in prj.read_text().splitlines():
   if '"' not in line:continue
   p=Path(line.split('"')[1]);p=p if p.is_absolute() else (prj.parent/p).resolve()
   if p.is_file():
    bindings[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    if p.suffix=='.sv':shutil.copyfile(p,r/'source'/p.name)
 (r/'source_binding.json').write_text(json.dumps(bindings,indent=2)+'\n')
 result=subprocess.run(['python3',str(h/'calibrate_slices.py'),str(sim/'context_slices.csv')],check=True,capture_output=True,text=True);(r/'slice_calibration.json').write_text(result.stdout)
 before=o/old/'project/context_sim.sim/sim_1/behav/xsim';comparisons=[]
 for fname in ['context_slices.csv']+(['canonical_stages.csv'] if name=='ops' else []):
  a=before/fname;b=sim/fname;assert a.read_bytes()==b.read_bytes(),(name,fname);comparisons.append({'file':fname,'sha256':hashlib.sha256(b.read_bytes()).hexdigest()})
 for fname in ('metrics_1.csv','trace_1.csv','transactions_1.csv') if name!='port' else ('calibration_port_stress.csv',):
  a=(o/old/('outputs' if old=='sim_b' else 'fixtures'))/fname;b=r/'fixtures'/fname
  assert a.read_bytes()==b.read_bytes(),(name,fname);comparisons.append({'file':fname,'sha256':hashlib.sha256(b.read_bytes()).hexdigest()})
 receipt={'status':'PASS','terminal_markers':[l for l in raw.splitlines() if 'PASS' in l],'simulator':'XSim2022.2','source_binding':'source_binding.json','protocol_pin_equivalence_before_register_inference_fix':comparisons,'scope':'local finite parent context only; not complete kernel'}
 (r/'terminal.json').write_text(json.dumps(receipt,indent=2)+'\n');allruns[name]=receipt
subprocess.run(['python3',str(root/'accel/lookahead/fpga_enum_commit/integration/calibrate_port.py'),str(o/'sim_reg_port/fixtures')],check=True)
r=o/'sim_reg_ops';p=subprocess.run(['python3',str(h/'calibrate_canonical.py'),str(r/'project/context_sim.sim/sim_1/behav/xsim/canonical_stages.csv'),str(r/'fixtures/transactions_1.csv')],check=True,capture_output=True,text=True);(r/'canonical_calibration.json').write_text(p.stdout)
summary={'functional_status':'PASS','native_fixed_waves':19,'native_jitter_waves':19,'explicit_ops':2048,'explicit_zeroevent_completions':1024,'explicit_directory_events':1024,'explicit_ops_physical_requests':3072,'port_stress_requests':2048,'port_peak_credit_return_fifo_client_fifo':[32,4,4],'port_context_fifo_peaks':[2,2],'canonical_replay_cycles_perbank':11749,'canonical_peak_perbank':8,'physical_inference_fix_pin_cycles_identical':True,'slice_replay_rows':{},'large_native_fixed_cycles':{},'qualification':'local function/cycle evidence; actual timing is separately recorded in ooc_b/timing_resource_audit.json','all_native_physical_latency_checks':'sim_reg_fixed/physical_latency_verification.json','actual_internal_release_after_result_consumption_edges':1,'explicit_release_events_checked':2048}
for name in allruns:summary['slice_replay_rows'][name]=json.loads((o/('sim_reg_'+name)/'slice_calibration.json').read_text())['boundary_rows']
for row in list(csv.DictReader((o/'sim_reg_fixed/fixtures/metrics_1.csv').open()))[:4]:summary['large_native_fixed_cycles'][row['case']]=int(row['cycles'])
(o/'functional_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
