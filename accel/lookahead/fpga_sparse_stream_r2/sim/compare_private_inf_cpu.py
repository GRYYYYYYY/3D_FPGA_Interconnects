"""Same-host paired CPU control, independently labeled from the H100-worker baseline."""
from pathlib import Path
import datetime,json,os,socket,subprocess,time
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';o=r/'software/private_inf_local_a'
cpus=[];keys=set()
for cpu in sorted(os.sched_getaffinity(0)):
 p=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology');key=((p/'physical_package_id').read_text(),(p/'core_id').read_text())
 if key not in keys:keys.add(key);cpus.append(cpu)
 if len(cpus)==8:break
os.sched_setaffinity(0,cpus)
(o/'environment.json').write_text(json.dumps({'host':socket.gethostname(),'affinity':cpus,'scope':'same local host sequential controls under concurrent FPGA tasks; not a replacement of H100 CPU numbers','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
for x in json.loads((r/'semantics/native_complete.json').read_text()):
 c=x['command'];case=Path(c[3]).name
 for name in ['cpu_prepared_pop','cpu_private_inf']:
  cmd=[str(o/name),c[1],c[2],'local_p0','8','4'];start=time.time()
  with (o/(case+'_'+name+'.jsonl')).open('x') as f,(o/(case+'_'+name+'.stderr')).open('x') as err:rc=subprocess.run(cmd,stdout=f,stderr=err).returncode
  (o/(case+'_'+name+'_receipt.json')).write_text(json.dumps({'command':cmd,'returncode':rc,'elapsed_seconds':time.time()-start},indent=2)+'\n');assert rc==0
(o/'terminal.json').write_text(json.dumps({'all_pass':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
