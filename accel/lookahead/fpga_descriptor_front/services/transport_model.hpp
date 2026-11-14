#pragma once
#include <array>
#include <vector>
#include <optional>
#include <stdexcept>
#include <cstdint>
#include <algorithm>
namespace dfservice {
template<class P,unsigned DEPTH> struct Queue {
 std::array<P,DEPTH> a{};unsigned head=0,n=0,peak=0;
 bool empty()const{return n==0;}bool full()const{return n==DEPTH;}
 const P&front()const{if(!n)throw std::runtime_error("QUEUE_EMPTY");return a[head];}
 void push(const P&p){if(full())throw std::runtime_error("QUEUE_FULL");a[(head+n)%DEPTH]=p;peak=std::max(peak,++n);}
 P pop(){P p=front();head=(head+1)%DEPTH;--n;return p;}
 // push/pop eligibility must be computed from pre-edge state by caller.
 void tick(const std::optional<P>&in,bool take){bool wr=in.has_value()&&!full(),rd=take&&!empty();if(rd)pop();if(wr)push(*in);}
};
template<class P> struct Routed {unsigned dest=0;P payload{};};
// Fully registered output, RR cursor moves ONLY on actual input handshake.
// Inputs are existing source queue/register heads, not newly pushed packets.
template<class P> struct RegisteredRouter {
 unsigned ni,no;std::vector<unsigned> cursor;std::vector<std::optional<P>> out;
 explicit RegisteredRouter(unsigned inputs,unsigned outputs):ni(inputs),no(outputs),cursor(outputs,0),out(outputs){}
 std::vector<int> grants(const std::vector<std::optional<Routed<P>>>&in,const std::vector<bool>&ready)const{
  if(in.size()!=ni||ready.size()!=no)throw std::runtime_error("ROUTER_GEOMETRY");
  std::vector<int> g(no,-1);
  std::vector<unsigned> rank(no,ni);
  for(unsigned i=0;i<ni;++i)if(in[i]){unsigned o=in[i]->dest;if(o>=no)throw std::runtime_error("ROUTER_DESTINATION");
   if(!out[o]||ready[o]){unsigned r=i>=cursor[o]?i-cursor[o]:i+ni-cursor[o];if(r<rank[o]){rank[o]=r;g[o]=int(i);}}
  }
  return g;
 }
 std::vector<bool> input_ready(const std::vector<std::optional<Routed<P>>>&in,const std::vector<bool>&ready)const{
  auto g=grants(in,ready);std::vector<bool> r(ni,false);for(int i:g)if(i>=0)r[i]=true;return r;
 }
 void tick(const std::vector<std::optional<Routed<P>>>&in,const std::vector<bool>&ready){auto g=grants(in,ready);for(unsigned o=0;o<no;++o)if(!out[o]||ready[o]){out[o].reset();if(g[o]>=0){out[o]=in[g[o]]->payload;cursor[o]=(unsigned(g[o])+1)%ni;}}}
};
// Exact metadata/handshake counterpart of df_tagged_port. Packet retains all
// source/context/generation information. Functional backing resolves read data.
template<class P> struct PhysicalPort {
 struct Tagged{P packet{};unsigned tag=0;};struct Return{unsigned client=0;P packet{};};
 std::array<Queue<P,4>,4> q{};std::array<std::optional<P>,4> client{};
 std::array<std::optional<Return>,32> busy{};Queue<Return,4> back;
 std::optional<Tagged> req;unsigned cursor=0,peak_credits=0;
 uint64_t accepted=0,issued=0,returned=0,delivered=0;
 std::array<bool,4> ready()const{std::array<bool,4> r{};for(unsigned c=0;c<4;++c)r[c]=!q[c].full();return r;}
 bool response_ready()const{return !back.full();}
 unsigned credits()const{unsigned n=0;for(auto&v:busy)n+=v.has_value();return n;}
 bool idle()const{if(req||!back.empty()||credits())return false;for(unsigned c=0;c<4;++c)if(client[c]||!q[c].empty())return false;return true;}
 void tick(const std::array<std::optional<P>,4>&in,const std::array<bool,4>&rr,bool mr,std::optional<unsigned>response_tag={}){
  const auto cr=ready();const bool sr=response_ready();peak_credits=std::max(peak_credits,credits());int chosen=-1,free=-1;
  for(unsigned k=0;k<4;++k){unsigned c=(cursor+k)&3;if(chosen<0&&!q[c].empty())chosen=int(c);}
  for(unsigned t=0;t<32;++t)if(free<0&&!busy[t])free=int(t);
  const bool fill=(!req||mr)&&chosen>=0&&free>=0;
  const bool bp=!back.empty()&&(!client[back.front().client]||rr[back.front().client]);
  std::optional<Return> incoming;
  if(response_tag&&sr){if(*response_tag>=32||!busy[*response_tag])throw std::runtime_error("INVALID_PHYSICAL_TAG");incoming=busy[*response_tag];}
  if(req&&mr)++issued;
  if(!req||mr){req.reset();if(fill){auto p=q[chosen].pop();req=Tagged{p,unsigned(free)};busy[free]=Return{unsigned(chosen),p};cursor=(unsigned(chosen)+1)&3;}}
  for(unsigned c=0;c<4;++c){if(in[c]&&cr[c]){q[c].push(*in[c]);++accepted;}if(client[c]&&rr[c]){client[c].reset();++delivered;}}
  if(bp){auto r=back.pop();client[r.client]=r.packet;}
  if(incoming){busy[*response_tag].reset();back.push(*incoming);++returned;}
 }
};
}
