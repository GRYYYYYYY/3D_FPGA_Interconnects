#include "target_router.hpp"
#include <cuda_runtime.h>
#include <cooperative_groups.h>
#include <algorithm>
#include <chrono>
#include <stdexcept>

namespace h3d {
namespace {
using Label=unsigned long long;
struct DeviceNode { int x,y,z;uint32_t capacity,units,span; };
struct DeviceEdge {uint32_t src,dst,delay;};
struct Control {Label minimum,best;uint32_t count,visits,window_size;};
void ck(cudaError_t e){if(e!=cudaSuccess)throw std::runtime_error(std::string("target CUDA: ")+cudaGetErrorString(e));}
template<class T>void alloc(T*& p,size_t n){ck(cudaMalloc(reinterpret_cast<void**>(&p),std::max(n,size_t(1))*sizeof(T)));}
template<class T>void copy(T* p,const std::vector<T>& v){if(!v.empty())ck(cudaMemcpy(p,v.data(),v.size()*sizeof(T),cudaMemcpyHostToDevice));}
__global__ void apply_state(uint32_t n,const StateDelta* changes,uint32_t* occ,uint32_t* history){auto i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n){auto c=changes[i];occ[c.node]=c.occupancy;history[c.node]=c.history;}}
__global__ void apply_tree(uint32_t n,const TreeSeed* changes,uint32_t epoch,uint32_t* tree,Label* prefix){auto i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n){auto c=changes[i];tree[c.node]=epoch;prefix[c.node]=c.delay_ps;}}
__global__ void init_window(uint32_t n,const uint32_t* window,uint32_t epoch,uint32_t* allowed,Label* dist,uint32_t* marks){auto i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n){auto v=window[i];allowed[v]=epoch;dist[v]=TARGET_INF;marks[v]=0;}}
__global__ void reset_control(Control* c,const Label* dist,uint32_t sink){c->minimum=TARGET_INF;c->best=dist[sink];c->count=0;c->visits=0;c->window_size=0;}
__global__ void start_query(Control* c,Label* dist,uint32_t sink){dist[sink]=TARGET_INF;c->minimum=TARGET_INF;c->best=TARGET_INF;c->count=0;c->visits=0;c->window_size=0;}
__device__ Label heuristic(uint32_t v,const DeviceNode* nodes,uint32_t sink,uint32_t step,uint32_t crit,uint32_t norm,Label rate){auto a=nodes[v],b=nodes[sink];return target_lower_bound(a.x,a.y,a.z,b.x,b.y,b.z,step,crit,norm,a.span,rate);}
__global__ void seed_window(uint32_t n,const uint32_t* window,uint32_t tree_epoch,const uint32_t* tree,
                            const Label* prefix,Label* dist,uint32_t* front,Control* ctrl,const DeviceNode* nodes,
                            uint32_t sink,uint32_t step,uint32_t crit,uint32_t norm,Label rate) {
    auto i=blockIdx.x*blockDim.x+threadIdx.x;
    if(i<n){auto v=window[i];if(tree[v]==tree_epoch){Label d=Label(crit)*prefix[v];dist[v]=d;front[atomicAdd(&ctrl->count,1U)]=v;atomicMin(&ctrl->minimum,d+heuristic(v,nodes,sink,step,crit,norm,rate));}}
}
// Every node is owned by the lowest XY tile in its intersection with the box.
// This makes spanning-node initialization unique without racing dedup atomics.
__global__ void init_box(WindowBox b,uint32_t width,const uint32_t* offsets,const uint32_t* vertices,
                        const DeviceNode* nodes,uint32_t epoch,uint32_t* allowed,Label* dist,uint32_t* marks,
                        uint32_t tree_epoch,const uint32_t* tree,const Label* prefix,uint32_t* front,
                        Control* ctrl,uint32_t sink,uint32_t step,uint32_t crit,uint32_t norm,Label rate) {
    uint32_t columns=b.xhigh-b.xlow+1,tiles=columns*(b.yhigh-b.ylow+1);
    for(uint32_t tile=blockIdx.x;tile<tiles;tile+=gridDim.x) {
        int x=b.xlow+tile%columns,y=b.ylow+tile/columns;
        uint32_t cell=y*width+x;
        for(uint32_t i=offsets[cell]+threadIdx.x;i<offsets[cell+1];i+=blockDim.x) {
            uint32_t v=vertices[i];auto node=nodes[v];
            if(x!=max(node.x,b.xlow) || y!=max(node.y,b.ylow))continue;
            allowed[v]=epoch;marks[v]=0;
            Label d=tree[v]==tree_epoch?Label(crit)*prefix[v]:TARGET_INF;dist[v]=d;
            atomicAdd(&ctrl->window_size,1U);
            if(d!=TARGET_INF){front[atomicAdd(&ctrl->count,1U)]=v;atomicMin(&ctrl->minimum,d+heuristic(v,nodes,sink,step,crit,norm,rate));}
        }
    }
}
__device__ void enqueue(uint32_t v,Label f,uint32_t round,uint32_t* marks,uint32_t* next,Control* ctrl) {
    atomicMin(&ctrl->minimum,f);
    if(atomicExch(marks+v,round)!=round)next[atomicAdd(&ctrl->count,1U)]=v;
}
// A priority band limits speculative work. Termination uses the minimum lower
// bound of ALL pending labels, never the first discovery of the sink.
__global__ void expand_target(uint32_t count,const uint32_t* front,const uint32_t* offset,const uint32_t* outgoing,
                              const DeviceEdge* edges,const DeviceNode* nodes,const uint32_t* occ,const uint32_t* history,
                              const uint32_t* allowed,uint32_t window_epoch,const uint32_t* tree,uint32_t tree_epoch,
                              Label* dist,uint32_t* marks,uint32_t round,uint32_t* next,Control* ctrl,
                              uint32_t sink,uint32_t step,uint32_t crit,uint32_t norm,uint32_t present,Label rate,bool hard,Label threshold) {
    auto thread=blockIdx.x*blockDim.x+threadIdx.x,item=thread/32,lane=thread%32;
    if(item>=count)return;
    auto u=front[item];Label du=atomicAdd(dist+u,0ULL),f=du+heuristic(u,nodes,sink,step,crit,norm,rate);
    Label best=atomicAdd(dist+sink,0ULL);
    if(f>=best || du==TARGET_INF)return;
    if(f>threshold){if(!lane)enqueue(u,f,round,marks,next,ctrl);return;}
    if(!lane)atomicAdd(&ctrl->visits,1U);
    for(uint32_t i=offset[u]+lane;i<offset[u+1];i+=32) {
        auto e=edges[outgoing[i]];auto v=e.dst;
        if(allowed[v]!=window_epoch || tree[v]==tree_epoch)continue;
        auto node=nodes[v];Label cost=timing_cost(e.delay,node.units,occ[v],node.capacity,history[v],present,crit,norm,hard);
        if(cost==TARGET_INF)continue;
        Label candidate=du+cost,priority=candidate+heuristic(v,nodes,sink,step,crit,norm,rate);
        if(priority>=atomicAdd(dist+sink,0ULL))continue;
        if(candidate<atomicMin(dist+v,candidate)) {
            if(v==sink)atomicMin(&ctrl->best,candidate);
            else enqueue(v,priority,round,marks,next,ctrl);
        }
    }
}
__global__ void trace_target(uint32_t n,uint32_t sink,const uint32_t* offset,const uint32_t* incoming,
                             const DeviceEdge* edges,const DeviceNode* nodes,const uint32_t* occ,const uint32_t* history,
                             const uint32_t* allowed,uint32_t window_epoch,const uint32_t* tree,uint32_t tree_epoch,
                             const Label* dist,uint32_t crit,uint32_t norm,uint32_t present,bool hard,uint32_t* path,int* length) {
    if(allowed[sink]!=window_epoch || dist[sink]==TARGET_INF){*length=-1;return;}
    uint32_t v=sink,count=0;
    while(tree[v]!=tree_epoch) {
        uint32_t best=UINT32_MAX,source=UINT32_MAX;auto node=nodes[v];
        for(auto i=offset[v];i<offset[v+1];++i){auto ei=incoming[i];auto e=edges[ei];
            if(allowed[e.src]!=window_epoch || dist[e.src]==TARGET_INF)continue;
            auto cost=timing_cost(e.delay,node.units,occ[v],node.capacity,history[v],present,crit,norm,hard);
            if(cost!=TARGET_INF && dist[e.src]+cost==dist[v] && (e.src<source || (e.src==source && ei<best))){best=ei;source=e.src;}}
        if(best==UINT32_MAX || count>=n){*length=-2;return;}path[count++]=best;v=source;
    }
    *length=int(count);
}
struct PersistentContext {
    const uint32_t *offset,*outgoing,*occ,*history,*allowed,*tree;
    const DeviceEdge* edges;const DeviceNode* nodes;
    Label* dist;uint32_t *marks,*front,*next;Control* ctrl;Label* totals;
    uint32_t window_epoch,tree_epoch,sink,step,crit,norm,present,bucket;
    Label rate;
    bool hard;
};
// One cooperative launch executes all priority bands. Grid barriers replace
// host round trips; the termination lower bound is identical to host stepping.
__global__ void persistent_target(PersistentContext p) {
    auto grid=cooperative_groups::this_grid();
    uint32_t rank=grid.thread_rank(),warp=rank/32,lane=rank%32,warps=grid.size()/32,round=0;
    if(rank==0){p.totals[0]=0;p.totals[1]=0;p.totals[2]=0;}
    grid.sync();
    uint32_t* front=p.front;uint32_t* next=p.next;
    while(true) {
        uint32_t count=p.ctrl->count;Label minimum=p.ctrl->minimum,best=p.ctrl->best;
        // Every thread must have captured the previous control before reset.
        grid.sync();
        if(!count || minimum>=best)break;
        if(++round>1000000){if(rank==0)p.totals[2]=1;break;}
        Label threshold=minimum+p.bucket;
        if(rank==0){p.ctrl->minimum=TARGET_INF;p.ctrl->best=p.dist[p.sink];p.ctrl->count=0;p.ctrl->visits=0;}
        grid.sync();
        for(uint32_t item=warp;item<count;item+=warps) {
            auto u=front[item];Label du=atomicAdd(p.dist+u,0ULL),f=du+heuristic(u,p.nodes,p.sink,p.step,p.crit,p.norm,p.rate);
            if(f>=atomicAdd(p.dist+p.sink,0ULL) || du==TARGET_INF)continue;
            if(f>threshold){if(!lane)enqueue(u,f,round,p.marks,next,p.ctrl);continue;}
            if(!lane)atomicAdd(&p.ctrl->visits,1U);
            for(uint32_t i=p.offset[u]+lane;i<p.offset[u+1];i+=32) {
                auto e=p.edges[p.outgoing[i]];auto v=e.dst;
                if(p.allowed[v]!=p.window_epoch || p.tree[v]==p.tree_epoch)continue;
                auto node=p.nodes[v];Label cost=timing_cost(e.delay,node.units,p.occ[v],node.capacity,p.history[v],p.present,p.crit,p.norm,p.hard);
                if(cost==TARGET_INF)continue;
                Label candidate=du+cost,priority=candidate+heuristic(v,p.nodes,p.sink,p.step,p.crit,p.norm,p.rate);
                if(priority>=atomicAdd(p.dist+p.sink,0ULL))continue;
                if(candidate<atomicMin(p.dist+v,candidate)) {
                    if(v==p.sink)atomicMin(&p.ctrl->best,candidate);
                    else enqueue(v,priority,round,p.marks,next,p.ctrl);
                }
            }
        }
        grid.sync();
        if(rank==0){++p.totals[0];p.totals[1]+=p.ctrl->visits;}
        auto swap=front;front=next;next=swap;
    }
}
class GpuSearch final:public TargetSearch {
    uint32_t n,m,step,norm,bucket,window_epoch=0,tree_epoch=0;
    DeviceNode* nodes=nullptr;DeviceEdge* edges=nullptr;
    uint32_t *out_offset=nullptr,*outgoing=nullptr,*in_offset=nullptr,*incoming=nullptr;
    uint32_t *occ=nullptr,*hist=nullptr,*allowed=nullptr,*tree=nullptr,*marks=nullptr,*front=nullptr,*next=nullptr,*window=nullptr,*path=nullptr;
    Label *prefix=nullptr,*dist=nullptr;StateDelta* updates=nullptr;TreeSeed* seeds=nullptr;Control* control=nullptr;int* length=nullptr;
    GpuMetrics stats;bool persistent;int persistent_blocks=0;Label* totals=nullptr;
    uint32_t *spatial_offset=nullptr,*spatial_vertices=nullptr;int spatial_width=0,spatial_height=0;
    std::array<uint64_t,991> rates;
    using Clock=std::chrono::steady_clock;
    double elapsed(Clock::time_point t)const{return std::chrono::duration<double>(Clock::now()-t).count();}
public:
    GpuSearch(const Graph& g,const TimingModel& model,uint32_t b,bool use_persistent):n(g.nodes.size()),m(g.edges.size()),step(model.max_step),norm(model.norm_ps),bucket(b),persistent(use_persistent) {
        if(n>INT32_MAX)throw std::runtime_error("target CUDA graph too large");rates=model.spatial_rates;
        std::vector<DeviceNode> hn(n);std::vector<DeviceEdge> he(m);std::vector<uint32_t> io(n+1),ie(m);
        for(uint32_t v=0;v<n;++v){auto x=g.nodes[v];hn[v]={x.xlow,x.ylow,x.zlow,x.capacity,model.units[v],model.spans[v]};}
        for(uint32_t e=0;e<m;++e){auto x=g.edges[e];he[e]={x.src,x.dst,model.delay_ps[e]};++io[x.dst+1];}
        for(uint32_t i=1;i<=n;++i)io[i]+=io[i-1];auto cursor=io;
        for(uint32_t e=0;e<m;++e)ie[cursor[he[e].dst]++]=e;
        alloc(nodes,n);alloc(edges,m);alloc(out_offset,n+1);alloc(outgoing,m);alloc(in_offset,n+1);alloc(incoming,m);
        alloc(occ,n);alloc(hist,n);alloc(allowed,n);alloc(tree,n);alloc(marks,n);alloc(front,n);alloc(next,n);alloc(window,n);alloc(path,n);
        alloc(prefix,n);alloc(dist,n);alloc(updates,n);alloc(seeds,n);alloc(control,1);alloc(length,1);alloc(totals,3);
        copy(nodes,hn);copy(edges,he);copy(out_offset,g.offsets);copy(outgoing,g.adjacency);copy(in_offset,io);copy(incoming,ie);
        ck(cudaMemset(occ,0,n*sizeof(uint32_t)));ck(cudaMemset(hist,0,n*sizeof(uint32_t)));
        ck(cudaMemset(allowed,0,n*sizeof(uint32_t)));ck(cudaMemset(tree,0,n*sizeof(uint32_t)));
        stats.h2d_bytes=uint64_t(n)*sizeof(DeviceNode)+uint64_t(m)*sizeof(DeviceEdge)+uint64_t(2)*(n+1)*4+uint64_t(2)*m*4;
        SpatialIndex index(g);spatial_width=index.width;spatial_height=index.height;
        alloc(spatial_offset,index.offsets.size());alloc(spatial_vertices,index.vertices.size());
        copy(spatial_offset,index.offsets);copy(spatial_vertices,index.vertices);
        stats.spatial_index_bytes=uint64_t(index.offsets.size()+index.vertices.size())*sizeof(uint32_t);stats.h2d_bytes+=stats.spatial_index_bytes;
        if(persistent){int device=0,active=0;cudaDeviceProp prop;ck(cudaGetDevice(&device));ck(cudaGetDeviceProperties(&prop,device));
            if(!prop.cooperativeLaunch)throw std::runtime_error("persistent target search requires cooperative launch support");
            ck(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&active,persistent_target,256,0));persistent_blocks=std::min(32,active*prop.multiProcessorCount);
            if(!persistent_blocks)throw std::runtime_error("no resident cooperative target grid");}
    }
    ~GpuSearch(){cudaFree(spatial_offset);cudaFree(spatial_vertices);cudaFree(nodes);cudaFree(edges);cudaFree(out_offset);cudaFree(outgoing);cudaFree(in_offset);cudaFree(incoming);cudaFree(occ);cudaFree(hist);cudaFree(allowed);cudaFree(tree);cudaFree(marks);cudaFree(front);cudaFree(next);cudaFree(window);cudaFree(path);cudaFree(prefix);cudaFree(dist);cudaFree(updates);cudaFree(seeds);cudaFree(control);cudaFree(length);cudaFree(totals);}
    void update(const std::vector<StateDelta>& values)override {
        if(values.empty())return;if(values.size()>n)throw std::runtime_error("too many sparse updates");auto t=Clock::now();
        copy(updates,values);apply_state<<<(values.size()+255)/256,256>>>(values.size(),updates,occ,hist);ck(cudaGetLastError());ck(cudaDeviceSynchronize());
        auto seconds=elapsed(t);stats.state_updates+=values.size();stats.h2d_bytes+=values.size()*sizeof(StateDelta);stats.prepare_seconds+=seconds;stats.state_update_seconds+=seconds;
    }
    void begin_tree()override {if(++tree_epoch==0){ck(cudaMemset(tree,0,n*sizeof(uint32_t)));tree_epoch=1;}}
    void add_tree(const std::vector<TreeSeed>& values)override {
        if(values.empty())return;if(values.size()>n)throw std::runtime_error("too many tree seeds");auto t=Clock::now();
        copy(seeds,values);apply_tree<<<(values.size()+255)/256,256>>>(values.size(),seeds,tree_epoch,tree,prefix);ck(cudaGetLastError());ck(cudaDeviceSynchronize());
        auto seconds=elapsed(t);stats.h2d_bytes+=values.size()*sizeof(TreeSeed);stats.prepare_seconds+=seconds;stats.tree_update_seconds+=seconds;
    }
    std::vector<uint32_t> search(const std::vector<uint32_t>& vertices,uint32_t sink,uint32_t crit,uint32_t present,bool hard)override {
        if(vertices.empty() || vertices.size()>n || sink>=n || crit>990)throw std::runtime_error("invalid target window");
        auto t=Clock::now();
        if(++window_epoch==0){ck(cudaMemset(allowed,0,n*sizeof(uint32_t)));window_epoch=1;}
        start_query<<<1,1>>>(control,dist,sink);ck(cudaGetLastError());
        copy(window,vertices);auto uploaded=Clock::now();stats.window_upload_seconds+=elapsed(t);
        init_window<<<(vertices.size()+255)/256,256>>>(vertices.size(),window,window_epoch,allowed,dist,marks);ck(cudaGetLastError());
        reset_control<<<1,1>>>(control,dist,sink);ck(cudaGetLastError());
        seed_window<<<(vertices.size()+255)/256,256>>>(vertices.size(),window,tree_epoch,tree,prefix,dist,front,control,nodes,sink,step,crit,norm,rates[crit]);ck(cudaGetLastError());
        Control c;ck(cudaMemcpy(&c,control,sizeof(c),cudaMemcpyDeviceToHost));
        stats.h2d_bytes+=vertices.size()*sizeof(uint32_t);stats.d2h_bytes+=sizeof(c);stats.window_vertices+=vertices.size();++stats.preparations;
        stats.window_h2d_bytes+=vertices.size()*sizeof(uint32_t);stats.window_init_seconds+=elapsed(uploaded);
        stats.prepare_seconds+=elapsed(t);
        return finish_search(vertices.size(),sink,crit,present,hard,c);
    }
    std::vector<uint32_t> search_box(WindowBox b,uint32_t sink,uint32_t crit,uint32_t present,bool hard)override {
        if(sink>=n || crit>990 || b.xlow<0 || b.ylow<0 || b.xhigh>=spatial_width || b.yhigh>=spatial_height || b.xlow>b.xhigh || b.ylow>b.yhigh)throw std::runtime_error("invalid target box");
        auto t=Clock::now();
        if(++window_epoch==0){ck(cudaMemset(allowed,0,n*sizeof(uint32_t)));window_epoch=1;}
        start_query<<<1,1>>>(control,dist,sink);ck(cudaGetLastError());
        uint32_t tiles=uint32_t(b.xhigh-b.xlow+1)*(b.yhigh-b.ylow+1);
        init_box<<<std::min(tiles,65535U),256>>>(b,spatial_width,spatial_offset,spatial_vertices,nodes,window_epoch,allowed,dist,marks,tree_epoch,tree,prefix,front,control,sink,step,crit,norm,rates[crit]);ck(cudaGetLastError());
        Control c;ck(cudaMemcpy(&c,control,sizeof(c),cudaMemcpyDeviceToHost));
        // Kernel arguments carry the descriptor; count its logical payload in
        // H2D, separately from the once-only index, not as a node-ID upload.
        stats.h2d_bytes+=sizeof(b);stats.window_h2d_bytes+=sizeof(b);stats.d2h_bytes+=sizeof(c);
        stats.window_vertices+=c.window_size;++stats.box_queries;++stats.preparations;
        auto seconds=elapsed(t);stats.prepare_seconds+=seconds;stats.window_init_seconds+=seconds;
        return finish_search(c.window_size,sink,crit,present,hard,c);
    }
    std::vector<uint32_t> finish_search(uint32_t window_size,uint32_t sink,uint32_t crit,uint32_t present,bool hard,Control c) {
        auto t=Clock::now();uint32_t round=0;
        if(persistent) {
            PersistentContext context{out_offset,outgoing,occ,hist,allowed,tree,edges,nodes,dist,marks,front,next,control,totals,
                window_epoch,tree_epoch,sink,step,crit,norm,present,bucket,rates[crit],hard};
            void* args[]={&context};ck(cudaLaunchCooperativeKernel(reinterpret_cast<void*>(persistent_target),persistent_blocks,256,args));
            Label counts[3];ck(cudaMemcpy(counts,totals,sizeof(counts),cudaMemcpyDeviceToHost));stats.d2h_bytes+=sizeof(counts);
            if(counts[2])throw std::runtime_error("persistent target search did not converge");stats.rounds+=counts[0];stats.frontier_vertices+=counts[1];
        } else while(c.count && c.minimum<c.best) {
            if(++round==0)throw std::runtime_error("target frontier epoch exhausted");
            auto count=c.count;Label threshold=c.minimum+bucket;
            reset_control<<<1,1>>>(control,dist,sink);ck(cudaGetLastError());
            expand_target<<<(count+7)/8,256>>>(count,front,out_offset,outgoing,edges,nodes,occ,hist,allowed,window_epoch,tree,tree_epoch,dist,marks,round,next,control,sink,step,crit,norm,present,rates[crit],hard,threshold);ck(cudaGetLastError());
            ck(cudaMemcpy(&c,control,sizeof(c),cudaMemcpyDeviceToHost));stats.d2h_bytes+=sizeof(c);++stats.rounds;stats.frontier_vertices+=c.visits;
            if(c.count>n)throw std::runtime_error("target frontier overflow");std::swap(front,next);
        }
        stats.relaxation_seconds+=elapsed(t);auto tracing=Clock::now();
        trace_target<<<1,1>>>(window_size,sink,in_offset,incoming,edges,nodes,occ,hist,allowed,window_epoch,tree,tree_epoch,dist,crit,norm,present,hard,path,length);ck(cudaGetLastError());
        int len=0;ck(cudaMemcpy(&len,length,sizeof(len),cudaMemcpyDeviceToHost));stats.d2h_bytes+=sizeof(len);
        if(len<-1 || len>int(window_size))throw std::runtime_error("invalid target predecessor chain");
        std::vector<uint32_t> result(len>0?len:0);
        if(len>0){ck(cudaMemcpy(result.data(),path,len*sizeof(uint32_t),cudaMemcpyDeviceToHost));stats.d2h_bytes+=len*sizeof(uint32_t);std::reverse(result.begin(),result.end());}
        stats.traceback_seconds+=elapsed(tracing);++stats.searches;stats.search_seconds+=elapsed(t);return result;
    }
    GpuMetrics metrics()const override{return stats;}
};
}
std::unique_ptr<TargetSearch> cuda_target_search(const Graph& g,const TimingModel& m,uint32_t width,bool persistent){return std::make_unique<GpuSearch>(g,m,width,persistent);}
}
