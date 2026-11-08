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
// One round-robin microstep per context, with one expansion in flight per qid.
// No false-dependence assertions: synthesis must preserve all RAW dependencies.
#ifndef LA_CONTEXTS
#define LA_CONTEXTS 4
#endif
namespace {
la::Entry heap_read(la::Entry* external,la::Entry top[LA_CONTEXTS][LA_HEAP_TOP>0?LA_HEAP_TOP:1],unsigned t,uint32_t capacity,uint32_t index) {
#pragma HLS INLINE
 return index<LA_HEAP_TOP?top[t][index]:external[uint64_t(t)*capacity+index];
}
void heap_write(la::Entry* external,la::Entry top[LA_CONTEXTS][LA_HEAP_TOP>0?LA_HEAP_TOP:1],unsigned t,uint32_t capacity,uint32_t index,la::Entry value) {
#pragma HLS INLINE
 if(index<LA_HEAP_TOP)top[t][index]=value;else external[uint64_t(t)*capacity+index]=value;
}
enum Phase { INIT_LABELS, INIT_OUTPUT, SOURCE, POP_BEGIN, POP_DOWN, UP,
             UP_WRITE, CHECK, PARENT, IPIN, ROW, EDGE, CHILD, LABEL, COST,
             CANDIDATE, PUSH, COMMIT, FINISH };
struct Context {
 Phase phase; uint32_t q, index, count, hole, child, dst;
 uint64_t edge, end;
 bool popping;
 la::Entry current, value;
 la::Node parent, next;
 la::Cost cost;
 la::Stats st;
};
}
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
 Context state[LA_CONTEXTS];
 la::Entry top_cache[LA_CONTEXTS][LA_HEAP_TOP>0?LA_HEAP_TOP:1];
#pragma HLS ARRAY_PARTITION variable=state complete dim=1
#pragma HLS ARRAY_PARTITION variable=top_cache complete dim=1
 for(unsigned t=0;t<LA_CONTEXTS;++t) {
  Context c={};c.q=t;c.phase=INIT_LABELS;state[t]=c;
 }
 unsigned turn=0;uint32_t completed=0;
 while(completed<nj) {
#pragma HLS PIPELINE II=1
  const unsigned t=turn;turn=(turn+1)%LA_CONTEXTS;
  Context c=state[t];
  if(c.q>=nj)continue;
  const uint64_t base=uint64_t(t)*n;
  switch(c.phase) {
  case INIT_LABELS:
   if(c.index<n){visited[base+c.index]=-1.f;expanded[base+c.index]=0;++c.index;}
   else {c.index=0;c.phase=INIT_OUTPUT;}break;
  case INIT_OUTPUT:
   if(c.index<nc){la::Cost empty={la::missing(),la::missing()};output[uint64_t(c.q)*nc+c.index]=empty;++c.index;}
   else c.phase=SOURCE;break;
  case SOURCE:
   if(!capacity){c.st.status=la::QUEUE_OVERFLOW;c.phase=FINISH;break;}
   c.value={jobs[c.q].source,0,0};heap_write(heap,top_cache,t,capacity,0,c.value);
   c.count=1;c.st.pushes=1;c.st.peak=1;c.phase=POP_BEGIN;break;
  case POP_BEGIN:
   if(!c.count){c.phase=FINISH;break;}
   if(c.st.pops>=budget){c.st.status=la::BUDGET_EXCEEDED;c.phase=FINISH;break;}
   c.current=heap_read(heap,top_cache,t,capacity,0);c.value=heap_read(heap,top_cache,t,capacity,--c.count);++c.st.pops;
   c.hole=0;c.child=2;c.popping=true;c.phase=c.count?POP_DOWN:CHECK;break;
  case POP_DOWN:
   if(c.child<c.count){
    la::Entry right=heap_read(heap,top_cache,t,capacity,c.child),left=heap_read(heap,top_cache,t,capacity,c.child-1);
    if(right.delay>left.delay){--c.child;right=left;}
    heap_write(heap,top_cache,t,capacity,c.hole,right);c.hole=c.child;c.child=2*(c.hole+1);
   } else if(c.child==c.count) {
    heap_write(heap,top_cache,t,capacity,c.hole,heap_read(heap,top_cache,t,capacity,c.child-1));c.hole=c.child-1;c.phase=UP;
   } else c.phase=UP;
   break;
  case UP:
   if(c.hole){uint32_t parent=(c.hole-1)/2;la::Entry old=heap_read(heap,top_cache,t,capacity,parent);
    if(old.delay>c.value.delay){heap_write(heap,top_cache,t,capacity,c.hole,old);c.hole=parent;}
    else c.phase=UP_WRITE;
   } else c.phase=UP_WRITE;
   break;
  case UP_WRITE:
   heap_write(heap,top_cache,t,capacity,c.hole,c.value);
   c.phase=c.popping?CHECK:EDGE;break;
  case CHECK:
   c.phase=expanded[base+c.current.node]?POP_BEGIN:PARENT;break;
  case PARENT:
   c.parent=nodes[c.current.node];c.phase=IPIN;break;
  case IPIN:
   if(c.parent.type==1){int32_t cell=cells[uint64_t(c.q)*n+c.current.node];
    if(cell>=0){uint64_t at=uint64_t(c.q)*nc+cell;la::Cost value=output[at];la::record(value,c.current);output[at]=value;}}
   c.phase=ROW;break;
  case ROW:
   c.edge=row[c.current.node];c.end=row[c.current.node+1];c.phase=EDGE;break;
  case EDGE:
   if(c.edge==c.end){c.phase=COMMIT;break;}
   c.dst=edges[c.edge++].dst;++c.st.edges;c.phase=CHILD;break;
  case CHILD: {
   c.next=nodes[c.dst];int eligible=la::eligible(c.parent,c.next);
   c.phase=eligible<0?COMMIT:eligible?LABEL:EDGE;break;}
  case LABEL:
   c.phase=expanded[base+c.dst]?EDGE:COST;break;
  case COST:
   c.cost=costs[c.next.cost];c.phase=CANDIDATE;break;
  case CANDIDATE:
   if(!la::numeric(c.cost.delay)||!la::numeric(c.cost.congestion)){
    c.st.status=la::UNSUPPORTED_NUMERIC;c.phase=FINISH;break;}
   c.value={c.dst,c.current.delay+c.cost.delay,c.current.congestion+c.cost.congestion};
   if(!la::numeric(c.value.delay)||!la::numeric(c.value.congestion)){
    c.st.status=la::UNSUPPORTED_NUMERIC;c.phase=FINISH;break;}
   c.phase=PUSH;break;
  case PUSH: {
   float old=visited[base+c.dst];
   if(old>=0 && old<c.value.delay){c.phase=EDGE;break;}
   if(c.count==capacity){c.st.status=la::QUEUE_OVERFLOW;c.phase=FINISH;break;}
   visited[base+c.dst]=c.value.delay;c.hole=c.count++;c.popping=false;
   ++c.st.pushes;if(c.count>c.st.peak)c.st.peak=c.count;c.phase=UP;break;}
  case COMMIT:
   expanded[base+c.current.node]=1;++c.st.expanded;c.phase=POP_BEGIN;break;
  case FINISH: {
   stats[c.q]=c.st;
   if(c.st.status!=la::OK)return;
   ++completed;uint32_t next=c.q+LA_CONTEXTS;Context fresh={};
   fresh.q=next;fresh.phase=INIT_LABELS;c=fresh;break;}
  }
  state[t]=c;
 }
}
