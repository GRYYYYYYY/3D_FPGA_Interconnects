// Diagnostic paired replay. Independent snapshots are batched on the GPU.
// This executable does NOT yet dispatch or commit paths inside native VPR.
#include "replay.hpp"
#include <cuda_runtime.h>
#include <math_constants.h>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <memory>

namespace {
using namespace h3d_native;
using Clock=std::chrono::steady_clock;
void ck(cudaError_t e){if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}
template<class T> void alloc(T*&p,size_t n){ck(cudaMalloc(&p,n*sizeof(T)));}
template<class T> void upload(T*p,const std::vector<T>&v){if(!v.empty())ck(cudaMemcpy(p,v.data(),v.size()*sizeof(T),cudaMemcpyHostToDevice));}
struct GResult {float cost;uint32_t length,status;unsigned long long visits,rounds,edge_visits;};
struct Slot {
    QueryHeader q;uint32_t epoch;
    Entry* entries;Seed* seeds;
    unsigned long long* labels;
    float* cong;float* h;
    uint32_t *allowed,*marks,*front,*next,*path;
    GResult* result;
};
__device__ unsigned long long label(float cost,uint32_t edge){return (static_cast<unsigned long long>(__float_as_uint(cost))<<32)|edge;}
__device__ float value(unsigned long long l){return __uint_as_float(uint32_t(l>>32));}
__device__ bool improve(unsigned long long*p,float g,uint32_t edge){
    auto old=atomicCAS(p,0ULL,0ULL);
    while(g<value(old)){
        auto prior=atomicCAS(p,old,label(g,edge));if(prior==old)return true;old=prior;
    }return false;
}
__device__ float edge_cost(float g,float cong,const Edge&e,const QueryHeader&q){
    if(e.configurable)g=__double2float_rn(double(g)+(1.-double(q.criticality))*double(cong));
    g=__fadd_rn(g,__fmul_rn(q.criticality,e.delay));
    if(e.bend)g=__fadd_rn(g,q.bend_cost);return g;
}
__global__ void initialize(Slot*slots,int slot){
    Slot s=slots[slot];uint32_t i=blockIdx.x*blockDim.x+threadIdx.x;
    if(i<s.q.entries){auto e=s.entries[i];s.allowed[e.node]=s.epoch;s.labels[e.node]=label(CUDART_INF_F,invalid);s.cong[e.node]=e.congestion;s.h[e.node]=e.heuristic;s.marks[e.node]=0;}
    if(i==0)*s.result={CUDART_INF_F,0,0,0,0,0};
}
__global__ void initialize_seeds(Slot*slots,int slot){
    Slot s=slots[slot];uint32_t i=blockIdx.x*blockDim.x+threadIdx.x;
    if(i<s.q.seeds){auto seed=s.seeds[i];s.labels[seed.node]=label(seed.backward,invalid);s.front[i]=seed.node;}
}
__device__ void enqueue(uint32_t node,uint32_t round,Slot&s,uint32_t*count,uint32_t*next){
    if(atomicExch(s.marks+node,round)!=round){auto i=atomicAdd(count,1U);if(i<s.q.entries)next[i]=node;}
}
__global__ void solve(const Node*nodes,const Edge*edges,const uint32_t*native_to_edge,Slot*slots,float relative_width){
    Slot s=slots[blockIdx.x];
    __shared__ uint32_t count,next_count,round,done;
    __shared__ float minima[256],threshold;
    __shared__ unsigned long long visits,edge_visits;
    if(threadIdx.x==0){count=s.q.seeds;round=0;done=0;visits=0;edge_visits=0;}
    __syncthreads();uint32_t*front=s.front;uint32_t*next=s.next;
    while(true){
        float mine=CUDART_INF_F;
        for(uint32_t i=threadIdx.x;i<count;i+=blockDim.x){auto v=front[i];mine=fminf(mine,__fadd_rn(value(s.labels[v]),s.h[v]));}
        minima[threadIdx.x]=mine;__syncthreads();
        for(int stride=128;stride;stride/=2){if(threadIdx.x<stride)minima[threadIdx.x]=fminf(minima[threadIdx.x],minima[threadIdx.x+stride]);__syncthreads();}
        if(threadIdx.x==0){
            float best=s.allowed[s.q.sink]==s.epoch?value(s.labels[s.q.sink]):CUDART_INF_F;
            if(count==0 || minima[0]>=best)done=1;
            if(round>=1000000U){done=2;s.result->status=2;}
            threshold=minima[0]+fmaxf(fabsf(minima[0])*relative_width,1e-18f);
            next_count=0;++round;
        }__syncthreads();if(done)break;
        unsigned long long local_visits=0,local_edges=0;
        for(uint32_t i=threadIdx.x;i<count;i+=blockDim.x){
            uint32_t v=front[i];float g=value(s.labels[v]);
            if(__fadd_rn(g,s.h[v])>threshold){enqueue(v,round,s,&next_count,next);continue;}
            ++local_visits;if(v==s.q.sink)continue;
            auto node=nodes[v];
            for(uint32_t j=node.first;j<node.first+node.count;++j){const auto&e=edges[j];++local_edges;
                if(s.allowed[e.dst]!=s.epoch)continue;
                float candidate=edge_cost(g,s.cong[e.dst],e,s.q);
                if(improve(s.labels+e.dst,candidate,e.native_id))enqueue(e.dst,round,s,&next_count,next);
            }
        }
        atomicAdd(&visits,local_visits);atomicAdd(&edge_visits,local_edges);__syncthreads();
        if(threadIdx.x==0){count=next_count;if(count>s.q.entries){done=2;s.result->status=3;}}
        __syncthreads();if(done)break;auto tmp=front;front=next;next=tmp;
    }
    if(threadIdx.x==0){
        s.result->visits=visits;s.result->edge_visits=edge_visits;s.result->rounds=round;
        if(s.result->status)return;
        if(s.allowed[s.q.sink]!=s.epoch)return;
        float cost=value(s.labels[s.q.sink]);s.result->cost=cost;if(!isfinite(cost))return;
        uint32_t v=s.q.sink,len=0;
        while(true){uint32_t id=uint32_t(s.labels[v]);if(id==invalid)break;
            if(len>=s.q.entries){s.result->status=4;return;}s.path[len++]=id;v=edges[native_to_edge[id]].src;
        }s.result->length=len;
    }
}
struct Workspace {
    Slot s{};size_t entry_capacity=0,seed_capacity=0;uint32_t epoch=0;
    explicit Workspace(size_t n){alloc(s.labels,n);alloc(s.cong,n);alloc(s.h,n);alloc(s.allowed,n);alloc(s.marks,n);alloc(s.front,n);alloc(s.next,n);alloc(s.path,n);alloc(s.result,1);ck(cudaMemset(s.allowed,0,n*sizeof(uint32_t)));}
    ~Workspace(){cudaFree(s.labels);cudaFree(s.cong);cudaFree(s.h);cudaFree(s.allowed);cudaFree(s.marks);cudaFree(s.front);cudaFree(s.next);cudaFree(s.path);cudaFree(s.result);cudaFree(s.entries);cudaFree(s.seeds);}
    void prepare(const Query&q){
        s.q=q.header;if(++epoch==0)throw std::runtime_error("replay generation overflow");s.epoch=epoch;
        if(q.entries.size()>entry_capacity){cudaFree(s.entries);alloc(s.entries,q.entries.size());entry_capacity=q.entries.size();}
        if(q.seeds.size()>seed_capacity){cudaFree(s.seeds);alloc(s.seeds,q.seeds.size());seed_capacity=q.seeds.size();}
        upload(s.entries,q.entries);upload(s.seeds,q.seeds);
    }
};
class Gpu {
    Node*nodes=nullptr;Edge*edges=nullptr;uint32_t*ids=nullptr;Slot*device_slots=nullptr;
    std::vector<std::unique_ptr<Workspace>> work;
  public:
    Gpu(const Graph&g,size_t batch){alloc(nodes,g.nodes.size());alloc(edges,g.edges.size());alloc(ids,g.native_to_edge.size());
        upload(nodes,g.nodes);upload(edges,g.edges);upload(ids,g.native_to_edge);alloc(device_slots,batch);
        for(size_t i=0;i<batch;++i)work.emplace_back(new Workspace(g.nodes.size()));
    }
    ~Gpu(){cudaFree(nodes);cudaFree(edges);cudaFree(ids);cudaFree(device_slots);}
    std::vector<Result> run(const std::vector<Query*>&qs,float width){
        std::vector<Slot> slots;for(size_t i=0;i<qs.size();++i){work[i]->prepare(*qs[i]);slots.push_back(work[i]->s);}upload(device_slots,slots);
        for(size_t i=0;i<qs.size();++i){initialize<<<(qs[i]->entries.size()+255)/256,256>>>(device_slots,i);ck(cudaGetLastError());
            initialize_seeds<<<(qs[i]->seeds.size()+255)/256,256>>>(device_slots,i);ck(cudaGetLastError());}
        solve<<<qs.size(),256>>>(nodes,edges,ids,device_slots,width);ck(cudaGetLastError());
        std::vector<Result> out;
        for(size_t i=0;i<qs.size();++i){GResult raw;ck(cudaMemcpy(&raw,slots[i].result,sizeof(raw),cudaMemcpyDeviceToHost));
            require(raw.status==0,"GPU search failed status="+std::to_string(raw.status));Result r;r.cost=raw.cost;r.visits=raw.visits;r.edges=raw.edge_visits;
            require(raw.length<=qs[i]->entries.size(),"invalid GPU path length");r.path.resize(raw.length);
            if(raw.length)ck(cudaMemcpy(r.path.data(),slots[i].path,raw.length*sizeof(uint32_t),cudaMemcpyDeviceToHost));
            std::reverse(r.path.begin(),r.path.end());out.push_back(std::move(r));
        }return out;
    }
};
}
int main(int argc,char**argv){
    try{
        if(argc<4)throw std::runtime_error("usage: replay_cuda BATCH graph.bin query.bin ...");
        size_t batch=std::stoul(argv[1]);require(batch>=1&&batch<=32,"batch out of range");
        Graph graph(argv[2]);std::vector<Query> queries;for(int i=3;i<argc;++i)queries.emplace_back(argv[i]);
        CpuSearch cpu(graph);for(auto&q:queries)cpu.validate(q,q.reference,q.header.reference_cost);
        auto init=Clock::now();Gpu gpu(graph,batch);ck(cudaDeviceSynchronize());
        std::cerr<<"gpu_initialization_seconds="<<std::chrono::duration<double>(Clock::now()-init).count()<<'\n';
        std::cout<<"repeat,batch_start,batch_count,sequence,window,seeds,cpu_replay_ns,gpu_batch_ns,native_capture_prepare_ns,native_cost,cpu_cost,gpu_cost,gpu_visits,gpu_edges,valid\n"<<std::setprecision(9);
        for(int repeat=0;repeat<3;++repeat)for(size_t start=0;start<queries.size();start+=batch){
            std::vector<Query*> qs;for(size_t i=start;i<std::min(queries.size(),start+batch);++i)qs.push_back(&queries[i]);
            std::vector<Result> cpus,gpus;std::vector<long long> cpu_times;long long gpu_ns=0;
            auto cpu_run=[&](){for(auto q:qs){auto t=Clock::now();cpus.push_back(cpu.search(*q));cpu_times.push_back(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-t).count());}};
            auto gpu_run=[&](){auto t=Clock::now();gpus=gpu.run(qs,0.01f);gpu_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-t).count();};
            if(repeat%2){gpu_run();cpu_run();}else{cpu_run();gpu_run();}
            for(size_t i=0;i<qs.size();++i){auto&q=*qs[i];cpu.validate(q,cpus[i].path,cpus[i].cost);cpu.validate(q,gpus[i].path,gpus[i].cost);
                std::cout<<repeat<<','<<start<<','<<qs.size()<<','<<q.header.sequence<<','<<q.entries.size()<<','<<q.seeds.size()<<','<<cpu_times[i]<<','<<gpu_ns<<','
                    <<q.header.prepare_ns<<','<<q.header.reference_cost<<','<<cpus[i].cost<<','<<gpus[i].cost<<','<<gpus[i].visits<<','<<gpus[i].edges<<",1\n";
            }std::cout.flush();
        }
    }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
