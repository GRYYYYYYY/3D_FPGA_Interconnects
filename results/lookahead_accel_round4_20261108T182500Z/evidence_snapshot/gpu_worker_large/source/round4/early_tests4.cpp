#include "reference4.hpp"
#include "kernel.hpp"
#include <cassert>
#include <cstring>
#include <iostream>
#include <random>
#include <string>
struct Graph {
    std::vector<la::Node> nodes;std::vector<std::vector<unsigned>> adj;
    std::vector<la::Cost> costs;std::vector<int32_t> cells;unsigned nc=0,source=0;
};
int main(int argc,char** argv){try{
    if(argc!=2)throw std::runtime_error("fixture directory required");
    unsigned checks=0;
    auto test=[&](const std::string& name,const Graph& g,int expected_reason=-1){
        std::vector<uint64_t> row(1,0);std::vector<la::Edge> edges;
        for(auto& a:g.adj){for(auto v:a)edges.push_back({v,0});row.push_back(edges.size());}
        la::Header h={la::MAGIC,g.nodes.size(),edges.size(),1,g.costs.size(),g.nc,1};
        la::Job job={g.source,0,0,0,0,0};std::vector<float> visited(h.nodes);std::vector<uint32_t> expanded(h.nodes);
        std::vector<la::Entry> heap(h.edges+1);std::vector<la::Cost> golden(h.cells);la::Stats old;
        lookahead_top(row.data(),g.nodes.data(),edges.data(),g.costs.data(),&job,g.cells.data(),visited.data(),expanded.data(),heap.data(),golden.data(),&old,h.nodes,1,h.cells,h.edges+1,h.edges+1);
        assert(old.status==0);
        std::string path=std::string(argv[1])+"/"+name+".bin";
        {std::ofstream f(path,std::ios::binary);la::write(f,&h,1);la::write(f,row.data(),row.size());la::write(f,g.nodes.data(),g.nodes.size());la::write(f,edges.data(),edges.size());la::write(f,g.costs.data(),g.costs.size());la::write(f,&job,1);la::write(f,g.cells.data(),g.cells.size());la::write(f,golden.data(),golden.size());}
        la::Workload w(path.c_str());la4::Prepared prep(w);la4::Scratch scratch(h.nodes,h.edges+1);std::vector<la::Cost> out(h.cells);
        for(unsigned repeat=0;repeat<3;++repeat){la4::StopInfo info;
            auto full=la4::search<false>(w,0,prep.targets[0],scratch,out.data(),info);
            assert(full.status==0&&full.pops==old.pops&&full.pushes==old.pushes&&full.peak==old.peak&&full.edges==old.edges&&full.expanded==old.expanded);
            assert(!std::memcmp(out.data(),golden.data(),out.size()*sizeof(la::Cost)));
            auto early=la4::search<true>(w,0,prep.targets[0],scratch,out.data(),info);
            assert(!early.status&&!std::memcmp(out.data(),golden.data(),out.size()*sizeof(la::Cost)));
            assert(early.pops<=full.pops&&early.edges<=full.edges);
            if(expected_reason>=0)assert(info.reason==unsigned(expected_reason));
            ++checks;
        }
        if(name=="tie"){
            for(float bad:{-0.f,-1.f,std::numeric_limits<float>::denorm_min(),std::numeric_limits<float>::infinity(),la::missing(),FLT_MAX}){
                auto copy=w;copy.cost[2].delay=bad;bool rejected=false;
                try{la4::Prepared rejected_input(copy);}catch(const std::exception&){rejected=true;}
                assert(rejected);++checks;
            }
        }
    };
    Graph tie{{{0,0,1,0},{1,1,1,-1},{1,2,1,-1}},{{1,2},{},{}},{{0,0},{0,1},{0,2}},{-1,0,0},1};
    test("tie",tie,1);auto unreachable=tie;unreachable.adj[0]={1};unreachable.cells[2]=1;unreachable.nc=2;test("unreachable",unreachable,0);
    auto empty=tie;empty.cells={-1,-1,-1};test("empty_targets",empty,2);
    auto sink=tie;sink.nodes[1].type=2;sink.cells[1]=-1;test("sink_order",sink,0);
    auto filtered=sink;filtered.nodes[1].segment_kind=1;test("filtered_sink",filtered,1);
    auto duplicate=tie;duplicate.adj[0]={1,1,2};test("duplicate_edges",duplicate,1);
    auto cycle=tie;cycle.adj[1]={0,2};cycle.adj[2]={1};test("zero_cycle",cycle,1);
    auto hidden=unreachable;hidden.nodes[2].inter=0;test("ineligible_target_not_removed",hidden,0);
    auto source=tie;source.source=1;source.cells={-1,0,-1};test("source_ipin",source,1);
    std::mt19937 rng(4041);
    for(unsigned trial=0;trial<500;++trial){Graph g;unsigned n=2+rng()%95;g.nc=1+rng()%8;g.source=rng()%n;
        g.costs={{0,0},{0,2},{.25f,3},{1,4},{2,0}};g.adj.resize(n);
        for(unsigned u=0;u<n;++u){g.nodes.push_back({rng()%3,rng()%5,rng()%5?1u:0u,int(rng()%3)-1});g.cells.push_back(int(rng()%(g.nc+1))-1);
            for(unsigned k=0,z=rng()%9;k<z;++k)g.adj[u].push_back(rng()%n);
        }
        test("random_"+std::to_string(trial),g);
    }
    std::cout<<"PASS "<<checks<<" checks: legacy full Stats/maps, early maps, leftover/reuse, ties, shared/unreachable/empty targets, zero cycles, duplicate edges, SINK order, numeric admission\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
