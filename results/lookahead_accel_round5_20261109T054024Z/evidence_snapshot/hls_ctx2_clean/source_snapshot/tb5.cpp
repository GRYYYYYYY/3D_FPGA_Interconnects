#include "api5.hpp"
#include "reference4.hpp"
#include <cstring>
#include <iostream>

int main(int argc,char** argv){try{
    if(argc<2)throw std::runtime_error("at least one complete workload required");
    unsigned transaction=0;
    for(int arg=1;arg<argc;++arg){
        la::Workload w(argv[arg]);la4::Prepared prepared(w);
        std::vector<la::Stats> expected(w.h.jobs);std::vector<la::Cost> check(w.golden.size());
        la4::Scratch scratch(w.h.nodes,w.h.edges+1);
        for(unsigned q=0;q<w.h.jobs;++q){la4::StopInfo stop;
            expected[q]=LA4_EARLY?la4::search<true>(w,q,prepared.targets[q],scratch,check.data()+q*w.h.cells,stop):
                                  la4::search<false>(w,q,prepared.targets[q],scratch,check.data()+q*w.h.cells,stop);
        }
        if(std::memcmp(check.data(),w.golden.data(),check.size()*sizeof(la::Cost)))return 2;
        auto saved_cost=w.cost;
        w.row.resize(LA4_DEPTH_ROW);w.node.resize(LA4_DEPTH_NODES);w.edge.resize(LA4_DEPTH_EDGES);
        w.cost.resize(LA4_DEPTH_COSTS);w.job.resize(LA4_DEPTH_JOBS);w.cell.resize(LA4_DEPTH_CELLS);
        std::vector<la::Cost> out0(LA4_DEPTH_OUTPUT),out1(LA4_DEPTH_OUTPUT),out2(LA4_DEPTH_OUTPUT),out3(LA4_DEPTH_OUTPUT);
        std::vector<la::Stats> st0(LA4_DEPTH_STATS),st1(LA4_DEPTH_STATS),st2(LA4_DEPTH_STATS),st3(LA4_DEPTH_STATS);
        std::vector<la::Cost>* outputs[]={&out0,&out1,&out2,&out3};std::vector<la::Stats>* stat[]={&st0,&st1,&st2,&st3};
        // Combined first call, two warm calls (poisoned external costs), and load-only.
        unsigned commands[]={2,1,1,0};
        for(unsigned command:commands){
            if(command==1)for(auto& c:w.cost)c={la::missing(),la::missing()};
            else std::copy(saved_cost.begin(),saved_cost.end(),w.cost.begin());
            uint64_t metrics[64]={};unsigned s0=99,s1=99,s2=99,s3=99;
            lookahead_interleave5(w.row.data(),w.node.data(),w.edge.data(),w.cost.data(),w.job.data(),w.cell.data(),out0.data(),st0.data(),
              w.h.nodes,w.h.edges,w.h.jobs,w.h.costs,w.h.cells,command,s0,metrics
            );
            if(s0||(LA4_ENGINES==4&&(s1||s2||s3)))throw std::runtime_error("admission failed");
            if(command!=0)for(unsigned q=0;q<w.h.jobs;++q){unsigned e=q%LA4_ENGINES;auto st=(*stat[e])[q],ref=expected[q];
                if(st.status||st.pushes!=ref.pushes||st.pops!=ref.pops||st.edges!=ref.edges||st.expanded!=ref.expanded||st.peak!=ref.peak)throw std::runtime_error("statistics mismatch");
                if(std::memcmp(outputs[e]->data()+q*w.h.cells,w.golden.data()+q*w.h.cells,w.h.cells*sizeof(la::Cost)))throw std::runtime_error("native map mismatch");
            }
            if(command!=0){std::cout<<"METRICS ";for(unsigned i=0;i<64;++i)std::cout<<metrics[i]<<",";std::cout<<"\n";}
            std::cout<<"TRANSACTION "<<transaction++<<" command="<<command<<" input="<<argv[arg]<<" mode="<<la4::mode_name(LA4_EARLY)<<" engines="<<LA4_ENGINES<<" all_bits_and_stats_match=1\n";
        }
    }
    std::cout<<"PASS runtime graph replacement, poisoned warm external costs, complete maps and stats\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
