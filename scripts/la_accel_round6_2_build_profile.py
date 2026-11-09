"""Isolated diagnostic-only E2 stage overlay; frozen main implementation unchanged."""
import json,sys,shutil,subprocess
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]);old=(R/'results/lookahead_accel_round6_1_20261109T160000Z/native_build').resolve();o=r/'profile_build';o.mkdir();(o/'bin').mkdir();shutil.copytree(old/'source',o/'source')
p=o/'source/vpr_live.cpp';s=p.read_text()
s=s.replace(' std::vector<la::Cost> costs;', ' double graph_s=seconds(begin);auto mapping_begin=Clock::now();\n std::vector<la::Cost> costs;',1)
s=s.replace(' std::vector<la::Cost> out(', ' double mapping_s=seconds(mapping_begin);auto output_alloc_begin=Clock::now();\n std::vector<la::Cost> out(',1)
s=s.replace(' unsigned contexts=', ' double output_alloc_s=seconds(output_alloc_begin);\n unsigned contexts=',1)
s=s.replace(' double merge=seconds(merge_begin),total=seconds(begin);',' double merge=seconds(merge_begin),total=seconds(begin);\n VTR_LOG("R62_CONVERSION graph_csr_allocation_copy_s=%.9f dense_mapping_job_cost_s=%.9f output_allocation_s=%.9f conversion_s=%.9f\\n",graph_s,mapping_s,output_alloc_s,conversion);',1)
p.write_text(s)
commands=[]
for cwd,cmd in json.load(open(old/'commands.json')):
 cmd=[x.replace(str(old),str(o)) for x in cmd];commands.append([cwd,cmd])
(o/'commands.json').write_text(json.dumps(commands,indent=2))
with (o/'build.log').open('w') as f:
 for cwd,cmd in commands:subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=300,check=True)
# CUDA diagnostic overlay copied locally, compiled only on the GPU worker.
src=r/'profile_cuda_source';shutil.copytree(R/'accel/lookahead',src)
p=src/'round6_1/cuda_solver61.cuh';s=p.read_text()
s=s.replace('la61::Prepared p(la61::view(a));target_host=p.targets;','la61::Prepared p(la61::view(a));target_host=p.targets;double validation_targets_s=seconds(begin);auto context_begin=Clock::now();')
s=s.replace('try{row=copy', 'double context_capacity_s=seconds(context_begin);auto device_begin=Clock::now();try{row=copy')
s=s.replace('prepare_s=seconds(begin);}', 'prepare_s=seconds(begin);fprintf(stdout,"R62_PREPARE validation_targets_s=%.9f context_capacity_s=%.9f device_alloc_h2d_s=%.9f prepare_s=%.9f\\n",validation_targets_s,context_capacity_s,seconds(device_begin),prepare_s);}')
# Time cudaMalloc and H2D separately without changing operation order; sum measured calls only.
s=s.replace('template<class T>T* alloc', 'static double r62_alloc_s=0,r62_h2d_s=0;\ntemplate<class T>T* alloc')
s=s.replace('T* p=nullptr;if(n)CK(cudaMalloc(&p,n*sizeof(T)));return p;', 'auto t=std::chrono::steady_clock::now();T* p=nullptr;if(n)CK(cudaMalloc(&p,n*sizeof(T)));r62_alloc_s+=std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();return p;')
s=s.replace('T* d=alloc<T>(count);if(count)CK(cudaMemcpy(d,p,count*sizeof(T),cudaMemcpyHostToDevice));return d;', 'T* d=alloc<T>(count);auto t=Clock::now();if(count)CK(cudaMemcpy(d,p,count*sizeof(T),cudaMemcpyHostToDevice));r62_h2d_s+=seconds(t);return d;')
s=s.replace('prepare_s=seconds(begin);fprintf', 'prepare_s=seconds(begin);fprintf(stdout,"R62_TRANSFERS device_allocation_s=%.9f H2D_s=%.9f\\n",r62_alloc_s,r62_h2d_s);fprintf')
p.write_text(s)
# Split input numerical validation from target counting, before the one profile.
p=src/'round6_1/bucket61.hpp';s=p.read_text()
s=s.replace('#include <array>', '#include <array>\n#include <cstdio>')
s=s.replace(':targets(w.h.jobs){', ':targets(w.h.jobs){auto r62_begin=std::chrono::steady_clock::now();')
s=s.replace('  std::vector<bool> seen(w.h.cells);', '  double r62_validation_s=std::chrono::duration<double>(std::chrono::steady_clock::now()-r62_begin).count();auto r62_targets_begin=std::chrono::steady_clock::now();\n  std::vector<bool> seen(w.h.cells);',1)
needle='++targets[q];}}}\n }\n};'
assert needle in s
s=s.replace(needle,'++targets[q];}}}\n  fprintf(stdout,"R62_INPUT_PREP numeric_validation_s=%.9f target_count_s=%.9f\\n",r62_validation_s,std::chrono::duration<double>(std::chrono::steady_clock::now()-r62_targets_begin).count());\n }\n};',1)
p.write_text(s)
(o/'binding.json').write_text(json.dumps(dict(binary_sha256=sha256(o/'bin/vpr_flat'),sources={p.name:sha256(p) for p in (o/'source').iterdir() if p.is_file()},cuda_solver_sha256=sha256(src/'round6_1/cuda_solver61.cuh'),prepared_profile_sha256=sha256(p),purpose='One BNN non-formal profile, no kernel phase profiling; no optimization. Parent native timing contains observer overhead.'),indent=2))
print('profile build ready')

