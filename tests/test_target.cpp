#include "target_router.hpp"
#include <algorithm>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <unordered_map>
#include <fstream>
#include <filesystem>
#include <chrono>
using namespace h3d;
void check(bool b,const char*s){if(!b)throw std::runtime_error(s);}
Graph make_graph(uint32_t n){Graph g;for(uint32_t i=0;i<n;++i)g.nodes.push_back({i,CHANX,2,int(i%7),int(i/7),0,int(i%7),int(i/7),0});return g;}
void edge(Graph&g,uint32_t a,uint32_t b,uint32_t c){g.edges.push_back({uint32_t(g.edges.size()),a,b,0,c,0});}
// Independent wide-arithmetic oracle, deliberately not calling timing_cost.
uint64_t cost(uint32_t delay,uint32_t units,StateDelta s,uint32_t cap,uint32_t present,uint32_t crit,uint32_t norm,bool hard){
    if(!cap || (hard && s.occupancy>=cap))return TARGET_INF;
    uint64_t excess=s.occupancy>=cap?uint64_t(s.occupancy)-cap+1:0;
    unsigned __int128 raw=(1000-crit)*static_cast<unsigned __int128>(norm)*units*(uint64_t(s.history)+1)*(1+static_cast<unsigned __int128>(present)*excess)+uint64_t(crit)*delay+1;
    return raw>TARGET_FINITE_MAX?TARGET_FINITE_MAX:uint64_t(raw);
}
void verify_bounds(const Graph& g,const TimingModel& m) {
    for(uint32_t target=0;target<g.nodes.size();++target)for(auto crit:{0U,1U,500U,989U,990U}) {
        auto b=g.nodes[target];std::vector<uint64_t> h;
        for(uint32_t v=0;v<g.nodes.size();++v){auto a=g.nodes[v];h.push_back(target_lower_bound(a.xlow,a.ylow,a.zlow,b.xlow,b.ylow,b.zlow,m.max_step,crit,m.norm_ps,m.spans[v],m.spatial_rates[crit]));}
        check(h[target]==0,"heuristic nonzero at target");
        for(uint32_t i=0;i<g.edges.size();++i){auto e=g.edges[i];auto c=cost(m.delay_ps[i],m.units[e.dst],{e.dst,0,0},g.nodes[e.dst].capacity,0,crit,m.norm_ps,false);
            if(c!=TARGET_INF)check(h[e.src]<=c+h[e.dst],"spatial bound is not consistent with a legal edge");}
    }
}
void verify(const Graph&g,const TimingModel&m,TargetSearch&search,const std::vector<StateDelta>&states,
            const std::vector<TreeSeed>&roots,const std::vector<uint32_t>&window,uint32_t sink,uint32_t crit,uint32_t present,bool hard,const WindowBox* box=nullptr){
    std::vector<char> allowed(g.nodes.size()),isroot(g.nodes.size());std::vector<uint64_t>d(g.nodes.size(),TARGET_INF);
    for(auto v:window)allowed[v]=1;
    for(auto r:roots){isroot[r.node]=1;if(allowed[r.node])d[r.node]=uint64_t(crit)*r.delay_ps;}
    for(size_t k=1;k<g.nodes.size();++k){bool changed=false;
        for(size_t i=0;i<g.edges.size();++i){auto e=g.edges[i];if(!allowed[e.src] || !allowed[e.dst] || isroot[e.dst] || d[e.src]==TARGET_INF)continue;
            auto c=cost(m.delay_ps[i],m.units[e.dst],states[e.dst],g.nodes[e.dst].capacity,present,crit,m.norm_ps,hard);if(c==TARGET_INF)continue;
            if(d[e.src]+c<d[e.dst]){d[e.dst]=d[e.src]+c;changed=true;}}
        if(!changed)break;}
    auto before=search.metrics();
    auto path=box?search.search_box(*box,sink,crit,present,hard):search.search(window,sink,crit,present,hard);
    check(search.metrics().window_vertices-before.window_vertices==window.size(),"window index lost or duplicated spanning/layer nodes");
    check(path.empty()==(d[sink]==TARGET_INF),"target reachability differs from Bellman-Ford");
    if(path.empty())return;
    auto u=g.edges[path.front()].src;check(isroot[u],"target path not rooted in existing tree");
    uint64_t actual=0;for(auto r:roots)if(r.node==u)actual=uint64_t(crit)*r.delay_ps;
    std::vector<char> seen(g.nodes.size());seen[u]=1;
    for(auto ei:path){auto e=g.edges.at(ei);check(e.src==u && allowed[e.dst] && !seen[e.dst] && !isroot[e.dst],"invalid target tree path");actual+=cost(m.delay_ps[ei],m.units[e.dst],states[e.dst],g.nodes[e.dst].capacity,present,crit,m.norm_ps,hard);seen[e.dst]=1;u=e.dst;}
    check(u==sink && actual==d[sink],"target objective differs from independent optimum");
}
int main(){try{
    const std::vector<uint64_t> factors{0,1,TARGET_FINITE_MAX-1,TARGET_FINITE_MAX,TARGET_FINITE_MAX+1,UINT64_MAX};
    for(uint64_t a:factors)
        for(uint64_t b:factors) {
            auto wide=static_cast<unsigned __int128>(a)*b;
            check(finite_mul(a,b)==(wide>TARGET_FINITE_MAX?TARGET_FINITE_MAX:uint64_t(wide)),"bounded multiply differs from wide oracle");
        }
    check(timing_cost(999,4,20,1,1000000,1000000,990,999,false)==TARGET_FINITE_MAX,"finite pressure became unreachable");
    check(timing_cost(999,4,20,1,1000000,1000000,990,999,true)==TARGET_INF,"hard capacity ignored");
    std::mt19937 rng(7281);size_t checks=0;
    for(unsigned trial=0;trial<60;++trial){auto g=make_graph(21);
        for(unsigned j=0;j<110;++j)edge(g,rng()%21,rng()%21,1+rng()%80);g.index();auto m=timing_model(g,"");
        std::vector<std::unique_ptr<TargetSearch>> engines;engines.push_back(cpu_target_search(g,m));
#ifdef H3D_CUDA
        engines.push_back(cuda_target_search(g,m,trial%2?100000:1));
        engines.push_back(cuda_target_search(g,m,trial%2?100000:1,false));
#endif
        std::vector<StateDelta> state;for(uint32_t v=0;v<21;++v)state.push_back({v,0,0});
        for(auto&engine:engines)engine->update(state);
        for(unsigned snapshot=0;snapshot<3;++snapshot){std::vector<StateDelta> updates;
            for(unsigned k=0;k<4;++k){auto v=(snapshot*4+k)%21;state[v]={v,uint32_t(rng()%4),uint32_t(rng()%6)};updates.push_back(state[v]);}
            std::vector<TreeSeed> roots{{0,0},{1,uint64_t(10+rng()%500)}};
            std::vector<uint32_t> window{0,1,20};for(uint32_t v=2;v<20;++v)if(trial%2 || rng()%2)window.push_back(v);
            for(auto& engine:engines){engine->update(updates);engine->begin_tree();engine->add_tree(roots);
                for(auto crit:{0U,500U,990U})for(bool hard:{false,true}){verify(g,m,*engine,state,roots,window,20,crit,snapshot==2?1000000:3,hard);++checks;}}
        }
        for(auto& engine:engines)check(engine->metrics().state_updates==33,"sparse updates unexpectedly upload full state");
    }
    // Device CSR membership is checked against a separate rectangle-intersection
    // scan and Bellman-Ford, including spanning channels, layers, empty windows,
    // excluded sinks and repeated windows with different generation stamps.
    for(unsigned trial=0;trial<30;++trial){auto g=make_graph(35);int width=1,height=1;
        for(auto& n:g.nodes){n.xhigh+=rng()%4;n.yhigh+=rng()%3;n.zlow=n.zhigh=rng()%3;n.capacity=rng()%4;width=std::max(width,n.xhigh+1);height=std::max(height,n.yhigh+1);}
        for(unsigned j=0;j<180;++j)edge(g,rng()%35,rng()%35,1+rng()%90);g.index();auto m=timing_model(g,"");verify_bounds(g,m);
        std::vector<std::unique_ptr<TargetSearch>> engines;engines.push_back(cpu_target_search(g,m));
#ifdef H3D_CUDA
        engines.push_back(cuda_target_search(g,m,trial%2?65536:1));
        engines.push_back(cuda_target_search(g,m,trial%2?65536:1,false));
#endif
        std::vector<StateDelta> state;for(uint32_t v=0;v<35;++v)state.push_back({v,uint32_t(rng()%4),uint32_t(rng()%8)});
        std::vector<TreeSeed> roots{{0,0},{1,700}};
        for(auto& engine:engines){engine->update(state);engine->begin_tree();engine->add_tree(roots);}
        for(unsigned j=0;j<12;++j){int x=rng()%width,y=rng()%height;WindowBox b{x,y,std::min(width-1,x+int(rng()%width)),std::min(height-1,y+int(rng()%height))};
            if(j==0)b={0,0,width-1,height-1};
            std::vector<uint32_t> window;for(uint32_t v=0;v<g.nodes.size();++v){auto n=g.nodes[v];if(n.xlow<=b.xhigh && n.xhigh>=b.xlow && n.ylow<=b.yhigh && n.yhigh>=b.ylow)window.push_back(v);}
            for(auto& engine:engines)for(auto crit:{0U,500U,990U})for(bool hard:{false,true}){verify(g,m,*engine,state,roots,window,34,crit,j%2?1000000:1,hard,&b);++checks;}
        }
    }
    // Existing prefix must influence the connection. A cheap tail on a slow
    // tree branch must lose to a more expensive tail from the real source.
    auto g=make_graph(4);edge(g,1,3,1);edge(g,0,2,10);edge(g,2,3,10);g.index();auto m=timing_model(g,"");
    std::vector<std::unique_ptr<TargetSearch>> engines;engines.push_back(cpu_target_search(g,m));
#ifdef H3D_CUDA
    engines.push_back(cuda_target_search(g,m,10000000));
#endif
    for(auto& engine:engines){engine->begin_tree();engine->add_tree({{0,0},{1,10000}});
        auto timing=engine->search({0,1,2,3},3,990,1,false);check(timing==std::vector<uint32_t>({1,2}),"lost existing tree delay");
        auto sharing=engine->search({0,1,2,3},3,0,1,false);check(sharing==std::vector<uint32_t>({0}),"zero criticality did not favor sharing");}
    // A legal path leaves the initial window; full-window retry must find it.
    g=make_graph(4);g.nodes[2].xlow=g.nodes[2].xhigh=50;edge(g,0,2,1);edge(g,2,3,1);g.index();
    for(auto backend:{"cpu_target"
#ifdef H3D_CUDA
        ,"cuda_target"
#endif
    }){Options o;o.backend=backend;o.bbox_margin=0;o.present=1;auto r=route(g,{{0,0,{3}}},o);check(r.success && r.fallbacks>0,"target window fallback lost legal path");}
    // Both nets remain reachable in a narrow window, but legality requires a
    // detour outside it. A reachability-only fallback would never widen here.
    g=make_graph(6);for(auto& n:g.nodes){n.capacity=1;n.ylow=n.yhigh=0;}
    g.nodes[0].xlow=g.nodes[0].xhigh=0;g.nodes[1].xlow=g.nodes[1].xhigh=0;
    g.nodes[2].xlow=g.nodes[2].xhigh=1;g.nodes[3].xlow=g.nodes[3].xhigh=50;
    g.nodes[4].xlow=g.nodes[4].xhigh=2;g.nodes[5].xlow=g.nodes[5].xhigh=2;
    edge(g,0,2,1);edge(g,2,4,1);edge(g,1,2,1);edge(g,2,5,1);edge(g,1,3,2);edge(g,3,5,2);g.index();
    for(auto backend:{"cpu_target"
#ifdef H3D_CUDA
        ,"cuda_target"
#endif
    }){Options o;o.backend=backend;o.bbox_margin=0;o.present=1;o.iterations=30;auto r=route(g,{{0,0,{4}},{1,1,{5}}},o);check(r.success,"congested reachable window never expanded");}
    // A single congested branch must not cause unrelated terminals of the
    // same fanout tree to be searched again. Compare with full-net negotiation.
    for(auto backend:{"cpu_target"
#ifdef H3D_CUDA
        ,"cuda_target"
#endif
    }) {
        g=make_graph(10);for(auto& n:g.nodes)n.capacity=1;
        edge(g,0,2,1);edge(g,2,4,1);edge(g,0,3,2);edge(g,3,4,1);
        edge(g,0,5,1);edge(g,0,6,1);edge(g,0,7,1);edge(g,1,2,1);edge(g,2,9,1);g.index();
        Options o;o.backend=backend;o.present=1;o.bbox_margin=20;o.incremental_congestion=false;
        std::vector<Net> nets{{0,0,{4,5,6,7}},{1,1,{9}}};auto full=route(g,nets,o);
        o.incremental_congestion=true;auto partial=route(g,nets,o);
        check(full.success && partial.success,"congestion subtree repair failed");
        check(partial.congestion_connections_reused>=3 && partial.gpu.searches+3<=full.gpu.searches,"unrelated fanout branches searched again");
        for(auto ei:{4U,5U,6U})check(std::find(partial.trees[0].edges.begin(),partial.trees[0].edges.end(),ei)!=partial.trees[0].edges.end(),"lost retained terminal branch");
        std::vector<uint32_t> occupancy(g.nodes.size());for(auto t:partial.trees)for(auto v:t.nodes)++occupancy[v];
        for(auto v:occupancy)check(v<=1,"subtree repair capacity accounting mismatch");
    }
    // Selective feedback must improve the critical branch without changing a
    // retained noncritical branch; occupied alternatives must roll back cleanly.
    for(bool blocked:{false,true})for(auto backend:{"cpu_target"
#ifdef H3D_CUDA
        ,"cuda_target"
#endif
    }) {
        g=make_graph(7);for(auto& n:g.nodes)n.capacity=1;
        edge(g,0,1,100);edge(g,1,4,1);edge(g,1,5,1);edge(g,0,2,1);edge(g,2,3,1);edge(g,3,4,1);edge(g,6,2,1);g.index();
        std::vector<Net> nets{{0,0,{4,5}}};if(blocked)nets.push_back({1,6,{2}});
        auto file=std::filesystem::temp_directory_path()/("h3d-refinement-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".txt");
        {std::ofstream f(file);f<<"H3DCRITICALITY 1 "<<(blocked?3:2)<<"\n0 4 990\n0 5 0\n";if(blocked)f<<"1 2 0\n";}
        Options o;o.backend=backend;o.bootstrap_criticality=0;o.present=1;o.bbox_margin=20;unsigned epoch=0;
        auto r=route_target_session(g,nets,o,[&](const Result& current){
            check(current.success,"persistent session lost legality");std::vector<uint64_t> delays(7);
            for(auto ei:current.trees[0].edges){auto e=g.edges[ei];delays[e.dst]=delays[e.src]+e.base;}
            check(delays[5]==101,"refinement changed noncritical tree prefix");
            check(delays[4]==(!epoch || blocked?101:3),"critical refinement failed or ignored occupied route");
            if(epoch){check(current.gpu.spatial_index_bytes==0,"refinement reloaded static spatial index");check(current.refinement_accepted==(!blocked && epoch==1?1U:0U),"refinement acceptance mismatch");}
            if(epoch++<2)return TargetFeedback{file.string(),700,1};return TargetFeedback{};
        });
        std::filesystem::remove(file);check(r.incremental_refinement && epoch==3,"missing persistent refinement checkpoints");
    }
    // The fast critical route is occupied by another net. Soft refinement must
    // move that blocker to its alternative; a one-iteration budget must restore
    // the original legal forest and its device occupancy on repeated attempts.
    for(bool rollback:{false,true})for(auto backend:{"cpu_target"
#ifdef H3D_CUDA
        ,"cuda_target"
#endif
    }) {
        g=make_graph(10);for(auto& n:g.nodes)n.capacity=1;
        edge(g,0,1,100);edge(g,1,4,1);edge(g,1,5,1);edge(g,0,2,1);edge(g,2,3,1);edge(g,3,4,1);
        edge(g,6,2,1);edge(g,2,7,1);edge(g,6,8,1);edge(g,8,9,1);edge(g,9,7,1);g.index();
        std::vector<Net> nets{{0,0,{4,5}},{1,6,{7}}};Options o;o.backend=backend;o.bootstrap_criticality=0;o.present=1;o.bbox_margin=20;o.iterations=rollback?1:30;
        auto file=std::filesystem::temp_directory_path()/("h3d-negotiate-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".txt");
        {std::ofstream f(file);f<<"H3DCRITICALITY 1 3\n0 4 990\n0 5 0\n1 7 0\n";}
        unsigned epoch=0;std::vector<Tree> original;
        route_target_session(g,nets,o,[&](const Result& current){
            check(current.success,"negotiated refinement lost legal checkpoint");
            std::vector<uint32_t> occupancy(10);for(auto t:current.trees)for(auto v:t.nodes)++occupancy[v];
            for(auto count:occupancy)check(count<=1,"negotiated refinement retained overuse");
            if(!epoch)original=current.trees;
            else {
                check(current.refinement_converged!=rollback,"negotiation convergence/rollback mismatch");
                check(current.gpu.spatial_index_bytes==0,"negotiation recreated GPU context");
                if(rollback){check(current.refinement_failed_overflow>0,"rollback hid failed negotiation");for(size_t i=0;i<nets.size();++i)check(current.trees[i].edges==original[i].edges && current.trees[i].nodes==original[i].nodes,"rollback did not restore exact forest");}
                else {std::vector<uint64_t> delay(10);for(auto ei:current.trees[0].edges){auto e=g.edges[ei];delay[e.dst]=delay[e.src]+e.base;}check(delay[4]==3 && delay[5]==101,"critical improvement or preserved branch delay wrong");check(std::find(current.trees[1].nodes.begin(),current.trees[1].nodes.end(),2)==current.trees[1].nodes.end(),"blocking net not repaired");}
            }
            if(epoch++<2)return TargetFeedback{file.string(),700,1,true};return TargetFeedback{};
        });std::filesystem::remove(file);
    }
    std::cout<<"target search: "<<checks<<" independent weighted-prefix/window/sparse-state oracle checks PASS\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
