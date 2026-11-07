// Replays actual native partial-frontier captures. CPU samples were produced
// by the original VPR continuation with heap/labels restored in-process.
// This executable never substitutes a different CPU shortest-path oracle.
#include "takeover_validate.hpp"
#include <chrono>
#include <dlfcn.h>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <sstream>

using namespace h3d_native;
using Clock=std::chrono::steady_clock;
uint64_t elapsed(Clock::time_point t){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-t).count();}
void check(const char*error){if(error)throw std::runtime_error(error);}
int main(int argc,char**argv){
    void*handle=nullptr;void*gpu=nullptr;DestroyFn destroy=nullptr;
    try{
        require(argc==4,"usage: takeover_replay LIBRARY|validate CAPTURE_DIRECTORY REPEATS");
        const std::filesystem::path directory=argv[2];unsigned repeats=std::stoul(argv[3]);require(repeats>0&&repeats<=20,"invalid repeats");
        Graph graph((directory/"graph.bin").string());Model model=Model::load((directory/"model.bin").string());
        std::vector<std::filesystem::path>files;
        for(const auto&f:std::filesystem::directory_iterator(directory))if(f.path().extension()==".bin"&&f.path().stem().string().find("takeover_")==0&&f.path().stem().string().find('.')==std::string::npos)files.push_back(f.path());
        auto sequence=[](const auto&p){return std::stoull(p.stem().string().substr(9));};
        std::sort(files.begin(),files.end(),[&](const auto&a,const auto&b){return sequence(a)<sequence(b);});require(!files.empty(),"no takeover snapshots");
        bool validate=std::string(argv[1])=="validate";CreateFn create=nullptr;UpdateFn update=nullptr;ExecuteFn execute=nullptr;TimingFn timing_fn=nullptr;
        if(!validate){
            handle=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);require(handle,"GPU library load failed");
            create=reinterpret_cast<CreateFn>(dlsym(handle,"h3d_gpu_create"));update=reinterpret_cast<UpdateFn>(dlsym(handle,"h3d_gpu_update"));
            execute=reinterpret_cast<ExecuteFn>(dlsym(handle,"h3d_gpu_execute"));destroy=reinterpret_cast<DestroyFn>(dlsym(handle,"h3d_gpu_destroy"));timing_fn=reinterpret_cast<TimingFn>(dlsym(handle,"h3d_gpu_timing"));
            require(create&&update&&execute&&destroy&&timing_fn,"GPU v3 API missing");
        }
        std::vector<uint32_t>path(graph.nodes.size());bool all_valid=true;
        std::cout<<"sequence,net,iteration,repeat,seeds,active,prepare_ns,update_ns,execute_ns,validate_ns,dispatch_ns,status,valid,cost,visits,rounds,state_h2d_event_ns,update_kernel_event_ns,query_h2d_event_ns,search_kernel_event_ns,d2h_event_ns,sync_host_ns,allocation_host_ns,h2d_bytes,d2h_bytes\n"<<std::setprecision(9);
        for(const auto&file:files){
            Takeover t=Takeover::load(file.string());TakeoverValidator validator(graph,model,t);
            auto prefix=file;prefix.replace_extension();
            std::ifstream samples(prefix.string()+".native.csv");require(bool(samples),"native repeat results missing");std::string line;std::getline(samples,line);
            std::vector<float>costs;std::vector<uint32_t>native_path;
            while(std::getline(samples,line)){
                std::stringstream ss(line);std::vector<std::string>fields;std::string f;while(std::getline(ss,f,','))fields.push_back(f);
                require(fields.size()==9&&fields[8]=="1","native repeat changed path");costs.push_back(std::stof(fields[6]));
            }
            require(costs.size()>=1,"missing native CPU repetitions");
            std::ifstream pf(prefix.string()+".native_path.bin",std::ios::binary|std::ios::ate);require(bool(pf),"native path missing");auto bytes=pf.tellg();require(bytes>=0&&bytes%4==0,"bad native path size");pf.seekg(0);native_path=read_vector<uint32_t>(pf,size_t(bytes)/4);
            for(float c:costs)validator.path(native_path,c);
            if(validate){std::cerr<<"validated takeover "<<t.header.query.sequence<<" labels="<<t.labels.size()<<" active="<<t.active.size()<<" native_repeats="<<costs.size()<<'\n';continue;}
            if(!gpu){GpuStatic input;input.graph=graph.header;input.nodes=graph.nodes.data();input.edges=graph.edges.data();input.native_to_edge=graph.native_to_edge.data();input.model=model.view();input.state=t.state.data();check(create(&input,&gpu));}
            // Restore the complete captured device state outside query timings.
            // Then replay the actual pending delta payload, including on repeats.
            std::vector<StateDelta>reset;reset.reserve(t.state.size());for(uint32_t i=0;i<t.state.size();++i)reset.push_back({i,t.state[i]});check(update(gpu,reset.data(),reset.size()));
            // Repeat -1 is a reported warm-up: it drains reset work and warms
            // allocations. Only repeats >=0 are comparable warm query timings.
            for(int rep=-1;rep<int(repeats);++rep){
                auto start=Clock::now();auto tick=start;
                auto prepared=validator.prepare();auto query=t.gpu_query();query.seeds=prepared.seeds.data();query.active=prepared.active.data();query.base_costs=prepared.base.data();
                uint64_t prep=elapsed(tick);GpuResult result;result.path=path.data();result.path_capacity=path.size();
                tick=Clock::now();const char*error=update(gpu,t.deltas.data(),t.deltas.size());uint64_t update_time=elapsed(tick);
                tick=Clock::now();if(!error)error=execute(gpu,&query,&result,1);uint64_t execute_time=elapsed(tick);
                GpuTiming timing{};if(!error)error=timing_fn(gpu,&timing);bool valid=false;tick=Clock::now();
                if(!error&&result.status==0){try{validator.path(std::vector<uint32_t>(path.begin(),path.begin()+result.length),result.cost,&prepared);valid=true;}catch(const std::exception&e){std::cerr<<file<<" repeat "<<rep<<": "<<e.what()<<'\n';}}
                uint64_t validation=elapsed(tick),dispatch=elapsed(start);all_valid&=valid;
                if(error)std::cerr<<file<<" repeat "<<rep<<": "<<error<<'\n';
                std::cout<<t.header.query.sequence<<','<<t.header.query.net<<','<<t.header.iteration<<','<<rep<<','<<prepared.seeds.size()<<','<<prepared.active.size()<<','<<prep<<','<<update_time<<','<<execute_time<<','<<validation<<','<<dispatch<<','<<(error?UINT32_MAX:result.status)<<','<<valid<<','<<result.cost<<','<<result.visits<<','<<result.rounds<<','
                    <<timing.state_h2d_event_ns<<','<<timing.update_kernel_event_ns<<','<<timing.query_h2d_event_ns<<','<<timing.search_kernel_event_ns<<','<<timing.d2h_event_ns<<','<<timing.sync_host_ns<<','<<timing.allocation_host_ns<<','<<timing.h2d_bytes<<','<<timing.d2h_bytes<<'\n';std::cout.flush();
            }
        }
        if(gpu){destroy(gpu);gpu=nullptr;}if(handle){dlclose(handle);handle=nullptr;}return all_valid?0:2;
    }catch(const std::exception&e){if(gpu&&destroy)destroy(gpu);if(handle)dlclose(handle);std::cerr<<e.what()<<'\n';return 1;}
}
