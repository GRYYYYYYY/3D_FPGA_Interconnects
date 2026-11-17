#!/usr/bin/env python3
"""User-authorized suspension; observer NEVER resumes, terminates or launches EDA."""
import pathlib,os,sys,json,time,signal,fcntl,hashlib,subprocess,datetime
R=pathlib.Path(sys.argv[2]).resolve()
HERE=pathlib.Path(__file__).resolve().parent
KEYS=('pid','start_ticks','pgid','session','cmdline','cwd','boot_id')
def save(p,x):
 p=pathlib.Path(p);q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def ident(pid):
 try:
  p=pathlib.Path('/proc')/str(pid);s=(p/'stat').read_text().rsplit(') ',1)[1].split()
  return dict(pid=pid,start_ticks=int(s[19]),pgid=int(s[2]),session=int(s[3]),state=s[0],cpu_ticks=int(s[11])+int(s[12]),rss_pages=int(s[21]),cmdline=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(),cwd=os.readlink(p/'cwd'),boot_id=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 except (OSError,ValueError):return None
def same(a,b):return b and all(a[k]==b[k] for k in KEYS)
def group(g):return [i for p in pathlib.Path('/proc').iterdir() if p.name.isdigit() and (i:=ident(int(p.name))) and i['pgid']==g]
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def snapshot(owner):
 m=group(owner['pgid']);threads={}
 for i in m:
  threads[str(i['pid'])]=[{'tid':int(p.name),'state':(p/'stat').read_text().rsplit(') ',1)[1].split()[0]} for p in (pathlib.Path('/proc')/str(i['pid'])/'task').iterdir()]
 return dict(epoch=time.time(),members=m,threads=threads,cpu_ticks=sum(i['cpu_ticks'] for i in m),rss_bytes=sum(i['rss_pages'] for i in m)*os.sysconf('SC_PAGE_SIZE'))
def owned(owner,m):return bool(m) and same(owner,ident(owner['pid'])) and owner['pgid']==owner['pid'] and owner['pgid']!=os.getpgrp() and all(i['session']==owner['session'] and i['boot_id']==owner['boot_id'] and pathlib.Path(i['cwd']).is_relative_to(R) for i in m)
def stopped(s):return bool(s['members']) and all(i['state'] in ('T','t','Z') for i in s['members']) and all(t['state'] in ('T','t','Z') for ts in s['threads'].values() for t in ts)
def observe():
 locks=[]
 for n in ('supervisor','publisher'):
  f=(R/(n+'.lock')).open('a');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 me=ident(os.getpid());code=sha(__file__);owner=json.loads((R/'worker_identity.json').read_text());budget=json.loads((R/'budget.json').read_text())
 save(R/'pause_observer_identity.json',dict(identity=me,code_sha256=code,locks=['supervisor.lock','publisher.lock']))
 for n in ('supervisor','publisher'):save(R/(n+'_identity.json'),me)
 while True:
  s=snapshot(owner);state='PAUSED_BY_USER' if stopped(s) and owned(owner,s['members']) else 'PAUSE_REQUESTED_NOT_CONFIRMED'
  if state=='PAUSED_BY_USER' and time.time()>budget['compute_deadline_epoch']:state='PAUSED_BY_USER_BUDGET_DECISION_REQUIRED'
  if not s['members']:state='OBSERVED_GROUP_ABSENT_REQUIRES_USER_REVIEW'
  h=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),state=state,observer=me,loaded_code_sha256=code,snapshot=s,original_compute_deadline_epoch=budget['compute_deadline_epoch'],auto_resume_allowed=False,budget_signals_allowed=False,terminal_publication_allowed=False,whole_task_complete=False,last_complete_dcp=[str(p) for p in R.glob('*.dcp.sha256')])
  save(R/'pause_heartbeat.json',h);save(R/'heartbeat.json',h);save(R/'publisher_heartbeat.json',h)
  time.sleep(60)
def apply():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=R/('pause_receipt_'+stamp);out.mkdir();owner=json.loads((R/'worker_identity.json').read_text());before=snapshot(owner);assert owned(owner,before['members'])
 assert not (R/'publisher_invocation.json').exists(),'Existing auditor must be reconciled'
 controllers=[]
 for n in ('supervisor','publisher'):
  old=json.loads((R/(n+'_identity.json')).read_text());live=ident(old['pid']);assert live and all(old[k]==live[k] for k in ('pid','start_ticks','pgid','boot_id','cmdline'))
  assert pathlib.Path(live['cwd'])==R and live['session']==live['pgid']==live['pid'] and len(group(live['pgid']))==1
  assert ('/supervise.py ' if n=='supervisor' else '/terminal_publisher.py ') in live['cmdline'];controllers.append(live)
 save(out/'before.json',dict(compute=before,controllers=controllers))
 for n in ['budget.json','heartbeat.json','publisher_heartbeat.json','supervisor_identity.json','publisher_identity.json','worker_identity.json','stage.txt','stages.txt']:
  if (R/n).exists():(out/n).write_bytes((R/n).read_bytes())
 protected={str(p.relative_to(R)):sha(p) for p in [R/'budget.json',R/'flow_binding.json',R/'source_binding.json',*sorted((R/'source').glob('*'))] if p.is_file()}
 save(out/'protected_before.json',protected)
 override=dict(task='CPU_GPU_PAPER_FIRST_GEMM_BNN_V2',utc=stamp,state='PAUSE_REQUESTED',original_budget_sha256=sha(R/'budget.json'),original_budget=json.loads((R/'budget.json').read_text()),auto_resume_allowed=False,old_deadline_interrupt_allowed=False,terminal_publication_allowed=False,whole_task_complete=False,pause_receipt=str(out))
 save(R/('software_priority_override_'+stamp+'.json'),override);save(R/'software_priority_override.json',override)
 for c in controllers:
  assert same(c,ident(c['pid']));fd=os.pidfd_open(c['pid']);assert same(c,ident(c['pid']));signal.pidfd_send_signal(fd,signal.SIGTERM);os.close(fd)
 for _ in range(50):
  if all(not ident(c['pid']) or ident(c['pid'])['state']=='Z' for c in controllers):break
  time.sleep(.1)
 assert all(not ident(c['pid']) or ident(c['pid'])['state']=='Z' for c in controllers)
 log=(R/'pause_observer.log').open('ab');p=subprocess.Popen([sys.executable,str(pathlib.Path(__file__).resolve()),'observe',str(R)],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 for _ in range(50):
  if (R/'pause_observer_identity.json').exists():break
  time.sleep(.1)
 new=json.loads((R/'pause_observer_identity.json').read_text());assert new['identity']['pid']==p.pid and new['code_sha256']==sha(__file__)
 m=group(owner['pgid']);assert owned(owner,m) and all(same(i,ident(i['pid'])) for i in m)
 os.killpg(owner['pgid'],signal.SIGSTOP)
 samples=[]
 for _ in range(3):time.sleep(2);samples.append(snapshot(owner))
 confirmed=all(stopped(s) for s in samples) and len({s['cpu_ticks'] for s in samples})==1
 dcps=[]
 for receipt in sorted(R.glob('*.dcp.sha256')):
  parts=receipt.read_text().split();p=R/receipt.name.removesuffix('.sha256');actual=sha(p);assert actual==parts[0];assert p.stat().st_size==int(parts[1]);dcps.append(dict(path=str(p),bytes=p.stat().st_size,sha256=actual))
 assert all(sha(R/n)==h for n,h in protected.items())
 mem={n:(pathlib.Path('/sys/fs/cgroup')/n).read_text() for n in ['memory.current','memory.max','memory.swap.current','memory.swap.max','cpu.max']};mem['host']=pathlib.Path('/proc/meminfo').read_text()
 result=dict(state='PAUSED_BY_USER' if confirmed else 'PAUSE_REQUESTED_NOT_CONFIRMED',samples=samples,new_controller=new,old_controllers_exited=True,complete_dcps=dcps,protected_unchanged=True,memory=mem,elapsed_wall_seconds=time.time()-override['original_budget']['start_epoch'],compute_cpu_seconds=samples[-1]['cpu_ticks']/os.sysconf('SC_CLK_TCK'),whole_task_complete=False,auto_resume_allowed=False)
 save(out/'verification.json',result);save(R/'pause_receipt.json',dict(directory=str(out),**result))
 for f in out.iterdir():
  if f.is_file():(HERE/f.name).write_bytes(f.read_bytes())
 print(json.dumps(dict(state=result['state'],receipt=str(out),observer=p.pid,cpu_ticks=[s['cpu_ticks'] for s in samples],rss_bytes=samples[-1]['rss_bytes']),indent=2))
if __name__=='__main__':
 {'apply':apply,'observe':observe}[sys.argv[1]]()
