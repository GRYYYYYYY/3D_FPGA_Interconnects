#include "router.hpp"
#include <algorithm>
#include <iostream>
#include <queue>
#include <random>
#include <set>
#include <stdexcept>
using namespace h3d;
constexpr uint64_t INF=UINT64_MAX/4;
void check(bool ok,const char* text) {if(!ok)throw std::runtime_error(text);}
Graph make_graph(uint32_t n) {
    Graph g;for(uint32_t i=0;i<n;++i)g.nodes.push_back({i,CHANX,2,int(i),0,0,int(i),0,0});return g;
}
void edge(Graph& g,uint32_t u,uint32_t v,uint32_t cost=1) {
    g.edges.push_back({uint32_t(g.edges.size()),u,v,0,cost,0});
}
std::vector<uint64_t> oracle(const Graph& g,const std::vector<uint32_t>& roots,const std::vector<uint32_t>& costs) {
    std::vector<uint64_t> d(g.nodes.size(),INF);
    using Item=std::pair<uint64_t,uint32_t>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> q;
    for(auto v:roots){d[v]=0;q.push({0,v});}
    while(!q.empty()) {
        auto [du,u]=q.top();q.pop();if(d[u]!=du)continue;
        for(auto a=g.offsets[u];a<g.offsets[u+1];++a) {
            auto e=g.adjacency[a],v=g.edges[e].dst;if(costs[e]==COST_INF)continue;
            if(du+costs[e]<d[v]){d[v]=du+costs[e];q.push({d[v],v});}
        }
    }
    return d;
}
void check_path(const Graph& g,const std::vector<uint32_t>& roots,uint32_t sink,
                const std::vector<uint32_t>& costs,uint64_t expected,const std::vector<uint32_t>& path) {
    if(expected==INF || expected==0) {check(path.empty(),"unexpected reachable path");return;}
    check(!path.empty(),"missing CUDA path");
    uint32_t u=g.edges.at(path.front()).src;std::set<uint32_t> seen{u};uint64_t cost=0;
    check(std::find(roots.begin(),roots.end(),u)!=roots.end(),"path starts outside roots");
    for(auto ei:path) {
        const auto& e=g.edges.at(ei);check(e.src==u && seen.insert(e.dst).second,"path connectivity/cycle failure");
        check(costs[ei]!=COST_INF,"blocked CUDA path");cost+=costs[ei];u=e.dst;
    }
    check(u==sink && cost==expected,"CUDA path differs from independent Dijkstra optimum");
}
int main() {try {
    std::mt19937 rng(217);
    for(int trial=0;trial<40;++trial) {
        auto g=make_graph(31);
        for(int i=0;i<240;++i){edge(g,rng()%31,rng()%31,1+rng()%70);g.edges.back().vertical=rng()%2;}
        for(auto& n:g.nodes)n.capacity=rng()%4;
        g.index();CudaSearch gpu(g);
        std::vector<uint32_t> occupancy(31),history(31),costs(g.edges.size());std::vector<char> allow(31,1);
        for(int snapshot=0;snapshot<3;++snapshot) {
            for(uint32_t v=0;v<31;++v){occupancy[v]=rng()%4;history[v]=rng()%3;allow[v]=rng()%5!=0;}
            const uint32_t present=19,penalty=7;bool hard=snapshot==1;
            for(size_t i=0;i<g.edges.size();++i) {
                const auto& e=g.edges[i];auto v=e.dst;
                uint64_t cost=(uint64_t(e.base)+e.vertical*penalty)*(history[v]+1)
                    +uint64_t(present)*(occupancy[v]>=g.nodes[v].capacity ? occupancy[v]-g.nodes[v].capacity+1 : 0);
                costs[i]=!allow[v] || !g.nodes[v].capacity || (hard && occupancy[v]>=g.nodes[v].capacity)
                    ? COST_INF:uint32_t(std::min(cost,uint64_t(COST_INF)));
            }
            gpu.prepare(occupancy,history,allow,present,penalty,hard);
            std::vector<uint32_t> roots;
            for(uint32_t root=0;root<5;++root) {
                roots.push_back(root);auto d=oracle(g,roots,costs);
                // Repeated searches without added roots also exercise distance reuse.
                for(uint32_t sink=0;sink<31;++sink)check_path(g,roots,sink,costs,d[sink],gpu.search_path(roots,sink));
            }
        }
        check(gpu.metrics().preparations==3,"snapshot count mismatch");
    }
    // Many simultaneously improving edges to one target: no queue duplicates,
    // races in predecessor publication, or premature sink termination.
    auto g=make_graph(130);
    for(uint32_t i=1;i<129;++i){edge(g,0,i,i);edge(g,i,129,260-2*i);}
    g.index();CudaSearch gpu(g);std::vector<uint32_t> occ(130,0),hist(130,0),costs;
    for(auto e:g.edges)costs.push_back(e.base);
    std::vector<char> allow(130,1);
    for(int repeat=0;repeat<30;++repeat) {
        gpu.prepare(occ,hist,allow,0,0,false);
        auto d=oracle(g,{0},costs);check_path(g,{0},129,costs,d[129],gpu.search_path({0},129));
    }
    // Distances exceed 32 bits; a 270-vertex chain also spans multiple warps.
    g=make_graph(270);for(uint32_t i=1;i<270;++i)edge(g,i-1,i,1000000000);g.index();
    CudaSearch wide(g);occ.assign(270,0);hist.assign(270,0);allow.assign(270,1);costs.assign(269,1000000000);
    wide.prepare(occ,hist,allow,0,0,false);
    check_path(g,{0},269,costs,269000000000ULL,wide.search_path({0},269));
    check_path(g,{0,268},269,costs,1000000000ULL,wide.search_path({0,268},269));
    bool rejected=false;try{wide.search_path({0},269);}catch(const std::runtime_error&){rejected=true;}
    check(rejected,"shrinking root set accepted");
    // End-to-end multi-terminal tree, repair and candidate fallback.
    g=make_graph(8);g.nodes[2].kind=g.nodes[3].kind=CHANZ;g.nodes[2].capacity=g.nodes[3].capacity=1;
    g.nodes[2].zhigh=g.nodes[3].zhigh=1;g.nodes[3].xlow=g.nodes[3].xhigh=100;
    edge(g,0,2);edge(g,1,2);edge(g,2,4);edge(g,2,5);edge(g,2,6);edge(g,1,3,3);edge(g,3,6);g.index();
    for(const char* backend:{"cuda","cuda_dense"}) {
        Options o;o.backend=backend;o.batch=2;
        auto r=route(g,{{0,0,{4,5}},{1,1,{6}}},o);check(r.success,"CUDA conflict repair failed");
        o.repair=false;r=route(g,{{0,0,{4,5}},{1,1,{6}}},o);check(r.success,"CUDA negotiation failed");
        o.portal_k=1;r=route(g,{{0,1,{6}}},o);check(r.success,"CUDA portal search failed");
    }
    // The shortlisted portal is unreachable; full-graph fallback must reset
    // cached costs, including when the following sink needs another fallback.
    g=make_graph(6);g.nodes[1].kind=g.nodes[2].kind=CHANZ;g.nodes[1].zhigh=g.nodes[2].zhigh=1;
    g.nodes[2].xlow=g.nodes[2].xhigh=100;edge(g,0,2);edge(g,2,4);edge(g,2,5);g.index();
    Options o;o.backend="cuda";o.portal_k=1;
    auto r=route(g,{{0,0,{4,5}}},o);check(r.success && r.fallbacks>=1,"CUDA snapshot fallback failed");
    std::cout<<"CUDA incremental snapshots, 18600 oracle paths, contention, 64-bit distances and routing PASS\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
