#pragma once
#include "compact61.hpp"
#include "directory61.hpp"
#include <algorithm>
#include <map>
#include <climits>
#include <cstring>
#include <cmath>
#include <chrono>
#include <array>
namespace la61 {
inline uint32_t bits(float f){uint32_t u;std::memcpy(&u,&f,4);return u;}
inline bool less(la::Cost a,la::Cost b){return a.delay<b.delay || (a.delay==b.delay&&a.congestion<b.congestion);}
struct Prepared {
 std::vector<uint32_t> targets;
 template<class W> explicit Prepared(const W& w):targets(w.h.jobs){
  for(auto n:w.node)if(n.inter&&n.type!=2){auto c=w.cost[n.cost];if(!la::numeric(c.delay)||!la::numeric(c.congestion))throw std::runtime_error("UNSUPPORTED_NUMERIC admission");}
  std::vector<bool> seen(w.h.cells);
  for(size_t q=0;q<w.h.jobs;++q){std::fill(seen.begin(),seen.end(),false);for(size_t u=0;u<w.h.nodes;++u){int c=w.cell[q*w.h.nodes+u];if(w.node[u].type==1&&c>=0&&!seen[c]){seen[c]=true;++targets[q];}}}
 }
};
struct Wave {uint64_t bucket,width,raw,edges,distinct_dst,max_dst,bank_max;};
struct Witness {uint64_t parent;uint32_t dst;la::Cost pair;};
struct Profile {
 uint64_t raw=0,eligible=0,updates=0,stale=0,migrations=0,dedup=0,dir_lookup=0,min_select=0,closures=0,pending_peak=0,bucket_peak=0,processed=0,repeat_nodes=0,targets=0,recorded=0;
 std::vector<Wave> waves;std::vector<Witness> witness;uint32_t status=0;
};
template<class Directory> struct ScratchT {
 std::vector<la::Cost> label,proposal;
 std::vector<uint32_t> pending,seen,counts,touched,closed,active;
 std::vector<uint64_t> version,prop_parent;
 std::vector<unsigned char> in_closed,ever;
 Directory directory;
 explicit ScratchT(size_t n):label(n),proposal(n),pending(n),seen(n),counts(n),version(n),prop_parent(n),in_closed(n),ever(n){touched.reserve(n);closed.reserve(n);active.reserve(n);}
};
// All mutable state is reset inside E1. No persistent graph residency or fallback.
template<bool PROFILE,class W,class D>
Profile search(const W& w,size_t q,uint32_t nt,unsigned shift,ScratchT<D>& s,la::Cost* out,bool witness=false,uint64_t edge_budget=500000000,uint64_t member_budget=0){
 Profile p;p.targets=nt;const uint32_t absent=UINT32_MAX;const la::Cost inf={INFINITY,INFINITY};
 std::fill(s.label.begin(),s.label.end(),inf);std::fill(s.pending.begin(),s.pending.end(),absent);std::fill(s.seen.begin(),s.seen.end(),0);std::fill(s.in_closed.begin(),s.in_closed.end(),0);std::fill(s.ever.begin(),s.ever.end(),0);
 std::fill(s.version.begin(),s.version.end(),0);s.directory.clear();s.closed.clear();s.touched.clear();s.active.clear();
 for(size_t c=0;c<w.h.cells;++c)out[c]={la::missing(),la::missing()};
 if(!nt)return p;
 uint32_t src=w.job[q].source;s.label[src]={0,0};s.pending[src]=0;s.directory[0].push_back(src);
 if(witness){p.witness.push_back({0,src,{0,0}});}
 uint64_t entries=1,wave=0,raw_total=0;member_budget=member_budget?member_budget:4*w.h.nodes+1;
 p.pending_peak=p.bucket_peak=1;
 auto start=std::chrono::steady_clock::now();
 while(!s.directory.empty()){
  if(++wave>=1000000 || std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()>180){p.status=la::BUDGET_EXCEEDED;return p;}
  ++p.min_select;auto it=s.directory.begin();uint32_t b=it->first;s.active=std::move(it->second);s.directory.erase(it);entries-=s.active.size();
  size_t valid=0;for(auto u:s.active){if(s.pending[u]!=b){++p.stale;continue;}s.pending[u]=absent;s.active[valid++]=u;if(!s.in_closed[u]){s.in_closed[u]=1;s.closed.push_back(u);}if(PROFILE){p.repeat_nodes+=s.ever[u]!=0;s.ever[u]=1;}}
  s.active.resize(valid);p.processed+=valid;s.touched.clear();Wave ws={b,valid,0,0,0,0,0};std::array<uint64_t,16> banks{};
  for(auto u:s.active){
   const auto parent=s.label[u];
   for(uint64_t k=w.row[u];k<w.row[u+1];++k){
    ++raw_total;++ws.raw;if(raw_total>edge_budget){p.status=la::BUDGET_EXCEEDED;return p;}
    auto v=w.edge[k].dst;int eligible=la::eligible(w.node[u],w.node[v]);if(!eligible)continue;if(eligible<0)break;++ws.edges;
    auto cost=w.cost[w.node[v].cost];la::Cost cand={parent.delay+cost.delay,parent.congestion+cost.congestion};
    if(!la::numeric(cand.delay)||!la::numeric(cand.congestion)){p.status=la::UNSUPPORTED_NUMERIC;return p;}
    if(s.seen[v]!=wave){s.seen[v]=wave;s.proposal[v]=s.label[v];s.touched.push_back(v);s.counts[v]=0;s.prop_parent[v]=UINT64_MAX;}
    if(PROFILE){++s.counts[v];++banks[v%16];ws.max_dst=std::max<uint64_t>(ws.max_dst,s.counts[v]);}
    if(less(cand,s.proposal[v])){s.proposal[v]=cand;if(witness)s.prop_parent[v]=s.version[u];}
   }
  }
  ws.distinct_dst=s.touched.size();if(PROFILE)ws.bank_max=*std::max_element(banks.begin(),banks.end());
  // Commit only after every edge read its wave-start label.
  for(auto v:s.touched)if(less(s.proposal[v],s.label[v])){
   ++p.updates;s.label[v]=s.proposal[v];uint32_t dest=bits(s.label[v].delay)>>shift;
   if(dest<b)throw std::runtime_error("nonmonotone bucket");
   if(witness){if(p.witness.size()>=2000000){p.status=la::BUDGET_EXCEEDED;return p;}p.witness.push_back({s.prop_parent[v],v,s.label[v]});s.version[v]=p.witness.size()-1;}
   if(s.pending[v]==dest){++p.dedup;continue;}
   if(s.pending[v]!=absent)++p.migrations;
   if(entries==member_budget){p.status=la::QUEUE_OVERFLOW;return p;}
   ++p.dir_lookup;s.directory[dest].push_back(v);s.pending[v]=dest;++entries;
  }
  p.raw+=ws.raw;p.eligible+=ws.edges;p.pending_peak=std::max(p.pending_peak,entries);p.bucket_peak=std::max<uint64_t>(p.bucket_peak,s.directory.size());if(PROFILE&&valid)p.waves.push_back(ws);
  if(s.directory.empty()||s.directory.begin()->first!=b){
   ++p.closures;for(auto u:s.closed){int c=w.cell[q*w.h.nodes+u];if(w.node[u].type==1&&c>=0){bool first=std::isnan(out[c].delay);if(first||less(s.label[u],out[c]))out[c]=s.label[u];p.recorded+=first;}s.in_closed[u]=0;}s.closed.clear();
   if(p.recorded==nt)break;
  }
 }
 return p;
}
}
