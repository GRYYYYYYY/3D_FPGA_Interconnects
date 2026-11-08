// Serial control: identical two engines and eight logical AXI masters.
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
#include "workload.hpp"
#include "strict_heap.hpp"
template<int ID> static void engine(const uint64_t* row,const la::Node* nodes,const la::Edge* edges,const la::Cost* costs,const la::Job* jobs,const int32_t* cells,float* visited,uint32_t* expanded,la::Entry* heap,la::Cost* output,la::Stats* stats,uint32_t n,uint32_t nj,uint32_t nc,uint32_t capacity,uint64_t budget) {
#pragma HLS INLINE off
 for(uint32_t q=0;q<nj;++q) {
  la::Stats st={0,0,0,0,0,la::OK};
  for(uint32_t u=0;u<n;++u) {visited[u]=-1.f;expanded[u]=0;}
  for(uint32_t c=0;c<nc;++c) {la::Cost v={la::missing(),la::missing()};output[uint64_t(q)*nc+c]=v;}
  uint32_t count=0;
  if(!capacity) {st.status=la::QUEUE_OVERFLOW;stats[q]=st;return;}
  la::Entry first={jobs[q].source,0,0};la::push(heap,count,first);st.pushes=1;st.peak=1;
  while(count) {
   if(st.pops>=budget){st.status=la::BUDGET_EXCEEDED;break;}
   la::Entry cur=la::pop(heap,count);++st.pops;uint32_t u=cur.node;
   if(expanded[u])continue;
   la::Node parent=nodes[u];int32_t cell=cells[uint64_t(q)*n+u];
   if(parent.type==1 && cell>=0) {uint64_t index=uint64_t(q)*nc+cell;la::Cost v=output[index];la::record(v,cur);output[index]=v;}
   uint64_t end=row[u+1];
   for(uint64_t i=row[u];i<end;++i) {
    ++st.edges;uint32_t v=edges[i].dst;la::Node child=nodes[v];int e=la::eligible(parent,child);if(!e)continue;if(e<0)break;if(expanded[v])continue;
    la::Cost c=costs[child.cost];
    if(!la::numeric(c.delay)||!la::numeric(c.congestion)){st.status=la::UNSUPPORTED_NUMERIC;break;}
    la::Entry next={v,cur.delay+c.delay,cur.congestion+c.congestion};
    if(!la::numeric(next.delay)||!la::numeric(next.congestion)){st.status=la::UNSUPPORTED_NUMERIC;break;}
    float old=visited[v];if(old>=0 && old<next.delay)continue;
    if(count==capacity){st.status=la::QUEUE_OVERFLOW;break;}
    visited[v]=next.delay;la::push(heap,count,next);++st.pushes;if(count>st.peak)st.peak=count;
   }
   if(st.status!=la::OK)break;
   expanded[u]=1;++st.expanded;
  }
  stats[q]=st;
  if(st.status!=la::OK)return; // fail closed: no incomplete batch can be reported successful
 }
}
extern "C" void lookahead_dual(const uint64_t* row0,const la::Node* nodes0,const la::Edge* edges0,const la::Cost* costs0,const la::Job* jobs0,const int32_t* cells0,float* visited0,uint32_t* expanded0,la::Entry* heap0,la::Cost* output0,la::Stats* stats0,const uint64_t* row1,const la::Node* nodes1,const la::Edge* edges1,const la::Cost* costs1,const la::Job* jobs1,const int32_t* cells1,float* visited1,uint32_t* expanded1,la::Entry* heap1,la::Cost* output1,la::Stats* stats1,uint32_t n,uint32_t nj0,uint32_t nj1,uint32_t nc,uint32_t capacity,uint64_t budget){
#pragma HLS INTERFACE m_axi port=row0 bundle=graph0 depth=LA_DEPTH_ROW
#pragma HLS INTERFACE m_axi port=nodes0 bundle=graph0 depth=LA_DEPTH_NODES
#pragma HLS INTERFACE m_axi port=edges0 bundle=graph0 depth=LA_DEPTH_EDGES
#pragma HLS INTERFACE m_axi port=costs0 bundle=graph0 depth=LA_DEPTH_COSTS
#pragma HLS INTERFACE m_axi port=jobs0 bundle=graph0 depth=LA_DEPTH_JOBS
#pragma HLS INTERFACE m_axi port=cells0 bundle=graph0 depth=LA_DEPTH_CELLS
#pragma HLS INTERFACE m_axi port=visited0 bundle=state0 depth=LA_DEPTH_VISITED
#pragma HLS INTERFACE m_axi port=expanded0 bundle=state0 depth=LA_DEPTH_EXPANDED
#pragma HLS INTERFACE m_axi port=heap0 bundle=queue0 depth=LA_DEPTH_HEAP
#pragma HLS INTERFACE m_axi port=output0 bundle=result0 depth=LA_DEPTH_OUTPUT
#pragma HLS INTERFACE m_axi port=stats0 bundle=result0 depth=LA_DEPTH_STATS
#pragma HLS INTERFACE m_axi port=row1 bundle=graph1 depth=LA_DEPTH_ROW
#pragma HLS INTERFACE m_axi port=nodes1 bundle=graph1 depth=LA_DEPTH_NODES
#pragma HLS INTERFACE m_axi port=edges1 bundle=graph1 depth=LA_DEPTH_EDGES
#pragma HLS INTERFACE m_axi port=costs1 bundle=graph1 depth=LA_DEPTH_COSTS
#pragma HLS INTERFACE m_axi port=jobs1 bundle=graph1 depth=LA_DEPTH_JOBS
#pragma HLS INTERFACE m_axi port=cells1 bundle=graph1 depth=LA_DEPTH_CELLS
#pragma HLS INTERFACE m_axi port=visited1 bundle=state1 depth=LA_DEPTH_VISITED
#pragma HLS INTERFACE m_axi port=expanded1 bundle=state1 depth=LA_DEPTH_EXPANDED
#pragma HLS INTERFACE m_axi port=heap1 bundle=queue1 depth=LA_DEPTH_HEAP
#pragma HLS INTERFACE m_axi port=output1 bundle=result1 depth=LA_DEPTH_OUTPUT
#pragma HLS INTERFACE m_axi port=stats1 bundle=result1 depth=LA_DEPTH_STATS
#pragma HLS INTERFACE s_axilite port=return bundle=control
// No DATAFLOW: control case executes both engines sequentially.
 engine<0>(row0,nodes0,edges0,costs0,jobs0,cells0,visited0,expanded0,heap0,output0,stats0,n,nj0,nc,capacity,budget);
 engine<1>(row1,nodes1,edges1,costs1,jobs1,cells1,visited1,expanded1,heap1,output1,stats1,n,nj1,nc,capacity,budget);
}
