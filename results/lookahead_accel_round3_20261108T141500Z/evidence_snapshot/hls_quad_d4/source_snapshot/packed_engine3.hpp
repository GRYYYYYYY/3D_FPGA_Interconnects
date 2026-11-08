#pragma once
// Same search/cache algorithm as the round-two resident core. Each engine owns all scratch and caches.
#include "packed_kernel3.hpp"
#include "packed_label3.hpp"
#include "cache.hpp"
#ifndef LA_COST_LINES
#define LA_COST_LINES 64
#endif
namespace {
struct CostLine {uint32_t tag;bool valid;la::Cost cost;};
}
template<int ID> static void packed_engine(const uint64_t* row,const la::Node* nodes,const la::Edge* edges,const la::Cost* costs,const la::Job* jobs,const int32_t* cells,uint64_t* label,la::Entry* heap,la::Cost* output,la::Stats* stats,uint32_t n,uint32_t nj,uint32_t nc,uint32_t capacity,uint64_t budget) {
#pragma HLS INLINE off
 CostLine table[LA_COST_LINES>0?LA_COST_LINES:1];
 for(unsigned k=0;k<LA_COST_LINES;++k)table[k].valid=false;
 la::HeapMemory queue;queue.external=heap;la::PackedLabelMemory labels;labels.external=label;
 for(uint32_t q=0;q<nj;++q) {
  labels.reset();
  la::Stats st={0,0,0,0,0,la::OK};
  for(uint32_t u=0;u<n;++u) {label[u]=0x00000000bf800000ULL;}
  for(uint32_t c=0;c<nc;++c) {la::Cost v={la::missing(),la::missing()};output[uint64_t(q)*nc+c]=v;}
  uint32_t count=0;
  if(!capacity) {st.status=la::QUEUE_OVERFLOW;stats[q]=st;return;}
  la::Entry first={jobs[q].source,0,0};la::cached_push(queue,count,first);st.pushes=1;st.peak=1;
  while(count) {
   if(st.pops>=budget){st.status=la::BUDGET_EXCEEDED;break;}
   la::Entry cur=la::cached_pop(queue,count);++st.pops;uint32_t u=cur.node;
   if(labels.get(u).expanded)continue;
   la::Node parent=nodes[u];int32_t cell=cells[uint64_t(q)*n+u];
   if(parent.type==1 && cell>=0) {uint64_t index=uint64_t(q)*nc+cell;la::Cost v=output[index];la::record(v,cur);output[index]=v;}
   uint64_t end=row[u+1];
   for(uint64_t i=row[u];i<end;++i) {
    ++st.edges;uint32_t v=edges[i].dst;la::Node child=nodes[v];int e=la::eligible(parent,child);if(!e)continue;if(e<0)break;if(labels.get(v).expanded)continue;
    la::Cost c;
#if LA_COST_LINES > 0
    unsigned ci=child.cost%LA_COST_LINES;CostLine hit=table[ci];
    if(hit.valid && hit.tag==child.cost)c=hit.cost;
    else {c=costs[child.cost];CostLine fill={child.cost,true,c};table[ci]=fill;}
#else
    c=costs[child.cost];
#endif
    if(!la::numeric(c.delay)||!la::numeric(c.congestion)){st.status=la::UNSUPPORTED_NUMERIC;break;}
    la::Entry next={v,cur.delay+c.delay,cur.congestion+c.congestion};
    if(!la::numeric(next.delay)||!la::numeric(next.congestion)){st.status=la::UNSUPPORTED_NUMERIC;break;}
    float old=labels.get(v).visited;if(old>=0 && old<next.delay)continue;
    if(count==capacity){st.status=la::QUEUE_OVERFLOW;break;}
    labels.set_visited(v,next.delay);la::cached_push(queue,count,next);++st.pushes;if(count>st.peak)st.peak=count;
   }
   if(st.status!=la::OK)break;
   labels.set_expanded(u);++st.expanded;
  }
  labels.flush();
  stats[q]=st;
  if(st.status!=la::OK)return; // fail closed: no incomplete batch can be reported successful
 }
}
