#pragma once
#include "onchip_types4.hpp"
#include <hls_stream.h>
#ifndef __SYNTHESIS__
#include <mutex>
#include <condition_variable>
#include <deque>
#include <thread>
#endif
namespace svc51 {
using namespace on4;
static const unsigned N=32,E=128,J=8,C=8,Q=2,H=E+1;
enum Kind {RESET=0,PUSH=1,POP=2,END=3,STOP=4,MAP=5};
struct Tag {unsigned generation,qid,context,parent_seq,edge_ordinal;};
struct Message {Tag tag;unsigned kind;Word value;bool valid;};
struct Candidate {Tag tag;Word value;int eligible;bool end;};
struct MapReply {Tag tag;bool stop;};
#ifdef __SYNTHESIS__
template<class T> using Pipe=hls::stream<T>;
#else
// Identical finite capacities to RTL, including response/backpressure cycles.
// Host wall time and thread interleaving are never reported as hardware cycles.
template<class T> class Pipe {
 std::mutex m;std::condition_variable cv;std::deque<T> q;
 public:
 bool empty(){std::lock_guard<std::mutex> l(m);return q.empty();}
 bool full(){std::lock_guard<std::mutex> l(m);return q.size()==4;}
 bool read_nb(T& v){std::lock_guard<std::mutex> l(m);if(q.empty())return false;v=q.front();q.pop_front();cv.notify_all();return true;}
 bool write_nb(const T& v){std::lock_guard<std::mutex> l(m);if(q.size()==4)return false;q.push_back(v);cv.notify_all();return true;}
 T read(){std::unique_lock<std::mutex> l(m);cv.wait(l,[&]{return !q.empty();});T v=q.front();q.pop_front();cv.notify_all();return v;}
 void write(const T& v){std::unique_lock<std::mutex> l(m);cv.wait(l,[&]{return q.size()<4;});q.push_back(v);cv.notify_all();}
};
#endif
inline Message message(Tag t,unsigned k,Word v=0){Message x={t,k,v,true};return x;}
// Instrumented counters are separate per owner. Generated RTL FIFO handshakes,
// not these host counters, establish simultaneity and latency.
template<int ID>
void heap(Pipe<Message>& req,Pipe<Message>& rsp,unsigned hold,unsigned metrics[8]){
#pragma HLS INLINE off
 Word even[(H+1)/2],odd[(H+1)/2];unsigned count=0;
#pragma HLS BIND_STORAGE variable=even type=ram_t2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=odd type=ram_t2p impl=bram latency=1
 for(unsigned i=0;i<8;++i)metrics[i]=0;
 while(true){
  Message x=req.read();++metrics[0];if(x.kind==STOP)break;
  // Deliberate bounded service backpressure in the mechanism probe only.
  for(unsigned d=0;d<hold;++d){
#pragma HLS PIPELINE II=1
   ++metrics[7];
  }
  if(x.kind==RESET)count=0;
  else if(x.kind==PUSH){
   unsigned hole=count++;
   while(hole){unsigned p=(hole-1)/2;Word parent=(p&1)?odd[p>>1]:even[p>>1];if(!(delay(parent)>delay(x.value)))break;if(hole&1)odd[hole>>1]=parent;else even[hole>>1]=parent;hole=p;}
   if(hole&1)odd[hole>>1]=x.value;else even[hole>>1]=x.value;++metrics[1];
  }else if(x.kind==POP){
   Word result=even[0];unsigned last=--count;Word value=(last&1)?odd[last>>1]:even[last>>1];
   unsigned hole=0,child=2;
   if(count){
    while(child<count){Word r=even[child>>1],l=odd[(child-1)>>1];bool left=delay(r)>delay(l);Word v=left?l:r;if(left)--child;if(hole&1)odd[hole>>1]=v;else even[hole>>1]=v;hole=child;child=2*(hole+1);}
    if(child==count){Word v=odd[(child-1)>>1];if(hole&1)odd[hole>>1]=v;else even[hole>>1]=v;hole=child-1;}
    while(hole){unsigned p=(hole-1)/2;Word v=(p&1)?odd[p>>1]:even[p>>1];if(!(delay(v)>delay(value)))break;if(hole&1)odd[hole>>1]=v;else even[hole>>1]=v;hole=p;}
    if(hole&1)odd[hole>>1]=value;else even[hole>>1]=value;
   }x.value=result;++metrics[2];
  }
  rsp.write(x);++metrics[3];
 }
}
void edge(const uint32_t row[N+1],const NodeWord nodes[N],const uint32_t edges[E],const CostWord costs[64],Pipe<Message>& req,Pipe<Candidate>& c0,Pipe<Candidate>& c1,unsigned metrics[8]){
#pragma HLS INLINE off
 for(unsigned i=0;i<8;++i)metrics[i]=0;
 while(true){Message p=req.read();if(p.kind==STOP)break;auto cur=unpack(p.value);auto pn=node(nodes[cur.node]);++metrics[0];
  for(unsigned i=row[cur.node];i<row[cur.node+1];++i){
   unsigned dst=edges[i];auto cn=node(nodes[dst]);int a=la::eligible(pn,cn);la::Entry v={dst,0,0};
   if(a>0){auto c=cost(costs[cn.cost]);v.delay=cur.delay+c.delay;v.congestion=cur.congestion+c.congestion;++metrics[1];}
   Tag t=p.tag;t.edge_ordinal=i;Candidate x={t,pack(v),a,false};
   if(t.context==0)c0.write(x);else c1.write(x);++metrics[2];if(a<0)break;
  }
  Candidate end={p.tag,0,0,true};if(p.tag.context==0)c0.write(end);else c1.write(end);++metrics[3];
 }
}
void map_service(const NodeWord nodes[N],const int32_t cells[J*N],const uint32_t targets[J],CostWord output[J*C],unsigned nc,bool early,Pipe<Message>& req,Pipe<MapReply>& rsp,unsigned hold,unsigned metrics[8]){
#pragma HLS INLINE off
 unsigned remaining[Q]={};
#pragma HLS ARRAY_PARTITION variable=remaining complete
 for(unsigned i=0;i<8;++i)metrics[i]=0;
 while(true){Message p=req.read();if(p.kind==STOP)break;++metrics[0];unsigned s=p.tag.context,q=p.tag.qid;bool stop=false;
  for(unsigned d=0;d<hold;++d){
#pragma HLS PIPELINE II=1
   ++metrics[7];
  }
  if(p.kind==RESET){remaining[s]=targets[q];for(unsigned c=0;c<nc;++c)output[q*C+c]=pack_cost({la::missing(),la::missing()});stop=early&&!remaining[s];}
  else{auto cur=unpack(p.value);int c=cells[q*N+cur.node];if(node(nodes[cur.node]).type==1&&c>=0){auto old=cost(output[q*C+c]);bool first=old.delay!=old.delay;la::record(old,cur);output[q*C+c]=pack_cost(old);++metrics[1];if(early&&first&&--remaining[s]==0)stop=true;}}
  MapReply r={p.tag,stop};rsp.write(r);++metrics[2];
 }
}
enum State {INIT,INIT_SEND,INIT_WAIT,SEED,WAIT_SEED,NEED_POP,WAIT_POP,MAP_SEND,MAP_WAIT,EDGE_SEND,EDGES,DRAIN,FINISHED,DEAD};
struct Context {unsigned state,qid,generation,pos,size,pending,parent_seq,last_edge;bool heap_ready,map_ready,cancel,ended,empty;Word cur;la::Stats st;};
void commit(const uint32_t sources[J],unsigned n,unsigned nj,unsigned capacity,unsigned generation,Pipe<Message>& h0,Pipe<Message>& h1,Pipe<Message>& r0,Pipe<Message>& r1,Pipe<Message>& er,Pipe<Candidate>& c0,Pipe<Candidate>& c1,Pipe<Message>& mr,Pipe<MapReply>& ma,la::Stats stats[J],unsigned metrics[8]){
#pragma HLS INLINE off
 uint32_t visited[Q][N];bool expanded[Q][N];Context ctx[Q];
#pragma HLS ARRAY_PARTITION variable=ctx complete
#pragma HLS ARRAY_PARTITION variable=visited complete dim=1
#pragma HLS ARRAY_PARTITION variable=expanded complete dim=1
#pragma HLS BIND_STORAGE variable=visited type=ram_t2p impl=bram latency=1
#pragma HLS BIND_STORAGE variable=expanded type=ram_t2p impl=bram latency=1
 for(unsigned i=0;i<8;++i)metrics[i]=0;
 for(unsigned s=0;s<Q;++s){ctx[s]={};ctx[s].qid=s;ctx[s].generation=generation;ctx[s].state=s<nj?INIT:DEAD;}
 unsigned next=Q,done=0,slot=0;
 while(done<nj){
  MapReply a;if(ma.read_nb(a)){unsigned s=a.tag.context;ctx[s].map_ready=true;ctx[s].empty=a.stop;}
  unsigned s=slot;slot=(slot+1)%Q;Context x=ctx[s];Tag t={x.generation,x.qid,s,x.parent_seq,0};
  Message ack;bool got=s==0?r0.read_nb(ack):r1.read_nb(ack);
  if(got){++metrics[1];if(ack.kind==PUSH)--x.pending;else if(ack.kind==RESET)x.heap_ready=true;else if(ack.kind==POP){x.cur=ack.value;x.state=MAP_SEND;}}
  bool room=s==0?!h0.full():!h1.full();bool send=false;Message req=message(t,RESET);
  switch(x.state){
   case INIT:visited[s][x.pos]=0xbf800000u;expanded[s][x.pos]=false;if(++x.pos==n)x.state=INIT_SEND;break;
   case INIT_SEND:if(room&&!mr.full()){send=true;mr.write(req);x.state=INIT_WAIT;}break;
   case INIT_WAIT:if(x.heap_ready&&x.map_ready){x.map_ready=false;x.state=x.empty?FINISHED:SEED;}break;
   case SEED:if(room){req=message(t,PUSH,pack({sources[x.qid],0,0}));send=true;x.size=1;x.pending=1;x.st.pushes=x.st.peak=1;x.state=WAIT_SEED;}break;
   case WAIT_SEED:if(!x.pending)x.state=NEED_POP;break;
   case NEED_POP:if(!x.size)x.state=FINISHED;else if(room){req=message(t,POP);send=true;--x.size;++x.st.pops;++x.parent_seq;x.state=WAIT_POP;}break;
   case WAIT_POP:break;
   case MAP_SEND:if(expanded[s][unpack(x.cur).node])x.state=NEED_POP;else if(!mr.full()){t.parent_seq=x.parent_seq;mr.write(message(t,MAP,x.cur));x.state=MAP_WAIT;}break;
   case MAP_WAIT:if(x.map_ready){x.map_ready=false;x.state=x.empty?FINISHED:EDGE_SEND;}break;
   case EDGE_SEND:if(!er.full()){t.parent_seq=x.parent_seq;er.write(message(t,MAP,x.cur));x.state=EDGES;x.ended=false;x.cancel=false;x.last_edge=0;}break;
   case EDGES:{
    // A full physical request FIFO is backpressure, NOT logical overflow.
    // Reserve capacity only on accepted ordered PUSH; pending is not added twice.
    if(!room&&!x.cancel)break;
    Candidate v;bool have=s==0?c0.read_nb(v):c1.read_nb(v);if(!have)break;
    if(v.end){x.ended=true;x.state=DRAIN;break;}
    if(x.cancel){++metrics[6];break;}
    ++x.st.edges;++metrics[2];x.last_edge=v.tag.edge_ordinal;
    if(v.eligible<0){x.cancel=true;break;}
    auto e=unpack(v.value);if(v.eligible==0||expanded[s][e.node])break;
    if(!la::numeric(e.delay)||!la::numeric(e.congestion)){x.st.status=la::UNSUPPORTED_NUMERIC;x.cancel=true;break;}
    unsigned old=visited[s][e.node];if(!(old>>31)&&old<bits(e.delay))break;
    if(x.size==capacity){x.st.status=la::QUEUE_OVERFLOW;x.cancel=true;break;}
    visited[s][e.node]=bits(e.delay);++x.size;++x.pending;++x.st.pushes;if(x.size>x.st.peak)x.st.peak=x.size;
    req=message(v.tag,PUSH,v.value);send=true;++metrics[3];break;
   }
   case DRAIN:if(!x.pending){if(x.st.status)x.state=FINISHED;else{expanded[s][unpack(x.cur).node]=true;++x.st.expanded;x.state=NEED_POP;}}break;
   case FINISHED:stats[x.qid]=x.st;++done;if(next<nj){x={};x.qid=next++;x.generation=generation+x.qid;x.state=INIT;}else x.state=DEAD;break;
   default:break;
  }
  if(send){if(s==0)h0.write(req);else h1.write(req);++metrics[0];}
  ctx[s]=x;
 }
 Tag t={generation,0,0,0,0};Message eos=message(t,STOP);h0.write(eos);h1.write(eos);er.write(eos);mr.write(eos);
}
void network(const uint32_t row[N+1],const NodeWord nodes[N],const uint32_t edges[E],const CostWord costs[64],const uint32_t sources[J],const int32_t cells[J*N],const uint32_t targets[J],CostWord output[J*C],la::Stats stats[J],unsigned n,unsigned nj,unsigned nc,unsigned capacity,unsigned generation,bool early,unsigned heap_hold,unsigned map_hold,unsigned hm0[8],unsigned hm1[8],unsigned em[8],unsigned mm[8],unsigned cm[8]){
#pragma HLS INLINE off
#pragma HLS DATAFLOW disable_start_propagation
 Pipe<Message> h0,h1,r0,r1,er,mr;Pipe<Candidate> c0,c1;Pipe<MapReply> ma;
#pragma HLS STREAM variable=h0 depth=4
#pragma HLS STREAM variable=h1 depth=4
#pragma HLS STREAM variable=r0 depth=4
#pragma HLS STREAM variable=r1 depth=4
#pragma HLS STREAM variable=er depth=4
#pragma HLS STREAM variable=mr depth=4
#pragma HLS STREAM variable=c0 depth=4
#pragma HLS STREAM variable=c1 depth=4
#pragma HLS STREAM variable=ma depth=4
#ifdef __SYNTHESIS__
 heap<0>(h0,r0,heap_hold,hm0);
 heap<1>(h1,r1,heap_hold,hm1);
 edge(row,nodes,edges,costs,er,c0,c1,em);
 map_service(nodes,cells,targets,output,nc,early,mr,ma,map_hold,mm);
 commit(sources,n,nj,capacity,generation,h0,h1,r0,r1,er,c0,c1,mr,ma,stats,cm);
#else
 std::thread a([&]{heap<0>(h0,r0,heap_hold,hm0);});
 std::thread b([&]{heap<1>(h1,r1,heap_hold,hm1);});
 std::thread c([&]{edge(row,nodes,edges,costs,er,c0,c1,em);});
 std::thread d([&]{map_service(nodes,cells,targets,output,nc,early,mr,ma,map_hold,mm);});
 commit(sources,n,nj,capacity,generation,h0,h1,r0,r1,er,c0,c1,mr,ma,stats,cm);
 a.join();b.join();c.join();d.join();
#endif
}
}
