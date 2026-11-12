"""Wait for a running complete RTL suite, then calibrate before full batches.

This deterministic gate never treats elapsed time or partial fixtures as a pass.
An explicit producer failure aborts; no automatic change to hardware/parameters.
"""
from pathlib import Path
import datetime, json, subprocess, sys, time

root=Path(__file__).resolve().parents[4]
s=root/'accel/lookahead/fpga_sparse_stream_r2/sim'
r=root/'results/fpga_sparse_stream_r2_20261112'
model,rtl=sys.argv[1:3]
receipt=r/'model'/model/'complete_run_gate.json'
if receipt.exists():raise RuntimeError('gate already exists; inspect before resuming')
suffixes=['native_l60','fixtures_l60','stress,stress_random_l120','external_nodes_65536,external_nodes_4194304_l60']
state={'model':model,'RTL':rtl,'status':'waiting_for_complete_RTL','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':[]}
def save():receipt.write_text(json.dumps(state,indent=2))
save()
while True:
 paths=[r/'rtl'/f'{rtl}_{x}'/'summary.json' for x in suffixes]
 present=[json.loads(p.read_text()) for p in paths if p.exists()]
 if any(not x['all_pass'] for x in present):
  state['status']='failed_RTL_reference';save();raise RuntimeError(state['status'])
 if len(present)==4:
  if sum(len(x['results']) for x in present)!=97:raise RuntimeError('wrong suite count')
  break
 time.sleep(5)
for name,cmd in [('calibrating',[sys.executable,str(s/'calibrate_many_suites.py'),model,rtl]),
                 ('running_complete_native_batches',[sys.executable,str(s/'run_large_model.py'),model,'60','2'])]:
 state['status']=name;state['commands'].append(cmd);save()
 rc=subprocess.run(cmd,cwd=root).returncode
 if rc:
  state.update(status='failed_'+name,returncode=rc);save();sys.exit(rc)
state.update(status='passed_complete_batches',ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save()
