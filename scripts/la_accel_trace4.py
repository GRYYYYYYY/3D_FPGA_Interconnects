"""Add logical cross-layer counters to a frozen reference copy, never a timing run."""
import argparse,json,subprocess
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--workload',type=Path,action='append',required=True);a=p.parse_args();o=a.output.resolve();o.mkdir(parents=True,exist_ok=False)
 source=ROOT/'accel/lookahead/round4/reference4.hpp';s=source.read_text();s=s.replace('namespace la4 {','namespace la4 {\nstatic std::vector<unsigned> layers;static uint64_t cross_scanned=0,cross_pushed=0;')
 before='++st.edges;auto v=w.edge[i].dst;';assert s.count(before)==1;s=s.replace(before,before+'cross_scanned+=layers[u]!=layers[v];')
 before='s.visited[v]=next.delay;s.queue.push(next);++st.pushes;';assert s.count(before)==1;s=s.replace(before,before+'cross_pushed+=layers[u]!=layers[v];')
 (o/'trace_reference.hpp').write_text(s)
 (o/'trace.cpp').write_text(r'''#include "trace_reference.hpp"
#include <iostream>
#include <cstring>
int main(int argc,char** argv){try{la::Workload w(argv[1]);la4::Prepared p(w);la4::layers.resize(w.h.nodes);std::ifstream f(argv[2],std::ios::binary);la::read(f,la4::layers.data(),w.h.nodes);
la4::Scratch scratch(w.h.nodes,w.h.edges+1);std::vector<la::Cost> out(w.h.cells);
for(unsigned early=0;early<2;++early)for(unsigned q=0;q<w.h.jobs;++q){la4::cross_scanned=la4::cross_pushed=0;la4::StopInfo stop;auto st=early?la4::search<true>(w,q,p.targets[q],scratch,out.data(),stop):la4::search<false>(w,q,p.targets[q],scratch,out.data(),stop);
if(st.status||std::memcmp(out.data(),w.golden.data()+q*w.h.cells,out.size()*sizeof(la::Cost)))return 2;
std::cout<<"{\"early\":"<<early<<",\"qid\":"<<q<<",\"pops\":"<<st.pops<<",\"edges\":"<<st.edges<<",\"cross_scanned\":"<<la4::cross_scanned<<",\"cross_pushed\":"<<la4::cross_pushed<<",\"map_bits_match\":true}\n";}
}catch(const std::exception& e){std::cerr<<e.what();return 1;}}
''')
 command=['g++','-O2','-std=c++14','-ffp-contract=off','-fno-fast-math','-I'+str(ROOT/'accel/lookahead/include'),str(o/'trace.cpp'),'-o',str(o/'trace')]
 with (o/'build.log').open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
 rows=[]
 for w in a.workload:
  w=w.resolve();layer=w.parent/'layers.bin';cmd=[str(o/'trace'),str(w),str(layer)]
  result=subprocess.run(cmd,capture_output=True,text=True,check=True);(o/(w.parent.name+'.jsonl')).write_text(result.stdout)
  obs=[json.loads(l) for l in result.stdout.splitlines()];assert all(sum(x['cross_pushed'] for x in obs if x['early']==mode)>0 for mode in [0,1]),'Both full and early workload batches must actually traverse layers'
  rows.append(dict(workload=str(w),workload_sha256=sha256(w),layer_sha256=sha256(layer),observations=obs))
 (o/'result.json').write_text(json.dumps(dict(status='passed',evidence_type='logical_counts_not_FPGA_cycles',source_reference_sha256=sha256(source),instrumented_sha256=sha256(o/'trace_reference.hpp'),compile_command=command,workloads=rows),indent=2)+'\n')
if __name__=='__main__':main()
