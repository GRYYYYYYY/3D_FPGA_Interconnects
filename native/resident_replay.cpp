#include "gpu_api.hpp"
#include "model_io.hpp"
#include <chrono>
#include <dlfcn.h>
#include <iomanip>
#include <iostream>

namespace {
using namespace h3d_native;
struct SnapshotState {
    StateHeader header;std::vector<float>base;std::vector<StateDelta>deltas;
    explicit SnapshotState(const std::string&file){
        std::ifstream f(file,std::ios::binary);header=read<StateHeader>(f);
        require(std::string(header.magic,7)=="H3DSTA1"&&header.version==1,"bad state ABI");
        base=read_vector<float>(f,header.base_count);deltas=read_vector<StateDelta>(f,header.deltas);require(f.peek()==EOF,"trailing state bytes");
    }
};
void check(const char*error){if(error)throw std::runtime_error(error);}
float single(const Model&m,const std::vector<State>&state,const SnapshotState&s,uint32_t id,float present){
    auto n=m.nodes[id];auto r=state[id];int over=r.occupancy-int(n.capacity);
    float p=over>=0?float(1.+float(present*float(over+1))):1.f;
    return s.base[n.cost_index]*r.accumulated*p;
}
void validate_state(const Graph&g,const Model&m,const Query&q,const SnapshotState&s,std::vector<State>&state){
    require(s.header.nodes==g.nodes.size()&&s.base.size()==m.header.base_count,"state/model shape mismatch");
    for(auto d:s.deltas){require(d.node<state.size() && d.state.occupancy>=0 && std::isfinite(d.state.accumulated)&&d.state.accumulated>=0,"bad sparse state delta");state[d.node]=d.state;}
    for(auto e:q.entries){auto n=m.nodes[e.node];float cost=single(m,state,s,e.node,q.header.present);
        for(uint32_t i=n.group_begin;i<n.group_begin+n.group_count;++i){auto member=m.groups[i];if(member!=e.node)cost+=single(m,state,s,member,q.header.present);}
        require(cost==e.congestion,"sparse occupancy/history disagrees with native congestion snapshot");
        float h=expected(m.view(),e.node,q.header.sink,q.header.criticality,s.base[m.header.reserved]);h=q.header.astar*std::max(0.f,h-q.header.astar_offset);
        require(h==e.heuristic,"exported lookahead not bit-exact for snapshot");
    }
}
}

int main(int argc,char**argv){
    void*handle=nullptr;void*gpu=nullptr;h3d_native::DestroyFn destroy=nullptr;
    try{
        using namespace h3d_native;using Clock=std::chrono::steady_clock;
        if(argc!=4)throw std::runtime_error("usage: resident_replay libgpu.so capture_directory COPIES (batch-isolation oracle only)");
        std::string directory=argv[2];uint32_t copies=std::stoul(argv[3]);require(copies>=1&&copies<=8,"invalid copies");
        Graph graph(directory+"/graph.bin");Model model=Model::load(directory+"/model.bin");
        std::ifstream csv(directory+"/queries.csv");std::string line;std::getline(csv,line);std::vector<uint64_t>sequence;
        while(std::getline(csv,line))if(line.find("query_")!=std::string::npos)sequence.push_back(std::stoull(line.substr(0,line.find(','))));
        require(!sequence.empty(),"no captured queries");
        std::vector<Query>queries;std::vector<SnapshotState>states;
        for(auto id:sequence){queries.emplace_back(directory+"/query_"+std::to_string(id)+".bin");states.emplace_back(directory+"/state_"+std::to_string(id)+".bin");}
        std::vector<State>host_state(graph.nodes.size());CpuSearch cpu(graph);
        require(states[0].deltas.size()==graph.nodes.size(),"first captured state must initialize all nodes");
        for(size_t i=0;i<queries.size();++i){validate_state(graph,model,queries[i],states[i],host_state);cpu.validate(queries[i],queries[i].reference,queries[i].header.reference_cost);}
        for(auto d:states[0].deltas)host_state[d.node]=d.state;
        handle=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);require(handle,dlerror()?"GPU library failed to load":"GPU library missing");
        auto create=reinterpret_cast<CreateFn>(dlsym(handle,"h3d_gpu_create"));auto update=reinterpret_cast<UpdateFn>(dlsym(handle,"h3d_gpu_update"));
        auto execute=reinterpret_cast<ExecuteFn>(dlsym(handle,"h3d_gpu_execute"));destroy=reinterpret_cast<DestroyFn>(dlsym(handle,"h3d_gpu_destroy"));
        require(create&&update&&execute&&destroy,"GPU library API missing");
        GpuStatic input;input.slots=copies;input.graph=graph.header;input.nodes=graph.nodes.data();input.edges=graph.edges.data();input.native_to_edge=graph.native_to_edge.data();input.model=model.view();input.state=host_state.data();
        auto init=Clock::now();check(create(&input,&gpu));std::cerr<<"resident_initialization_seconds="<<std::chrono::duration<double>(Clock::now()-init).count()<<'\n';
        std::vector<std::vector<uint32_t>>paths(copies,std::vector<uint32_t>(graph.nodes.size()));
        std::cout<<"repeat,sequence,copies,copy,state_deltas,state_bytes,seed_bytes,gpu_update_ns,gpu_search_ns,native_cost,gpu_cost,visits,rounds,edges,valid\n"<<std::setprecision(9);
        for(int repeat=0;repeat<3;++repeat)for(size_t i=0;i<queries.size();++i){
            const auto&q=queries[i];const auto&s=states[i];auto update_start=Clock::now();
            check(update(gpu,s.deltas.data(),s.deltas.size()));
            auto update_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-update_start).count();
            GpuQuery query;query.sink=q.header.sink;query.seed_count=q.seeds.size();query.base_count=s.base.size();
            std::copy(q.header.box,q.header.box+6,query.box);std::copy(s.header.target,s.header.target+6,query.target);
            query.criticality=q.header.criticality;query.astar=q.header.astar;query.astar_offset=q.header.astar_offset;
            query.bend_cost=q.header.bend_cost;query.present=q.header.present;query.seeds=q.seeds.data();query.base_costs=s.base.data();
            std::vector<GpuQuery>batch(copies,query);std::vector<GpuResult>results(copies);
            for(uint32_t j=0;j<copies;++j){results[j].path=paths[j].data();results[j].path_capacity=paths[j].size();}
            auto tick=Clock::now();check(execute(gpu,batch.data(),results.data(),copies));
            auto elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-tick).count();
            for(uint32_t j=0;j<copies;++j){auto&r=results[j];require(r.status==0,"resident kernel status "+std::to_string(r.status));
                std::vector<uint32_t>path(paths[j].begin(),paths[j].begin()+r.length);cpu.validate(q,path,r.cost);
                std::cout<<repeat<<','<<q.header.sequence<<','<<copies<<','<<j<<','<<s.deltas.size()<<','<<s.deltas.size()*sizeof(StateDelta)<<','<<q.seeds.size()*sizeof(Seed)<<','<<update_ns<<','<<elapsed<<','
                    <<q.header.reference_cost<<','<<r.cost<<','<<r.visits<<','<<r.rounds<<','<<r.edges<<",1\n";
            }std::cout.flush();
        }
        destroy(gpu);gpu=nullptr;dlclose(handle);handle=nullptr;
    }catch(const std::exception&e){if(gpu&&destroy)destroy(gpu);if(handle)dlclose(handle);std::cerr<<e.what()<<'\n';return 1;}
}
