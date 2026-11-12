#include "io.hpp"
#include <iostream>
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("workload output");la::Workload w(argv[1]);if(w.h.nodes>=(1u<<28)||w.h.costs>16)throw std::runtime_error("representation admission");
 std::vector<uint64_t>row;std::vector<uint32_t>edge;row.reserve(w.h.nodes+1);edge.reserve(w.h.edges);
 for(unsigned n=0;n<w.h.nodes;++n){row.push_back(edge.size());for(auto k=w.row[n];k<w.row[n+1];++k){auto v=w.edge[k].dst;int a=la::eligible(w.node[n],w.node[v]);if(a<0)break;if(!a)continue;edge.push_back(v|(w.node[v].cost<<28));}}row.push_back(edge.size());
 std::ofstream f(argv[2],std::ios::binary);uint64_t h[]={0x5350415253455632ull,w.h.nodes,edge.size(),w.h.jobs,w.h.costs,w.h.cells};la::write(f,h,6);la::write(f,row.data(),row.size());la::write(f,edge.data(),edge.size());std::cout<<"CSR_ONLY nodes="<<w.h.nodes<<" edges="<<edge.size()<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
