#include "io.hpp"
#include "dual_kernel.hpp"
#include <iostream>
#include <cstring>
int main(int argc,char** argv){
 if(argc!=2)return 1;la::Workload w(argv[1]);unsigned half=(w.h.jobs+1)/2;
 std::vector<la::Job> jobs[2];std::vector<int32_t> cells[2];std::vector<float> v[2];std::vector<uint32_t> e[2];std::vector<la::Entry> heap[2];std::vector<la::Cost> out[2];std::vector<la::Stats> stats[2];
 for(unsigned i=0;i<2;++i){jobs[i].resize(w.h.jobs+64);cells[i].resize(w.cell.size()+64);v[i].resize(2*w.h.nodes+64);e[i].resize(2*w.h.nodes+64);heap[i].resize(2*(w.h.edges+1)+64);out[i].resize(w.golden.size()+64);stats[i].resize(w.h.jobs+64);unsigned begin=i?half:0,count=i?w.h.jobs-half:half;std::copy(w.job.begin()+begin,w.job.begin()+begin+count,jobs[i].begin());std::copy(w.cell.begin()+begin*w.h.nodes,w.cell.begin()+(begin+count)*w.h.nodes,cells[i].begin());}
 w.row.resize(w.row.size()+64);w.node.resize(w.node.size()+64);w.edge.resize(w.edge.size()+64);w.cost.resize(w.cost.size()+64);
 lookahead_dual(w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),jobs[0].data(),cells[0].data(),v[0].data(),e[0].data(),heap[0].data(),out[0].data(),stats[0].data(),w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),jobs[1].data(),cells[1].data(),v[1].data(),e[1].data(),heap[1].data(),out[1].data(),stats[1].data(),w.h.nodes,half,w.h.jobs-half,w.h.cells,w.h.edges+1,w.h.edges+1);
 for(unsigned q=0;q<w.h.jobs;++q){unsigned i=q>=half,index=q-(i?half:0);if(stats[i][index].status)return 2;if(std::memcmp(out[i].data()+index*w.h.cells,w.golden.data()+q*w.h.cells,w.h.cells*sizeof(la::Cost)))return 3;}
 std::cout<<"PASS dual independent AXI interfaces, native golden; overlap requires RTL evidence\n";
}
