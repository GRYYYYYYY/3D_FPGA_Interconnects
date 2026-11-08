#pragma once
#include "io.hpp"
#include <algorithm>
#include <cfloat>
#include <queue>

namespace la4 {
static std::vector<unsigned> layers;static uint64_t cross_scanned=0,cross_pushed=0;
enum Mode { STRICT_FULL_FLOOD=0, MAP_EQUIVALENT_EARLY_STOP=1 };
inline const char* mode_name(bool early) {
    return early ? "MAP_EQUIVALENT_EARLY_STOP" : "STRICT_FULL_FLOOD";
}
struct Prepared {
    std::vector<uint32_t> targets;
    explicit Prepared(const la::Workload& w) : targets(w.h.jobs,0) {
        // Admission proof, not a reachability search or golden-data prepass.
        // Any expanded path is simple; at most N nonnegative additions occur.
        // N*u < 1/2 implies the standard RN error bound is less than 2*N*max.
        if(w.h.nodes >= (1u<<23) || w.h.edges >= UINT32_MAX)
            throw std::runtime_error("unsupported numeric/capacity admission bound");
        double maximum=0;
        for(const auto& node:w.node) if(node.inter && node.type!=2) {
            auto c=w.cost[node.cost];
            if(!la::numeric(c.delay)||!la::numeric(c.congestion))
                throw std::runtime_error("unsupported eligible cost: finite normal positive or +0 required");
            maximum=std::max(maximum,double(std::max(c.delay,c.congestion)));
        }
        if(2.*w.h.nodes*maximum>double(FLT_MAX))
            throw std::runtime_error("path accumulation cannot be certified finite");
        std::vector<unsigned char> mask(w.h.cells);
        for(size_t q=0;q<w.h.jobs;++q) {
            std::fill(mask.begin(),mask.end(),0);
            for(size_t u=0;u<w.h.nodes;++u) {
                int c=w.cell[q*w.h.nodes+u];
                if(w.node[u].type==1 && c>=0 && !mask[c]) {
                    mask[c]=1; ++targets[q];
                }
            }
        }
    }
};
struct Compare { bool operator()(la::Entry a,la::Entry b)const{return a.delay>b.delay;} };
struct Queue : std::priority_queue<la::Entry,std::vector<la::Entry>,Compare> {
    void reserve(size_t n){this->c.reserve(n);}
    void reset(){this->c.clear();} // Entry is trivial: discard an early suffix in O(1).
};
struct Scratch {
    std::vector<float> visited;
    std::vector<unsigned char> expanded;
    Queue queue;
    Scratch(size_t n,size_t capacity):visited(n),expanded(n){queue.reserve(capacity);}
};
struct StopInfo { uint32_t remaining,recorded,reason; }; // 0 exhausted, 1 covered, 2 empty targets

template<bool EARLY>
inline la::Stats search(const la::Workload& w,size_t q,uint32_t targets,Scratch& s,
                        la::Cost* output,StopInfo& info) {
    std::fill(s.visited.begin(),s.visited.end(),-1.f);
    std::fill(s.expanded.begin(),s.expanded.end(),0);
    // A NaN delay is also the unseen-cell bit. This logical seen reset is in E1.
    for(size_t c=0;c<w.h.cells;++c)output[c]={la::missing(),la::missing()};
    s.queue.reset(); info={0,0,0};
    la::Stats st={0,0,0,0,0,la::OK};
    if(EARLY && !targets){info.reason=2;return st;}
    s.queue.push({w.job[q].source,0,0});st.pushes=st.peak=1;
    while(!s.queue.empty()) {
        auto cur=s.queue.top();s.queue.pop();++st.pops;
        unsigned u=cur.node;if(s.expanded[u])continue;
        int cell=w.cell[q*w.h.nodes+u];
        if(w.node[u].type==1 && cell>=0) {
            bool first=output[cell].delay!=output[cell].delay;
            la::record(output[cell],cur);
            if(EARLY && first && ++info.recorded==targets){info.reason=1;break;}
        }
        for(uint64_t i=w.row[u];i<w.row[u+1];++i) {
            ++st.edges;auto v=w.edge[i].dst;cross_scanned+=layers[u]!=layers[v];int eligible=la::eligible(w.node[u],w.node[v]);
            if(!eligible)continue;if(eligible<0)break;if(s.expanded[v])continue;
            auto c=w.cost[w.node[v].cost];
            la::Entry next={v,cur.delay+c.delay,cur.congestion+c.congestion};
            if(!la::numeric(c.delay)||!la::numeric(c.congestion)||!la::numeric(next.delay)||!la::numeric(next.congestion))
                {st.status=la::UNSUPPORTED_NUMERIC;break;}
            if(s.visited[v]>=0 && s.visited[v]<next.delay)continue;
            if(s.queue.size()==w.h.edges+1){st.status=la::QUEUE_OVERFLOW;break;}
            s.visited[v]=next.delay;s.queue.push(next);++st.pushes;cross_pushed+=layers[u]!=layers[v];
            st.peak=std::max<uint64_t>(st.peak,s.queue.size());
        }
        if(st.status)break;
        s.expanded[u]=1;++st.expanded;
    }
    info.remaining=s.queue.size();return st;
}
}
