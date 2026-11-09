"""Single-owner bounded follow-up after a failed oversized DLA control."""
import os,sys,time,json,signal,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();pid=int(sys.argv[2]);deadline=time.monotonic()+180
# Wait for the registered DLA control timeout to be reaped by its owner.
while not (r/'native/runs.json').exists():
 if time.monotonic()>deadline:raise RuntimeError('control has not returned; no blind cancellation')
 time.sleep(2)
rows=json.load(open(r/'native/runs.json'))
if rows[0]['case']!='dla_like.medium' or rows[0]['returncode']==0:raise RuntimeError('unexpected control result; review before cancellation')
def children(pid):
 p=Path(f'/proc/{pid}/task/{pid}/children');return [int(x) for x in p.read_text().split()] if p.exists() else []
targets=children(pid)+[pid];receipt=[]
for p in targets:
 f=Path(f'/proc/{p}/cmdline')
 if not f.exists():continue
 cmd=f.read_bytes().replace(b'\0',b' ').decode();assert str(r.relative_to(R)) in cmd or str(r) in cmd,(p,cmd)
 receipt.append(dict(pid=p,command=cmd));os.kill(p,signal.SIGTERM)
time.sleep(2)
for x in receipt:
 p=x['pid']
 if Path(f'/proc/{p}/cmdline').exists() and Path(f'/proc/{p}/cmdline').read_bytes():os.kill(p,signal.SIGKILL)
(r/'native/oversized_control_stop.json').write_text(json.dumps(dict(reason='DLA control exhausted its 600-second qualification budget. No valid pair; stop its dependent ALT arm. DLA is larger than BNN, so required small3D screen uses frozen s38417 instead. Failed control retained.',processes=receipt),indent=2))
cmd=['python3',str(R/'scripts/la_accel_round6_native.py'),str(r/'native_required')]
with (r/'native_required.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=2500)
(r/'native_required_exit.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode)))
