#pragma once
#include "router.hpp"
#include <memory>
#include <array>
#include <functional>

#ifdef __CUDACC__
#define TARGET_HD __host__ __device__
#else
#define TARGET_HD
#endif
namespace h3d {
// Finite congestion never becomes the unreachable sentinel. All label sums
// are 64-bit; at the supported 2^31 nodes even a simple capped path fits.
constexpr uint64_t TARGET_FINITE_MAX=(1ULL<<30)-2;
constexpr uint64_t TARGET_INF=(1ULL<<62)-1;
TARGET_HD inline uint64_t finite_mul(uint64_t a,uint64_t b) {
    // min(L,a*b) = min(L,min(L,a)*min(L,b)) for nonnegative integers.
    // L^2 < 2^60, so the product cannot overflow uint64_t. Avoid a costly
    // variable 64-bit division for every factor of every relaxed edge.
    a=a>TARGET_FINITE_MAX?TARGET_FINITE_MAX:a;
    b=b>TARGET_FINITE_MAX?TARGET_FINITE_MAX:b;
    uint64_t product=a*b;
    return product>TARGET_FINITE_MAX?TARGET_FINITE_MAX:product;
}
TARGET_HD inline uint64_t timing_cost(uint32_t delay_ps,uint32_t units,uint32_t occ,uint32_t capacity,
                                      uint32_t history,uint32_t present,uint32_t criticality,uint32_t norm_ps,bool hard) {
    if(!capacity || (hard && occ>=capacity))return TARGET_INF;
    uint64_t excess=occ>=capacity ? uint64_t(occ)-capacity+1 : 0;
    uint64_t pressure=finite_mul(present,excess);
    uint64_t congestion=finite_mul(units,uint64_t(history)+1);
    congestion=finite_mul(congestion,pressure+1);
    congestion=finite_mul(congestion,norm_ps);
    congestion=finite_mul(congestion,1000-criticality);
    uint64_t delay=finite_mul(criticality,delay_ps);
    uint64_t sum=congestion+delay+1;
    return sum>TARGET_FINITE_MAX ? TARGET_FINITE_MAX : sum;
}
TARGET_HD inline uint64_t target_lower_bound(int x,int y,int z,int tx,int ty,int tz,
                                            uint32_t max_step,uint32_t crit,uint32_t norm_ps,uint32_t span=0,uint64_t rate=0) {
    uint64_t d=uint64_t(x>tx?x-tx:tx-x)+uint64_t(y>ty?y-ty:ty-y)+uint64_t(z>tz?z-tz:tz-z);
    uint64_t hops=(d+max_step-1)/max_step;
    uint64_t minimum=timing_cost(0,1,0,1,0,0,crit,norm_ps,false);
    uint64_t old=hops*minimum;
    uint64_t geometric=d>span?((d-span)*rate)>>16:0;
    return old>geometric?old:geometric;
}
struct StateDelta { uint32_t node,occupancy,history; };
struct TreeSeed { uint32_t node; uint64_t delay_ps; };
struct WindowBox { int xlow,ylow,xhigh,yhigh; };
// CSR tile index includes every layer and every tile touched by a node.
struct SpatialIndex {
    int width=1,height=1;
    std::vector<uint32_t> offsets,vertices;
    explicit SpatialIndex(const Graph&);
};
struct TimingModel {
    std::vector<uint32_t> delay_ps, units, spans;
    std::array<uint64_t,991> spatial_rates{};
    uint32_t norm_ps=1,max_step=1;
};
TimingModel timing_model(const Graph&,const std::string& delay_file);
class TargetSearch {
public:
    virtual ~TargetSearch()=default;
    virtual void update(const std::vector<StateDelta>&)=0;
    virtual void begin_tree()=0;
    virtual void add_tree(const std::vector<TreeSeed>&)=0;
    // Exact minimum of weighted prefix delay + new branch cost in this window.
    // Existing tree vertices are seeds, never destinations of a new branch.
    virtual std::vector<uint32_t> search(const std::vector<uint32_t>& window,uint32_t sink,
                                        uint32_t criticality,uint32_t present,bool hard)=0;
    virtual std::vector<uint32_t> search_box(WindowBox,uint32_t sink,uint32_t criticality,uint32_t present,bool hard)=0;
    virtual GpuMetrics metrics() const=0;
};
std::unique_ptr<TargetSearch> cpu_target_search(const Graph&,const TimingModel&);
struct TargetFeedback {
    std::string criticality_file; // empty means finish the persistent session
    uint32_t threshold=700,max_connections=2048;
    bool negotiate=false;
};
Result route_target_session(const Graph&,const std::vector<Net>&,const Options&,
                            const std::function<TargetFeedback(const Result&)>& checkpoint);
#ifdef H3D_CUDA
std::unique_ptr<TargetSearch> cuda_target_search(const Graph&,const TimingModel&,uint32_t bucket_width,bool persistent=true);
#endif
}
