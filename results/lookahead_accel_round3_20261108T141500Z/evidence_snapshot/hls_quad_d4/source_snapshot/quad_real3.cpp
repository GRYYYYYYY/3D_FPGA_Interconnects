#include "io.hpp"
#include "quad_kernel3.hpp"
#include <iostream>
#include <cstring>
int main(int argc,char** argv){
 if(argc!=2)return 1;la::Workload w(argv[1]);unsigned chunk=(w.h.jobs+3)/4,begin[4],count[4];
 std::vector<la::Job> jobs[4];std::vector<int32_t> cells[4];std::vector<float> v[4];std::vector<uint32_t> e[4];std::vector<la::Entry> heap[4];std::vector<la::Cost> out[4];std::vector<la::Stats> stats[4];
 for(unsigned i=0;i<4;++i){
  begin[i]=std::min<uint64_t>(i*chunk,w.h.jobs);count[i]=std::min<uint64_t>(chunk,w.h.jobs-begin[i]);
  jobs[i].resize(w.h.jobs+64);cells[i].resize(w.cell.size()+64);v[i].resize(4*w.h.nodes+64);e[i].resize(4*w.h.nodes+64);heap[i].resize(4*(w.h.edges+1)+64);out[i].resize(w.golden.size()+64);stats[i].resize(w.h.jobs+64);
  std::copy(w.job.begin()+begin[i],w.job.begin()+begin[i]+count[i],jobs[i].begin());std::copy(w.cell.begin()+begin[i]*w.h.nodes,w.cell.begin()+(begin[i]+count[i])*w.h.nodes,cells[i].begin());
 }
 w.row.resize(w.row.size()+64);w.node.resize(w.node.size()+64);w.edge.resize(w.edge.size()+64);w.cost.resize(w.cost.size()+64);
 lookahead_quad(
  w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),jobs[0].data(),cells[0].data(),v[0].data(),e[0].data(),heap[0].data(),out[0].data(),stats[0].data(),
  w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),jobs[1].data(),cells[1].data(),v[1].data(),e[1].data(),heap[1].data(),out[1].data(),stats[1].data(),
  w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),jobs[2].data(),cells[2].data(),v[2].data(),e[2].data(),heap[2].data(),out[2].data(),stats[2].data(),
  w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),jobs[3].data(),cells[3].data(),v[3].data(),e[3].data(),heap[3].data(),out[3].data(),stats[3].data(),
  w.h.nodes,count[0],count[1],count[2],count[3],w.h.cells,w.h.edges+1,w.h.edges+1);
 for(unsigned q=0;q<w.h.jobs;++q){unsigned i=q/chunk,index=q-begin[i];if(stats[i][index].status)return 2;if(std::memcmp(out[i].data()+index*w.h.cells,w.golden.data()+q*w.h.cells,w.h.cells*sizeof(la::Cost)))return 3;std::cout<<"qid="<<q<<" engine="<<i<<" pops="<<stats[i][index].pops<<" edges="<<stats[i][index].edges<<" peak="<<stats[i][index].peak<<'\n';}
 std::cout<<"PASS quad independent resident engines; all native samples bitwise correct\n";
}
