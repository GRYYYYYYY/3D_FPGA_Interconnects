#!/usr/bin/env python3
"""One observer/launcher; observe the entire owned group and never restart EDA."""
import pathlib,subprocess,os,json,time,fcntl,signal,sys,datetime
R=pathlib.Path(sys.argv[1]).resolve()
def save(n,d):
 p=R/n;t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(d,indent=2));t.replace(p)
def identity(pid):
 p=pathlib.Path('/proc')/str(pid)
 try:
  s=(p/'stat').read_text().split(') ',1)[1].split()
  return dict(pid=pid,start_ticks=int(s[19]),state=s[0],pgid=int(s[2]),session=int(s[3]),cpu_ticks=int(s[11])+int(s[12]),rss_pages=int(s[21]),cmdline=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(),cwd=str((p/'cwd').resolve()),boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 except (OSError,ValueError):return None
def same(a,b):return bool(b) and all(a[k]==b[k] for k in ('pid','start_ticks','pgid','session','cmdline','cwd','boot_id'))
def group(pgid):
 members=[]
 for p in pathlib.Path('/proc').iterdir():
  if p.name.isdigit():
   item=identity(int(p.name))
   if item and item['pgid']==pgid:members.append(item)
 return members
def owned_group(owner,members):
 return owner['pgid']==owner['pid'] and all(m['session']==owner['session'] and m['boot_id']==owner['boot_id'] and pathlib.Path(m['cwd']).is_relative_to(R) for m in members)
def main():
 lock=(R/'supervisor.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 budget=json.loads((R/'budget.json').read_text());save('supervisor_identity.json',identity(os.getpid()))
 save('recovery.json',{'command':['python3',str(pathlib.Path(__file__).resolve()),str(R)],'policy':'Resume the unique observer under flock; never launch again if worker_identity exists. Preserve original deadlines. Entire process group checked before declaring exit. Sole final publisher remains terminal_publisher.py.','luna_available':False})
 worker=None;owner=json.loads((R/'worker_identity.json').read_text()) if (R/'worker_identity.json').exists() else None
 while True:
  now=time.time()
  if (R/'close_supervisor.json').exists() and not owner:
   save('supervisor_terminal.json',{'state':'PRECHECK_TERMINAL','utc':now});break
  if not owner and (R/'READY.json').exists() and now<budget['compute_deadline_epoch']:
   cmd=json.loads((R/'READY.json').read_text())['command'];log=(R/'worker_console.log').open('ab')
   worker=subprocess.Popen(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   time.sleep(.2);owner=identity(worker.pid)
   if not owner:raise RuntimeError('Launcher exited before identity capture; inspect console, do not retry')
   owner['command']=cmd;save('worker_identity.json',owner)
  live=identity(owner['pid']) if owner else None
  members=group(owner['pgid']) if owner else []
  active=[m for m in members if m['state']!='Z']
  verified=owned_group(owner,active) if owner else False
  save('heartbeat.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observer':identity(os.getpid()),'worker':live,'owned_group_members':members,'group_identity_verified':verified,'group_cpu_ticks':sum(m['cpu_ticks'] for m in members),'group_rss_pages':sum(m['rss_pages'] for m in members),'compute_deadline_epoch':budget['compute_deadline_epoch'],'stage':(R/'stage.txt').read_text() if (R/'stage.txt').exists() else 'PRECHECK','last_complete_dcp':[str(p) for p in R.glob('*.dcp.sha256')],'whole_task_complete':False})
  if owner and not active:
   rc=worker.wait() if worker else None
   if rc is None and (R/'vivado_exit.json').exists():rc=json.loads((R/'vivado_exit.json').read_text())['returncode']
   save('worker_exit.json',{'returncode':rc,'utc':now,'active_owned_processes':[],'remaining_zombies':members,'requires_terminal_audit':True})
   save('supervisor_terminal.json',{'state':'OWNED_PROCESS_GROUP_EXITED','utc':now});break
  if owner and (not same(owner,live) or not verified):
   save('supervisor_anomaly.json',{'utc':now,'reason':'Launcher identity lost or group contains unverified members; do not infer completion or signal group','members':members})
  if now>=budget['compute_deadline_epoch']:
   if active:
    can_signal=verified and same(owner,live)
    if can_signal and not (R/'stop_requested.json').exists():
     # Revalidate the root and every currently observed member immediately before signalling.
     check=group(owner['pgid']);can_signal=owned_group(owner,check) and same(owner,identity(owner['pid'])) and all(same(m,identity(m['pid'])) for m in check)
     if can_signal:
      save('stop_requested.json',{'utc':now,'members':check,'signal':'SIGINT','reason':'22h compute cutoff; preserve last complete DCP; no remote stop API for blocking batch Tcl'})
      os.killpg(owner['pgid'],signal.SIGINT)
    save('budget_state.json',{'state':'STOP_REQUESTED_NOT_CONFIRMED','verified':can_signal,'active_owned_processes':active})
   else:
    save('budget_state.json',{'state':'BUDGET_EXHAUSTED','active_owned_processes':[]});break
  time.sleep(60)
if __name__=='__main__':main()
