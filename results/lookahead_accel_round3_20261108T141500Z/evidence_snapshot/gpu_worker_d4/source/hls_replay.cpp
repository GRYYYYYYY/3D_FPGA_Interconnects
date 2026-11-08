#include "io.hpp"
#include "kernel.hpp"
#include <iostream>
#include <cstring>
int main(int argc,char** argv){try{
 if(argc!=3)throw std::runtime_error("usage: hls_replay workload.bin output.bin");if(std::ifstream(argv[2]).good())throw std::runtime_error("output exists");la::Workload w(argv[1]);if(w.h.edges>=UINT32_MAX)throw std::runtime_error("queue bound unsupported");
 std::vector<float> visited(w.h.nodes);std::vector<uint32_t> expanded(w.h.nodes);std::vector<la::Entry> heap(w.h.edges+1);std::vector<la::Cost> out(w.golden.size());std::vector<la::Stats> stats(w.h.jobs);for(auto& s:stats)s.status=la::INVALID_INPUT;
 lookahead_top(w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),w.job.data(),w.cell.data(),visited.data(),expanded.data(),heap.data(),out.data(),stats.data(),w.h.nodes,w.h.jobs,w.h.cells,w.h.edges+1,w.h.edges+1);
 for(size_t q=0;q<stats.size();++q)if(stats[q].status){std::cerr<<"sample "<<q<<" failed status "<<stats[q].status<<'\n';return 2;}
 for(size_t i=0;i<out.size();++i)if(std::memcmp(&out[i],&w.golden[i],sizeof(la::Cost))){std::cerr<<"first mismatch "<<i<<'\n';return 3;}
 std::ofstream f(argv[2],std::ios::binary);la::write(f,out.data(),out.size());std::cout<<"{\"status\":\"passed\",\"matches_reference\":true,\"evidence_type\":\"host_c_functional_check\",\"core_cycles\":null,\"jobs\":"<<w.h.jobs<<"}\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
