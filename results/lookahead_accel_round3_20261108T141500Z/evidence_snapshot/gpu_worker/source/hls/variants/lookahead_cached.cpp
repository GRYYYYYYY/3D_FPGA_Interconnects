#ifndef LA_DEPTH_ROW
#define LA_DEPTH_ROW 65
#endif
#ifndef LA_DEPTH_NODES
#define LA_DEPTH_NODES 64
#endif
#ifndef LA_DEPTH_EDGES
#define LA_DEPTH_EDGES 256
#endif
#ifndef LA_DEPTH_COSTS
#define LA_DEPTH_COSTS 64
#endif
#ifndef LA_DEPTH_JOBS
#define LA_DEPTH_JOBS 8
#endif
#ifndef LA_DEPTH_CELLS
#define LA_DEPTH_CELLS 512
#endif
#ifndef LA_DEPTH_VISITED
#define LA_DEPTH_VISITED 64
#endif
#ifndef LA_DEPTH_EXPANDED
#define LA_DEPTH_EXPANDED 64
#endif
#ifndef LA_DEPTH_HEAP
#define LA_DEPTH_HEAP 257
#endif
#ifndef LA_DEPTH_OUTPUT
#define LA_DEPTH_OUTPUT 512
#endif
#ifndef LA_DEPTH_STATS
#define LA_DEPTH_STATS 8
#endif
#include "kernel.hpp"
#include "cache.hpp"
extern "C" void lookahead_top(const uint64_t* row,const la::Node* nodes,const la::Edge* edges,const la::Cost* costs,const la::Job* jobs,const int32_t* cells,float* visited,uint32_t* expanded,la::Entry* heap,la::Cost* output,la::Stats* stats,uint32_t n,uint32_t nj,uint32_t nc,uint32_t capacity,uint64_t budget) {
#if LA_SHARED_PORT
#define LA_GRAPH graph
#endif
#pragma HLS INTERFACE m_axi port=row bundle=graph depth=LA_DEPTH_ROW
#pragma HLS INTERFACE m_axi port=nodes bundle=graph depth=LA_DEPTH_NODES
#pragma HLS INTERFACE m_axi port=edges bundle=graph depth=LA_DEPTH_EDGES
#pragma HLS INTERFACE m_axi port=costs bundle=graph depth=LA_DEPTH_COSTS
#pragma HLS INTERFACE m_axi port=jobs bundle=graph depth=LA_DEPTH_JOBS
#pragma HLS INTERFACE m_axi port=cells bundle=graph depth=LA_DEPTH_CELLS
#if LA_SHARED_PORT
#pragma HLS INTERFACE m_axi port=visited bundle=graph depth=LA_DEPTH_VISITED
#else
#pragma HLS INTERFACE m_axi port=visited bundle=state depth=LA_DEPTH_VISITED
#endif
#if LA_SHARED_PORT
#pragma HLS INTERFACE m_axi port=expanded bundle=graph depth=LA_DEPTH_EXPANDED
#else
#pragma HLS INTERFACE m_axi port=expanded bundle=state depth=LA_DEPTH_EXPANDED
#endif
#if LA_SHARED_PORT
#pragma HLS INTERFACE m_axi port=heap bundle=graph depth=LA_DEPTH_HEAP
#else
#pragma HLS INTERFACE m_axi port=heap bundle=queue depth=LA_DEPTH_HEAP
#endif
#if LA_SHARED_PORT
#pragma HLS INTERFACE m_axi port=output bundle=graph depth=LA_DEPTH_OUTPUT
#else
#pragma HLS INTERFACE m_axi port=output bundle=result depth=LA_DEPTH_OUTPUT
#endif
#if LA_SHARED_PORT
#pragma HLS INTERFACE m_axi port=stats bundle=graph depth=LA_DEPTH_STATS
#else
#pragma HLS INTERFACE m_axi port=stats bundle=result depth=LA_DEPTH_STATS
#endif
#pragma HLS INTERFACE s_axilite port=return bundle=control
 la::HeapMemory queue;queue.external=heap;la::LabelMemory labels;labels.v=visited;labels.e=expanded;
 for(uint32_t q=0;q<nj;++q) {
  labels.reset();
  la::Stats st={0,0,0,0,0,la::OK};
  for(uint32_t u=0;u<n;++u) {visited[u]=-1.f;expanded[u]=0;}
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
    la::Cost c=costs[child.cost];
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
  stats[q]=st;
  if(st.status!=la::OK)return; // fail closed: no incomplete batch can be reported successful
 }
}
