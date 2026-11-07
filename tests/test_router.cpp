#include "router.hpp"
#include <algorithm>
#include <iostream>
#include <queue>
#include <random>
#include <set>
#include <stdexcept>
using namespace h3d;
void check(bool x,const char* message) { if(!x) throw std::runtime_error(message); }
Graph graph(uint32_t n) {
    Graph g;
    for(uint32_t i=0;i<n;++i) g.nodes.push_back({i,CHANX,1,int(i),0,0,int(i),0,0});
    return g;
}
void edge(Graph& g,uint32_t s,uint32_t t,uint32_t c=1) { g.edges.push_back({uint32_t(g.edges.size()),s,t,0,c,uint32_t(g.nodes[t].kind==CHANZ)}); }
void audit(const Graph& g,const std::vector<Net>& nets,const Result& r) {
    std::vector<int> occupancy(g.nodes.size(),0);
    for(size_t i=0;i<nets.size();++i) {
        const auto& t=r.trees[i];std::set<uint32_t> nodes(t.nodes.begin(),t.nodes.end()),reached{nets[i].source};
        check(nodes.size()==t.nodes.size(),"duplicate node occupancy");
        if(!t.connected) {check(nodes.empty()&&t.edges.empty(),"partial failed net");continue;}
        for(auto ei:t.edges) { const auto& e=g.edges.at(ei);check(reached.count(e.src)&&!reached.count(e.dst),"broken directed tree");reached.insert(e.dst); }
        check(reached==nodes,"nodes do not match edges");
        for(auto s:nets[i].sinks) check(reached.count(s),"missing sink");
        for(auto v:nodes) ++occupancy[v];
    }
    if(r.success) for(size_t v=0;v<occupancy.size();++v) check(occupancy[v]<=int(g.nodes[v].capacity),"overcapacity success");
}
int main() { try {
    // Sparse unordered IDs remain supported, duplicates still fail, and the
    // CSR preserves edge order rather than sorting graph connectivity by ID.
    {
        auto ids=graph(3);ids.nodes[0].external=50;ids.nodes[1].external=10;ids.nodes[2].external=100;
        edge(ids,0,1);edge(ids,2,0);edge(ids,0,2);ids.edges[0].external=9;ids.edges[1].external=3;ids.edges[2].external=12;ids.index();
        check(ids.offsets==std::vector<uint32_t>({0,2,2,3}) && ids.adjacency==std::vector<uint32_t>({0,2,1}),"unordered IDs changed connectivity order");
        auto bad=ids;bad.nodes[2].external=50;bool rejected=false;try{bad.index();}catch(const std::runtime_error&){rejected=true;}check(rejected,"duplicate unordered node ID accepted");
        bad=ids;bad.edges[0].external=3;bad.edges[1].external=9;bad.edges[2].external=9;rejected=false;try{bad.index();}catch(const std::runtime_error&){rejected=true;}check(rejected,"duplicate ordered edge ID accepted");
        bad=ids;bad.nodes[0].external=10;bad.nodes[1].external=10;rejected=false;try{bad.index();}catch(const std::runtime_error&){rejected=true;}check(rejected,"duplicate adjacent node ID accepted");
    }
    // A shared vertical node has one capacity budget across both incident edges
    // and both sinks of a single net; the second net must take the alternate.
    auto g=graph(8);g.nodes[2].kind=g.nodes[3].kind=CHANZ;g.nodes[2].zhigh=g.nodes[3].zhigh=1;
    edge(g,0,2);edge(g,1,2);edge(g,2,4);edge(g,2,5);edge(g,2,6);edge(g,1,3,3);edge(g,3,6);g.index();
    std::vector<Net> nets{{0,0,{4,5}},{1,1,{6}}}; Options o;o.threads=1;o.batch=2;
    auto r=route(g,nets,o);check(r.success,"conflict repair failed");audit(g,nets,r);
    check(r.iterations[0].conflicts==1 && r.iterations[0].repairs==1,"conflict was not repaired");
#ifdef _OPENMP
    o.threads=4;auto parallel=route(g,nets,o);check(parallel.success,"parallel failed");
    for(size_t i=0;i<nets.size();++i)check(parallel.trees[i].edges==r.trees[i].edges,"nondeterministic commit");
#endif
    o.threads=1;o.repair=false;r=route(g,nets,o);check(r.success&&r.iterations.size()>1,"negotiation failed");audit(g,nets,r);
    g.nodes[3].capacity=0;r=route(g,nets,o);check(!r.success,"impossible congestion accepted");audit(g,nets,r);
    // Restriction picks an unreachable portal, then the full directed graph works.
    g=graph(5);g.nodes[1].kind=g.nodes[2].kind=CHANZ;g.nodes[1].zhigh=g.nodes[2].zhigh=1;g.nodes[2].xlow=g.nodes[2].xhigh=100;
    edge(g,0,2);edge(g,2,4);g.index();o=Options{};o.portal_k=1;
    r=route(g,{{0,0,{4}}},o);check(r.success&&r.fallbacks==1,"portal fallback failed");
    r=route(g,{{0,4,{0}}},o);check(!r.success&&r.trees[0].nodes.empty(),"reverse edge invented");
    // Independent Bellman-Ford oracle on random graphs, including parallel edges.
    std::mt19937 rng(92);o=Options{};
    for(int trial=0;trial<120;++trial) {
        g=graph(14);for(int j=0;j<60;++j)edge(g,rng()%14,rng()%14,1+rng()%25);g.index();
        std::vector<uint64_t> distance(14,UINT64_MAX/4);distance[0]=0;
        for(int j=0;j<13;++j)for(const auto& e:g.edges)distance[e.dst]=std::min(distance[e.dst],distance[e.src]+e.base);
        std::vector<Net> one{{0,0,{13}}};r=route(g,one,o);audit(g,one,r);
        check(r.success==(distance[13]<UINT64_MAX/4),"reachability oracle mismatch");
        if(r.success) {uint64_t c=0;for(auto e:r.trees[0].edges)c+=g.edges[e].base;check(c==distance[13],"shortest path oracle mismatch");}
        // A multi-terminal source tree must preserve every root-to-sink optimum,
        // not merely the cheapest incremental branch. Includes cycles and ties.
        if(trial<24) {
            Net many{0,0,{}};
            for(uint32_t v=1;v<14;++v)if(distance[v]<UINT64_MAX/4)many.sinks.push_back(v);
            std::vector<std::string> backends{"cpu"};
#ifdef H3D_CUDA
            backends.push_back("cuda");
#endif
            for(const auto& backend:backends) {
                Options so;so.source_tree=true;so.backend=backend;
                auto sr=route(g,{many},so);audit(g,{many},sr);check(sr.success,"source tree failed");
                std::vector<uint64_t> actual(14,UINT64_MAX/4);actual[0]=0;
                for(auto ei:sr.trees[0].edges){auto e=g.edges[ei];actual[e.dst]=actual[e.src]+e.base;}
                for(auto sink:many.sinks)check(actual[sink]==distance[sink],"source tree lost root delay optimum");
            }
        }
#ifdef H3D_CUDA
        for(const char* backend:{"cuda","cuda_dense"}) {
            Options co=o;co.backend=backend;auto cr=route(g,one,co);audit(g,one,cr);
            check(cr.success==r.success,"CUDA reachability mismatch");
            if(cr.success){uint64_t c=0;for(auto e:cr.trees[0].edges)c+=g.edges[e].base;check(c==distance[13],"CUDA cost mismatch");}
        }
#endif
    }
    std::cout<<"router invariants and 120 shortest-path oracle cases PASS\n";
    return 0;
} catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;} }
