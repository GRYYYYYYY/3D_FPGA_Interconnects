#include "replay.hpp"
#include <chrono>
#include <iomanip>
#include <iostream>
int main(int argc,char**argv){
    try{
        if(argc<3)throw std::runtime_error("usage: replay_cpu graph.bin query.bin ...");
        h3d_native::Graph graph(argv[1]);h3d_native::CpuSearch cpu(graph);
        std::cout<<"sequence,window,seeds,native_cpu_ns,cpu_replay_ns,native_cost,replay_cost,visits,edges,valid\n"<<std::setprecision(9);
        for(int i=2;i<argc;++i){h3d_native::Query q(argv[i]);cpu.validate(q,q.reference,q.header.reference_cost);
            auto start=std::chrono::steady_clock::now();auto result=cpu.search(q);
            auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start).count();
            cpu.validate(q,result.path,result.cost);
            std::cout<<q.header.sequence<<','<<q.entries.size()<<','<<q.seeds.size()<<','<<q.header.cpu_ns<<','<<ns<<','
                <<q.header.reference_cost<<','<<result.cost<<','<<result.visits<<','<<result.edges<<",1\n";
        }
    }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
