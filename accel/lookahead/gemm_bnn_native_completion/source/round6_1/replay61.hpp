#pragma once
#include "bucket61.hpp"
namespace la61 {
template<bool PROFILE,class W,class D,class O>
Profile search_replay(const W& w,size_t q,uint32_t nt,unsigned shift,ScratchT<D>& s,la::Cost* out,bool witness,uint64_t edge_budget,uint64_t member_budget,O& observer){
 Profile p;p.targets=nt;const uint32_t absent=UINT32_MAX;const la::Cost inf={INFINITY,INFINITY};
 std::fill(s.label.begin(),s.label.end(),inf);std::fill(s.pending.begin(),s.pending.end(),absent);std::fill(s.seen.begin(),s.seen.end(),0);std::fill(s.in_closed.begin(),s.in_closed.end(),0);std::fill(s.ever.begin(),s.ever.end(),0);
 std::fill(s.version.begin(),s.version.end(),0);s.directory.clear();s.closed.clear();s.touched.clear();s.active.clear();
 for(size_t c=0;c<w.h.cells;++c)out[c]={la::missing(),la::missing()};
 if(!nt)return p;
 uint32_t src=w.job[q].source;s.label[src]={0,0};s.pending[src]=0;s.directory[0].push_back(src);observer.member(0,src);
 if(witness){p.witness.push_back({0,src,{0,0}});}
 uint64_t entries=1,wave=0,raw_total=0;member_budget=member_budget?member_budget:4*w.h.nodes+1;
 p.pending_peak=p.bucket_peak=1;
 auto start=std::chrono::steady_clock::now();
 while(!s.directory.empty()){
  if(++wave>=1000000 || std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()>180){p.status=la::BUDGET_EXCEEDED;return p;}
  ++p.min_select;auto it=s.directory.begin();uint32_t b=it->first;s.active=std::move(it->second);s.directory.erase(it);entries-=s.active.size();
  size_t valid=0;for(auto u:s.active){if(s.pending[u]!=b){++p.stale;continue;}s.pending[u]=absent;s.active[valid++]=u;if(!s.in_closed[u]){s.in_closed[u]=1;s.closed.push_back(u);}if(PROFILE){p.repeat_nodes+=s.ever[u]!=0;s.ever[u]=1;}}
  s.active.resize(valid);observer.begin_wave(b,wave,s.active,s.label);p.processed+=valid;s.touched.clear();Wave ws={b,valid,0,0,0,0,0};std::array<uint64_t,16> banks{};
  for(auto u:s.active){
   const auto parent=s.label[u];
   for(uint64_t k=w.row[u];k<w.row[u+1];++k){
    ++raw_total;++ws.raw;if(raw_total>edge_budget){p.status=la::BUDGET_EXCEEDED;return p;}
    auto v=w.edge[k].dst;int eligible=la::eligible(w.node[u],w.node[v]);if(!eligible)continue;if(eligible<0)break;++ws.edges;
    auto cost=w.cost[w.node[v].cost];la::Cost cand={parent.delay+cost.delay,parent.congestion+cost.congestion};
    observer.edge(q,v,cand,wave);
    if(!la::numeric(cand.delay)||!la::numeric(cand.congestion)){p.status=la::UNSUPPORTED_NUMERIC;return p;}
    if(s.seen[v]!=wave){s.seen[v]=wave;s.proposal[v]=s.label[v];s.touched.push_back(v);s.counts[v]=0;s.prop_parent[v]=UINT64_MAX;}
    if(PROFILE){++s.counts[v];++banks[v%16];ws.max_dst=std::max<uint64_t>(ws.max_dst,s.counts[v]);}
    if(less(cand,s.proposal[v])){s.proposal[v]=cand;if(witness)s.prop_parent[v]=s.version[u];}
   }
  }
  ws.distinct_dst=s.touched.size();if(PROFILE)ws.bank_max=*std::max_element(banks.begin(),banks.end());
  observer.flush();
  // Commit only after every edge read its wave-start label.
  for(auto v:s.touched)if(less(s.proposal[v],s.label[v])){
   ++p.updates;s.label[v]=s.proposal[v];uint32_t dest=bits(s.label[v].delay)>>shift;
   if(dest<b)throw std::runtime_error("nonmonotone bucket");
   if(witness){if(p.witness.size()>=2000000){p.status=la::BUDGET_EXCEEDED;return p;}p.witness.push_back({s.prop_parent[v],v,s.label[v]});s.version[v]=p.witness.size()-1;}
   if(s.pending[v]==dest){++p.dedup;continue;}
   if(s.pending[v]!=absent)++p.migrations;
   if(entries==member_budget){p.status=la::QUEUE_OVERFLOW;return p;}
   ++p.dir_lookup;s.directory[dest].push_back(v);s.pending[v]=dest;++entries;observer.member(dest,v);
  }
  p.raw+=ws.raw;p.eligible+=ws.edges;p.pending_peak=std::max(p.pending_peak,entries);p.bucket_peak=std::max<uint64_t>(p.bucket_peak,s.directory.size());if(PROFILE&&valid)p.waves.push_back(ws);
  observer.end_wave(entries,s.directory.size());
  if(s.directory.empty()||s.directory.begin()->first!=b){
   ++p.closures;for(auto u:s.closed){int c=w.cell[q*w.h.nodes+u];if(w.node[u].type==1&&c>=0){bool first=std::isnan(out[c].delay);if(first||less(s.label[u],out[c]))out[c]=s.label[u];p.recorded+=first;}s.in_closed[u]=0;}s.closed.clear();
   if(p.recorded==nt)break;
  }
 }
 return p;
}
}
