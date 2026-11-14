#pragma once
#include "../../fpga_descriptor_front/services/transport_model.hpp"
#include "../network/sparse_router.hpp"
#include "../network/radix_model.hpp"
#include "../network/adapter.hpp"
#include <functional>
namespace ec {
struct Request{unsigned kind=0,id=0,gen=0,tag=0;uint64_t line=0,due=0,queued=0;unsigned source=0,cls=0;};
struct Transport {
 static constexpr unsigned SOURCES=208;
 using Primitive=dfservice::PhysicalPort<Request>;
 struct Flight{unsigned tag=0;uint64_t due=0;};
 struct Port:Primitive{
  dfservice::Queue<typename Primitive::Tagged,2> launch;
  dfservice::Queue<unsigned,2> capture;
  std::array<std::optional<Flight>,32> flight{};
  uint64_t issues=0,responses=0,response_full=0,credit_stalls=0,queue_stalls=0,return_hol=0;
  unsigned credit_peak=0;
 };
 std::array<Port,32> ports{};
 std::array<dfservice::Queue<Request,4>,SOURCES> source{};
 std::array<std::optional<Request>,SOURCES> incoming{};
 std::array<bool,SOURCES> can_enqueue{};
 lf::SparseRouter<Request> requests{true},returns{false};
 lf::Radix<Request> front_requests,front_returns;
 std::array<unsigned,32> admin_cursor{};
 std::vector<std::optional<dfservice::Routed<Request>>> ri=decltype(ri)(SOURCES),bi=decltype(bi)(128);
 std::vector<bool> qr=std::vector<bool>(128),cr=std::vector<bool>(SOURCES);
 std::array<uint64_t,SOURCES> accepted{},delivered{},source_stalls{},return_stalls{};
 bool jitter=false;
 static unsigned cls(unsigned s){return s<16?0:s<48?1:s<112?2:s<176?3:1;}
 bool push(unsigned s,Request r){if(!lf::legal(s,r.kind,r.line))throw std::runtime_error("SOURCE_ADDRESS_KIND_LEGALITY");
 auto w=lf::pack(s,r.kind,r.id,r.gen);if(lf::unpack_source(w,r.line&31)!=s||uint32_t(w.lo)!=r.id||uint32_t(w.lo>>32)!=r.gen||(w.hi&15)!=r.kind)throw std::runtime_error("WIRE_IDENTITY_ROUNDTRIP");if(!can_enqueue[s]||incoming[s]){++source_stalls[s];return false;}r.source=s;r.cls=cls(s);incoming[s]=r;++accepted[s];return true;}
 template<class Sink,class Issue>void begin(uint64_t t,Sink sink,Issue issue){
  incoming.fill({});
  for(unsigned s=0;s<SOURCES;++s){can_enqueue[s]=!source[s].full();ri[s].reset();if(!source[s].empty())ri[s]=dfservice::Routed<Request>{unsigned((source[s].front().line&31)*4+cls(s)),source[s].front()};if(s<48)ri[s].reset();cr[s]=false;if(returns.out[s]){cr[s]=sink(*returns.out[s]);if(cr[s])++delivered[s];else ++return_stalls[s];}}
  for(unsigned p=0;p<32;++p){auto ready=ports[p].ready();for(unsigned c=0;c<4;++c){qr[p*4+c]=ready[c];bi[p*4+c].reset();if(ports[p].client[c]){auto r=*ports[p].client[c];bi[p*4+c]=dfservice::Routed<Request>{r.source,r};}}}
  typename lf::Radix<Request>::Inputs front_heads{},back_inputs{};
  typename lf::Radix<Request>::Ready front_ready{},back_ready{};
  auto local_bi=bi;
  const auto return_ingress=front_returns.ready();
  for(unsigned s=0;s<48;++s){if(!source[s].empty())front_heads[s]=dfservice::Routed<Request>{unsigned((source[s].front().line&31)*2+(s>=16)),source[s].front()};back_ready[s]=cr[s];}
  for(unsigned p=0;p<32;++p)for(unsigned c=0;c<2;++c){unsigned o=p*4+c,e=p*2+c;if(bi[o]&&bi[o]->payload.source<48){back_inputs[e]=bi[o];local_bi[o].reset();}}
  auto pop_source=requests.input_ready(ri,qr);auto port_rr=returns.input_ready(local_bi,cr);
  std::array<int,32> merge{};merge.fill(-1);
  for(unsigned p=0;p<32;++p){
   front_ready[p*2]=qr[p*4];
   unsigned o=p*4+1,s=176+p;pop_source[s]=false;
   if(!requests.out[o]||qr[o])for(unsigned k=0;k<2;++k){unsigned i=(admin_cursor[p]+k)&1;if((i==0&&front_requests.out[p*2+1])||(i==1&&ri[s])){merge[p]=int(i);if(i==0)front_ready[p*2+1]=true;else pop_source[s]=true;break;}}
   for(unsigned c=0;c<2;++c){unsigned o_=p*4+c;if(bi[o_]&&bi[o_]->payload.source<48)port_rr[o_]=return_ingress[p*2+c];}
  }
  for(unsigned p=0;p<32;++p){auto&port=ports[p];std::array<std::optional<Request>,4> in{};std::array<bool,4> rr{};
   for(unsigned c=0;c<4;++c){in[c]=c==0?front_requests.out[p*2]:requests.out[p*4+c];rr[c]=port_rr[p*4+c];}
   bool launch_ready=!port.launch.full(),capture_ready=!port.capture.full();
   auto launch_in=launch_ready?port.req:std::optional<Primitive::Tagged>{};
   std::optional<unsigned> port_response;if(!port.capture.empty()&&port.response_ready())port_response=port.capture.front();
   std::optional<unsigned> physical_response;uint64_t earliest=~uint64_t(0);
   for(unsigned tag=0;tag<32;++tag)if(port.flight[tag]&&port.flight[tag]->due<=t&&port.flight[tag]->due<earliest){earliest=port.flight[tag]->due;physical_response=tag;}
   if(physical_response&&!capture_ready){++port.response_full;physical_response.reset();}
   bool actual_issue=!port.launch.empty();
   if(actual_issue){auto x=port.launch.front();if(port.flight[x.tag])throw std::runtime_error("LIVE_TAG_REISSUE");port.flight[x.tag]=Flight{x.tag,t+16+(jitter?(port.issues*17+p)%7:0)};++port.issues;issue(x.packet,p);}
   if(physical_response){port.flight[*physical_response].reset();++port.responses;}
   if(port.credits()==32)++port.credit_stalls;
   if(!port.back.empty()){unsigned c=port.back.front().client;if(port.client[c]&&!rr[c])++port.return_hol;}
   port.tick(in,rr,launch_ready,port_response);
   port.launch.tick(launch_in,actual_issue);port.capture.tick(physical_response,port_response.has_value());port.credit_peak=port.peak_credits;
  }
  // Snapshot admin output update before either router mutates. Class0 has no
  // extra hold; class1 merges the front stage2 hold with local admin FIFO4.
  std::array<std::optional<Request>,32> admin_next{};
  for(unsigned p=0;p<32;++p){admin_next[p]=requests.out[p*4+1];if(!admin_next[p]||qr[p*4+1]){admin_next[p].reset();if(merge[p]>=0){admin_next[p]=merge[p]==0?front_requests.out[p*2+1]:std::optional<Request>(ri[176+p]->payload);admin_cursor[p]=(merge[p]+1)&1;}}}
  requests.tick(ri,qr);returns.tick(local_bi,cr);
  for(unsigned p=0;p<32;++p)requests.out[p*4+1]=admin_next[p];
  auto front_pop=front_requests.tick(front_heads,front_ready,true);
  front_returns.tick(back_inputs,back_ready);
  for(unsigned s=0;s<48;++s){pop_source[s]=front_pop[s];returns.out[s]=front_returns.out[s];}
  for(unsigned s=0;s<SOURCES;++s)if(pop_source[s])source[s].pop();
 }
 void end(){for(unsigned s=0;s<SOURCES;++s)if(incoming[s])source[s].push(*incoming[s]);}
 bool idle()const{
  if(!front_requests.idle()||!front_returns.idle())return false;
  for(unsigned s=0;s<SOURCES;++s)if(!source[s].empty()||incoming[s]||returns.out[s])return false;
  for(auto&r:requests.out)if(r)return false;
  for(auto&p:ports){if(!p.idle()||!p.launch.empty()||!p.capture.empty())return false;for(auto&f:p.flight)if(f)return false;}
  return true;
 }
};
}
