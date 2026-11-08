import json,subprocess,time,re,os
from pathlib import Path
root=Path(__file__).resolve().parent
repo=root.parents[1]
names=['full_1','full_4','early_1','early_4'];processes={};state={}
while True:
 for name in names:
  h=root/('hls_'+name);receipt=h/'cosim.json'
  if name not in state and receipt.exists():
   if json.loads(receipt.read_text())['status']!='passed':state[name]={'status':'failed_cosim'};continue
   rpt=h/'project/solution/sim/verilog/lookahead_onchip4.performance.result.transaction.xml'
   cycles=[int(x) for x in re.findall(r'transaction\s+\d+:\s+(\d+)',rpt.read_text())];assert len(cycles)==12
   # All four fixed candidates are required matched architecture/algorithm controls.
   # Huge external-full cycle reduction and <25% estimated device BRAM justify one implementation each.
   state[name]={'status':'followups_running','rtl_cycles':cycles,'reason':'Required matched full/early single/four controls; no engine/capacity/frequency sweep.'}
   for kind,cmd in [('impl',['python3',str(repo/'scripts/la_accel_hls4.py'),'--output',str(h),'--resume','--phases','impl']),('monitor',['python3',str(repo/'scripts/la_accel_monitor4.py'),'--hls',str(h),'--output',str(root/('monitor_'+name))])]:
    log=(root/(name+'_'+kind+'_driver.log')).open('w');processes[(name,kind)]=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=repo);log.close()
 for (name,kind),p in processes.items():
  rc=p.poll()
  if rc is not None:state[name][kind+'_exit']=rc
 (root/'followup_supervisor.json').write_text(json.dumps(state,indent=2)+'\n')
 if len(state)==len(names) and all(p.poll() is not None for p in processes.values()):break
 time.sleep(20)
