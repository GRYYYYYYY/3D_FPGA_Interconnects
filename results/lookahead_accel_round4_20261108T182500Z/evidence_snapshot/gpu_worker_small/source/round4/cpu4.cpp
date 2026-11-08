#include "reference4.hpp"
#include <chrono>
#include <cfenv>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <omp.h>
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
int main(int argc,char** argv){try{
    if(argc!=5)throw std::runtime_error("cpu4 workload workers warm_repeats full|early|diff");
    std::fesetround(FE_TONEAREST);la::Workload w(argv[1]);
    unsigned workers=std::stoul(argv[2]),repeats=std::stoul(argv[3]);std::string mode=argv[4];
    if(!workers||workers>128||(mode!="full"&&mode!="early"&&mode!="diff"))throw std::runtime_error("invalid config");
    auto start=Clock::now();la4::Prepared prepared(w);double target_prepare=seconds(start);
    std::vector<la4::Scratch> scratch;for(unsigned i=0;i<workers;++i)scratch.emplace_back(w.h.nodes,w.h.edges+1);
    std::vector<la::Cost> out(w.golden.size());std::vector<la::Stats> stats(w.h.jobs);
    std::vector<la4::StopInfo> stop(w.h.jobs);double prepare=seconds(start);
    std::cout<<std::setprecision(17);
    for(unsigned pass=0;pass<(mode=="diff"?2u:1u);++pass){
        bool early=mode=="early"||(mode=="diff"&&pass==1);
        for(unsigned repeat=0;repeat<=(mode=="diff"?0:repeats);++repeat){
            start=Clock::now();
            #pragma omp parallel for schedule(dynamic) num_threads(workers)
            for(size_t q=0;q<w.h.jobs;++q){auto& s=scratch[omp_get_thread_num()];
                stats[q]=early?la4::search<true>(w,q,prepared.targets[q],s,out.data()+q*w.h.cells,stop[q]):
                               la4::search<false>(w,q,prepared.targets[q],s,out.data()+q*w.h.cells,stop[q]);
            }
            double elapsed=seconds(start);uint64_t pops=0,edges=0,pushes=0,unreached=0;
            for(size_t q=0;q<w.h.jobs;++q){
                if(stats[q].status||std::memcmp(out.data()+q*w.h.cells,w.golden.data()+q*w.h.cells,w.h.cells*sizeof(la::Cost)))
                    throw std::runtime_error("status/golden mismatch at qid "+std::to_string(q));
                pops+=stats[q].pops;edges+=stats[q].edges;pushes+=stats[q].pushes;
                if(early&&prepared.targets[q]&&stop[q].reason==0)++unreached;
                if(mode=="diff")std::cout<<"{\"kind\":\"sample\",\"mode\":\""<<la4::mode_name(early)<<"\",\"qid\":"<<q<<",\"targets\":"<<prepared.targets[q]<<",\"recorded\":"<<stop[q].recorded<<",\"remaining_heap\":"<<stop[q].remaining<<",\"stop_reason\":"<<stop[q].reason<<",\"pops\":"<<stats[q].pops<<",\"edges\":"<<stats[q].edges<<",\"peak\":"<<stats[q].peak<<",\"golden_bits_match\":true}\n";
            }
            std::cout<<"{\"kind\":\"batch\",\"backend\":\"cpu4_std_priority_queue\",\"mode\":\""<<la4::mode_name(early)<<"\",\"scope\":\"E1_resident_flood_batch\",\"evidence_type\":\""<<(mode=="diff"?"functional_diagnostic":"cpu_measured")<<"\",\"phase\":\""<<(repeat?"warm":"cold_first_call")<<"\",\"repeat\":"<<repeat<<",\"workers\":"<<workers<<",\"resident_s\":"<<elapsed<<",\"prepare_s\":"<<prepare<<",\"target_prepare_s\":"<<target_prepare<<",\"pops\":"<<pops<<",\"edges\":"<<edges<<",\"pushes\":"<<pushes<<",\"unreached_target_samples\":"<<unreached<<",\"all_golden_bits_match\":true}\n";
        }
    }
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
