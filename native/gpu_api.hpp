#pragma once
#include "hybrid_snapshot.hpp"
#include "model.hpp"

namespace h3d_native {
constexpr uint32_t gpu_api_version=3;
struct State {int32_t occupancy;float accumulated;};
struct StateDelta {uint32_t node;State state;};
struct StateHeader {
    char magic[8]={'H','3','D','S','T','A','1','\0'};
    uint32_t version=1,nodes=0,base_count=0,deltas=0;
    int32_t target[6]={};
};
struct GpuStatic {
    uint32_t version=gpu_api_version,slots=1;
    GraphHeader graph;const Node*nodes;const Edge*edges;const uint32_t*native_to_edge;
    ModelView model;const State*state;
};
struct GpuQuery {
    uint32_t sink,seed_count,base_count,max_rounds=1000000;
    int32_t box[6],target[6];
    float criticality,astar,astar_offset,bend_cost,present,bucket_relative=0.01f;
    const Seed*seeds;const float*base_costs;
    // All labels preserve CPU dominance/prefixes; only the unexpanded heap
    // frontier is active. Null/zero retains snapshot-replay all-seed behavior.
    uint32_t active_count=0;const uint32_t*active=nullptr;
};
struct GpuResult {
    uint32_t status=0,length=0,path_capacity=0,reserved=0;
    float cost=INFINITY;
    uint64_t visits=0,rounds=0,edges=0;
    uint32_t*path=nullptr;
};
// One record per update/execute batch. Host durations and device event spans
// are different clocks and MUST NOT be added. Disabled unless H3D_GPU_TIMING=1.
struct GpuTiming {
    uint32_t version=gpu_api_version,enabled=0;
    uint64_t update_host_ns=0,execute_host_ns=0,allocation_host_ns=0;
    uint64_t state_h2d_host_ns=0,query_h2d_host_ns=0,launch_host_ns=0;
    uint64_t sync_host_ns=0,d2h_host_ns=0,event_collect_host_ns=0;
    uint64_t state_h2d_event_ns=0,update_kernel_event_ns=0;
    uint64_t query_h2d_event_ns=0,search_kernel_event_ns=0,d2h_event_ns=0;
    uint64_t h2d_bytes=0,d2h_bytes=0;
};
using CreateFn=const char*(*)(const GpuStatic*,void**);
using UpdateFn=const char*(*)(void*,const StateDelta*,uint32_t);
using ExecuteFn=const char*(*)(void*,const GpuQuery*,GpuResult*,uint32_t);
using DestroyFn=void(*)(void*);
using TimingFn=const char*(*)(void*,GpuTiming*);
static_assert(sizeof(State)==8 && sizeof(StateDelta)==12 && sizeof(StateHeader)==48);
}
extern "C" {
const char* h3d_gpu_create(const h3d_native::GpuStatic*,void**);
const char* h3d_gpu_update(void*,const h3d_native::StateDelta*,uint32_t);
const char* h3d_gpu_execute(void*,const h3d_native::GpuQuery*,h3d_native::GpuResult*,uint32_t);
void h3d_gpu_destroy(void*);
const char* h3d_gpu_timing(void*,h3d_native::GpuTiming*);
}
