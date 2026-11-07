#pragma once
#include "takeover_snapshot.hpp"
#include <unordered_map>
#include <unordered_set>

namespace h3d_native {
struct TakeoverValidator {
    const Graph&g;const Model&m;const Takeover&t;
    std::unordered_map<uint32_t,const NativeLabel*>labels;
    TakeoverValidator(const Graph&graph,const Model&model,const Takeover&snapshot):g(graph),m(model),t(snapshot){
        const auto&h=t.header;
        require(h.nodes==g.nodes.size()&&m.nodes.size()==g.nodes.size()&&h.base==m.header.base_count,"takeover graph/model shape mismatch");
        require(h.query.sink<h.nodes&&h.query.criticality>=0&&h.query.criticality<=1,"bad takeover query");
        for(auto state:t.state)require(state.occupancy>=0&&std::isfinite(state.accumulated)&&state.accumulated>=0,"bad takeover occupancy/history");
        for(auto&v:t.labels){
            require(v.node<h.nodes&&labels.emplace(v.node,&v).second,"duplicate/out-of-range native label");
            require(v.upstream==0.f&&!std::isnan(v.backward)&&!std::isnan(v.total),"unsupported native label");
            if(v.prev!=invalid)require(v.prev<g.edges.size()&&g.edges[g.native_to_edge[v.prev]].dst==v.node,"bad native predecessor");
        }
        std::vector<Seed>seeds;
        for(auto v:t.labels)if(std::isfinite(v.backward))seeds.push_back({v.node,v.backward,v.total});
        require(seeds.size()==t.seeds.size(),"incomplete native labels/seeds");
        for(size_t i=0;i<seeds.size();++i)require(seeds[i].node==t.seeds[i].node&&seeds[i].backward==t.seeds[i].backward&&seeds[i].total==t.seeds[i].total,"native seed changed");
        std::unordered_set<uint32_t>seen;std::vector<uint32_t>active;
        for(auto v:t.heap){require(labels.count(v.node)&&std::isfinite(v.priority),"heap label missing");
            if(v.priority<=labels.at(v.node)->total&&seen.insert(v.node).second)active.push_back(v.node);}
        require(!active.empty()&&active==t.active,"active frontier disagrees with native heap");
        for(auto d:t.deltas)require(d.node<h.nodes&&d.state.occupancy==t.state[d.node].occupancy&&d.state.accumulated==t.state[d.node].accumulated,"pending delta differs from captured state");
        require(std::count_if(t.tree.begin(),t.tree.end(),[](const auto&n){return n.parent==invalid;})==1,"captured tree must include exactly one root");
        for(auto n:t.tree)require(n.node<h.nodes&&n.upstream==0.f&&n.downstream==0.f&&std::isfinite(n.delay),"bad tree timing prefix");
    }
    struct Prepared {
        std::vector<Seed> seeds;
        std::vector<uint32_t> active;
        std::vector<float> base;
        std::unordered_map<uint32_t,uint32_t> previous;
    };
    Prepared prepare()const {
        // Reconstruct from the actual native labels/heap on every repetition.
        // Do not time just a copy of already prepared seed/frontier arrays.
        Prepared p;
        for(auto v:t.labels)if(std::isfinite(v.backward)){
            p.seeds.push_back({v.node,v.backward,v.total});p.previous.emplace(v.node,v.prev);
        }
        std::unordered_set<uint32_t>seen;
        for(auto h:t.heap)if(h.priority<=labels.at(h.node)->total&&seen.insert(h.node).second)p.active.push_back(h.node);
        for(float cost:t.base)p.base.push_back(cost);
        return p;
    }
    float congestion(uint32_t id)const {
        auto single=[&](uint32_t v){const auto&n=m.nodes[v];auto state=t.state[v];int over=state.occupancy-int(n.capacity);
            float p=over>=0?float(1.+float(t.header.query.present*float(over+1))):1.f;
            return t.base[n.cost_index]*state.accumulated*p;};
        float c=single(id);const auto&n=m.nodes[id];
        for(uint32_t i=n.group_begin;i<n.group_begin+n.group_count;++i)if(m.groups[i]!=id)c+=single(m.groups[i]);
        return c;
    }
    void path(const std::vector<uint32_t>&edges,float reported,const Prepared*prepared=nullptr)const {
        const auto&q=t.header.query;
        uint32_t first=edges.empty()?q.sink:g.edges.at(g.native_to_edge.at(edges.front())).src;
        require(labels.count(first),"path lacks captured prefix");float cost=INFINITY;
        if(prepared){for(auto seed:prepared->seeds)if(seed.node==first)cost=std::min(cost,seed.backward);}
        else cost=labels.at(first)->backward;
        require(std::isfinite(cost),"nonfinite prefix cost");
        uint32_t v=first;std::unordered_set<uint32_t>seen;seen.insert(v);
        for(auto id:edges){const auto&e=g.edges.at(g.native_to_edge.at(id));const auto&n=m.nodes[e.dst];
            require(e.src==v&&seen.insert(e.dst).second,"disconnected/cyclic suffix");
            require(inside(n,q.box),"suffix outside native bounding box");
            const auto*b=t.header.target;
            if(n.kind==Ipin)require(n.xlo>=b[0]&&n.xhi<=b[1]&&n.ylo>=b[2]&&n.yhi<=b[3]&&n.zlo>=b[4]&&n.zlo<=b[5],"off-target IPIN");
            cost=backward(cost,congestion(e.dst),e,q);v=e.dst;
        }
        require(v==q.sink&&std::isfinite(reported)&&std::abs(cost-reported)<=std::max(1e-20f,std::abs(cost)*2e-6f),"native suffix cost/sink mismatch");
        v=first;
        while(true){require(labels.count(v),"prefix absent from captured labels");uint32_t id=prepared?prepared->previous.at(v):labels.at(v)->prev;if(id==invalid)break;
            const auto&e=g.edges.at(g.native_to_edge.at(id));require(e.dst==v&&seen.insert(e.src).second,"cyclic/disconnected native prefix");v=e.src;}
        bool root=false;for(auto n:t.tree)if(n.node==v&&n.re_expand){root=true;break;}
        require(root,"prefix root absent from expandable native tree");
    }
};
}
