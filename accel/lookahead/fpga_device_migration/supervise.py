#!/usr/bin/env python3
"""One flock-protected observer/launcher. Never restarts EDA or signals other jobs."""
import pathlib,subprocess,os,json,time,fcntl,signal,sys,datetime
R=pathlib.Path(sys.argv[1]).resolve()
def save(n,d):
 p=R/n; t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(d,indent=2));t.replace(p)
def identity(pid):
 p=pathlib.Path('/proc')/str(pid)
 try:
  s=(p/'stat').read_text().split(') ',1)[1].split()
  return dict(pid=pid,start_ticks=int(s[19]),state=s[0],pgid=int(s[2]),session=int(s[3]),cpu_ticks=int(s[11])+int(s[12]),rss_pages=int(s[21]),cmdline=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(),cwd=str((p/'cwd').resolve()),boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 except (OSError,ValueError): return None
def same(a,b): return b and all(a[k]==b[k] for k in ('pid','start_ticks','pgid','session','cmdline','cwd','boot_id'))
lock=(R/'supervisor.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
budget=json.loads((R/'budget.json').read_text());save('supervisor_identity.json',identity(os.getpid()))
save('recovery.json',{'command':['python3',str(pathlib.Path(__file__).resolve()),str(R)],'policy':'Resume observer only; worker_identity prevents duplicate launch. Original budget retained. No automatic EDA retry. Main Codex owns interpretation and publication.','luna_available':False})
worker=None;owned=None
if (R/'worker_identity.json').exists(): owned=json.loads((R/'worker_identity.json').read_text())
while True:
 now=time.time()
 if (R/'close_supervisor.json').exists() and not owned:
  save('supervisor_terminal.json',{'state':'PRECHECK_TERMINAL','utc':now});break
 if not owned and (R/'READY.json').exists() and now<budget['compute_deadline_epoch']:
  ready=json.loads((R/'READY.json').read_text());cmd=ready['command']
  log=(R/'worker_console.log').open('ab')
  worker=subprocess.Popen(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  owned=identity(worker.pid);owned['command']=cmd;save('worker_identity.json',owned)
 live=identity(owned['pid']) if owned else None
 save('heartbeat.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observer':identity(os.getpid()),'worker':live,'compute_deadline_epoch':budget['compute_deadline_epoch'],'stage':(R/'stage.txt').read_text() if (R/'stage.txt').exists() else 'PRECHECK','last_complete_dcp':[str(p) for p in R.glob('*.dcp.sha256')],'whole_task_complete':False})
 if owned and (not same(owned,live) or live['state']=='Z'):
  rc=worker.wait() if worker else None
  save('worker_exit.json',{'returncode':rc,'utc':now,'active_owned_processes':[],'requires_terminal_audit':True})
  save('supervisor_terminal.json',{'state':'WORKER_EXITED','utc':now});break
 if now>=budget['compute_deadline_epoch']:
  if owned and same(owned,live):
   # Independently created process group; verify every group member belongs to this run cwd.
   members=[identity(int(p.name)) for p in pathlib.Path('/proc').iterdir() if p.name.isdigit()]
   members=[p for p in members if p and p['pgid']==owned['pgid']]
   verified=owned['pgid']==owned['pid'] and all(p['cwd'].startswith(str(R)) for p in members)
   if verified and not (R/'stop_requested.json').exists():
    save('stop_requested.json',{'utc':now,'members':members,'signal':'SIGINT','reason':'22h compute budget; blocking batch Tcl has no remote stop API. Keep prior complete checkpoint.'});os.killpg(owned['pgid'],signal.SIGINT)
   save('budget_state.json',{'state':'STOP_REQUESTED_NOT_CONFIRMED','verified':verified,'active_owned_processes':members})
  else:
   save('budget_state.json',{'state':'BUDGET_EXHAUSTED','active_owned_processes':[]});break
 time.sleep(60)
