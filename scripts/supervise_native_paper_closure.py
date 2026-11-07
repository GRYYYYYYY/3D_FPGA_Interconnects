"""Single read-only monitor; run terminal reports once, never submit or retry solvers."""
import fcntl,json,subprocess,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_paper_closure_20261105'
def read(p):return json.loads(p.read_text())
def save(p,x):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2));t.replace(p)
lock=(OUT/'supervisor.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
state=dict(pid=os.getpid(),status='monitoring',solver_retries=False,remote_pid=2086391,remote_notebook='24b4a633-9ad2-4133-9174-cfc8cd109508',started=time.time());save(OUT/'supervisor.json',state)
last=None
while True:
 s=read(OUT/'scaling/summary.json');rows=s['measurements'];key=(s['status'],len(rows),sum(r.get('component_valid',False) for r in rows))
 if key!=last:
  print(json.dumps(dict(status=key[0],attempted=key[1],valid=key[2],current=rows[-1]['key'] if rows else None)),flush=True);last=key
 state.update(last_check=time.time(),remote_status=s['status'],attempted=len(rows),valid=key[2]);save(OUT/'supervisor.json',state)
 if s['status']!='running':break
 time.sleep(30)
with (OUT/'scaling/terminal_report.log').open('w') as log:
 p=subprocess.run(['/usr/bin/python3',str(ROOT/'scripts/report_native_cpu_allocated_scaling.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
state.update(status='terminal_report_ready' if p.returncode==0 else 'report_failed',remote_terminal=s['status'],report_returncode=p.returncode,finished=time.time(),main_model_review_required=True);save(OUT/'supervisor.json',state);print(json.dumps(state),flush=True)
