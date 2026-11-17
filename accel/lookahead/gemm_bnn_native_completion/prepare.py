from pathlib import Path
import json,hashlib,datetime,shutil,subprocess,os,socket
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT.parent/'3D_FPGA_Interconnects';PAPER=ROOT.parent/'3D_FPGA_Interconnects_PAPER_CPU_GPU_V1';NATIVE=ROOT.parent/'3D_FPGA_Interconnects_R6_1/results/lookahead_accel_round6_1_20261109T160000Z';HERE=Path(__file__).resolve().parent
R=ROOT/'results/gemm_bnn_native_completion_20261117/post_v1_a'
def read(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 R.mkdir(parents=True,exist_ok=False)
 for d in ['environment','qualification','formal','analysis','receipts']:(R/d).mkdir()
 gate=read(PAPER/'results/cpu_gpu_paper_first_20261117/V1_publication.json');assert gate['new_experiments_allowed'];save(R/'receipts/V1_publication.json',gate);save(HERE/'V1_publication.json',gate)
 gemm=read(next((PAPER/'paper/dac2027_cpu_gpu_algorithm_first/evidence/gemm').glob('*stock*')))
 case=dict(id='gemm_layer_seed1_w100',circuit_id='gemm',seed=1,route_chan_width=100,device_width=0,target_utilization=.6,inputs=gemm['inputs'])
 bnn=read(BASE/'results/native_cpu_width120_20261104/bnn_s1/vpr_case.json');cases={'gemm':case,'bnn':bnn};bindings={}
 for name,case in cases.items():
  for role,x in case['inputs'].items():
   f=Path(x['path']);actual=sha(f);assert actual==x['sha256'],str(f);x['bytes']=f.stat().st_size
  bindings[name]=dict(case=case,all_inputs_hash_verified=True,metadata_status='NOT_MEASURED',source='historical CPU_GEMM_PROCESS exact seed1 cohort' if name=='gemm' else 'original R6.1 BNN bnn_s1 width120 cohort')
  print('INPUT_VERIFIED',name,flush=True)
 save(HERE/'input_manifest.json',bindings)
 bins={'stock':BASE.parent/'3D_FPGA_routing/artifacts/bin/baseline/vpr','pipeline':NATIVE/'native_build/bin/vpr_flat','alt_cpu':NATIVE/'libcpu61.so','alt_cuda':NATIVE/'gpu_worker/libcuda61.so'}
 expected={'stock':'37cc22c8b1b5d9d378e25379e85afcb7e56b5f1f6f72e3e9186e5e107ed5ce62','pipeline':'5d32c536b729d87ffd33a9c354ec157662b703f96dcc8ed02fcb522355de2355','alt_cpu':'24def217de2a67f0963d0244bc86c17548b48e4be22ccb25fb1efdd63b614cb6','alt_cuda':'9f5c60501adde4cec5a59aef55de0acf82732c7ff23821f4d456d444d20d00b1'}
 binding={}
 for k,p in bins.items():
  h=sha(p);assert h==expected[k],k;binding[k]=dict(path=str(p),sha256=h,bytes=p.stat().st_size)
 runtime=read(BASE/'data/vpr_runtime_20261025/runtime.json')
 for l in runtime['libraries']:assert sha(l['path'])==l['sha256']
 save(HERE/'runtime.json',runtime)
 src=HERE/'source';src.mkdir()
 for sub in ['include','round6_1']:shutil.copytree(ROOT/'accel/lookahead'/sub,src/sub)
 shutil.copytree(NATIVE/'native_build/source',src/'native_outer')
 sources={str(p.relative_to(HERE)):sha(p) for p in src.rglob('*') if p.is_file()}
 save(HERE/'source_binding.json',dict(source_commit='c8933bac394a1c177725bec6d9a0ccb6af3437a6',binary=binding,source_sha256=sources,native_original_binding=read(NATIVE/'native_build/binding.json'),native_original_commands=read(NATIVE/'native_build/commands.json')))
 pools={};seen=set()
 for cpu in sorted(os.sched_getaffinity(0)):
  d=Path(f'/sys/devices/system/cpu/cpu{cpu}');key=((d/'topology/physical_package_id').read_text(),(d/'topology/core_id').read_text())
  if key in seen:continue
  seen.add(key);pools.setdefault(sorted(d.glob('node*'))[0].name,[]).append(cpu)
 pool=sorted(pools.items(),key=lambda x:(-len(x[1]),x[1]))[0];cpus=pool[1][:8]
 env=dict(hostname=socket.gethostname(),affinity=cpus,numa=pool[0],cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text(),memory_max=Path('/sys/fs/cgroup/memory.max').read_text(),memory_current=Path('/sys/fs/cgroup/memory.current').read_text(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),cpu_stat=Path('/sys/fs/cgroup/cpu.stat').read_text(),lscpu=subprocess.check_output(['lscpu'],text=True),gpu_available=False,gpu_query='No nvidia-smi or /dev/nvidia*',inspire_status='RESOURCE_BLOCKED_AUTH_EXPIRED_INVALID_GRANT',formal_resource_contract_frozen=False)
 save(R/'environment/local.json',env)
 plan=dict(task='CPU_GPU_PAPER_FIRST_GEMM_BNN_V2',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),V1_commit=gate['V1_commit'],run=str(R),case_order=['bnn','gemm'],metadata_order=['gemm','bnn'],representation='original',mode='ALT_BUCKET_FP32_V1',shift=20,formal_repeats=3,arms=['stock','pipeline','alt_cuda'],orders=[['stock','pipeline','alt_cuda'],['pipeline','alt_cuda','stock'],['alt_cuda','stock','pipeline']],formal_process_target=18,timeout_seconds={'gemm':900,'bnn':600},timeout_basis='GEMM exact historical cohort frozen timeout900s, observed Stock about330s; BNN prior native600s. Fixed before new runs.',qualification=['stock','pipeline','alt_cpu','alt_cuda'],qor_max_fraction=0.05,resources=env,formal_allowed=False,formal_block_reason='GPU worker authentication unavailable; local CPU diagnostics are NOT formal cohort',independent_readback_outside_Process=True,FPGA_auto_resume_allowed=False,retries=0,source_manifest_sha256=sha(HERE/'source_binding.json'),input_manifest_sha256=sha(HERE/'input_manifest.json'))
 save(HERE/'experiment_plan.json',plan);save(R/'receipts/initial_plan.json',plan);print('PLAN_WRITTEN',R,flush=True)
if __name__=='__main__':main()
