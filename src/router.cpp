#include "router.hpp"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <numeric>
#include <queue>
#include <set>
#include <stdexcept>
#ifdef _OPENMP
#include <omp.h>
#endif
namespace h3d {
namespace {
void require(bool ok, const std::string& why) { if (!ok) throw std::runtime_error(why); }
constexpr uint64_t INF = std::numeric_limits<uint64_t>::max() / 4;
}
void Graph::index() {
    require(!nodes.empty() && nodes.size() < UINT32_MAX && edges.size() < UINT32_MAX, "invalid graph size");
    // Frozen RRG projections are ordered by external ID. Strict order already
    // proves uniqueness, avoiding a tree allocation for every one of ~84M edges.
    // Unordered inputs retain the general duplicate-ID validation.
    bool ordered_nodes=std::adjacent_find(nodes.begin(),nodes.end(),[](const Node& a,const Node& b){return a.external>=b.external;})==nodes.end();
    bool ordered_edges=std::adjacent_find(edges.begin(),edges.end(),[](const Edge& a,const Edge& b){return a.external>=b.external;})==edges.end();
    std::set<uint32_t> ids;
    for (const auto& n : nodes) {
        if(!ordered_nodes)require(ids.insert(n.external).second, "duplicate external node ID");
        require(n.kind <= CHANZ && n.xlow <= n.xhigh && n.ylow <= n.yhigh && n.zlow <= n.zhigh && n.zlow >= 0, "invalid node");
    }
    ids.clear(); offsets.assign(nodes.size()+1, 0);
    for (const auto& e : edges) {
        require(e.src < nodes.size() && e.dst < nodes.size() && e.base > 0 && e.base < COST_INF && e.vertical <= 1, "invalid edge");
        if(!ordered_edges)require(ids.insert(e.external).second, "duplicate external edge ID");
        ++offsets[e.src+1];
    }
    std::partial_sum(offsets.begin(), offsets.end(), offsets.begin());
    auto cursor = offsets; adjacency.resize(edges.size());
    for (uint32_t i=0; i<edges.size(); ++i) adjacency[cursor[edges[i].src]++] = i;
}
Graph Graph::read(const std::string& path) {
    std::ifstream in(path); std::string magic; uint64_t version=0,n=0,m=0;
    in >> magic >> version >> n >> m;
    require(in && magic=="H3DRRG" && version==1 && n>0 && n<UINT32_MAX && m<UINT32_MAX, "invalid graph header: "+path);
    Graph g; g.nodes.resize(n); g.edges.resize(m);
    for (auto& v:g.nodes) in >> v.external >> v.kind >> v.capacity >> v.xlow >> v.ylow >> v.zlow >> v.xhigh >> v.yhigh >> v.zhigh;
    for (auto& e:g.edges) in >> e.external >> e.src >> e.dst >> e.sw >> e.base >> e.vertical;
    require(bool(in), "truncated graph"); std::string extra; require(!(in>>extra), "trailing graph records");
    g.index(); return g;
}
std::vector<Net> read_nets(const std::string& path, const Graph& graph) {
    std::ifstream in(path); std::string magic; uint64_t version=0,n=0;
    in>>magic>>version>>n;
    require(in && magic=="H3DNETS" && version==1 && n<UINT32_MAX, "invalid net header");
    std::vector<Net> nets(n); std::set<uint32_t> ids;
    for(auto& net:nets) {
        uint64_t count=0; in>>net.id>>net.source>>count;
        require(in && count<=graph.nodes.size() && net.source<graph.nodes.size() && ids.insert(net.id).second, "invalid net");
        net.sinks.resize(count);
        for(auto& s:net.sinks) { in>>s; require(in && s<graph.nodes.size(), "invalid sink"); }
        auto sorted=net.sinks; std::sort(sorted.begin(),sorted.end());
        require(std::adjacent_find(sorted.begin(),sorted.end())==sorted.end(), "duplicate sink in projection");
    }
    std::string extra; require(!(in>>extra), "trailing net records"); return nets;
}
namespace {
std::vector<char> shortlist(const Graph& g, const Net& net, int k) {
    std::vector<char> allow(g.nodes.size(),1);
    if (!k) return allow;
    const auto& source=g.nodes[net.source];
    std::map<std::pair<int,int>,std::vector<std::pair<int64_t,uint32_t>>> groups;
    for(uint32_t i=0;i<g.nodes.size();++i) if(g.nodes[i].kind==CHANZ) {
        const auto& p=g.nodes[i]; allow[i]=0;
        int64_t distance=std::numeric_limits<int64_t>::max()/4;
        for(auto s:net.sinks) {
            const auto& t=g.nodes[s];
            int64_t d=std::abs(int64_t(source.xlow)-p.xlow)+std::abs(int64_t(source.ylow)-p.ylow)
                +std::abs(int64_t(t.xlow)-p.xlow)+std::abs(int64_t(t.ylow)-p.ylow);
            distance=std::min(distance,d);
        }
        groups[{p.zlow,p.zhigh}].push_back({distance,i});
    }
    for(auto& group:groups) {
        auto& v=group.second; const size_t count=std::min(v.size(),size_t(k));
        std::partial_sort(v.begin(),v.begin()+count,v.end());
        for(size_t i=0;i<count;++i) allow[v[i].second]=1;
    }
    return allow;
}
struct SearchContext {
    const Graph& g; const std::vector<uint32_t>& occupancy; const std::vector<uint32_t>& history;
    const Options& options; uint32_t present;
#ifdef H3D_CUDA
    CudaSearch* gpu;
    CudaDenseSearch* dense;
#endif
    uint32_t cost(uint32_t ei, const std::vector<char>& allow, bool hard) const {
        const auto& e=g.edges[ei]; const auto& n=g.nodes[e.dst];
        if(!allow[e.dst] || (hard && occupancy[e.dst]>=n.capacity)) return COST_INF;
        return candidate_cost({e.base,history[e.dst],occupancy[e.dst],n.capacity,present,options.vertical_penalty,e.vertical,0});
    }
    bool extend(Tree& tree, std::vector<char>& used, uint32_t sink,
                const std::vector<char>& allow, bool hard) const {
        if(used[sink]) return true;
        // Source trees retain the source-to-node cost. The fixed snapshot gives
        // one shortest-path predecessor tree, independent of sink order.
        const std::vector<uint32_t> source_root = options.source_tree
            ? std::vector<uint32_t>{tree.nodes.front()} : std::vector<uint32_t>{};
        const auto& roots = options.source_tree ? source_root : tree.nodes;
#ifdef H3D_CUDA
        if(gpu) {
            auto path=gpu->search_path(roots,sink);
            if(path.empty()) return false;
            size_t begin=0;
            if(options.source_tree) {
                // The already committed prefix has the same deterministic
                // tight predecessors. Append only the new branch.
                while(begin<path.size() && used[g.edges[path[begin]].dst]) ++begin;
            }
            if(begin==path.size()) return used[sink];
            uint32_t previous=g.edges[path[begin]].src;
            require(used[previous],"CUDA path must start in the existing tree");
            for(size_t j=begin;j<path.size();++j) {
                auto ei=path[j];
                const auto& e=g.edges[ei];
                require(e.src==previous && !used[e.dst],"invalid CUDA branch");
                tree.edges.push_back(ei); tree.nodes.push_back(e.dst); used[e.dst]=1; previous=e.dst;
            }
            require(previous==sink,"CUDA path missed sink");
            return true;
        }
#endif
        std::vector<int64_t> parent(g.nodes.size(),-1);
#ifdef H3D_CUDA
        if(dense) {
            std::vector<uint32_t> costs(g.edges.size());
            for(uint32_t e=0;e<costs.size();++e) costs[e]=cost(e,allow,hard);
            parent=dense->search(roots,sink,costs);
        } else
#endif
        {
            std::vector<uint64_t> distance(g.nodes.size(),INF);
            using Item=std::pair<uint64_t,uint32_t>;
            std::priority_queue<Item,std::vector<Item>,std::greater<Item>> queue;
            for(auto n:roots) { distance[n]=0; queue.push({0,n}); }
            while(!queue.empty()) {
                auto [d,u]=queue.top(); queue.pop();
                if(d!=distance[u]) continue;
                ++tree.expansions;
                if(u==sink) break;
                for(uint32_t a=g.offsets[u];a<g.offsets[u+1];++a) {
                    auto ei=g.adjacency[a]; const auto& e=g.edges[ei]; auto c=cost(ei,allow,hard);
                    if(c==COST_INF) continue;
                    const uint64_t next=d+c;
                    if(next<distance[e.dst]) { distance[e.dst]=next; parent[e.dst]=ei; queue.push({next,e.dst}); }
                }
            }
        }
        if(parent[sink]<0) return false;
        std::vector<uint32_t> path;
        uint32_t v=sink;
        while(!used[v]) {
            require(parent[v]>=0 && path.size()<g.nodes.size(), "invalid search predecessor chain");
            const auto e=uint32_t(parent[v]); path.push_back(e); v=g.edges[e].src;
        }
        for(auto it=path.rbegin();it!=path.rend();++it) {
            const auto& e=g.edges[*it]; tree.edges.push_back(*it); tree.nodes.push_back(e.dst); used[e.dst]=1;
        }
        return true;
    }
    Tree make_tree(const Net& net, bool hard=false, bool restrict_portals=true) const {
        Tree t;
        if(!g.nodes[net.source].capacity || (hard && occupancy[net.source]>=g.nodes[net.source].capacity)) return t;
        t.nodes.push_back(net.source); std::vector<char> used(g.nodes.size(),0); used[net.source]=1;
        auto allow=shortlist(g,net,restrict_portals?options.portal_k:0);
#ifdef H3D_CUDA
        if(gpu) gpu->prepare(occupancy,history,allow,present,options.vertical_penalty,hard);
#endif
        for(auto sink:net.sinks) {
            if(!extend(t,used,sink,allow,hard)) {
                if(restrict_portals && options.portal_k) {
                    ++t.fallbacks; std::vector<char> full(g.nodes.size(),1);
#ifdef H3D_CUDA
                    if(gpu) gpu->prepare(occupancy,history,full,present,options.vertical_penalty,hard);
#endif
                    if(extend(t,used,sink,full,hard)) {
                        // Later sinks return to the restricted cost snapshot.
#ifdef H3D_CUDA
                        if(gpu) gpu->prepare(occupancy,history,allow,present,options.vertical_penalty,hard);
#endif
                        continue;
                    }
                }
                // Failed nets never retain partial occupancy.
                t.nodes.clear(); t.edges.clear(); return t;
            }
        }
        t.connected=true; return t;
    }
};
}
Result route(const Graph& g, const std::vector<Net>& nets, const Options& o) {
    if(o.backend=="cpu_target" || o.backend=="cuda_target") return route_target(g,nets,o);
    require(o.threads>0 && o.batch>0 && o.iterations>0 && o.portal_k>=0 &&
            o.present<COST_INF && o.history_step<COST_INF && o.vertical_penalty<COST_INF, "invalid options");
    require(o.backend=="cpu" || o.backend=="cuda" || o.backend=="cuda_dense", "unknown backend");
    require(!o.source_tree || (o.portal_k==0 && o.backend!="cuda_dense"),
            "source trees require full-graph CPU or frontier CUDA search");
#ifndef _OPENMP
    require(o.threads==1,"OpenMP unavailable; use --threads 1");
#endif
#ifdef H3D_CUDA
    std::unique_ptr<CudaSearch> gpu;
    std::unique_ptr<CudaDenseSearch> dense;
    if(o.backend=="cuda") gpu=std::make_unique<CudaSearch>(g);
    if(o.backend=="cuda_dense") dense=std::make_unique<CudaDenseSearch>(g);
#else
    require(o.backend=="cpu", "CUDA backend not built; configure -DH3D_CUDA=ON on a CUDA machine");
#endif
    const auto start=std::chrono::steady_clock::now();
    Result result; result.trees.resize(nets.size());
    std::vector<uint32_t> occupancy(g.nodes.size(),0),history(g.nodes.size(),0);
    uint32_t present=o.present;
    for(int iteration=0;iteration<o.iterations;++iteration) {
        Iteration stats{}; std::vector<uint32_t> pending;
        // Keep conflict-free trees; only rip up unrouted or overused nets.
        // This also prevents parallel batches from repeatedly disrupting legal trees.
        for(uint32_t ni=0;ni<nets.size();++ni) {
            const auto& tree=result.trees[ni];
            bool needs_route=!tree.connected;
            for(auto v:tree.nodes) if(occupancy[v]>g.nodes[v].capacity) { needs_route=true;break; }
            if(needs_route) pending.push_back(ni);
        }
        const auto rerouted=pending.size();
        uint64_t committed=0;
        while(!pending.empty()) {
            std::vector<uint32_t> batch, remaining; std::set<uint32_t> portals;
            for(auto ni:pending) {
                bool conflict=false;
                if(o.portal_schedule) for(auto v:result.trees[ni].nodes)
                    if(g.nodes[v].kind==CHANZ && portals.count(v)) { conflict=true; break; }
                if(batch.size()<size_t(o.batch) && !conflict) {
                    batch.push_back(ni);
                    for(auto v:result.trees[ni].nodes) if(g.nodes[v].kind==CHANZ) portals.insert(v);
                } else remaining.push_back(ni);
            }
            pending.swap(remaining);
            for(auto ni:batch) for(auto v:result.trees[ni].nodes) { require(occupancy[v]>0,"occupancy underflow"); --occupancy[v]; }
            SearchContext ctx{g,occupancy,history,o,present
#ifdef H3D_CUDA
                ,gpu.get(),dense.get()
#endif
            };
            std::vector<Tree> candidates(batch.size());
            // Immutable occupancy/history during search. All commits happen after the barrier.
            int worker_count=o.backend=="cpu"?o.threads:1;
#ifdef _OPENMP
#pragma omp parallel for schedule(static) num_threads(worker_count) if(worker_count>1)
#else
            (void)worker_count;
#endif
            for(size_t j=0;j<batch.size();++j) candidates[j]=ctx.make_tree(nets[batch[j]]);
            for(size_t j=0;j<batch.size();++j) {
                auto& t=candidates[j]; result.expansions+=t.expansions; result.fallbacks+=t.fallbacks;
                bool conflict=false;
                for(auto v:t.nodes) if(occupancy[v]>=g.nodes[v].capacity) { conflict=true; break; }
                if(conflict) {
                    ++stats.conflicts;
                    if(o.repair) {
                        auto repaired=ctx.make_tree(nets[batch[j]],true,false);
                        result.expansions+=repaired.expansions;
                        if(repaired.connected) { t=std::move(repaired); ++stats.repairs; }
                        else {
                            // A hard-capacity search can fail when other trees
                            // need to move. Recompute with the live negotiated
                            // costs so later nets see earlier commits. Retaining
                            // a stale snapshot path here can lock a batch into
                            // choosing the same OPIN/portal every iteration.
                            auto negotiated=ctx.make_tree(nets[batch[j]],false,false);
                            result.expansions+=negotiated.expansions;
                            if(negotiated.connected) t=std::move(negotiated);
                        }
                    }
                }
                for(auto v:t.nodes) ++occupancy[v];
                result.trees[batch[j]]=std::move(t);
            }
            committed+=batch.size();
            if(committed%4096==0) {
                std::cerr<<"progress iteration="<<iteration+1<<" committed="<<committed<<" pending="<<pending.size()
                         <<" elapsed="<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
#ifdef H3D_CUDA
                if(gpu) { const auto m=gpu->metrics(); std::cerr<<" gpu_search_seconds="<<m.search_seconds
                    <<" frontier_vertices="<<m.frontier_vertices<<" h2d_bytes="<<m.h2d_bytes; }
#endif
                std::cerr<<'\n';
            }
        }
        for(auto& t:result.trees) stats.unrouted+=!t.connected;
        for(size_t v=0;v<g.nodes.size();++v) if(occupancy[v]>g.nodes[v].capacity) {
            const uint64_t excess=occupancy[v]-g.nodes[v].capacity; stats.overflow+=excess;
            history[v]=uint32_t(std::min(uint64_t(COST_INF-1),uint64_t(history[v])+excess*o.history_step));
        }
        result.iterations.push_back(stats);
        std::cerr<<"iteration="<<iteration+1<<" rerouted="<<rerouted<<" overflow="<<stats.overflow
                 <<" unrouted="<<stats.unrouted<<" conflicts="<<stats.conflicts<<" repairs="<<stats.repairs<<'\n';
        if(stats.unrouted==0 && stats.overflow==0) { result.success=true; break; }
        // Disconnected topology cannot be fixed by congestion negotiation.
        if(stats.unrouted && !stats.overflow) break;
        present=uint32_t(std::min(uint64_t(COST_INF-1),uint64_t(present)*3/2+1));
    }
    result.routing_seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
#ifdef H3D_CUDA
    if(gpu) result.gpu=gpu->metrics();
#endif
    return result;
}
void write_result(const std::string& path, const Graph& g, const std::vector<Net>& nets, const Options& o, const Result& r) {
    std::ofstream out(path); require(bool(out),"cannot write result: "+path);
    out.precision(10);
    out<<"{\n\"schema_version\":1,\"execution_kind\":\"rrg_projection\",\"vpr_full_check\":false,\n"
       <<"\"success\":"<<(r.success?"true":"false")<<",\"backend\":\""<<o.backend<<"\",\"threads\":"<<o.threads
       <<",\"batch\":"<<o.batch<<",\"portal_k\":"<<o.portal_k<<",\"portal_schedule\":"<<(o.portal_schedule?"true":"false")
       <<",\"repair\":"<<(o.repair?"true":"false")<<",\"source_tree\":"<<(o.source_tree?"true":"false")<<",\"vertical_penalty\":"<<o.vertical_penalty
       <<",\"routing_seconds\":"<<r.routing_seconds<<",\"expansions\":"<<r.expansions<<",\"fallbacks\":"<<r.fallbacks<<",\n\"iterations\":[";
    for(size_t i=0;i<r.iterations.size();++i) {
        const auto& s=r.iterations[i]; if(i) out<<',';
        out<<"{\"overflow\":"<<s.overflow<<",\"unrouted\":"<<s.unrouted<<",\"conflicts\":"<<s.conflicts<<",\"repairs\":"<<s.repairs<<'}';
    }
    out<<"],\n\"gpu_metrics\":";
    if(o.backend!="cuda" && o.backend!="cuda_target" && o.backend!="cpu_target") out<<"null";
    else out<<"{\"preparations\":"<<r.gpu.preparations<<",\"searches\":"<<r.gpu.searches
        <<",\"rounds\":"<<r.gpu.rounds<<",\"frontier_vertices\":"<<r.gpu.frontier_vertices
        <<",\"h2d_bytes\":"<<r.gpu.h2d_bytes<<",\"d2h_bytes\":"<<r.gpu.d2h_bytes
        <<",\"prepare_seconds\":"<<r.gpu.prepare_seconds<<",\"search_seconds\":"<<r.gpu.search_seconds
        <<",\"state_updates\":"<<r.gpu.state_updates<<",\"window_vertices\":"<<r.gpu.window_vertices
        <<",\"window_fallbacks\":"<<r.gpu.window_fallbacks
        <<",\"window_h2d_bytes\":"<<r.gpu.window_h2d_bytes
        <<",\"spatial_index_bytes\":"<<r.gpu.spatial_index_bytes
        <<",\"box_queries\":"<<r.gpu.box_queries
        <<",\"cpu_window_seconds\":"<<r.gpu.cpu_window_seconds
        <<",\"window_upload_seconds\":"<<r.gpu.window_upload_seconds
        <<",\"window_init_seconds\":"<<r.gpu.window_init_seconds
        <<",\"relaxation_seconds\":"<<r.gpu.relaxation_seconds
        <<",\"traceback_seconds\":"<<r.gpu.traceback_seconds
        <<",\"state_update_seconds\":"<<r.gpu.state_update_seconds
        <<",\"tree_update_seconds\":"<<r.gpu.tree_update_seconds<<'}';
    out<<",\"timing_driven\":"<<((o.backend=="cpu_target" || o.backend=="cuda_target")?"true":"false")
       <<",\"bootstrap_criticality\":"<<o.bootstrap_criticality<<",\"sta_feedback\":"<<((r.incremental_refinement || !o.criticality_file.empty())?"true":"false")
       <<",\"incremental_refinement\":"<<(r.incremental_refinement?"true":"false")
       <<",\"refinement_connections\":"<<r.refinement_connections<<",\"refinement_accepted\":"<<r.refinement_accepted
       <<",\"incremental_congestion\":"<<(o.incremental_congestion?"true":"false")
       <<",\"congestion_connections_reused\":"<<r.congestion_connections_reused
       <<",\"refinement_mode\":\""<<r.refinement_mode<<"\",\"refinement_converged\":"<<(r.refinement_converged?"true":"false")
       <<",\"refinement_failed_overflow\":"<<r.refinement_failed_overflow<<",\"refinement_failed_unrouted\":"<<r.refinement_failed_unrouted
       <<",\"present_cap\":"<<o.present_cap<<",\"window_mode\":\""<<o.window_mode<<"\",\"heuristic\":\""<<o.heuristic<<'"';
    out<<",\n\"routes\":[";
    for(size_t i=0;i<nets.size();++i) {
        if(i) out<<',';
        const auto& t=r.trees[i];
        out<<"{\"net\":"<<nets[i].id<<",\"connected\":"<<(t.connected?"true":"false")<<",\"nodes\":[";
        for(size_t j=0;j<t.nodes.size();++j) { if(j) out<<','; out<<g.nodes[t.nodes[j]].external; }
        out<<"],\"edges\":[";
        for(size_t j=0;j<t.edges.size();++j) { if(j) out<<','; out<<g.edges[t.edges[j]].external; }
        out<<"]}";
    }
    out<<"]\n}\n"; require(bool(out),"result write failed");
}
}
