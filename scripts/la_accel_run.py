"""Run resident backends with hashes, fresh outputs, command logs and explicit evidence types."""
import argparse,json,subprocess,os,time
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=Path,required=True);p.add_argument('--workload',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--backend',choices=['cpu','cuda','hls-c'],required=True);p.add_argument('--repeats',type=int,default=3);p.add_argument('--contexts',type=int,default=1);p.add_argument('--workers',type=int,default=1);p.add_argument('--timeout',type=int,default=600);a=p.parse_args();assert a.repeats>0;o=a.output.resolve();o.mkdir(parents=True,exist_ok=False)
 fields=['core_cycles','implemented_frequency_hz','resident_elapsed_s','host_service_elapsed_s','h2d_bytes','d2h_bytes','external_memory_bytes','pushes','pops','edge_visits','peak_queue_entries','output_sha256','matches_reference','memory_model_config','implementation_report','failure_reason','gpu_model','fpga_part']
 records=[]
 for i in range(a.repeats):
  output=o/f'output_{i}.bin';cmd=[str(a.binary.resolve()),str(a.workload.resolve()),str(output)]+([str(a.contexts)] if a.backend=='cuda' else [str(a.workers)] if a.backend=='cpu' else []);start=time.time()
  record={k:None for k in fields};record.update(schema_version='la_accel_v1',run_id=f'{o.name}_{i}',backend=a.backend,semantic_mode='STRICT_FP32',timing_scope='resident_flood_batch',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip(),binary_sha256=sha256(a.binary),workload_sha256=sha256(a.workload),command=cmd,cpu_affinity=sorted(os.sched_getaffinity(0)),cpu_workers=a.workers if a.backend=='cpu' else None,contexts=a.contexts,status='failed')
  try:
   r=subprocess.run(cmd,text=True,capture_output=True,timeout=a.timeout);(o/f'run_{i}.stdout').write_text(r.stdout);(o/f'run_{i}.stderr').write_text(r.stderr);record['returncode']=r.returncode
   if r.returncode==0:
    measurements=[json.loads(line) for line in r.stdout.splitlines() if line.startswith('{')];record.update(measurements[-1]);record['measurements']=measurements;record['status']='passed';record['output_sha256']=sha256(output)
   else:record['failure_reason']=r.stderr[-2000:]
  except subprocess.TimeoutExpired as e:record.update(returncode=None,failure_reason='timeout');(o/f'run_{i}.stdout').write_bytes(e.stdout or b'');(o/f'run_{i}.stderr').write_bytes(e.stderr or b'')
  record['process_elapsed_s']=time.time()-start;records.append(record);(o/'runs.json').write_text(json.dumps(records,indent=2))
 return 0 if all(r['status']=='passed' for r in records) else 1
if __name__=='__main__':raise SystemExit(main())
