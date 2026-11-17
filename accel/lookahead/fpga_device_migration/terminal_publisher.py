#!/usr/bin/env python3
"""Persistent single publisher entry: invoke substantive Codex audit on terminal/budget.
No EDA launch, recovery or publication is inferred merely from a heartbeat.
"""
import pathlib,sys,os,time,json,fcntl,subprocess,datetime
r=pathlib.Path(sys.argv[1]).resolve();root=r.parents[2]
def save(name,value):
 p=r/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(value,indent=2));t.replace(p)
def ident(pid):
 p=pathlib.Path('/proc')/str(pid);s=(p/'stat').read_text().split(') ',1)[1].split()
 return {'pid':pid,'start_ticks':int(s[19]),'pgid':os.getpgid(pid),'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'cmdline':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode()}
lock=(r/'publisher.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
save('publisher_identity.json',ident(os.getpid()));b=json.loads((r/'budget.json').read_text())
while True:
 now=time.time();terminal=(r/'worker_exit.json').exists() or (r/'budget_state.json').exists()
 save('publisher_heartbeat.json',{'utc':now,'state':'WAITING_FOR_TERMINAL_OR_BUDGET','terminal_seen':terminal,'enabled':(r/'PUBLISHER_ENABLED').exists(),'whole_task_complete':False})
 if (r/'PUBLISHER_ENABLED').exists() and (terminal or now>=b['compute_deadline_epoch']):break
 time.sleep(60)
if (r/'publisher_invocation.json').exists():
 save('publisher_error.json',{'reason':'A prior audit invocation exists; no duplicate publisher. Inspect its process/session and resume that owner.'});sys.exit(2)
cmd=['/inspire/hdd/global_user/guoruiyuan-253208540291/codex/bin/codex','exec','-C',str(root),'-s','danger-full-access','-c','approval_policy="never"','--json','-o',str(r/'publisher_final_message.txt'),'-']
with (r/'publisher_agent.jsonl').open('ab') as log, (root/'accel/lookahead/fpga_device_migration/terminal_prompt.txt').open('rb') as prompt:
 p=subprocess.Popen(cmd,stdin=prompt,stdout=log,stderr=subprocess.STDOUT,cwd=root,start_new_session=True)
 time.sleep(.2);save('publisher_invocation.json',{'command':cmd,'identity':ident(p.pid),'utc':time.time(),'role':'sole final auditor and publisher; inherits configured main model; no second experiment'})
 rc=p.wait()
save('publisher_exit.json',{'returncode':rc,'utc':time.time(),'completion_requires_remote_receipt':True})
