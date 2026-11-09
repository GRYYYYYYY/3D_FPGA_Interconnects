"""Profile complete immutable exports in C++; bounded text traces only for small graphs."""
import argparse,json,struct,subprocess,time
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--experiment',type=Path,required=True);a=p.parse_args();r=a.experiment.resolve();out=r/'profiles';out.mkdir(exist_ok=False)
old3=ROOT/'results/lookahead_accel_round3_20261108T141500Z';old4=ROOT/'results/lookahead_accel_round4_20261108T182500Z';old1=ROOT/'results/lookahead_accel_20261108T125500Z'
paths=[old3/'native_d3_w8',old3/'native_d4_w8',old4/'native_d5_w8',r/'native_d6_w8',r/'native_d8_w8',r/'native_d6_w8_l1',old1/'tseng_export',old1/'bnn_export'];manifest=[]
for folder in paths:
 w=folder/'workload.bin';header=struct.unpack('<7Q',w.open('rb').read(56));n,e,j,k,c,g=header[1:];layer=folder/'layers.bin';digest=sha256(w)
 if folder not in paths[3:6]:
  reports=list((ROOT/'results/lookahead_accel_round4_20261108T182500Z').glob('gpu_worker_*/worker.json'))
  known={key:value for report in reports for key,value in json.loads(report.read_text())['workloads'].items()};assert known[str(w)]==digest
 row=dict(case=folder.name,path=str(w),sha256=digest,N=n,E=e,J=j,G=g,cells=c,costs=k,representation='unmodified native CSR',task_source='complete native global sample list',heldout=folder.name=='native_d8_w8',graph_bytes=(n+1)*8+n*16+e*8+k*8,cell_map_bytes=j*n*4,dynamic_bytes_per_context=n*5+(e+1)*12+c*8,evidence='measured',layer_map=str(layer) if layer.exists() else None)
 manifest.append(row);(r/'workload_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 trace=str(out/(folder.name+'.csv')) if n<10000 else '-';cmd=[str(r/'profile5'),str(w),str(layer) if layer.exists() else '-',str(out/(folder.name+'.jsonl')),trace]
 start=time.monotonic()
 with (out/(folder.name+'.log')).open('w') as f:run=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 (out/(folder.name+'_run.json')).write_text(json.dumps(dict(command=cmd,returncode=run.returncode,host_elapsed_s=time.monotonic()-start,not_fpga_time=True),indent=2));assert run.returncode==0
 print(folder.name,'profile passed',flush=True)
