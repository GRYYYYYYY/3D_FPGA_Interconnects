#include "api5.hpp"
#include "reference4.hpp"
#include <cstring>
#include <iostream>
void run(la::Workload w){
 // Replication here is ONLY a semantic interleaving unit test, never a workload.
 auto old=w;w.h.jobs=7;w.job.resize(7);w.cell.resize(7*w.h.nodes);w.golden.resize(7*w.h.cells);
 for(unsigned q=0;q<7;++q){unsigned src=q%old.h.jobs;w.job[q]=old.job[src];std::copy_n(old.cell.data()+src*w.h.nodes,w.h.nodes,w.cell.data()+q*w.h.nodes);std::copy_n(old.golden.data()+src*w.h.cells,w.h.cells,w.golden.data()+q*w.h.cells);}
 la4::Prepared p(w);std::vector<la::Cost> out(w.golden.size());std::vector<la::Stats> stats(7);la4::Scratch scratch(w.h.nodes,w.h.edges+1);uint64_t metrics[64];unsigned status;
 for(unsigned command:{2u,1u}){
 auto saved=w.cost;if(command==1)for(auto&c:w.cost)c={la::missing(),la::missing()};
 lookahead_interleave5(w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),w.job.data(),w.cell.data(),out.data(),stats.data(),w.h.nodes,w.h.edges,7,w.h.costs,w.h.cells,command,status,metrics);w.cost=saved;
 if(status||std::memcmp(out.data(),w.golden.data(),out.size()*8))throw std::runtime_error("interleaved map mismatch");
 for(unsigned q=0;q<7;++q){la4::StopInfo info;std::vector<la::Cost> ref(w.h.cells);auto st=LA4_EARLY?la4::search<true>(w,q,p.targets[q],scratch,ref.data(),info):la4::search<false>(w,q,p.targets[q],scratch,ref.data(),info);auto got=stats[q];if(st.pops!=got.pops||st.pushes!=got.pushes||st.edges!=got.edges||st.peak!=got.peak||st.expanded!=got.expanded||got.status)throw std::runtime_error("interleaved stats mismatch");}
 }
 // Invalid reload must invalidate resident image, including subsequent warm call.
 lookahead_interleave5(w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),w.job.data(),w.cell.data(),out.data(),stats.data(),4097,w.h.edges,7,w.h.costs,w.h.cells,0,status,metrics);if(status!=la::INVALID_INPUT)throw std::runtime_error("oversize accepted");
 lookahead_interleave5(w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),w.job.data(),w.cell.data(),out.data(),stats.data(),w.h.nodes,w.h.edges,7,w.h.costs,w.h.cells,1,status,metrics);if(status!=la::INVALID_INPUT)throw std::runtime_error("invalid reload retained image");
}
int main(int argc,char**argv){try{for(int i=1;i<argc;++i)run(la::Workload(argv[i]));std::cout<<"PASS "<<argc-1<<" semantic fixtures, 7 interleaved test-only qids, repeated warm and reload invalidation\n";}catch(std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
