#include "trace_reference.hpp"
#include <iostream>
#include <cstring>
int main(int argc,char** argv){try{la::Workload w(argv[1]);la4::Prepared p(w);la4::layers.resize(w.h.nodes);std::ifstream f(argv[2],std::ios::binary);la::read(f,la4::layers.data(),w.h.nodes);
la4::Scratch scratch(w.h.nodes,w.h.edges+1);std::vector<la::Cost> out(w.h.cells);
for(unsigned early=0;early<2;++early)for(unsigned q=0;q<w.h.jobs;++q){la4::cross_scanned=la4::cross_pushed=0;la4::StopInfo stop;auto st=early?la4::search<true>(w,q,p.targets[q],scratch,out.data(),stop):la4::search<false>(w,q,p.targets[q],scratch,out.data(),stop);
if(st.status||std::memcmp(out.data(),w.golden.data()+q*w.h.cells,out.size()*sizeof(la::Cost)))return 2;
std::cout<<"{\"early\":"<<early<<",\"qid\":"<<q<<",\"pops\":"<<st.pops<<",\"edges\":"<<st.edges<<",\"cross_scanned\":"<<la4::cross_scanned<<",\"cross_pushed\":"<<la4::cross_pushed<<",\"map_bits_match\":true}\n";}
}catch(const std::exception& e){std::cerr<<e.what();return 1;}}
