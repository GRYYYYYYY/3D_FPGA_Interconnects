#include "router.hpp"
#include <cuda_runtime.h>
#include <algorithm>
#include <chrono>
#include <memory>
#include <stdexcept>

namespace h3d {
namespace {
using Distance = unsigned long long;
constexpr Distance GPU_INF=0x3fffffffffffffffULL;
void check(cudaError_t e) {
    if(e!=cudaSuccess) throw std::runtime_error(std::string("CUDA: ")+cudaGetErrorString(e));
}
template<class T> void allocate(T*& p,size_t n) {
    check(cudaMalloc(reinterpret_cast<void**>(&p),std::max(n,size_t(1))*sizeof(T)));
}
template<class T> void upload(T* dst,const std::vector<T>& src) {
    if(!src.empty()) check(cudaMemcpy(dst,src.data(),src.size()*sizeof(T),cudaMemcpyHostToDevice));
}
__global__ void reset_state(uint32_t n,Distance* distance,uint32_t* marks) {
    uint32_t v=blockIdx.x*blockDim.x+threadIdx.x;
    if(v<n) { distance[v]=GPU_INF; marks[v]=0; }
}
__global__ void make_costs(uint32_t m,const uint32_t* dst,const uint32_t* base,const uint32_t* vertical,
                           const uint32_t* capacity,const uint32_t* occupancy,const uint32_t* history,
                           const char* allow,uint32_t present,uint32_t penalty,bool hard,uint32_t* cost) {
    uint32_t e=blockIdx.x*blockDim.x+threadIdx.x;
    if(e>=m) return;
    auto v=dst[e];
    cost[e]=!allow[v] || (hard && occupancy[v]>=capacity[v]) ? COST_INF :
        candidate_cost({base[e],history[v],occupancy[v],capacity[v],present,penalty,vertical[e],0});
}
__global__ void seed(uint32_t count,const uint32_t* roots,Distance* distance,uint32_t* frontier) {
    uint32_t i=blockIdx.x*blockDim.x+threadIdx.x;
    if(i<count) { distance[roots[i]]=0; frontier[i]=roots[i]; }
}
// One warp per active vertex, rather than scanning every incoming edge each
// round. All concurrent distance accesses are atomic. A per-round marker keeps
// the next frontier bounded by n, even when many edges improve the same vertex.
__global__ void expand(uint32_t count,const uint32_t* frontier,const uint32_t* offset,
                       const uint32_t* outgoing,const uint32_t* dst,const uint32_t* cost,
                       Distance* distance,uint32_t* marks,uint32_t epoch,
                       uint32_t* next,uint32_t* next_count) {
    uint32_t thread=blockIdx.x*blockDim.x+threadIdx.x;
    uint32_t item=thread/32,lane=thread%32;
    if(item>=count) return;
    auto u=frontier[item];
    auto du=atomicAdd(distance+u,0ULL);
    for(uint32_t a=offset[u]+lane;a<offset[u+1];a+=32) {
        auto e=outgoing[a],w=cost[e];
        if(w==COST_INF || du==GPU_INF) continue;
        auto v=dst[e]; auto candidate=du+w;
        if(candidate<atomicMin(distance+v,candidate) && atomicExch(marks+v,epoch)!=epoch) {
            next[atomicAdd(next_count,1U)]=v;
        }
    }
}
// Construct predecessors only after distances converge. Every selected edge is
// tight and strictly decreases distance in reverse, preventing torn parent/
// distance races and predecessor cycles. Only the requested path leaves GPU.
__global__ void trace(uint32_t n,uint32_t sink,const uint32_t* offset,const uint32_t* incoming,
                      const uint32_t* src,const uint32_t* cost,const Distance* distance,
                      uint32_t* path,int* length) {
    if(distance[sink]==GPU_INF) { *length=-1; return; }
    uint32_t v=sink,count=0;
    while(distance[v]!=0) {
        uint32_t best=UINT32_MAX,best_src=UINT32_MAX;
        for(uint32_t a=offset[v];a<offset[v+1];++a) {
            auto e=incoming[a],u=src[e],w=cost[e];
            if(w!=COST_INF && distance[u]!=GPU_INF && distance[u]+w==distance[v] &&
               (u<best_src || (u==best_src && e<best))) { best=e; best_src=u; }
        }
        if(best==UINT32_MAX || count>=n) { *length=-2; return; }
        path[count++]=best; v=best_src;
    }
    *length=int(count);
}
}

struct CudaSearch::Impl {
    uint32_t n=0,m=0,epoch=0;
    uint32_t *out_offset=nullptr,*outgoing=nullptr,*in_offset=nullptr,*incoming=nullptr;
    uint32_t *src=nullptr,*dst=nullptr,*base=nullptr,*vertical=nullptr,*capacity=nullptr;
    uint32_t *occupancy=nullptr,*history=nullptr,*cost=nullptr,*marks=nullptr;
    uint32_t *front=nullptr,*next=nullptr,*next_count=nullptr,*roots=nullptr,*path=nullptr;
    char* allow=nullptr; Distance* distance=nullptr; int* length=nullptr;
    bool prepared=false;
    std::vector<uint32_t> seeded_roots;
    GpuMetrics stats;
    ~Impl() {
        cudaFree(out_offset);cudaFree(outgoing);cudaFree(in_offset);cudaFree(incoming);
        cudaFree(src);cudaFree(dst);cudaFree(base);cudaFree(vertical);cudaFree(capacity);
        cudaFree(occupancy);cudaFree(history);cudaFree(cost);cudaFree(marks);
        cudaFree(front);cudaFree(next);cudaFree(next_count);cudaFree(roots);cudaFree(path);
        cudaFree(allow);cudaFree(distance);cudaFree(length);
    }
};
CudaSearch::CudaSearch(const Graph& g):impl(nullptr) {
    int devices=0;check(cudaGetDeviceCount(&devices));
    if(!devices) throw std::runtime_error("No CUDA device available");
    auto p=std::make_unique<Impl>();p->n=g.nodes.size();p->m=g.edges.size();
    if(p->n>uint32_t(INT32_MAX)) throw std::runtime_error("CUDA path exceeds supported size");
    std::vector<uint32_t> in_offset(p->n+1,0),incoming(p->m),src(p->m),dst(p->m),base(p->m),vertical(p->m),capacity(p->n);
    for(uint32_t v=0;v<p->n;++v) capacity[v]=g.nodes[v].capacity;
    for(const auto& e:g.edges) ++in_offset[e.dst+1];
    for(uint32_t i=1;i<=p->n;++i) in_offset[i]+=in_offset[i-1];
    auto cursor=in_offset;
    for(uint32_t e=0;e<p->m;++e) {
        src[e]=g.edges[e].src;dst[e]=g.edges[e].dst;base[e]=g.edges[e].base;vertical[e]=g.edges[e].vertical;
        incoming[cursor[dst[e]]++]=e;
    }
    allocate(p->out_offset,p->n+1);allocate(p->outgoing,p->m);allocate(p->in_offset,p->n+1);allocate(p->incoming,p->m);
    allocate(p->src,p->m);allocate(p->dst,p->m);allocate(p->base,p->m);allocate(p->vertical,p->m);allocate(p->capacity,p->n);
    allocate(p->occupancy,p->n);allocate(p->history,p->n);allocate(p->cost,p->m);allocate(p->marks,p->n);
    allocate(p->front,p->n);allocate(p->next,p->n);allocate(p->next_count,1);allocate(p->roots,p->n);allocate(p->path,p->n);
    allocate(p->allow,p->n);allocate(p->distance,p->n);allocate(p->length,1);
    upload(p->out_offset,g.offsets);upload(p->outgoing,g.adjacency);upload(p->in_offset,in_offset);upload(p->incoming,incoming);
    upload(p->src,src);upload(p->dst,dst);upload(p->base,base);upload(p->vertical,vertical);upload(p->capacity,capacity);
    p->stats.h2d_bytes=uint64_t(2)*(p->n+1)*sizeof(uint32_t)+uint64_t(6)*p->m*sizeof(uint32_t)+uint64_t(p->n)*sizeof(uint32_t);
    impl=p.release();
}
CudaSearch::~CudaSearch(){delete impl;}
void CudaSearch::prepare(const std::vector<uint32_t>& occupancy,const std::vector<uint32_t>& history,
                         const std::vector<char>& allow,uint32_t present,uint32_t penalty,bool hard) {
    auto& p=*impl;
    if(occupancy.size()!=p.n || history.size()!=p.n || allow.size()!=p.n)
        throw std::runtime_error("Invalid CUDA snapshot size");
    auto started=std::chrono::steady_clock::now();
    upload(p.occupancy,occupancy);upload(p.history,history);upload(p.allow,allow);
    reset_state<<<(p.n+255)/256,256>>>(p.n,p.distance,p.marks);
    check(cudaGetLastError());
    if(p.m) {
        make_costs<<<(p.m+255)/256,256>>>(p.m,p.dst,p.base,p.vertical,p.capacity,p.occupancy,p.history,p.allow,present,penalty,hard,p.cost);
        check(cudaGetLastError());
    }
    check(cudaDeviceSynchronize());
    p.seeded_roots.clear();p.epoch=0;p.prepared=true;
    ++p.stats.preparations;p.stats.h2d_bytes+=uint64_t(p.n)*(2*sizeof(uint32_t)+sizeof(char));
    p.stats.prepare_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
}
std::vector<uint32_t> CudaSearch::search_path(const std::vector<uint32_t>& roots,uint32_t sink) {
    auto& p=*impl;
    if(!p.prepared || sink>=p.n || roots.size()>p.n || roots.size()<p.seeded_roots.size() ||
       !std::equal(p.seeded_roots.begin(),p.seeded_roots.end(),roots.begin()))
        throw std::runtime_error("CUDA roots must grow within a prepared snapshot");
    auto started=std::chrono::steady_clock::now();
    uint32_t count=roots.size()-p.seeded_roots.size();
    if(count) {
        std::vector<uint32_t> added(roots.begin()+p.seeded_roots.size(),roots.end());
        auto sorted=roots;std::sort(sorted.begin(),sorted.end());
        if(sorted.back()>=p.n || std::adjacent_find(sorted.begin(),sorted.end())!=sorted.end())
            throw std::runtime_error("Invalid or duplicate CUDA root");
        upload(p.roots,added);p.stats.h2d_bytes+=uint64_t(count)*sizeof(uint32_t);
        seed<<<(count+255)/256,256>>>(count,p.roots,p.distance,p.front);check(cudaGetLastError());
        p.seeded_roots=roots;
    }
    uint32_t rounds=0;
    while(count) {
        if(++rounds>p.n) throw std::runtime_error("CUDA frontier failed to converge");
        if(++p.epoch==0) { check(cudaMemset(p.marks,0,p.n*sizeof(uint32_t)));p.epoch=1; }
        ++p.stats.rounds;p.stats.frontier_vertices+=count;
        check(cudaMemset(p.next_count,0,sizeof(uint32_t)));
        expand<<<(count+7)/8,256>>>(count,p.front,p.out_offset,p.outgoing,p.dst,p.cost,p.distance,p.marks,p.epoch,p.next,p.next_count);
        check(cudaGetLastError());
        check(cudaMemcpy(&count,p.next_count,sizeof(uint32_t),cudaMemcpyDeviceToHost));p.stats.d2h_bytes+=sizeof(uint32_t);
        if(count>p.n) throw std::runtime_error("CUDA frontier overflow");
        std::swap(p.front,p.next);
    }
    trace<<<1,1>>>(p.n,sink,p.in_offset,p.incoming,p.src,p.cost,p.distance,p.path,p.length);check(cudaGetLastError());
    int length=0;check(cudaMemcpy(&length,p.length,sizeof(int),cudaMemcpyDeviceToHost));p.stats.d2h_bytes+=sizeof(int);
    if(length < -1 || length>int(p.n)) throw std::runtime_error("Invalid converged CUDA predecessor chain");
    std::vector<uint32_t> path(length>0?length:0);
    if(length>0) {
        check(cudaMemcpy(path.data(),p.path,length*sizeof(uint32_t),cudaMemcpyDeviceToHost));
        p.stats.d2h_bytes+=uint64_t(length)*sizeof(uint32_t);std::reverse(path.begin(),path.end());
    }
    ++p.stats.searches;p.stats.search_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
    return path;
}
GpuMetrics CudaSearch::metrics() const {return impl->stats;}
}
