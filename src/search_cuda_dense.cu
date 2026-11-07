#include "router.hpp"
#include <cuda_runtime.h>
#include <algorithm>
#include <memory>
#include <stdexcept>
#include <string>
namespace h3d {
namespace {
void check(cudaError_t e) { if(e!=cudaSuccess) throw std::runtime_error(std::string("CUDA: ")+cudaGetErrorString(e)); }
template<class T> void allocate(T*& p,size_t n) { check(cudaMalloc(reinterpret_cast<void**>(&p),std::max(n,size_t(1))*sizeof(T))); }
constexpr unsigned long long GPU_INF=0x3fffffffffffffffULL;
// Synchronous pull relaxation: exactly one writer per vertex. Predecessors and
// distances are double buffered, so no torn distance/parent pair is possible.
__global__ void relax(uint32_t n,const uint32_t* offset,const uint32_t* incoming,
                      const uint32_t* src,const uint32_t* dst_cost,
                      const unsigned long long* before,unsigned long long* after,
                      const int64_t* old_parent,int64_t* new_parent,int* changed) {
    uint32_t v=blockIdx.x*blockDim.x+threadIdx.x;
    if(v>=n) return;
    auto best=before[v]; auto parent=old_parent[v];
    for(uint32_t a=offset[v];a<offset[v+1];++a) {
        auto e=incoming[a]; auto w=dst_cost[e];
        if(w==COST_INF || before[src[e]]==GPU_INF) continue;
        auto candidate=before[src[e]]+w;
        if(candidate<best) { best=candidate; parent=e; }
    }
    after[v]=best; new_parent[v]=parent;
    if(best!=before[v]) atomicExch(changed,1);
}
}
struct CudaDenseSearch::Impl {
    uint32_t n=0,m=0;
    uint32_t *offset=nullptr,*incoming=nullptr,*src=nullptr,*cost=nullptr;
    unsigned long long *a=nullptr,*b=nullptr;
    int64_t *pa=nullptr,*pb=nullptr; int* changed=nullptr;
    ~Impl() { cudaFree(offset);cudaFree(incoming);cudaFree(src);cudaFree(cost);cudaFree(a);cudaFree(b);cudaFree(pa);cudaFree(pb);cudaFree(changed); }
};
CudaDenseSearch::CudaDenseSearch(const Graph& g):impl(nullptr) {
    int devices=0; check(cudaGetDeviceCount(&devices)); if(!devices) throw std::runtime_error("No CUDA device available");
    auto p=std::make_unique<Impl>(); p->n=g.nodes.size();p->m=g.edges.size();
    std::vector<uint32_t> offset(p->n+1,0),incoming(p->m),src(p->m);
    for(const auto& e:g.edges) ++offset[e.dst+1];
    for(uint32_t i=1;i<=p->n;++i) offset[i]+=offset[i-1];
    auto cursor=offset;
    for(uint32_t i=0;i<p->m;++i) { incoming[cursor[g.edges[i].dst]++]=i;src[i]=g.edges[i].src; }
    allocate(p->offset,offset.size());allocate(p->incoming,p->m);allocate(p->src,p->m);allocate(p->cost,p->m);
    allocate(p->a,p->n);allocate(p->b,p->n);allocate(p->pa,p->n);allocate(p->pb,p->n);allocate(p->changed,1);
    check(cudaMemcpy(p->offset,offset.data(),offset.size()*sizeof(uint32_t),cudaMemcpyHostToDevice));
    check(cudaMemcpy(p->incoming,incoming.data(),p->m*sizeof(uint32_t),cudaMemcpyHostToDevice));
    check(cudaMemcpy(p->src,src.data(),p->m*sizeof(uint32_t),cudaMemcpyHostToDevice));
    impl=p.release();
}
CudaDenseSearch::~CudaDenseSearch(){delete impl;}
std::vector<int64_t> CudaDenseSearch::search(const std::vector<uint32_t>& roots,uint32_t sink,const std::vector<uint32_t>& costs) {
    auto& p=*impl;
    if(costs.size()!=p.m || sink>=p.n) throw std::runtime_error("invalid CUDA search input");
    std::vector<unsigned long long> distance(p.n,GPU_INF); std::vector<int64_t> parent(p.n,-1);
    for(auto r:roots) distance.at(r)=0;
    check(cudaMemcpy(p.cost,costs.data(),p.m*sizeof(uint32_t),cudaMemcpyHostToDevice));
    check(cudaMemcpy(p.a,distance.data(),p.n*sizeof(unsigned long long),cudaMemcpyHostToDevice));
    check(cudaMemcpy(p.pa,parent.data(),p.n*sizeof(int64_t),cudaMemcpyHostToDevice));
    // n-1 rounds suffice for positive-weight simple shortest paths; do not stop
    // when the sink is first reached, since later rounds may improve it.
    for(uint32_t round=1;round<p.n;++round) {
        check(cudaMemset(p.changed,0,sizeof(int)));
        relax<<<(p.n+255)/256,256>>>(p.n,p.offset,p.incoming,p.src,p.cost,p.a,p.b,p.pa,p.pb,p.changed);
        check(cudaGetLastError()); int changed=0;
        check(cudaMemcpy(&changed,p.changed,sizeof(int),cudaMemcpyDeviceToHost));
        std::swap(p.a,p.b);std::swap(p.pa,p.pb);
        if(!changed) break;
    }
    check(cudaMemcpy(parent.data(),p.pa,p.n*sizeof(int64_t),cudaMemcpyDeviceToHost));
    return parent;
}
}
