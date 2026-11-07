"""Probe own existing notebooks via short-lived kernels; credentials stay in memory."""
import json,os,subprocess,uuid,time,sys
from pathlib import Path
from urllib.parse import urlsplit,parse_qs,urlunsplit
import requests,websocket
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_paper_closure_20261105/platform'
Q='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/bin/qz'
def access(n):
 env=dict(os.environ);env['NO_PROXY']=env.get('NO_PROXY','')+',qz.sii.edu.cn';env['no_proxy']=env['NO_PROXY']
 p=subprocess.run([Q,'notebook','GetNotebookAccessUrl','--data',json.dumps({'notebook_id':n})],env=env,capture_output=True,text=True,check=True)
 r=json.loads(p.stdout)['Result'];u=urlsplit(r['jupyter_url']);token=parse_qs(u.query)['token'][0]
 base=urlunsplit((u.scheme,u.netloc,u.path.rsplit('/lab',1)[0]+'/', '', ''))
 return base,token

def execute(n,code):
 base,token=access(n);s=requests.Session();s.trust_env=False;s.headers['Authorization']='token '+token
 # Read-only metadata first. No existing kernel/session is changed.
 z=s.get(base+'api/kernelspecs',timeout=30);z.raise_for_status();spec=z.json()['default']
 k=s.post(base+'api/kernels',json={'name':spec},timeout=30);k.raise_for_status();kid=k.json()['id'];ws=None
 try:
  u=urlsplit(base);url=urlunsplit(('wss' if u.scheme=='https' else 'ws',u.netloc,u.path+'api/kernels/'+kid+'/channels','',''))
  os.environ['NO_PROXY']=os.environ.get('NO_PROXY','')+','+u.hostname
  os.environ['no_proxy']=os.environ['NO_PROXY']
  ws=websocket.create_connection(url,header=['Authorization: token '+token],origin=u.scheme+'://'+u.netloc,timeout=45,http_no_proxy=[u.hostname])
  mid=uuid.uuid4().hex;msg={'header':{'msg_id':mid,'username':'native-paper-study','session':uuid.uuid4().hex,'date':'','msg_type':'execute_request','version':'5.3'},'parent_header':{},'metadata':{},'channel':'shell','content':{'code':code,'silent':False,'store_history':False,'user_expressions':{},'allow_stdin':False,'stop_on_error':True},'buffers':[]}
  ws.send(json.dumps(msg));parts=[];deadline=time.monotonic()+90
  while time.monotonic()<deadline:
   r=json.loads(ws.recv())
   if r.get('parent_header',{}).get('msg_id')!=mid:continue
   if r['msg_type']=='stream':parts.append(r['content']['text'])
   if r['msg_type']=='error':raise RuntimeError(r['content']['ename']+': '+r['content']['evalue'])
   if r['msg_type']=='status' and r['content']['execution_state']=='idle':return ''.join(parts)
  raise TimeoutError('Own kernel reply timeout')
 finally:
  if ws:ws.close()
  s.delete(base+'api/kernels/'+kid,timeout=30).raise_for_status()

def main():
 ids=['25889fa2-27d3-4e64-91e8-34874b073977','24b4a633-9ad2-4133-9174-cfc8cd109508','e6e06586-4338-4d74-8ecc-72bfa719011c','e83731d4-e90f-40b3-8089-5e8de292dbd1']
 for n in ids:
  code="""import json,os,socket,subprocess,time
from pathlib import Path
files=['/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/cpuset.cpus.effective','/sys/fs/cgroup/cpuset.cpus.exclusive.effective','/sys/fs/cgroup/memory.max']
r=dict(hostname=socket.gethostname(),affinity=sorted(os.sched_getaffinity(0)),files={p:Path(p).read_text() for p in files if Path(p).exists()},topology=subprocess.check_output(['lscpu','-p=CPU,CORE,SOCKET,NODE'],text=True),processes=subprocess.check_output(['ps','-eo','pid,comm,pcpu','--sort=-pcpu'],text=True),workspace=Path(ROOT).is_dir())
def stat():
 return {l.split()[0]:list(map(int,l.split()[1:])) for l in Path('/proc/stat').read_text().splitlines() if l.startswith('cpu')}
a=stat();time.sleep(2);b=stat();r['cpu_busy_fraction']={k:1-(b[k][3]-v[3]+b[k][4]-v[4])/max(1,sum(b[k][:8])-sum(v[:8])) for k,v in a.items()}
print(json.dumps(r))
""".replace('ROOT',repr(str(ROOT)))
  try:
   output=execute(n,code);r=json.loads(output);r['notebook_id']=n;(OUT/('existing_probe_'+n+'.json')).write_text(json.dumps(r,indent=2));print(n,r['hostname'],r['files'],r['processes'][:450],flush=True)
  except Exception as e:
   # URLs may contain credentials in client exception messages: only expose type.
   print(n,'probe_error',type(e).__name__,flush=True);(OUT/('existing_probe_'+n+'.error.json')).write_text(json.dumps({'error_type':type(e).__name__}))
if __name__=='__main__':main()
