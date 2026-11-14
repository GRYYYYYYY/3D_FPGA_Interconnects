"""Temporarily suspend only this round's identified EDA tree for CPU timing.
The same processes resume in finally; no experiment is restarted.
"""
from pathlib import Path
import os,signal,json,subprocess,time,datetime
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_descriptor_front_20261114';rec=json.loads((R/'services_memory_synth/running.json').read_text());pid=rec['pid']
def stat(p):
 s=Path(f'/proc/{p}/stat').read_text().rsplit(')',1)[1].split();return {'pid':p,'ppid':int(s[1]),'start_ticks':int(s[19]),'state':s[0],'ticks':int(s[11])+int(s[12])}
def scan():
 d={}
 for p in Path('/proc').glob('[0-9]*'):
  try:d[int(p.name)]=stat(int(p.name))
  except (FileNotFoundError,ProcessLookupError):pass
 return d
a=stat(pid);assert str(a['start_ticks'])==str(rec['process_start_ticks']);assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==rec['boot_id']
paused=[];log={'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'same EDA process tree suspended in memory; no CPU competition; no restart; resident EDA memory remains','root':a,'commands':[]}
def stop_handler(signum,frame):raise SystemExit(signum)
for sig in [signal.SIGTERM,signal.SIGHUP,signal.SIGINT]:signal.signal(sig,stop_handler)
try:
 os.kill(pid,signal.SIGSTOP);paused.append(a)
 d=scan();ids={pid}
 while True:
  new={p for p,s in d.items() if s['ppid'] in ids}-ids
  if not new:break
  ids|=new
 for p in sorted(ids-{pid}):
  s=stat(p)
  if s['state']!='Z':os.kill(p,signal.SIGSTOP);paused.append(s)
 time.sleep(1)
 for s in paused:assert stat(s['pid'])['state'] in ['T','t']
 log['suspended']=paused;(R/'isolated_window.json').write_text(json.dumps(log,indent=2)+'\n')
 for script,args in [('formal.py',['--isolated-window']),('measure_construction.py',[])]:
  cmd=['python3',str(Path(__file__).with_name(script)),*args];start=time.monotonic()
  result=subprocess.run(cmd,cwd=ROOT);log['commands'].append({'command':cmd,'returncode':result.returncode,'wall_seconds':time.monotonic()-start});assert result.returncode==0
finally:
 log['paused_ticks_after']=[stat(s['pid']) for s in paused if Path(f'/proc/{s["pid"]}').exists()]
 log['resumed']=[]
 for s in reversed(paused):
  try:
   if stat(s['pid'])['start_ticks']==s['start_ticks']:os.kill(s['pid'],signal.SIGCONT);log['resumed'].append(s['pid'])
  except (FileNotFoundError,ProcessLookupError):pass
 log['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(R/'isolated_window.json').write_text(json.dumps(log,indent=2)+'\n')
print('QUIET_WINDOW_FINISHED_ORIGINAL_EDA_RESUMED')
