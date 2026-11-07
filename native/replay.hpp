#pragma once
#include "hybrid_snapshot.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <vector>

namespace h3d_native {
inline void require(bool b,const std::string& s){if(!b)throw std::runtime_error(s);}
template<class T> T read(std::ifstream& f){T t;f.read(reinterpret_cast<char*>(&t),sizeof(t));require(bool(f),"truncated snapshot");return t;}
template<class T> std::vector<T> read_vector(std::ifstream& f,size_t n){
    require(n<=size_t(std::numeric_limits<std::streamsize>::max())/sizeof(T),"oversized snapshot array");
    auto begin=f.tellg();require(begin>=0,"unreadable snapshot array");f.seekg(0,std::ios::end);auto end=f.tellg();f.seekg(begin);
    require(end>=begin&&uint64_t(end-begin)>=uint64_t(n)*sizeof(T),"truncated snapshot array");
    std::vector<T> v(n);f.read(reinterpret_cast<char*>(v.data()),n*sizeof(T));require(bool(f),"truncated snapshot array");return v;
}
struct Graph {
    GraphHeader header;std::vector<Node> nodes;std::vector<Edge> edges;std::vector<uint32_t> native_to_edge;
    explicit Graph(const std::string& file){
        std::ifstream f(file,std::ios::binary);header=read<GraphHeader>(f);
        require(std::string(header.magic,7)=="H3DNGR1" && header.version==abi_version,"bad graph ABI");
        nodes=read_vector<Node>(f,header.nodes);edges=read_vector<Edge>(f,header.edges);
        require(f.peek()==EOF,"trailing graph data");native_to_edge.assign(edges.size(),invalid);
        size_t expected=0;
        for(size_t i=0;i<nodes.size();++i){auto n=nodes[i];require(n.first==expected && size_t(n.first)+n.count<=edges.size(),"invalid CSR");
            for(size_t j=n.first;j<size_t(n.first)+n.count;++j){const auto&e=edges[j];
                require(e.src==i && e.dst<nodes.size() && e.native_id<edges.size() && native_to_edge[e.native_id]==invalid,"invalid edge");
                require(std::isfinite(e.delay)&&e.delay>=0 && e.configurable<=1 && e.bend<=1,"invalid edge cost");native_to_edge[e.native_id]=j;
            }expected+=n.count;
        }require(expected==edges.size(),"incomplete graph CSR");
    }
};
struct Query {
    QueryHeader header;std::vector<Entry> entries;std::vector<Seed> seeds;std::vector<uint32_t> reference;
    explicit Query(const std::string& file){
        std::ifstream f(file,std::ios::binary);header=read<QueryHeader>(f);
        require(std::string(header.magic,7)=="H3DNQR1" && header.version==abi_version,"bad query ABI");
        entries=read_vector<Entry>(f,header.entries);seeds=read_vector<Seed>(f,header.seeds);reference=read_vector<uint32_t>(f,header.reference_edges);
        require(f.peek()==EOF,"trailing query data");
        require(header.criticality>=0 && header.criticality<=1 && std::isfinite(header.bend_cost)&&header.bend_cost>=0,"invalid query parameters");
    }
};
// VPR's congestion term uses double promotion (1. is a double literal),
// followed by a separately rounded float delay product and addition.
inline float backward(float g,float congestion,const Edge& e,const QueryHeader& q){
    if(e.configurable)g=float(double(g)+(1.-double(q.criticality))*double(congestion));
    float delay=q.criticality*e.delay;g=g+delay;
    if(e.bend)g=g+q.bend_cost;
    return g;
}
struct Result { float cost=INFINITY;std::vector<uint32_t> path;uint64_t visits=0,edges=0; };
struct CpuSearch {
    const Graph& graph;std::vector<float> dist,congestion,h;std::vector<uint32_t> allowed,prev;uint32_t epoch=0;
    explicit CpuSearch(const Graph&g):graph(g),dist(g.nodes.size()),congestion(dist.size()),h(dist.size()),allowed(dist.size()),prev(dist.size()){}
    void prepare(const Query&q){
        require(q.header.sink<dist.size(),"bad sink");
        if(++epoch==0){std::fill(allowed.begin(),allowed.end(),0);++epoch;}
        for(auto e:q.entries){require(e.node<dist.size()&&allowed[e.node]!=epoch,"duplicate/out-of-range window node");
            require(std::isfinite(e.congestion)&&e.congestion>=0 && std::isfinite(e.heuristic)&&e.heuristic>=0,"invalid window cost");
            allowed[e.node]=epoch;dist[e.node]=INFINITY;prev[e.node]=invalid;congestion[e.node]=e.congestion;h[e.node]=e.heuristic;
        }
        for(auto s:q.seeds)require(s.node<dist.size()&&allowed[s.node]==epoch&&std::isfinite(s.backward)&&s.backward>=0,"invalid seed");
    }
    Result search(const Query&q,bool dijkstra=false){
        prepare(q);Result result;
        struct Item{float f,g;uint32_t node;};struct Greater{bool operator()(Item a,Item b)const{return a.f>b.f;}};
        std::priority_queue<Item,std::vector<Item>,Greater> heap;
        for(auto s:q.seeds){if(s.backward<=dist[s.node]){dist[s.node]=s.backward;heap.push({dijkstra?s.backward:s.total,s.backward,s.node});}}
        while(!heap.empty()){
            auto top=heap.top();heap.pop();++result.visits;
            if(top.g!=dist[top.node])continue;
            if(top.node==q.header.sink)break;
            auto n=graph.nodes[top.node];
            for(size_t j=n.first;j<size_t(n.first)+n.count;++j){const auto&e=graph.edges[j];++result.edges;
                if(allowed[e.dst]!=epoch || dist[e.dst]<=top.g)continue;
                float g=backward(top.g,congestion[e.dst],e,q.header);
                if(g<dist[e.dst]){dist[e.dst]=g;prev[e.dst]=e.native_id;heap.push({g+(dijkstra?0.f:h[e.dst]),g,e.dst});}
            }
        }
        if(allowed[q.header.sink]!=epoch)return result;
        result.cost=dist[q.header.sink];if(!std::isfinite(result.cost))return result;
        auto v=q.header.sink;
        while(prev[v]!=invalid){auto id=prev[v];result.path.push_back(id);v=graph.edges[graph.native_to_edge[id]].src;require(result.path.size()<=q.entries.size(),"CPU predecessor cycle");}
        std::reverse(result.path.begin(),result.path.end());return result;
    }
    float validate(const Query&q,const std::vector<uint32_t>& path,float reported){
        prepare(q);uint32_t start=path.empty()?q.header.sink:graph.edges.at(graph.native_to_edge.at(path[0])).src;
        float cost=INFINITY;for(auto s:q.seeds)if(s.node==start)cost=std::min(cost,s.backward);
        require(std::isfinite(cost),"path does not start at a seed");uint32_t v=start;
        std::vector<uint32_t> seen;seen.push_back(v);
        for(auto id:path){require(id<graph.native_to_edge.size(),"path edge outside graph");const auto&e=graph.edges[graph.native_to_edge[id]];
            require(e.src==v&&allowed[e.dst]==epoch,"path disconnected or outside native window");
            cost=backward(cost,congestion[e.dst],e,q.header);v=e.dst;seen.push_back(v);
        }
        require(v==q.header.sink,"path missed sink");std::sort(seen.begin(),seen.end());
        require(std::adjacent_find(seen.begin(),seen.end())==seen.end(),"path cycle");
        require(std::isfinite(reported)&&std::abs(cost-reported)<=std::max(1e-20f,std::abs(cost)*2e-6f),"path native cost mismatch");return cost;
    }
};
}
