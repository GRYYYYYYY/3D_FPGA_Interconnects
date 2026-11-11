#!/usr/bin/env python3
import pathlib,subprocess,json,time
root=pathlib.Path(__file__).resolve().parents[4];out=root/'results/fpga_sim_restart_20261111T231000Z/replay';out.mkdir(exist_ok=True)
inputs=json.loads((root/'accel/lookahead/fpga_sim_restart/config/inputs.json').read_text())
for row in inputs:
 for f in ['F0','F1']:
  name=row['case']+'_'+f
  cmd=[str(out.parent/'cache_replay'),row['path'],'64',f,str(out/(name+'.bin'))]
  t=time.time()
  with (out/(name+'.jsonl')).open('w') as stdout,(out/(name+'.stderr')).open('w') as stderr:
   run=subprocess.run(cmd,stdout=stdout,stderr=stderr)
  (out/(name+'.receipt.json')).write_text(json.dumps({'command':cmd,'returncode':run.returncode,'software_replay_wall_s_not_fpga_time':time.time()-t,'status':'functional_transaction_replay_only'},indent=2))
  if run.returncode:raise SystemExit(run.returncode)
