#pragma once
#include "gpu_api.hpp"
#include "model_io.hpp"

namespace h3d_native {
// A real partial native search, distinct from H3DNQR1 route-tree-only snapshots.
// Arrays follow in the order below. Full occupancy/history makes each capture
// independently replayable. Heap order (including stale entries) is preserved;
// only the unused sentinel is omitted. All floats are unquantized native values.
struct TakeoverHeader {
    char magic[8]={'H','3','D','T','A','K','2','\0'};
    uint32_t version=2,header_bytes=sizeof(TakeoverHeader);
    QueryHeader query;
    uint32_t nodes=0,labels=0,heap=0,active=0,base=0,tree=0,heap_arity=0,iteration=0;
    int32_t target[6]={};
    uint32_t max_rounds=1000000;float bucket_relative=0.01f;
    uint32_t pending_deltas=0,reserved=0;
    float post_target_prune_fac=1.2f,post_target_prune_offset=0.f;
    uint32_t delay_budget_present=0,delay_budget_algorithm=0;
    float short_path_criticality=0.f,min_delay=0.f,target_delay=0.f,max_delay=0.f;
};
struct NativeLabel {uint32_t node,prev;float backward,total,upstream;};
struct NativeHeap {float priority;uint32_t node;};
struct NativeTree {uint32_t node,parent,re_expand;float delay,upstream,downstream;};
struct NativeSample {uint64_t search_ns=0,pops=0;float cost=INFINITY;std::vector<uint32_t>path;};
struct Takeover {
    TakeoverHeader header;
    std::vector<State>state;
    std::vector<NativeLabel>labels;
    std::vector<NativeHeap>heap;
    std::vector<uint32_t>active;
    std::vector<float>base;
    std::vector<NativeTree>tree;
    std::vector<Seed>seeds;
    std::vector<StateDelta>deltas;
    void save(const std::string&path)const {
        std::ofstream f(path,std::ios::binary);f.exceptions(std::ios::failbit|std::ios::badbit);
        f.write(reinterpret_cast<const char*>(&header),sizeof(header));
        auto put=[&](const auto&v){f.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(v[0]));};
        put(state);put(labels);put(heap);put(active);put(base);put(tree);put(seeds);put(deltas);
    }
    static Takeover load(const std::string&path){
        std::ifstream f(path,std::ios::binary);Takeover t;t.header=read<TakeoverHeader>(f);const auto&h=t.header;
        require(std::string(h.magic,7)=="H3DTAK2"&&h.version==2&&h.header_bytes==sizeof(h),"bad takeover ABI");
        require(h.heap_arity==2||h.heap_arity==4,"unsupported native heap arity");
        require(h.labels<=h.nodes&&h.active<=h.labels&&h.query.seeds<=h.labels,"bad takeover counts");
        t.state=read_vector<State>(f,h.nodes);t.labels=read_vector<NativeLabel>(f,h.labels);
        t.heap=read_vector<NativeHeap>(f,h.heap);t.active=read_vector<uint32_t>(f,h.active);
        t.base=read_vector<float>(f,h.base);t.tree=read_vector<NativeTree>(f,h.tree);t.seeds=read_vector<Seed>(f,h.query.seeds);t.deltas=read_vector<StateDelta>(f,h.pending_deltas);
        require(f.peek()==EOF,"trailing takeover bytes");return t;
    }
    GpuQuery gpu_query()const {
        GpuQuery q{};q.sink=header.query.sink;q.seed_count=seeds.size();q.base_count=base.size();
        std::copy(header.query.box,header.query.box+6,q.box);std::copy(header.target,header.target+6,q.target);
        q.criticality=header.query.criticality;q.astar=header.query.astar;q.astar_offset=header.query.astar_offset;
        q.bend_cost=header.query.bend_cost;q.present=header.query.present;q.max_rounds=header.max_rounds;q.bucket_relative=header.bucket_relative;
        q.seeds=seeds.data();q.base_costs=base.data();q.active=active.data();q.active_count=active.size();return q;
    }
};
static_assert(sizeof(NativeLabel)==20&&sizeof(NativeHeap)==8&&sizeof(NativeTree)==24);
}
