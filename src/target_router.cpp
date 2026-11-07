#include "target_router.hpp"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <numeric>
#include <queue>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>

namespace h3d {
namespace {
void ensure(bool p,const char* message){if(!p)throw std::runtime_error(message);}
using Clock=std::chrono::steady_clock;
double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
class CpuSearch final:public TargetSearch {
    const Graph& g;const TimingModel& m;
    std::vector<uint32_t> occ,hist,allowed,tree;
    std::vector<uint64_t> prefix,distance;
    std::vector<uint32_t> parent;
    uint32_t window_epoch=0,tree_epoch=0;
    GpuMetrics stats;
public:
    CpuSearch(const Graph& graph,const TimingModel& model):g(graph),m(model),occ(g.nodes.size()),hist(occ),allowed(occ),tree(occ),
        prefix(g.nodes.size()),distance(g.nodes.size()),parent(g.nodes.size()){}
    void update(const std::vector<StateDelta>& values) override {
        for(auto v:values){ensure(v.node<occ.size(),"state node out of range");occ[v.node]=v.occupancy;hist[v.node]=v.history;}
        stats.state_updates+=values.size();
    }
    void begin_tree() override {if(++tree_epoch==0){std::fill(tree.begin(),tree.end(),0);tree_epoch=1;}}
    void add_tree(const std::vector<TreeSeed>& values) override {
        for(auto v:values){tree.at(v.node)=tree_epoch;prefix[v.node]=v.delay_ps;}
    }
    std::vector<uint32_t> search_box(WindowBox b,uint32_t sink,uint32_t crit,uint32_t present,bool hard) override {
        std::vector<uint32_t> vertices;
        for(uint32_t v=0;v<g.nodes.size();++v){auto n=g.nodes[v];if(n.xlow<=b.xhigh && n.xhigh>=b.xlow && n.ylow<=b.yhigh && n.yhigh>=b.ylow)vertices.push_back(v);}
        ++stats.box_queries;return search(vertices,sink,crit,present,hard);
    }
    std::vector<uint32_t> search(const std::vector<uint32_t>& window,uint32_t sink,uint32_t crit,uint32_t present,bool hard) override {
        ensure(crit<=990 && sink<g.nodes.size(),"invalid target search");
        auto started=Clock::now();
        if(++window_epoch==0){std::fill(allowed.begin(),allowed.end(),0);window_epoch=1;}
        const auto& target=g.nodes[sink];
        auto heuristic=[&](uint32_t v){const auto& n=g.nodes[v];return target_lower_bound(n.xlow,n.ylow,n.zlow,target.xlow,target.ylow,target.zlow,m.max_step,crit,m.norm_ps,m.spans[v],m.spatial_rates[crit]);};
        using Item=std::pair<uint64_t,uint32_t>;
        std::priority_queue<Item,std::vector<Item>,std::greater<Item>> queue;
        for(auto v:window){allowed.at(v)=window_epoch;distance[v]=TARGET_INF;parent[v]=UINT32_MAX;}
        for(auto v:window)if(tree[v]==tree_epoch){distance[v]=uint64_t(crit)*prefix[v];queue.push({distance[v]+heuristic(v),v});}
        ++stats.preparations;stats.window_vertices+=window.size();stats.prepare_seconds+=elapsed(started);
        started=Clock::now();
        while(!queue.empty()) {
            auto [priority,u]=queue.top();queue.pop();
            if(priority!=distance[u]+heuristic(u))continue;
            ++stats.frontier_vertices;
            if(u==sink)break;
            for(uint32_t i=g.offsets[u];i<g.offsets[u+1];++i) {
                uint32_t ei=g.adjacency[i];const auto& e=g.edges[ei];auto v=e.dst;
                if(allowed[v]!=window_epoch || tree[v]==tree_epoch)continue;
                auto c=timing_cost(m.delay_ps[ei],m.units[v],occ[v],g.nodes[v].capacity,hist[v],present,crit,m.norm_ps,hard);
                if(c==TARGET_INF)continue;
                auto d=distance[u]+c;
                if(d<distance[v]){distance[v]=d;parent[v]=ei;queue.push({d+heuristic(v),v});}
            }
        }
        std::vector<uint32_t> result;
        if(allowed[sink]==window_epoch && distance[sink]!=TARGET_INF) {
            uint32_t v=sink;
            while(tree[v]!=tree_epoch){auto ei=parent[v];ensure(ei<g.edges.size() && result.size()<window.size(),"invalid target predecessor");result.push_back(ei);v=g.edges[ei].src;}
            std::reverse(result.begin(),result.end());
        }
        ++stats.searches;stats.search_seconds+=elapsed(started);return result;
    }
    GpuMetrics metrics()const override{return stats;}
};
// A node is inserted into each tile it spans. Queries touch local bins, not N
// nodes; generation stamps remove duplicates without clearing an N-sized mask.
class SpatialWindows {
    const Graph& g;int width=1,height=1;
    std::vector<std::vector<uint32_t>> bins;
    std::vector<uint32_t> stamps;uint32_t epoch=0;
public:
    explicit SpatialWindows(const Graph& graph,bool host=true):g(graph) {
        for(auto n:g.nodes){ensure(n.xlow>=0 && n.ylow>=0,"negative RRG coordinates");width=std::max(width,n.xhigh+1);height=std::max(height,n.yhigh+1);}
        if(!host)return;
        stamps.resize(g.nodes.size());
        ensure(uint64_t(width)*height<100000000,"spatial index too large");bins.resize(size_t(width)*height);
        for(uint32_t v=0;v<g.nodes.size();++v){const auto& n=g.nodes[v];for(int y=n.ylow;y<=n.yhigh;++y)for(int x=n.xlow;x<=n.xhigh;++x)bins[size_t(y)*width+x].push_back(v);}
    }
    int extent()const{return std::max(width,height);}
    WindowBox box(uint32_t source,uint32_t sink,int margin) const {
        const auto& a=g.nodes[source];const auto& b=g.nodes[sink];
        int xl=std::max(0,std::min(a.xlow,b.xlow)-margin),xh=std::min(width-1,std::max(a.xhigh,b.xhigh)+margin);
        int yl=std::max(0,std::min(a.ylow,b.ylow)-margin),yh=std::min(height-1,std::max(a.yhigh,b.yhigh)+margin);
        return {xl,yl,xh,yh};
    }
    std::vector<uint32_t> query(uint32_t source,uint32_t sink,int margin) {
        if(++epoch==0){std::fill(stamps.begin(),stamps.end(),0);epoch=1;}
        auto b=box(source,sink,margin);
        std::vector<uint32_t> nodes;
        for(int y=b.ylow;y<=b.yhigh;++y)for(int x=b.xlow;x<=b.xhigh;++x)for(auto v:bins[size_t(y)*width+x])if(stamps[v]!=epoch){stamps[v]=epoch;nodes.push_back(v);}
        return nodes;
    }
};
}
SpatialIndex::SpatialIndex(const Graph& g) {
    for(auto n:g.nodes){ensure(n.xlow>=0 && n.ylow>=0 && n.xhigh>=n.xlow && n.yhigh>=n.ylow,"invalid spatial coordinates");width=std::max(width,n.xhigh+1);height=std::max(height,n.yhigh+1);}
    ensure(uint64_t(width)*height<100000000,"spatial index too large");
    offsets.resize(size_t(width)*height+1);
    for(auto n:g.nodes)for(int y=n.ylow;y<=n.yhigh;++y)for(int x=n.xlow;x<=n.xhigh;++x)++offsets[size_t(y)*width+x+1];
    uint64_t count=0;
    for(size_t i=1;i<offsets.size();++i){count+=offsets[i];ensure(count<UINT32_MAX,"spatial CSR exceeds 32-bit index range");offsets[i]=uint32_t(count);}
    vertices.resize(count);auto cursor=offsets;
    for(uint32_t v=0;v<g.nodes.size();++v){auto n=g.nodes[v];for(int y=n.ylow;y<=n.yhigh;++y)for(int x=n.xlow;x<=n.xhigh;++x)vertices[cursor[size_t(y)*width+x]++]=v;}
}
TimingModel timing_model(const Graph& g,const std::string& file) {
    TimingModel m;m.delay_ps.resize(g.edges.size());m.units.resize(g.nodes.size());m.spans.resize(g.nodes.size());
    std::vector<uint32_t> nonzero;
    if(file.empty()){for(size_t i=0;i<g.edges.size();++i)m.delay_ps[i]=g.edges[i].base;}
    else {
        std::ifstream f(file);std::string magic;uint64_t version=0,count=0;f>>magic>>version>>count;
        ensure(f && magic=="H3DDELAYS" && version==1 && count==g.edges.size(),"invalid delay sidecar");
        for(uint32_t i=0;i<count;++i){uint64_t id=0,d=0;f>>id>>d;ensure(f && id==g.edges[i].external && d<1000000000,"invalid edge delay/order");m.delay_ps[i]=uint32_t(d);}
        std::string extra;ensure(!(f>>extra),"trailing delay records");
    }
    for(auto d:m.delay_ps)if(d)nonzero.push_back(d);
    if(!nonzero.empty()){auto mid=nonzero.begin()+nonzero.size()/2;std::nth_element(nonzero.begin(),mid,nonzero.end());m.norm_ps=*mid;}
    uint64_t max_delay=nonzero.empty()?0:*std::max_element(nonzero.begin(),nonzero.end());
    ensure(!max_delay || g.nodes.size()<(TARGET_INF/2)/990/max_delay,"tree delay exceeds supported 64-bit label range");
    for(size_t i=0;i<g.nodes.size();++i){const auto& n=g.nodes[i];m.spans[i]=uint32_t(n.xhigh-n.xlow+n.yhigh-n.ylow+n.zhigh-n.zlow);m.units[i]=n.kind>=CHANX?m.spans[i]+1:1;}
    // A long source channel has already paid for its extent. Its cheap exit
    // must not set the rate for all future travel. For every edge enforce
    // rate*(step - span(src) + span(dst)) <= its zero-pressure cost.
    // Then max(0,rate*(distance_to_sink - span(v))) is a consistent lower
    // bound; max with the old hop bound remains admissible and consistent.
    std::unordered_map<uint64_t,uint32_t> denominators;
    for(size_t i=0;i<g.edges.size();++i){const auto&e=g.edges[i];const auto&a=g.nodes[e.src];const auto&b=g.nodes[e.dst];
        uint32_t step=uint32_t(std::abs(a.xlow-b.xlow)+std::abs(a.ylow-b.ylow)+std::abs(a.zlow-b.zlow));m.max_step=std::max(m.max_step,step);
        int64_t denominator=int64_t(step)-m.spans[e.src]+m.spans[e.dst];
        if(denominator>0 && b.capacity){uint64_t key=(uint64_t(m.delay_ps[i])<<32)|m.units[e.dst];auto& d=denominators[key];d=std::max(d,uint32_t(denominator));}
    }
    for(uint32_t crit=0;crit<=990;++crit){uint64_t rate=UINT64_MAX;
        for(auto [key,denominator]:denominators){uint64_t c=timing_cost(uint32_t(key>>32),uint32_t(key),0,1,0,0,crit,m.norm_ps,false);rate=std::min(rate,(c<<16)/denominator);}
        m.spatial_rates[crit]=rate==UINT64_MAX?0:rate;
    }
    int maxx=0,maxy=0,maxz=0;
    for(auto n:g.nodes){ensure(n.xlow>=0 && n.ylow>=0 && n.zlow>=0,"negative geometry for heuristic");maxx=std::max(maxx,n.xlow);maxy=std::max(maxy,n.ylow);maxz=std::max(maxz,n.zlow);}
    uint64_t extent=uint64_t(maxx)+maxy+maxz,rate=*std::max_element(m.spatial_rates.begin(),m.spatial_rates.end());
    ensure(!rate || extent<(TARGET_INF/2)/rate,"spatial heuristic exceeds fixed-point range");
    return m;
}
std::unique_ptr<TargetSearch> cpu_target_search(const Graph& g,const TimingModel&m){return std::make_unique<CpuSearch>(g,m);}

Result route_target_session(const Graph& g,const std::vector<Net>& nets,const Options& o,
                            const std::function<TargetFeedback(const Result&)>& checkpoint) {
    ensure(o.iterations>0 && o.bootstrap_criticality>=0 && o.bootstrap_criticality<=990 && o.bbox_margin>=0 && o.bucket_width>0,"invalid target options");
    ensure(o.present_cap>=o.present && o.present_cap<=1000000,"invalid finite present cap");
    ensure(!o.portal_k && !o.source_tree && !o.portal_schedule,"target backend has its own window and timing tree policy");
    auto init=Clock::now();
    std::cerr<<"target_phase=model_begin elapsed="<<elapsed(init)<<std::endl;
    auto model=timing_model(g,o.delay_file);
    if(o.heuristic=="hop")model.spatial_rates.fill(0);
    std::cerr<<"target_phase=model_end elapsed="<<elapsed(init)<<std::endl;
    std::vector<std::vector<uint32_t>> crit(nets.size());
    std::unordered_map<uint64_t,std::pair<size_t,size_t>> pins;
    for(size_t i=0;i<nets.size();++i){crit[i].assign(nets[i].sinks.size(),o.bootstrap_criticality);for(size_t j=0;j<nets[i].sinks.size();++j)pins[(uint64_t(nets[i].id)<<32)|g.nodes[nets[i].sinks[j]].external]={i,j};}
    auto load_criticalities=[&](const std::string& file) {
        if(file.empty())return;
        std::ifstream f(file);std::string magic;uint64_t version=0,count=0;f>>magic>>version>>count;
        ensure(f && magic=="H3DCRITICALITY" && version==1 && count==pins.size(),"criticality coverage mismatch");
        std::unordered_set<uint64_t> seen;
        for(size_t k=0;k<count;++k){uint64_t net=0,sink=0,c=0;f>>net>>sink>>c;ensure(f && net<UINT32_MAX && sink<UINT32_MAX && c<=990,"invalid criticality");uint64_t key=(net<<32)|sink;auto it=pins.find(key);ensure(it!=pins.end() && seen.insert(key).second,"unknown/duplicate criticality pin");auto [i,j]=it->second;crit[i][j]=uint32_t(c);}
        std::string extra;ensure(!(f>>extra),"trailing criticality records");
    };load_criticalities(o.criticality_file);
    std::unique_ptr<TargetSearch> search;
    std::cerr<<"target_phase=search_context_begin elapsed="<<elapsed(init)<<std::endl;
#ifdef H3D_CUDA
    if(o.backend=="cuda_target")search=cuda_target_search(g,model,o.bucket_width);
#else
    ensure(o.backend!="cuda_target","CUDA target backend not built");
#endif
    if(!search)search=cpu_target_search(g,model);
    std::cerr<<"target_phase=search_context_end elapsed="<<elapsed(init)<<std::endl;
    // Initialization (including static GPU upload) is included in process time,
    // but kept outside the legacy-compatible internal routing timer.
    const bool device_window=o.backend=="cuda_target" && o.window_mode=="device";
    SpatialWindows windows(g,!device_window);auto started=Clock::now();
    std::cerr<<"target_phase=spatial_index_end elapsed="<<elapsed(init)<<std::endl;
    std::ofstream trace;
    if(!o.trace_file.empty()) {
        trace.open(o.trace_file);ensure(bool(trace),"cannot open connection trace");trace.precision(12);
        trace<<"event,elapsed,iteration,net,sink,fanout,margin,criticality,present,window_vertices,cpu_window_seconds,prepare_seconds,relaxation_seconds,traceback_seconds,search_seconds,visits,rounds,h2d_bytes,path_edges\n";
    }
    double cpu_windows=0;auto heartbeat=Clock::now();uint64_t queries=0;
    Result r;r.trees.resize(nets.size());std::vector<uint32_t> occupancy(g.nodes.size()),history(occupancy),used(occupancy);
    std::vector<uint64_t> prefix(g.nodes.size());uint32_t used_epoch=0,present=o.present;
    std::vector<uint32_t> parent;
    std::vector<char> dirty_flag(g.nodes.size()),ever(g.nodes.size());std::vector<uint32_t> dirty,active;
    auto mark=[&](uint32_t v){if(!dirty_flag[v]){dirty_flag[v]=1;dirty.push_back(v);}if(!ever[v]){ever[v]=1;active.push_back(v);}};
    auto flush=[&](){std::vector<StateDelta> changes;changes.reserve(dirty.size());for(auto v:dirty){changes.push_back({v,occupancy[v],history[v]});dirty_flag[v]=0;}dirty.clear();search->update(changes);};
    std::vector<uint32_t> order(nets.size());std::iota(order.begin(),order.end(),0);
    auto max_crit=[&](size_t i){return crit[i].empty()?0:*std::max_element(crit[i].begin(),crit[i].end());};
    uint64_t fallbacks=0;
    auto negotiate=[&](const std::vector<std::vector<uint32_t>>& forced) {
    r.success=false;r.iterations.clear();present=o.present;
    std::iota(order.begin(),order.end(),0);
    std::stable_sort(order.begin(),order.end(),[&](auto a,auto b){if(max_crit(a)!=max_crit(b))return max_crit(a)>max_crit(b);return nets[a].sinks.size()>nets[b].sinks.size();});
    uint64_t previous=UINT64_MAX;unsigned stagnant=0;
    for(int iteration=0;iteration<o.iterations;++iteration) {
        Iteration stats{};uint64_t rerouted=0;
        bool global_retry=stagnant>=8;
        if(global_retry){stagnant=0;std::rotate(order.begin(),order.begin()+order.size()/3,order.end());}
        for(auto ni:order) {
            bool force=iteration==0 && !forced.empty() && !forced[ni].empty();
            auto& old=r.trees[ni];bool needs=force || global_retry || !old.connected,conflicted=false;
            for(auto v:old.nodes)if(occupancy[v]>g.nodes[v].capacity){needs=true;conflicted=true;break;}
            if(!needs)continue;
            ++rerouted;
            Tree t;const auto& net=nets[ni];
            if(used_epoch>=UINT32_MAX-2){std::fill(used.begin(),used.end(),0);used_epoch=0;}
            uint32_t safe_epoch=++used_epoch;++used_epoch;
            prefix[net.source]=0;
            if((o.incremental_congestion || !forced.empty()) && old.connected && !global_retry && occupancy[net.source]<=g.nodes[net.source].capacity) {
                if(parent.empty())parent.resize(g.nodes.size(),UINT32_MAX);
                used[net.source]=safe_epoch;parent[net.source]=net.source;
                for(auto ei:old.edges){auto e=g.edges[ei];parent[e.dst]=e.src;prefix[e.dst]=prefix[e.src]+model.delay_ps[ei];
                    if(used[e.src]==safe_epoch && occupancy[e.dst]<=g.nodes[e.dst].capacity)used[e.dst]=safe_epoch;}
                used[net.source]=used_epoch;
                std::vector<char> selected_sink(net.sinks.size());if(force)for(auto si:forced[ni])selected_sink[si]=1;
                for(size_t si=0;si<net.sinks.size();++si) {
                    auto sink=net.sinks[si];
                    if(selected_sink[si] || (used[sink]!=safe_epoch && used[sink]!=used_epoch))continue;
                    ++r.congestion_connections_reused;auto v=sink;size_t steps=0;
                    while(used[v]!=used_epoch){ensure(++steps<=old.nodes.size() && parent[v]!=UINT32_MAX,"invalid congestion subtree");used[v]=used_epoch;v=parent[v];}
                }
                for(auto v:old.nodes)if(used[v]==used_epoch)t.nodes.push_back(v);
                for(auto ei:old.edges)if(used[g.edges[ei].dst]==used_epoch)t.edges.push_back(ei);
            } else {t.nodes.push_back(net.source);used[net.source]=used_epoch;}
            for(auto v:old.nodes){ensure(occupancy[v]>0,"target occupancy underflow");--occupancy[v];mark(v);}flush();
            std::vector<TreeSeed> retained;for(auto v:t.nodes)retained.push_back({v,prefix[v]});
            search->begin_tree();search->add_tree(retained);
            std::vector<size_t> sinks(net.sinks.size());std::iota(sinks.begin(),sinks.end(),0);
            std::stable_sort(sinks.begin(),sinks.end(),[&](auto a,auto b){return crit[ni][a]>crit[ni][b];});
            t.connected=g.nodes[net.source].capacity>0;
            for(auto si:sinks) {
                if(!t.connected)break;
                auto sink=net.sinks[si];if(used[sink]==used_epoch)continue;
                std::vector<uint32_t> path;
                // A reachable local path can still be congested. Widen over
                // negotiation, and lift the window for stalled conflicted nets.
                int margin=global_retry && conflicted ? windows.extent() : std::min(o.bbox_margin+iteration/10,windows.extent());
                while(true) {
                    auto before=search->metrics();
                    if(trace.is_open())trace<<"begin,"<<elapsed(started)<<','<<iteration+1<<','<<net.id<<','<<g.nodes[sink].external<<','<<net.sinks.size()<<','<<margin<<','<<crit[ni][si]<<','<<present<<",,,,,,,,,,\n"<<std::flush;
                    if(!queries || elapsed(heartbeat)>=5) {
                        std::cerr<<"target_query_begin iteration="<<iteration+1<<" net="<<net.id<<" sink_index="<<si<<" fanout="<<net.sinks.size()<<" queries="<<queries<<" elapsed="<<elapsed(started)<<" visits="<<before.frontier_vertices<<" h2d_bytes="<<before.h2d_bytes<<std::endl;heartbeat=Clock::now();
                    }
                    auto query_start=Clock::now();std::vector<uint32_t> window;
                    auto box=windows.box(net.source,sink,margin);
                    if(!device_window)window=windows.query(net.source,sink,margin);
                    auto window_seconds=elapsed(query_start);cpu_windows+=window_seconds;
                    path=device_window?search->search_box(box,sink,crit[ni][si],present,false):search->search(window,sink,crit[ni][si],present,false);
                    auto after=search->metrics();++queries;
                    if(trace.is_open())trace<<"end,"<<elapsed(started)<<','<<iteration+1<<','<<net.id<<','<<g.nodes[sink].external<<','<<net.sinks.size()<<','<<margin<<','<<crit[ni][si]<<','<<present<<','<<after.window_vertices-before.window_vertices<<','<<window_seconds<<','<<after.prepare_seconds-before.prepare_seconds<<','<<after.relaxation_seconds-before.relaxation_seconds<<','<<after.traceback_seconds-before.traceback_seconds<<','<<after.search_seconds-before.search_seconds<<','<<after.frontier_vertices-before.frontier_vertices<<','<<after.rounds-before.rounds<<','<<after.h2d_bytes-before.h2d_bytes<<','<<path.size()<<'\n';
                    if(!path.empty() || margin>=windows.extent())break;
                    margin=std::min(windows.extent(),std::max(margin+1,margin*2));++fallbacks;
                }
                if(path.empty()){t.connected=false;break;}
                std::vector<TreeSeed> additions;
                for(auto ei:path){const auto& e=g.edges[ei];ensure(used[e.src]==used_epoch && used[e.dst]!=used_epoch,"target branch cycle/disconnection");used[e.dst]=used_epoch;prefix[e.dst]=prefix[e.src]+model.delay_ps[ei];t.nodes.push_back(e.dst);t.edges.push_back(ei);additions.push_back({e.dst,prefix[e.dst]});}
                ensure(used[sink]==used_epoch,"target missed sink");search->add_tree(additions);
            }
            if(!t.connected){t.nodes.clear();t.edges.clear();}
            for(auto v:t.nodes){if(occupancy[v]>=g.nodes[v].capacity)++stats.conflicts;++occupancy[v];mark(v);}
            old=std::move(t);
            if(rerouted%4096==0){auto m=search->metrics();std::cerr<<"target_progress iteration="<<iteration+1<<" rerouted="<<rerouted<<" elapsed="<<elapsed(started)<<" visits="<<m.frontier_vertices<<" h2d_bytes="<<m.h2d_bytes<<'\n';}
        }
        for(const auto& t:r.trees)stats.unrouted+=!t.connected;
        for(auto v:active)if(occupancy[v]>g.nodes[v].capacity){auto excess=occupancy[v]-g.nodes[v].capacity;stats.overflow+=excess;history[v]=uint32_t(std::min(uint64_t(1000000),uint64_t(history[v])+excess));mark(v);}
        r.iterations.push_back(stats);
        std::cerr<<"target_iteration="<<iteration+1<<" rerouted="<<rerouted<<" overflow="<<stats.overflow<<" unrouted="<<stats.unrouted<<" present="<<present<<'\n';
        if(!stats.overflow && !stats.unrouted){r.success=true;break;}
        stagnant=stats.overflow>=previous?stagnant+1:0;previous=stats.overflow;
        present=uint32_t(std::min(uint64_t(o.present_cap),uint64_t(present)*13/10+1));
    }
    };
    negotiate({});
    r.routing_seconds=elapsed(started);r.gpu=search->metrics();r.gpu.cpu_window_seconds=cpu_windows;r.gpu.window_fallbacks=fallbacks;r.expansions=r.gpu.frontier_vertices;r.fallbacks=fallbacks;
    while(checkpoint) {
        auto feedback=checkpoint(r);if(feedback.criticality_file.empty())break;
        ensure(r.success,"cannot refine an illegal checkpoint");
        ensure(feedback.threshold<=990 && feedback.max_connections>0,"invalid refinement budget");
        started=Clock::now();auto initial_metrics=search->metrics();double initial_windows=cpu_windows;auto initial_fallbacks=fallbacks;
        load_criticalities(feedback.criticality_file);flush();
        // Each feedback pass starts without obsolete negotiation penalties.
        for(auto v:active)if(history[v]){history[v]=0;mark(v);}
        flush();
        if(parent.empty())parent.resize(g.nodes.size(),UINT32_MAX);
        struct Connection {uint32_t net,sink,criticality;};std::vector<Connection> choices;
        for(uint32_t ni=0;ni<nets.size();++ni)for(uint32_t si=0;si<nets[ni].sinks.size();++si)
            if(crit[ni][si]>=feedback.threshold)choices.push_back({ni,si,crit[ni][si]});
        std::stable_sort(choices.begin(),choices.end(),[](auto a,auto b){return a.criticality>b.criticality;});
        if(choices.size()>feedback.max_connections)choices.resize(feedback.max_connections);
        std::vector<std::vector<uint32_t>> selected(nets.size());std::vector<uint32_t> selected_nets;
        for(auto c:choices){if(selected[c.net].empty())selected_nets.push_back(c.net);selected[c.net].push_back(c.sink);}
        r.refinement_connections=choices.size();r.refinement_accepted=0;
        r.congestion_connections_reused=0;
        r.refinement_mode=feedback.negotiate?"negotiate":"legal";r.refinement_converged=true;
        r.refinement_failed_overflow=0;r.refinement_failed_unrouted=0;
        std::cerr<<"target_refinement_begin mode="<<r.refinement_mode<<" connections="<<choices.size()<<" nets="<<selected_nets.size()<<std::endl;
        heartbeat=Clock::now();
        if(feedback.negotiate) {
            // The previous legal forest is a transaction checkpoint. Selected
            // connections may temporarily overuse nodes; only conflicted trees
            // subsequently need repair. The static graph/context stay resident.
            auto checkpoint_trees=r.trees;negotiate(selected);
            r.refinement_converged=r.success;
            if(!r.success) {
                r.refinement_failed_overflow=r.iterations.back().overflow;
                r.refinement_failed_unrouted=r.iterations.back().unrouted;
                r.trees=std::move(checkpoint_trees);
                for(auto v:active){occupancy[v]=0;history[v]=0;mark(v);}
                for(const auto& t:r.trees)for(auto v:t.nodes){++occupancy[v];mark(v);}
                r.success=true;r.iterations.push_back({0,0,0,0});
            } else r.refinement_accepted=choices.size();
        } else {
        for(auto ni:selected_nets) {
            const auto& net=nets[ni];auto& old=r.trees[ni];
            if(++used_epoch==0){std::fill(used.begin(),used.end(),0);used_epoch=1;}
            prefix[net.source]=0;parent[net.source]=net.source;
            for(auto ei:old.edges){auto e=g.edges[ei];parent[e.dst]=e.src;prefix[e.dst]=prefix[e.src]+model.delay_ps[ei];}
            std::vector<char> chosen(net.sinks.size());std::vector<uint64_t> old_delays;
            for(auto si:selected[ni]){chosen[si]=1;old_delays.push_back(prefix[net.sinks[si]]);}
            used[net.source]=used_epoch;
            // Retain every non-selected sink and all its ancestors. Only
            // exclusive branches of selected connections are ripped up.
            for(size_t si=0;si<net.sinks.size();++si)if(!chosen[si]) {
                uint32_t v=net.sinks[si],steps=0;
                while(used[v]!=used_epoch){ensure(++steps<=old.nodes.size() && parent[v]!=UINT32_MAX,"invalid retained tree");used[v]=used_epoch;v=parent[v];}
            }
            Tree candidate;candidate.connected=true;std::vector<uint32_t> removed;std::vector<TreeSeed> retained;
            for(auto v:old.nodes)if(used[v]==used_epoch){candidate.nodes.push_back(v);retained.push_back({v,prefix[v]});}
                else {ensure(occupancy[v]>0,"refinement occupancy underflow");--occupancy[v];mark(v);removed.push_back(v);}
            for(auto ei:old.edges)if(used[g.edges[ei].dst]==used_epoch)candidate.edges.push_back(ei);
            size_t retained_count=candidate.nodes.size();flush();search->begin_tree();search->add_tree(retained);
            for(auto si:selected[ni]) {
                auto sink=net.sinks[si];if(used[sink]==used_epoch)continue;
                std::vector<uint32_t> path;int margin=o.bbox_margin;
                while(true) {
                    auto tick=Clock::now();auto box=windows.box(net.source,sink,margin);std::vector<uint32_t> window;
                    if(!device_window)window=windows.query(net.source,sink,margin);
                    cpu_windows+=elapsed(tick);
                    path=device_window?search->search_box(box,sink,crit[ni][si],1,true):search->search(window,sink,crit[ni][si],1,true);
                    if(!path.empty() || margin>=windows.extent())break;
                    margin=std::min(windows.extent(),std::max(margin+1,margin*2));++fallbacks;
                }
                if(path.empty()){candidate.connected=false;break;}
                std::vector<TreeSeed> additions;
                for(auto ei:path){auto e=g.edges[ei];ensure(used[e.src]==used_epoch && used[e.dst]!=used_epoch,"refinement tree cycle");used[e.dst]=used_epoch;prefix[e.dst]=prefix[e.src]+model.delay_ps[ei];candidate.nodes.push_back(e.dst);candidate.edges.push_back(ei);additions.push_back({e.dst,prefix[e.dst]});}
                search->add_tree(additions);
            }
            bool improve=false,accept=candidate.connected;
            if(accept)for(size_t j=0;j<selected[ni].size();++j){auto delay=prefix[net.sinks[selected[ni][j]]];accept &= delay<=old_delays[j];improve |= delay<old_delays[j];}
            if(accept && improve){
                for(size_t i=retained_count;i<candidate.nodes.size();++i){auto v=candidate.nodes[i];ensure(occupancy[v]<g.nodes[v].capacity,"refinement overuse");++occupancy[v];mark(v);}
                old=std::move(candidate);r.refinement_accepted+=selected[ni].size();
            } else for(auto v:removed){++occupancy[v];mark(v);}
            if(elapsed(heartbeat)>=5){std::cerr<<"target_refinement_progress accepted="<<r.refinement_accepted<<" elapsed="<<elapsed(started)<<std::endl;heartbeat=Clock::now();}
        }
        r.iterations={{0,0,0,0}};
        }
        flush();for(auto v:active)ensure(occupancy[v]<=g.nodes[v].capacity,"refinement checkpoint not legal");
        r.incremental_refinement=true;r.routing_seconds=elapsed(started);r.gpu=search->metrics();
#define TARGET_DELTA(field) r.gpu.field-=initial_metrics.field
        TARGET_DELTA(preparations);TARGET_DELTA(searches);TARGET_DELTA(rounds);TARGET_DELTA(frontier_vertices);
        TARGET_DELTA(h2d_bytes);TARGET_DELTA(d2h_bytes);TARGET_DELTA(prepare_seconds);TARGET_DELTA(search_seconds);
        TARGET_DELTA(state_updates);TARGET_DELTA(window_vertices);TARGET_DELTA(window_h2d_bytes);TARGET_DELTA(spatial_index_bytes);TARGET_DELTA(box_queries);
        TARGET_DELTA(window_upload_seconds);TARGET_DELTA(window_init_seconds);TARGET_DELTA(relaxation_seconds);TARGET_DELTA(traceback_seconds);TARGET_DELTA(state_update_seconds);TARGET_DELTA(tree_update_seconds);
#undef TARGET_DELTA
        r.gpu.cpu_window_seconds=cpu_windows-initial_windows;r.gpu.window_fallbacks=fallbacks-initial_fallbacks;
        r.expansions=r.gpu.frontier_vertices;r.fallbacks=r.gpu.window_fallbacks;
        std::cerr<<"target_refinement_end attempted="<<r.refinement_connections<<" accepted="<<r.refinement_accepted<<" elapsed="<<r.routing_seconds<<std::endl;
    }
    return r;
}
Result route_target(const Graph& g,const std::vector<Net>& nets,const Options& o){return route_target_session(g,nets,o,{});}
}
