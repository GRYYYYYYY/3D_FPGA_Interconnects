#pragma once
#include "../services/transport_model.hpp"
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
 dfservice::RegisteredRouter<Request> requests{SOURCES,128},returns{128,SOURCES};
 std::vector<std::optional<dfservice::Routed<Request>>> ri=decltype(ri)(SOURCES),bi=decltype(bi)(128);
 std::vector<bool> qr=std::vector<bool>(128),cr=std::vector<bool>(SOURCES);
 std::array<uint64_t,SOURCES> accepted{},delivered{},source_stalls{},return_stalls{};
 bool jitter=false;
 static unsigned cls(unsigned s){return s<16?0:s<48?1:s<112?2:s<176?3:1;}
 bool push(unsigned s,Request r){if(!can_enqueue[s]||incoming[s]){++source_stalls[s];return false;}r.source=s;r.cls=cls(s);incoming[s]=r;++accepted[s];return true;}
 template<class Sink,class Issue>void begin(uint64_t t,Sink sink,Issue issue){
  incoming.fill({});
  for(unsigned s=0;s<SOURCES;++s){can_enqueue[s]=!source[s].full();ri[s].reset();if(!source[s].empty())ri[s]=dfservice::Routed<Request>{unsigned((source[s].front().line&31)*4+cls(s)),source[s].front()};cr[s]=false;if(returns.out[s]){cr[s]=sink(*returns.out[s]);if(cr[s])++delivered[s];else ++return_stalls[s];}}
  for(unsigned p=0;p<32;++p){auto ready=ports[p].ready();for(unsigned c=0;c<4;++c){qr[p*4+c]=ready[c];bi[p*4+c].reset();if(ports[p].client[c]){auto r=*ports[p].client[c];bi[p*4+c]=dfservice::Routed<Request>{r.source,r};}}}
  const auto pop_source=requests.input_ready(ri,qr);const auto port_rr=returns.input_ready(bi,cr);
  for(unsigned p=0;p<32;++p){auto&port=ports[p];std::array<std::optional<Request>,4> in{};std::array<bool,4> rr{};
   for(unsigned c=0;c<4;++c){in[c]=requests.out[p*4+c];rr[c]=port_rr[p*4+c];}
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
  requests.tick(ri,qr);returns.tick(bi,cr);
  for(unsigned s=0;s<SOURCES;++s)if(pop_source[s])source[s].pop();
 }
 void end(){for(unsigned s=0;s<SOURCES;++s)if(incoming[s])source[s].push(*incoming[s]);}
 bool idle()const{
  for(unsigned s=0;s<SOURCES;++s)if(!source[s].empty()||incoming[s]||returns.out[s])return false;
  for(auto&r:requests.out)if(r)return false;
  for(auto&p:ports){if(!p.idle()||!p.launch.empty()||!p.capture.empty())return false;for(auto&f:p.flight)if(f)return false;}
  return true;
 }
};
}
