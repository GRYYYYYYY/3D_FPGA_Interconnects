"""Native complete-batch transform check against read-only original ALT outputs."""
from pathlib import Path
import argparse,concurrent.futures,csv,gzip,hashlib,json,shutil,subprocess,time
root=Path(__file__).resolve().parents[4];s=root/'accel/lookahead/fpga_sparse_stream_r2';r=root/'results/fpga_sparse_stream_r2_20261112/semantics'
old=root.parent/'3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def run(case):
 out=r/case['case'];out.mkdir(exist_ok=False)
 binary=r/'reference_pop_reduce';gold=old/f"replay/{case['case']}_F1.bin"
 args=[str(binary),case['path'],str(gold),str(out),'524288','524288']
 if case['header'][1]>4096:args+=['--no-prepared-export']
 source=out/'reference_pop_reduce.cpp';shutil.copy2(s/'reference_pop_reduce.cpp',source)
 start=time.time()
 with open(out/'console.log','w') as log:done=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT)
 receipt={'command':args,'returncode':done.returncode,'source_sha256':sha(source),'executable_sha256':sha(binary),'workload_sha256':sha(Path(case['path'])),'golden_sha256':sha(gold),'wall_seconds':time.time()-start,'scope':'functional verification, not FPGA or CPU performance'}
 assert receipt['workload_sha256']==case['sha256']
 if done.returncode==0:
  receipt['output_sha256']=sha(out/'output.bin');assert receipt['output_sha256']==receipt['golden_sha256']
  with gzip.open(root/f"results/fpga_sparse_stream_20261112/evidence_snapshot/{case['case']}/waves.csv.gz",'rt') as f:prior=list(csv.DictReader(f))
  new=list(csv.DictReader(open(out/'waves.csv')));assert len(prior)==len(new)
  for a,b in zip(prior,new):assert all(a[k]==b[k] for k in a),(case['case'],a,b)
  receipt['all_R1_per_wave_work_and_capacity_counts_exact']=True
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(case['case'],done.returncode,flush=True)
 if done.returncode:raise RuntimeError((out/'console.log').read_text())
 return receipt
if __name__=='__main__':
 inputs=json.loads((root/'accel/lookahead/fpga_sim_restart/config/inputs.json').read_text())
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,inputs))
 (r/'native_complete.json').write_text(json.dumps(results,indent=2)+'\n')
