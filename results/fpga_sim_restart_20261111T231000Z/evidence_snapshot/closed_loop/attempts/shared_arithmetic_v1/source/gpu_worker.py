# Prepared reproducible cohort. Requires a valid GPU worker; does not submit jobs.
import pathlib,json,subprocess,os,shutil,hashlib,time
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z/closed_loop/gpu_v2';r.mkdir(exist_ok=True)
nvcc=shutil.which('nvcc');assert nvcc,'nvcc required';assert shutil.which('nvidia-smi'),'CUDA worker required'
subprocess.run(['nvidia-smi'],stdout=open(r/'nvidia-smi.txt','w'),check=True)
cpus=sorted(os.sched_getaffinity(0))[:8];assert len(cpus)==8;os.sched_setaffinity(0,cpus)
src=root/'accel/lookahead/round6/cuda6.cu';s=src.read_text();old='CK(cudaMemcpy(&err,error,4,cudaMemcpyDeviceToHost));CK(cudaMemcpy(packed.data()';new='CK(cudaMemcpy(&err,error,4,cudaMemcpyDeviceToHost));double resident_s=seconds(start);CK(cudaMemcpy(packed.data()';assert s.count(old)==1;s=s.replace(old,new)
old='<<elapsed<<",\\\"device_timeline_including_host_gaps_s\\\":"';new='<<elapsed<<",\\\"resident_s\\\":"<<resident_s<<",\\\"device_timeline_including_host_gaps_s\\\":"';assert s.count(old)==1;s=s.replace(old,new)
(r/'cuda6_resident.cu').write_text(s)
solver=(root/'accel/lookahead/round6_1/cuda_solver61.cuh').read_text()
old_solver='std::vector<la::Cost> solve(){auto start=Clock::now();std::vector<la::Cost> out(j*nc);'
new_solver='std::vector<la::Cost> solve(){std::vector<la::Cost> out(j*nc);auto start=Clock::now();'
assert solver.count(old_solver)==1
(r/'cuda_solver61.cuh').write_text(solver.replace(old_solver,new_solver))
(r/'cuda61.cu').write_bytes((root/'accel/lookahead/round6_1/cuda61.cu').read_bytes())
commands=[([nvcc,'-O3','-std=c++17','--fmad=false','-I'+str(root/'accel/lookahead/include'),'-I'+str(root/'accel/lookahead/round6'),str(r/'cuda6_resident.cu'),'-o',str(r/'basic')]),([nvcc,'-O3','-std=c++17','--fmad=false','-I'+str(root/'accel/lookahead/include'),'-I'+str(root/'accel/lookahead/round6_1'),str(r/'cuda61.cu'),'-o',str(r/'compact')])]
for command in commands:
 with open(r/('build_'+pathlib.Path(command[-1]).name+'.log'),'w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
(r/'binding.json').write_text(json.dumps({'commands':commands,'affinity':cpus,'old_cuda6_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'timer_only_variant_sha256':hashlib.sha256(s.encode()).hexdigest(),'compact_timer_only_solver_sha256':hashlib.sha256((r/'cuda_solver61.cuh').read_bytes()).hexdigest(),'scope':'RESIDENT_COMPLETE_BATCH_V2','repetitions':'3 processes, each 1 warmup+3 measured complete batches'},indent=2))
for x in json.load(open(root/'accel/lookahead/fpga_sim_restart/config/inputs.json')):
 reference=str(r.parent.parent/f"replay/{x['case']}_F1.bin")
 for process in range(3):
  for kind in ['basic','compact']:
   out=r/f"{x['case']}_{kind}_p{process}";command=[str(r/kind),x['path'],'20','3',reference,str(out)+'.bin']
   if kind=='compact':command+=['compact','0']
   with open(str(out)+'.jsonl','w') as log,open(str(out)+'.stderr','w') as err:subprocess.run(command,stdout=log,stderr=err,check=True)
   assert pathlib.Path(str(out)+'.bin').read_bytes()==pathlib.Path(reference).read_bytes()
(r/'completed.json').write_text(json.dumps({'status':'complete','scope':'RESIDENT_COMPLETE_BATCH_V2'}))
