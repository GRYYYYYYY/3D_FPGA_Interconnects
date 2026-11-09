import subprocess,json,sys,os,struct,hashlib,time,socket
from prepare import sha256
from pathlib import Path
R=Path(__file__).resolve().parents[1];o=Path(sys.argv[1]);o.mkdir(exist_ok=True,parents=True)
paths=[R/'results/lookahead_accel_20261108T125500Z'/c/'workload.bin' for c in ['tseng_export','bnn_export']]
records=[]
for path in paths:
 with path.open('rb') as f:h=struct.unpack('<7Q',f.read(56))
 digest=sha256(path)
 manifest=json.loads((R/'results/lookahead_accel_round5_20261109T054024Z/evidence_snapshot/workload_manifest.json').read_text());entry=next(x for x in manifest if x['case']==path.parent.name)
 (o/(path.parent.name+'_preflight.json')).write_text(json.dumps(dict(path=str(path),sha256=digest,prior_manifest=entry,header=h,input_bytes=path.stat().st_size,fixed_scratch_8_workers_bytes=58*h[1]*8,conservative_scratch_with_dynamic_members_estimate_bytes=192*h[1]*8,budgets=dict(per_qid_raw_edges=500000000,per_qid_seconds=180,per_process_seconds=900,pending_entries_per_qid=4*h[1]+1),host=socket.gethostname(),cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text()),indent=2))
 for shift in [0,20]:
  name=f'{path.parent.name}_s{shift}';cmd=['/usr/bin/time','-v','/tmp/la_cpu6',str(path),str(shift),'8','1',str(o/(name+'.bin')),'1'];start=time.monotonic()
  with (o/(name+'.log')).open('w') as log:
   try:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=900);rc=p.returncode
   except subprocess.TimeoutExpired:rc=124
  records.append(dict(case=path.parent.name,shift=shift,command=cmd,returncode=rc,elapsed_s=time.monotonic()-start));(o/'runs.json').write_text(json.dumps(records,indent=2))
  print(records[-1],flush=True)
