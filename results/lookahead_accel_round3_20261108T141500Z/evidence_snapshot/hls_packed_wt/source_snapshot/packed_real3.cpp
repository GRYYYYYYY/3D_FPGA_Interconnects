#include "io.hpp"
#include "packed_kernel3.hpp"
#include <cstring>
#include <iostream>
#ifndef LA_CONTEXTS
#define LA_CONTEXTS 1
#endif
template<class T> void pad(std::vector<T>& v) {size_t q=64;while(q%sizeof(T))q+=64;size_t k=q/sizeof(T);v.resize((v.size()+k-1)/k*k);}
int main(int argc,char** argv){
 if(argc!=2){std::cerr<<"workload required\n";return 1;}la::Workload w(argv[1]);
 std::vector<uint64_t> label(w.h.nodes);std::vector<la::Entry> heap((w.h.edges+1)*LA_CONTEXTS);std::vector<la::Cost> out(w.golden.size());std::vector<la::Stats> stats(w.h.jobs);
 pad(w.row);pad(w.node);pad(w.edge);pad(w.cost);pad(w.job);pad(w.cell);pad(label);pad(heap);pad(out);pad(stats);
 lookahead_packed(w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),w.job.data(),w.cell.data(),label.data(),heap.data(),out.data(),stats.data(),w.h.nodes,w.h.jobs,w.h.cells,w.h.edges+1,w.h.edges+1);
 for(size_t q=0;q<w.h.jobs;++q){if(stats[q].status)return 2;std::cout<<"qid="<<q<<" pushes="<<stats[q].pushes<<" pops="<<stats[q].pops<<" edges="<<stats[q].edges<<" peak="<<stats[q].peak<<'\n';}
 if(std::memcmp(out.data(),w.golden.data(),w.golden.size()*sizeof(la::Cost)))return 3;
 std::cout<<"PASS complete native RRG sample maps, bitwise FP32\n";
}
