#pragma once
#include "onchip_types4.hpp"
#ifndef LA5_CONTEXTS
#define LA5_CONTEXTS 2
#endif
namespace on5 {
using namespace on4;
enum Phase {ASSIGN,RESET,OUT_RESET,SEED,POP_READ,DOWN_READ,DOWN_SELECT,DOWN_WRITE,UP_READ,UP_COMPARE,UP_WRITE,HEAP_STORE,PARENT,MAP,CSR,EDGE_READ,NODE_READ,COST_READ,ADD,LABEL,COMMIT,ADVANCE,FINISH,DEAD};
struct Context {unsigned phase,qid,pos,size,hole,child,parent,after,edge,end,dst,remaining; Word value,left,right,chosen;la::Entry cur,next;la::Node pn,cn;la::Cost cost;la::Stats st;uint64_t heap_start;};
// One shared, scheduled lane. A context cannot issue its next edge until its
// previous enqueue commits: conservative RAW interlock, including duplicate dst.
// Qid and original CSR edge ordinal remain in each context's token throughout.
template<int ID>
void search(const uint32_t row[MAX_N+1],const NodeWord nodes[MAX_N],const uint32_t edges[MAX_E],
 const CostWord costs[MAX_K],const uint32_t sources[LOCAL_J],const int32_t cells[LOCAL_J*MAX_N],
 const uint32_t targets[LOCAL_J],CostWord output[LOCAL_J*MAX_C],la::Stats stats[LOCAL_J],
 unsigned n,unsigned jobs,unsigned nc,unsigned capacity,uint64_t metrics[64]){
#pragma HLS INLINE off
 Context ctx[LA5_CONTEXTS];
#pragma HLS ARRAY_PARTITION variable=ctx complete
 Word even[LA5_CONTEXTS][BANK_DEPTH],odd[LA5_CONTEXTS][BANK_DEPTH];
 uint32_t visited[LA5_CONTEXTS][MAX_N];ap_uint<1> expanded[LA5_CONTEXTS][MAX_N];
#pragma HLS ARRAY_PARTITION variable=even complete dim=1
#pragma HLS ARRAY_PARTITION variable=odd complete dim=1
#pragma HLS ARRAY_PARTITION variable=visited complete dim=1
#pragma HLS ARRAY_PARTITION variable=expanded complete dim=1
#pragma HLS BIND_STORAGE variable=even type=ram_t2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=odd type=ram_t2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=visited type=ram_t2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=expanded type=ram_t2p impl=bram latency=1
 uint64_t counters[64]={};
#pragma HLS ARRAY_PARTITION variable=counters complete
 for(unsigned c=0;c<LA5_CONTEXTS;++c){ctx[c]={};ctx[c].phase=ASSIGN;}
 unsigned nextqid=0,done=0,slot=0;uint64_t tick=0;
 DISPATCH: while(done<jobs){
#pragma HLS PIPELINE II=1
  unsigned s=slot;slot=(slot+1)%LA5_CONTEXTS;Context x=ctx[s];++tick;++counters[x.phase];
  switch(x.phase){
  case ASSIGN: if(nextqid<jobs){x={};x.qid=nextqid++;x.phase=RESET;x.remaining=targets[x.qid];}else x.phase=DEAD;break;
  case RESET:visited[s][x.pos]=0xbf800000u;expanded[s][x.pos]=0;if(++x.pos==n){x.pos=0;x.phase=OUT_RESET;}break;
  case OUT_RESET:if(x.pos<nc)output[x.qid*MAX_C+x.pos++]=pack_cost({la::missing(),la::missing()});else x.phase=(LA4_EARLY&&!x.remaining)?FINISH:SEED;break;
  case SEED:x.value=pack({sources[x.qid],0,0});x.size=1;x.hole=0;x.st.pushes=x.st.peak=1;x.after=POP_READ;x.heap_start=tick;x.phase=HEAP_STORE;break;
  case POP_READ:
   if(!x.size){x.phase=FINISH;break;}
   x.cur=unpack(even[s][0]);x.value=get(even[s],odd[s],--x.size);++x.st.pops;x.hole=0;x.heap_start=tick;
   x.phase=x.size?DOWN_READ:PARENT;break;
  case DOWN_READ:x.child=2*(x.hole+1);
   if(x.child<x.size){x.right=even[s][x.child>>1];x.left=odd[s][(x.child-1)>>1];x.phase=DOWN_SELECT;}
   else if(x.child==x.size){x.chosen=odd[s][(x.child-1)>>1];--x.child;x.phase=DOWN_WRITE;}
   else{x.after=PARENT;x.phase=UP_READ;}break;
  case DOWN_SELECT:if(delay(x.right)>delay(x.left)){--x.child;x.chosen=x.left;}else x.chosen=x.right;x.phase=DOWN_WRITE;break;
  case DOWN_WRITE:put(even[s],odd[s],x.hole,x.chosen);x.hole=x.child;x.phase=DOWN_READ;break;
  case UP_READ:if(!x.hole)x.phase=HEAP_STORE;else{x.parent=(x.hole-1)/2;x.chosen=get(even[s],odd[s],x.parent);x.phase=UP_COMPARE;}break;
  case UP_COMPARE:x.phase=delay(x.chosen)>delay(x.value)?UP_WRITE:HEAP_STORE;break;
  case UP_WRITE:put(even[s],odd[s],x.hole,x.chosen);x.hole=x.parent;x.phase=UP_READ;break;
  case HEAP_STORE:put(even[s],odd[s],x.hole,x.value);counters[32]+=tick-x.heap_start+1;++counters[33];x.phase=x.after;break;
  case PARENT:
   if(expanded[s][x.cur.node]){x.phase=POP_READ;break;}
   x.pn=node(nodes[x.cur.node]);x.phase=MAP;break;
  case MAP:{int cell=cells[x.qid*MAX_N+x.cur.node];bool stop=false;
   if(x.pn.type==1&&cell>=0){auto old=cost(output[x.qid*MAX_C+cell]);bool first=old.delay!=old.delay;la::record(old,x.cur);output[x.qid*MAX_C+cell]=pack_cost(old);if(LA4_EARLY&&first&&--x.remaining==0)stop=true;}
   x.phase=stop?FINISH:CSR;break;}
  case CSR:x.edge=row[x.cur.node];x.end=row[x.cur.node+1];x.phase=EDGE_READ;break;
  case EDGE_READ:if(x.edge==x.end){expanded[s][x.cur.node]=1;++x.st.expanded;x.phase=POP_READ;}else{x.dst=edges[x.edge];++x.st.edges;x.phase=NODE_READ;}break;
  case NODE_READ:{x.cn=node(nodes[x.dst]);int a=la::eligible(x.pn,x.cn);
   if(a<0){x.edge=x.end;x.phase=EDGE_READ;}else if(!a||expanded[s][x.dst])x.phase=ADVANCE;else x.phase=COST_READ;break;}
  case COST_READ:x.cost=cost(costs[x.cn.cost]);x.phase=ADD;break;
  case ADD:x.next={x.dst,x.cur.delay+x.cost.delay,x.cur.congestion+x.cost.congestion};x.phase=LABEL;break;
  case LABEL:if(!la::numeric(x.next.delay)||!la::numeric(x.next.congestion)){x.st.status=la::UNSUPPORTED_NUMERIC;x.phase=FINISH;}
   else{unsigned old=visited[s][x.dst];x.phase=(!(old>>31)&&old<bits(x.next.delay))?ADVANCE:COMMIT;}break;
  case COMMIT:if(x.size==capacity){x.st.status=la::QUEUE_OVERFLOW;x.phase=FINISH;}else{visited[s][x.dst]=bits(x.next.delay);x.value=pack(x.next);x.hole=x.size++;x.after=ADVANCE;x.heap_start=tick;++x.st.pushes;if(x.size>x.st.peak)x.st.peak=x.size;x.phase=UP_READ;}break;
  case ADVANCE:++x.edge;x.phase=EDGE_READ;break;
  case FINISH:stats[x.qid]=x.st;++done;x.phase=ASSIGN;break;
  default:break;
  }
  ctx[s]=x;
 }
 counters[31]=tick;for(unsigned i=0;i<64;++i)metrics[i]=counters[i];
}
}
