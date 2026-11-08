import json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
name,top,engines=sys.argv[1:]
hls=root/('hls_'+name)
receipt=root/('bounded_'+name+'_pending.json')
assert not receipt.exists()
cmd=[sys.executable,str(root.parents[1]/'scripts/la_accel_bounded3.py'),'--hls',str(hls),'--output',str(root/('bounded_'+name)),'--top',top,'--engines',engines,'--timeout','21600','--minimal-debug']
receipt.write_text(json.dumps({'status':'waiting_for_cosim','command':cmd},indent=2))
while not (hls/'cosim.json').exists():
 try:
  state=json.loads((hls/'supervisor.json').read_text())
  if state.get('status')=='failed':raise RuntimeError('HLS predecessor failed')
 except json.JSONDecodeError:pass
 time.sleep(5)
assert json.loads((hls/'cosim.json').read_text())['status']=='passed'
receipt.write_text(json.dumps({'status':'running','command':cmd},indent=2))
result=subprocess.run(cmd)
receipt.write_text(json.dumps({'status':'passed' if result.returncode==0 else 'failed','command':cmd,'returncode':result.returncode},indent=2))
sys.exit(result.returncode)
