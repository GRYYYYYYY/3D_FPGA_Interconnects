"""Execute independent classic HLS 2022.2 phases with source binding and prerequisites."""
import argparse,json,subprocess,os,time,struct,shutil
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',required=True,choices=['csim','csynth','cosim','impl']);p.add_argument('--output',required=True,type=Path);p.add_argument('--workload',type=Path);p.add_argument('--source',type=Path,default=ROOT/'accel/lookahead/hls/lookahead_top.cpp');p.add_argument('--define',action='append',default=[]);p.add_argument('--top',default='lookahead_top');p.add_argument('--aligned-depths',action='store_true');p.add_argument('--contexts',type=int,choices=[1,2,4,8,16],default=1);p.add_argument('--frozen-flow',action='store_true',help='Resume recorded Tcl/config after checking synthesis sources unchanged');a=p.parse_args();o=a.output.resolve();o.mkdir(parents=True,exist_ok=True)
 sources=[a.source.resolve(),ROOT/'accel/lookahead/hls/run_hls.tcl',*[ROOT/'accel/lookahead/include'/x for x in ['workload.hpp','strict_heap.hpp','io.hpp','kernel.hpp']]];binding={str(s):sha256(s) for s in sources};b=o/'binding.json'
 interleaved=a.source.stem.startswith('lookahead_interleaved')
 tb=ROOT/('accel/lookahead/tests/interleaved_real.cpp' if (interleaved or a.source.name=='lookahead_resident.cpp') and a.workload else 'accel/lookahead/tests/dual_ports_testbench.cpp' if a.top=='lookahead_dual' else 'accel/lookahead/tests/dual_testbench.cpp' if a.contexts==2 else 'accel/lookahead/tests/real_testbench.cpp' if a.workload else 'accel/lookahead/tests/testbench.cpp');flags=''
 if a.workload:
  _,n,e,j,k,c,g=struct.unpack('<7Q',a.workload.open('rb').read(56));dims=dict(row=n+1,nodes=n,edges=e,costs=k,jobs=j,cells=j*n,visited=n*a.contexts,expanded=n*a.contexts,heap=(e+1)*a.contexts,output=j*c,stats=j);binding['workload']=sha256(a.workload)
  if a.aligned_depths:
   quantum=dict(row=8,nodes=4,edges=8,costs=8,jobs=8,cells=16,visited=16,expanded=16,heap=16,output=8,stats=4)
   dims={key:((value+quantum[key]-1)//quantum[key])*quantum[key] for key,value in dims.items()}
  flags=' '.join('-DLA_DEPTH_'+key.upper()+'='+str(value) for key,value in dims.items())
 if interleaved:flags+=' -DLA_CONTEXTS='+str(a.contexts)
 flags+=' '+ ' '.join('-D'+x for x in a.define);flags+=' -I'+str(ROOT/'accel/lookahead/hls/variants')
 for extra in (ROOT/'accel/lookahead/hls/variants').glob('*.hpp'):binding[str(extra)]=sha256(extra)
 if a.top=='lookahead_dual':binding['dual_header']=sha256(ROOT/'accel/lookahead/include/dual_kernel.hpp')
 binding['testbench']=sha256(tb)
 binding['flags']=flags;binding['top']=a.top
 if b.exists():
  recorded=json.loads(b.read_text())
  if a.frozen_flow:
   for src in sources:
    if src.suffix!='.tcl':assert recorded[str(src)]==sha256(src),'Synthesis source changed'
   assert recorded.get('testbench')==sha256(tb),'Testbench changed'
   for key,value in recorded.items():
    if key.startswith('/') and not key.endswith('.tcl'):assert Path(key).exists() and sha256(Path(key))==value,'Recorded synthesis dependency changed: '+key
   if a.workload:assert recorded['workload']==sha256(a.workload),'Workload changed'
   flags=recorded['flags']
  else:assert recorded==binding,'Source changed; use a new output directory'
 else:
  b.write_text(json.dumps(binding,indent=2));(o/'source_snapshot').mkdir()
  for src in [*sources,tb,*(ROOT/'accel/lookahead/hls/variants').glob('*.hpp'),ROOT/'accel/lookahead/include/dual_kernel.hpp']:shutil.copy2(src,o/'source_snapshot'/src.name)
 prev={'csynth':'csim','cosim':'csynth','impl':'cosim'}.get(a.phase)
 if prev:assert json.loads((o/(prev+'.json')).read_text())['status']=='passed','Missing passed prerequisite'
 log=o/(a.phase+'.log');assert not log.exists(),'Choose a new output directory for retry'
 env=os.environ.copy();env.update(LA_ROOT=str(ROOT),LA_HLS_OUT=str(o),LA_PHASE=a.phase,LA_TOP=a.top,LA_SOURCE=str(a.source.resolve()),LA_EXTRA_FLAGS=flags,LA_TESTBENCH=str(tb),LA_WORKLOAD=str(a.workload.resolve()) if a.workload else '',LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1')
 tcl=o/'source_snapshot/run_hls.tcl' if a.frozen_flow else ROOT/'accel/lookahead/hls/run_hls.tcl'
 cmd=['/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls','-f',str(tcl)];start=time.time()
 with log.open('w') as f:r=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT)
 text=log.read_text(errors='replace');marker={'csim':'CSim done with 0 errors','csynth':'Finished Command csynth_design','cosim':'C/RTL co-simulation finished: PASS','impl':'Finished Command export_design'}[a.phase]
 good=r.returncode==0 and marker in text and 'ERROR:' not in text
 (o/(a.phase+'.json')).write_text(json.dumps(dict(status='passed' if good else 'failed',command=cmd,returncode=r.returncode,elapsed_host_s=time.time()-start,not_fpga_runtime=True,testbench_sha256=sha256(tb),memory_model='HLS automatic functional AXI model; not bounded HBM'),indent=2));print(text[-3000:]);return 0 if good else 1
if __name__=='__main__':raise SystemExit(main())
