// H100 resident native-VPR search engine. Graph, native lookahead and
// occupancy/history remain on the device. Queries send only seeds, small
// descriptors and the native cost-index table. Per-query labels initialize on
// first touch with SM90 128-bit CAS; no whole-window scan/reset is performed.
#include "gpu_api.hpp"
#include <cuda_runtime.h>
#include <cooperative_groups.h>
#include <math_constants.h>
#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

namespace {
using namespace h3d_native;
void ck(cudaError_t e){if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}
template<class T>void alloc(T*&p,size_t n){ck(cudaMalloc(&p,n*sizeof(T)));}
template<class T>void copy(T*p,const T*v,size_t n){if(n)ck(cudaMemcpy(p,v,n*sizeof(T),cudaMemcpyHostToDevice));}
struct alignas(16) Label {uint32_t epoch;float cost;uint32_t edge,reserved;};
static_assert(sizeof(Label)==16 && std::is_trivially_copyable<Label>::value);
struct Slot {
    GpuQuery query;uint32_t epoch;
    Label*labels;unsigned long long*marks;
    uint32_t *front,*next,*path;GpuResult*result;
};
struct ContextView {
    GraphHeader graph;const Node*nodes;const Edge*edges;const uint32_t*ids;
    ModelView model;const State*state;Slot*slots;
};
__device__ Label load_label(Label*p){Label z{0,0.f,0,0};return atomicCAS(p,z,z);}
__device__ float distance(Slot&s,uint32_t n){auto l=load_label(s.labels+n);return l.epoch==s.epoch?l.cost:CUDART_INF_F;}
__device__ float heuristic(const ContextView&c,Slot&s,uint32_t node);
__device__ bool improve(const ContextView&c,Slot&s,uint32_t node,float cost,uint32_t edge){
    auto old=load_label(s.labels+node);
    while(old.epoch!=s.epoch || cost<old.cost){
        // The native lookahead is invariant for a query. Cache it on first
        // touch instead of repeating random table reads for every frontier scan.
        uint32_t h=old.epoch==s.epoch?old.reserved:__float_as_uint(heuristic(c,s,node));
        Label next{s.epoch,cost,edge,h};auto prior=atomicCAS(s.labels+node,old,next);
        if(prior.epoch==old.epoch && __float_as_uint(prior.cost)==__float_as_uint(old.cost) && prior.edge==old.edge && prior.reserved==old.reserved)return true;
        old=prior;
    }return false;
}
__device__ float heuristic(const ContextView&c,Slot&s,uint32_t node){
    float e=expected(c.model,node,s.query.sink,s.query.criticality,s.query.base_costs[c.model.header.reserved]);
    // SINK_COST_INDEX is exported in ModelHeader.reserved (do not assume enum layout).
    // The header's sink base remains available for model diagnostics only.
    return __fmul_rn(s.query.astar,fmaxf(0.f,__fsub_rn(e,s.query.astar_offset)));
}
__device__ bool allowed(const ContextView&c,Slot&s,uint32_t v){
    const auto&n=c.model.nodes[v];if(!inside(n,s.query.box))return false;
    if(n.kind==Ipin){const auto*b=s.query.target;
        if(n.xlo<b[0]||n.xhi>b[1]||n.ylo<b[2]||n.yhi>b[3]||n.zlo<b[4]||n.zlo>b[5])return false;
    }return true;
}
__device__ float single_congestion(const ContextView&c,Slot&s,uint32_t v){
    const auto&n=c.model.nodes[v];auto state=c.state[v];int over=state.occupancy-int(n.capacity);
    float p=over>=0?__double2float_rn(1.+double(__fmul_rn(s.query.present,float(over+1)))):1.f;
    return __fmul_rn(__fmul_rn(s.query.base_costs[n.cost_index],state.accumulated),p);
}
__device__ float congestion(const ContextView&c,Slot&s,uint32_t v){
    float result=single_congestion(c,s,v);const auto&n=c.model.nodes[v];
    for(uint32_t i=n.group_begin;i<n.group_begin+n.group_count;++i){uint32_t member=c.model.groups[i];if(member!=v)result=__fadd_rn(result,single_congestion(c,s,member));}
    return result;
}
__device__ float backward(const ContextView&c,Slot&s,float cost,const Edge&e){
    if(e.configurable)cost=__double2float_rn(double(cost)+(1.-double(s.query.criticality))*double(congestion(c,s,e.dst)));
    cost=__fadd_rn(cost,__fmul_rn(s.query.criticality,e.delay));if(e.bend)cost=__fadd_rn(cost,s.query.bend_cost);return cost;
}
__global__ void updates(State*state,const StateDelta*d,uint32_t count){uint32_t i=blockIdx.x*blockDim.x+threadIdx.x;if(i<count)state[d[i].node]=d[i].state;}
__device__ void enqueue(Slot&s,uint32_t v,uint32_t round,uint32_t*count,uint32_t*next,uint32_t capacity){
    unsigned long long mark=(static_cast<unsigned long long>(s.epoch)<<32)|round;
    if(atomicExch(s.marks+v,mark)!=mark){
        // Reserve one interval for the currently coalesced lanes. The frontier
        // counter must not serialize one global atomic per deferred node.
        auto lanes=cooperative_groups::coalesced_threads();uint32_t begin=0;
        if(lanes.thread_rank()==0)begin=atomicAdd(count,uint32_t(lanes.size()));
        begin=lanes.shfl(begin,0);uint32_t i=begin+lanes.thread_rank();
        if(i<capacity)next[i]=v;
    }
}
__global__ void solve(ContextView c){
    Slot s=c.slots[blockIdx.x];
    __shared__ uint32_t count,next_count,round,done;
    __shared__ float minima[256],threshold;
    __shared__ unsigned long long visits,edge_visits;
    if(threadIdx.x==0){count=s.query.active_count?s.query.active_count:s.query.seed_count;round=0;done=0;visits=0;edge_visits=0;*s.result=GpuResult{};}
    for(uint32_t i=threadIdx.x;i<s.query.seed_count;i+=blockDim.x){auto seed=s.query.seeds[i];improve(c,s,seed.node,seed.backward,invalid);}
    __syncthreads();
    for(uint32_t i=threadIdx.x;i<count;i+=blockDim.x)s.front[i]=s.query.active_count?s.query.active[i]:s.query.seeds[i].node;
    __syncthreads();uint32_t*front=s.front;uint32_t*next=s.next;
    while(true){
        float mine=CUDART_INF_F;
        // No label writers in this barrier-delimited minimum phase.
        for(uint32_t i=threadIdx.x;i<count;i+=blockDim.x){auto label=s.labels[front[i]];mine=fminf(mine,__fadd_rn(label.cost,__uint_as_float(label.reserved)));}
        minima[threadIdx.x]=mine;__syncthreads();
        for(int stride=128;stride;stride/=2){if(threadIdx.x<stride)minima[threadIdx.x]=fminf(minima[threadIdx.x],minima[threadIdx.x+stride]);__syncthreads();}
        if(threadIdx.x==0){
            if(count==0||minima[0]>=distance(s,s.query.sink))done=1;
            if(round>=s.query.max_rounds){done=2;s.result->status=2;}
            threshold=minima[0]+fmaxf(fabsf(minima[0])*s.query.bucket_relative,1e-18f);next_count=0;++round;
        }__syncthreads();if(done)break;
        unsigned long long local_visits=0,local_edges=0;
        for(uint32_t i=threadIdx.x;i<count;i+=blockDim.x){
            uint32_t v=front[i];auto label=load_label(s.labels+v);float cost=label.cost;
            if(__fadd_rn(cost,__uint_as_float(label.reserved))>threshold){enqueue(s,v,round,&next_count,next,c.graph.nodes);continue;}
            ++local_visits;if(v==s.query.sink)continue;auto n=c.nodes[v];
            for(uint32_t j=n.first;j<n.first+n.count;++j){const auto&e=c.edges[j];++local_edges;
                if(!allowed(c,s,e.dst) || distance(s,e.dst)<=cost)continue;
                float candidate=backward(c,s,cost,e);
                if(improve(c,s,e.dst,candidate,e.native_id))enqueue(s,e.dst,round,&next_count,next,c.graph.nodes);
            }
        }
        atomicAdd(&visits,local_visits);atomicAdd(&edge_visits,local_edges);__syncthreads();
        if(threadIdx.x==0){count=next_count;if(count>c.graph.nodes){s.result->status=3;done=2;}}
        __syncthreads();if(done)break;auto tmp=front;front=next;next=tmp;
    }
    if(threadIdx.x==0){
        s.result->visits=visits;s.result->rounds=round;s.result->edges=edge_visits;
        if(s.result->status)return;float cost=distance(s,s.query.sink);s.result->cost=cost;if(!isfinite(cost))return;
        uint32_t v=s.query.sink,len=0;
        while(true){auto l=load_label(s.labels+v);
            if(l.epoch!=s.epoch){s.result->status=5;return;}if(l.edge==invalid)break;
            if(l.edge>=c.graph.edges || len>=c.graph.nodes){s.result->status=4;return;}
            s.path[len++]=l.edge;v=c.edges[c.ids[l.edge]].src;
        }
        // Concurrent relaxation can improve a predecessor after a descendant
        // was labelled. Its final predecessor chain is valid but may be cheaper
        // than the stale sink label. Return the cost of the actual path, using
        // the same arithmetic and frozen occupancy as the search/host verifier.
        float realized=distance(s,v);
        for(uint32_t i=len;i>0;--i)realized=backward(c,s,realized,c.edges[c.ids[s.path[i-1]]]);
        if(!isfinite(realized)||realized>cost+fmaxf(1e-20f,fabsf(cost)*2e-6f)){s.result->status=6;return;}
        s.result->reserved=__float_as_uint(realized)!=__float_as_uint(cost);
        s.result->cost=realized;
        s.result->length=len;
    }
}
struct CooperativeState {
    uint32_t count,next_count,round,done,min_bits;
    float threshold;
    unsigned long long visits,edge_visits;
};
// A single long query can otherwise occupy only one SM. This optional engine
// distributes its frontier over a cooperatively resident grid. Every iteration
// retains the same priority interval, native cost model and lazy labels.
__global__ void solve_cooperative(ContextView c,CooperativeState*w){
    auto grid=cooperative_groups::this_grid();Slot s=c.slots[0];
    uint32_t tid=blockIdx.x*blockDim.x+threadIdx.x,stride=gridDim.x*blockDim.x;
    __shared__ float minima[256];
    if(tid==0){w->count=s.query.active_count?s.query.active_count:s.query.seed_count;w->round=0;w->done=0;w->visits=0;w->edge_visits=0;*s.result=GpuResult{};}
    for(uint32_t i=tid;i<s.query.seed_count;i+=stride){auto seed=s.query.seeds[i];improve(c,s,seed.node,seed.backward,invalid);}
    grid.sync();
    for(uint32_t i=tid;i<w->count;i+=stride)s.front[i]=s.query.active_count?s.query.active[i]:s.query.seeds[i].node;
    grid.sync();uint32_t*front=s.front;uint32_t*next=s.next;
    while(true){
        if(tid==0){w->min_bits=__float_as_uint(CUDART_INF_F);w->next_count=0;}
        grid.sync();float mine=CUDART_INF_F;
        // grid.sync() separates this read-only phase from all relaxations.
        for(uint32_t i=tid;i<w->count;i+=stride){auto label=s.labels[front[i]];mine=fminf(mine,__fadd_rn(label.cost,__uint_as_float(label.reserved)));}
        minima[threadIdx.x]=mine;__syncthreads();
        for(int step=128;step;step/=2){if(threadIdx.x<step)minima[threadIdx.x]=fminf(minima[threadIdx.x],minima[threadIdx.x+step]);__syncthreads();}
        if(threadIdx.x==0)atomicMin(&w->min_bits,__float_as_uint(minima[0]));
        grid.sync();
        if(tid==0){float minimum=__uint_as_float(w->min_bits);
            if(w->count==0||minimum>=distance(s,s.query.sink))w->done=1;
            if(w->round>=s.query.max_rounds){w->done=2;s.result->status=2;}
            w->threshold=minimum+fmaxf(fabsf(minimum)*s.query.bucket_relative,1e-18f);++w->round;
        }
        grid.sync();if(w->done)break;
        unsigned long long visits=0,edges=0;
        for(uint32_t i=tid;i<w->count;i+=stride){uint32_t v=front[i];auto label=load_label(s.labels+v);float cost=label.cost;
            if(__fadd_rn(cost,__uint_as_float(label.reserved))>w->threshold){enqueue(s,v,w->round,&w->next_count,next,c.graph.nodes);continue;}
            ++visits;if(v==s.query.sink)continue;auto node=c.nodes[v];
            for(uint32_t j=node.first;j<node.first+node.count;++j){const auto&e=c.edges[j];++edges;
                if(!allowed(c,s,e.dst)||distance(s,e.dst)<=cost)continue;
                if(improve(c,s,e.dst,backward(c,s,cost,e),e.native_id))enqueue(s,e.dst,w->round,&w->next_count,next,c.graph.nodes);
            }
        }
        if(visits)atomicAdd(&w->visits,visits);if(edges)atomicAdd(&w->edge_visits,edges);
        grid.sync();
        if(tid==0){w->count=w->next_count;if(w->count>c.graph.nodes){s.result->status=3;w->done=2;}}
        grid.sync();if(w->done)break;auto tmp=front;front=next;next=tmp;
    }
    if(tid==0){
        s.result->visits=w->visits;s.result->rounds=w->round;s.result->edges=w->edge_visits;
        if(s.result->status)return;float cost=distance(s,s.query.sink);s.result->cost=cost;if(!isfinite(cost))return;
        uint32_t v=s.query.sink,len=0;
        while(true){auto label=load_label(s.labels+v);
            if(label.epoch!=s.epoch){s.result->status=5;return;}if(label.edge==invalid)break;
            if(label.edge>=c.graph.edges||len>=c.graph.nodes){s.result->status=4;return;}
            s.path[len++]=label.edge;v=c.edges[c.ids[label.edge]].src;
        }
        float realized=distance(s,v);
        for(uint32_t i=len;i>0;--i)realized=backward(c,s,realized,c.edges[c.ids[s.path[i-1]]]);
        if(!isfinite(realized)||realized>cost+fmaxf(1e-20f,fabsf(cost)*2e-6f)){s.result->status=6;return;}
        s.result->reserved=__float_as_uint(realized)!=__float_as_uint(cost);s.result->cost=realized;s.result->length=len;
    }
}
class Device {
    std::vector<void*> allocations;
    template<class T>T* make(size_t n){if(!n)return nullptr;T*p=nullptr;alloc(p,n);allocations.push_back(p);return p;}
    struct Work {Slot slot{};Seed*seeds=nullptr;float*base=nullptr;uint32_t seed_capacity=0;uint32_t*active=nullptr;uint32_t active_capacity=0;};
    std::vector<Work>work;StateDelta*delta=nullptr;uint32_t delta_capacity=0;
    CooperativeState*cooperative_state=nullptr;
    uint32_t cooperative_blocks=0;uint64_t cooperative_queries=0,block_queries=0;
    uint32_t cooperative_min_seeds=1024;
  public:
    ContextView c{};
    GpuTiming timing{};
    using Clock=std::chrono::steady_clock;
    static uint64_t elapsed(Clock::time_point start){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count();}
    struct EventPair {cudaEvent_t begin{},end{};uint64_t GpuTiming::*field=nullptr;};
    std::vector<EventPair> events;size_t event_count=0;
    size_t begin_event(uint64_t GpuTiming::*field){
        if(!timing.enabled)return SIZE_MAX;
        if(event_count==events.size()){
            EventPair e;ck(cudaEventCreate(&e.begin));ck(cudaEventCreate(&e.end));events.push_back(e);
        }
        size_t i=event_count++;events[i].field=field;ck(cudaEventRecord(events[i].begin));return i;
    }
    void end_event(size_t i){if(i!=SIZE_MAX)ck(cudaEventRecord(events[i].end));}
    template<class T>void upload(T*dst,const T*src,size_t count,bool state=false){
        if(!count)return;
        auto event=begin_event(state?&GpuTiming::state_h2d_event_ns:&GpuTiming::query_h2d_event_ns);
        auto tick=Clock::now();copy(dst,src,count);
        (state?timing.state_h2d_host_ns:timing.query_h2d_host_ns)+=elapsed(tick);
        timing.h2d_bytes+=count*sizeof(T);end_event(event);
    }
    void download(void*dst,const void*src,size_t bytes){
        auto event=begin_event(&GpuTiming::d2h_event_ns);auto tick=Clock::now();
        ck(cudaMemcpy(dst,src,bytes,cudaMemcpyDeviceToHost));timing.d2h_host_ns+=elapsed(tick);
        timing.d2h_bytes+=bytes;end_event(event);
    }
    void collect(){
        if(!timing.enabled)return;
        auto tick=Clock::now();
        // The explicit wait is diagnostic only. It attributes the asynchronous
        // update/search work before result copies instead of charging it to D2H.
        if(event_count)ck(cudaEventSynchronize(events[event_count-1].end));
        for(size_t i=0;i<event_count;++i){float ms=0;ck(cudaEventElapsedTime(&ms,events[i].begin,events[i].end));timing.*(events[i].field)+=uint64_t(double(ms)*1e6);}
        timing.event_collect_host_ns=elapsed(tick);
    }
    explicit Device(const GpuStatic&s){
        if(s.version!=gpu_api_version||s.slots<1||s.slots>32)throw std::runtime_error("GPU ABI or slot count mismatch");
        cudaDeviceProp prop;int index;ck(cudaGetDevice(&index));ck(cudaGetDeviceProperties(&prop,index));
        if(prop.major<9)throw std::runtime_error("native lazy labels require SM90 (128-bit CAS)");
        if(const char*value=std::getenv("H3D_GPU_COOPERATIVE_MIN_SEEDS"))cooperative_min_seeds=std::stoul(value);
        if(const char*value=std::getenv("H3D_GPU_COOPERATIVE_BLOCKS")){
            auto requested=std::stoul(value);
            if(requested){
                if(!prop.cooperativeLaunch)throw std::runtime_error("cooperative launch unavailable");
                int resident=0;ck(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&resident,solve_cooperative,256,0));
                cooperative_blocks=std::min<unsigned long>(requested,uint32_t(resident*prop.multiProcessorCount));
                if(!cooperative_blocks)throw std::runtime_error("no cooperative occupancy");
                cooperative_state=make<CooperativeState>(1);
            }
        }
        c.graph=s.graph;c.model.header=s.model.header;
        auto initialize=[&](auto*&out,const auto*in,size_t n){using T=typename std::remove_cv<typename std::remove_pointer<typename std::remove_reference<decltype(out)>::type>::type>::type;T*p=make<T>(n);copy(p,in,n);out=p;};
        initialize(c.nodes,s.nodes,s.graph.nodes);initialize(c.edges,s.edges,s.graph.edges);initialize(c.ids,s.native_to_edge,s.graph.edges);
        initialize(c.model.nodes,s.model.nodes,s.model.header.nodes);initialize(c.model.wires,s.model.wires,s.model.header.wires);
        initialize(c.model.reachable,s.model.reachable,s.model.header.reachable);initialize(c.model.groups,s.model.groups,s.model.header.groups);
        initialize(c.state,s.state,s.graph.nodes);c.slots=make<Slot>(s.slots);work.resize(s.slots);
        for(auto&w:work){auto&t=w.slot;t.labels=make<Label>(s.graph.nodes);ck(cudaMemset(t.labels,0,s.graph.nodes*sizeof(Label)));
            t.marks=make<unsigned long long>(s.graph.nodes);ck(cudaMemset(t.marks,0,s.graph.nodes*sizeof(unsigned long long)));
            t.front=make<uint32_t>(s.graph.nodes);t.next=make<uint32_t>(s.graph.nodes);t.path=make<uint32_t>(s.graph.nodes);t.result=make<GpuResult>(1);
            w.base=make<float>(s.model.header.base_count);
        }
    }
    ~Device(){
        if(const char*path=std::getenv("H3D_GPU_DEVICE_REPORT")){
            std::ofstream f(path);f<<"{\"cooperative_blocks\":"<<cooperative_blocks<<",\"cooperative_queries\":"<<cooperative_queries<<",\"single_block_queries\":"<<block_queries<<"}\n";
        }
        for(auto e:events){cudaEventDestroy(e.begin);cudaEventDestroy(e.end);}
        for(auto p:allocations)cudaFree(p);for(auto&w:work){cudaFree(w.seeds);cudaFree(w.active);}cudaFree(delta);
    }
    void update(const StateDelta*d,uint32_t n){
        timing=GpuTiming{};timing.enabled=std::getenv("H3D_GPU_TIMING")&&std::string(std::getenv("H3D_GPU_TIMING"))=="1";event_count=0;
        auto start=Clock::now();
        if(n){
            for(uint32_t i=0;i<n;++i)if(d[i].node>=c.graph.nodes)throw std::runtime_error("invalid sparse state node");
            auto tick=Clock::now();
            if(n>delta_capacity){ck(cudaFree(delta));delta=nullptr;alloc(delta,n);delta_capacity=n;}
            timing.allocation_host_ns+=elapsed(tick);
            upload(delta,d,n,true);auto event=begin_event(&GpuTiming::update_kernel_event_ns);
            tick=Clock::now();updates<<<(n+255)/256,256>>>(const_cast<State*>(c.state),delta,n);ck(cudaGetLastError());
            timing.launch_host_ns+=elapsed(tick);end_event(event);
        }
        timing.update_host_ns=elapsed(start);
    }
    void execute(const GpuQuery*q,GpuResult*out,uint32_t n){
        if(!n || n>work.size())throw std::runtime_error("invalid query batch size");
        auto execute_start=Clock::now();
        std::vector<Slot>slots;
        for(uint32_t i=0;i<n;++i){auto&w=work[i];auto&s=w.slot;
            if(q[i].sink>=c.graph.nodes || !q[i].seed_count || q[i].seed_count>c.graph.nodes || q[i].base_count!=c.model.header.base_count)throw std::runtime_error("invalid native GPU query");
            if(q[i].active_count>q[i].seed_count||(q[i].active_count&&!q[i].active))throw std::runtime_error("invalid CPU frontier");
            if(++s.epoch==0)throw std::runtime_error("native query epoch overflow");s.query=q[i];
            auto allocation_start=Clock::now();
            if(q[i].seed_count>w.seed_capacity){cudaFree(w.seeds);w.seeds=nullptr;alloc(w.seeds,q[i].seed_count);w.seed_capacity=q[i].seed_count;}

            if(q[i].active_count>w.active_capacity){cudaFree(w.active);w.active=nullptr;alloc(w.active,q[i].active_count);w.active_capacity=q[i].active_count;}
            timing.allocation_host_ns+=elapsed(allocation_start);
            upload(w.seeds,q[i].seeds,q[i].seed_count);upload(w.base,q[i].base_costs,q[i].base_count);
            upload(w.active,q[i].active,q[i].active_count);s.query.active=w.active;
            s.query.seeds=w.seeds;s.query.base_costs=w.base;slots.push_back(s);
        }
        upload(c.slots,slots.data(),n);
        auto search_event=begin_event(&GpuTiming::search_kernel_event_ns);auto launch_start=Clock::now();
        if(n==1&&cooperative_blocks&&q[0].seed_count>=cooperative_min_seeds){
            void*args[]={&c,&cooperative_state};ck(cudaLaunchCooperativeKernel(reinterpret_cast<void*>(solve_cooperative),cooperative_blocks,256,args));++cooperative_queries;
        }else{solve<<<n,256>>>(c);block_queries+=n;}
        ck(cudaGetLastError());timing.launch_host_ns+=elapsed(launch_start);end_event(search_event);
        if(timing.enabled){auto tick=Clock::now();ck(cudaEventSynchronize(events[search_event].end));timing.sync_host_ns=elapsed(tick);}
        for(uint32_t i=0;i<n;++i){GpuResult result;download(&result,work[i].slot.result,sizeof(result));
            auto path=out[i].path;auto capacity=out[i].path_capacity;
            if(result.length>capacity)throw std::runtime_error("native GPU result exceeds output path capacity");
            result.path=path;result.path_capacity=capacity;out[i]=result;
            if(result.length){download(path,work[i].slot.path,result.length*sizeof(uint32_t));std::reverse(path,path+result.length);}
        }
        collect();timing.execute_host_ns=elapsed(execute_start);
    }
};
thread_local std::string last_error;
template<class F>const char*guard(F fn){try{fn();return nullptr;}catch(const std::exception&e){last_error=e.what();return last_error.c_str();}}
}
extern "C" const char* h3d_gpu_create(const h3d_native::GpuStatic*s,void**out){return guard([&]{*out=new Device(*s);});}
extern "C" const char* h3d_gpu_update(void*p,const h3d_native::StateDelta*d,uint32_t n){return guard([&]{static_cast<Device*>(p)->update(d,n);});}
extern "C" const char* h3d_gpu_execute(void*p,const h3d_native::GpuQuery*q,h3d_native::GpuResult*r,uint32_t n){return guard([&]{static_cast<Device*>(p)->execute(q,r,n);});}
extern "C" void h3d_gpu_destroy(void*p){delete static_cast<Device*>(p);}

extern "C" const char* h3d_gpu_timing(void*p,h3d_native::GpuTiming*out){return guard([&]{*out=static_cast<Device*>(p)->timing;});}
