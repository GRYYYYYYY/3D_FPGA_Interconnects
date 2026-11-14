#pragma once
#include "transport_model.hpp"
namespace dfservice {
// Packet must retain {source,cls,line}; all remaining context fields are opaque.
// This composition matches df_memory_network including both physical FIFO2s.
template<class P> struct MemoryNetwork {
 using Port=PhysicalPort<P>;using Tagged=typename Port::Tagged;
 unsigned ns,np;std::vector<Queue<P,4>> source;RegisteredRouter<P> request_router,response_router;
 std::vector<Port> port;std::vector<Queue<Tagged,2>> request_slice;std::vector<Queue<unsigned,2>> response_slice;
 MemoryNetwork(unsigned sources,unsigned ports):ns(sources),np(ports),source(sources),request_router(sources,ports*4),response_router(ports*4,sources),port(ports),request_slice(ports),response_slice(ports){}
 bool idle()const{for(auto&q:source)if(!q.empty())return false;for(auto&v:request_router.out)if(v)return false;for(auto&v:response_router.out)if(v)return false;for(unsigned p=0;p<np;++p)if(!port[p].idle()||!request_slice[p].empty()||!response_slice[p].empty())return false;return true;}
 void tick(const std::vector<std::optional<P>>&input,const std::vector<bool>&ready,const std::vector<bool>&memory_ready,const std::vector<std::optional<unsigned>>&memory_response){
  std::vector<std::optional<Routed<P>>> qi(ns),ri(np*4);std::vector<bool> qr(np*4);
  for(unsigned i=0;i<ns;++i)if(!source[i].empty()){auto p=source[i].front();qi[i]=Routed<P>{unsigned((p.line&31)*4+p.cls),p};}
  for(unsigned p=0;p<np;++p){auto cr=port[p].ready();for(unsigned c=0;c<4;++c){qr[p*4+c]=cr[c];if(port[p].client[c]){auto x=*port[p].client[c];ri[p*4+c]=Routed<P>{x.source,x};}}}
  const auto qtake=request_router.input_ready(qi,qr),rtake=response_router.input_ready(ri,ready);
  // Sample upstream register outputs before mutating any block.
  const auto old_request=request_router.out;
  for(unsigned p=0;p<np;++p){
   std::array<std::optional<P>,4> in;std::array<bool,4> rr;
   for(unsigned c=0;c<4;++c){in[c]=old_request[p*4+c];rr[c]=rtake[p*4+c];}
   auto req=port[p].req;bool pr=!request_slice[p].full(),sr=port[p].response_ready();
   std::optional<unsigned> rsp;if(!response_slice[p].empty())rsp=response_slice[p].front();
   port[p].tick(in,rr,pr,rsp);
   request_slice[p].tick(req,memory_ready[p]);response_slice[p].tick(memory_response[p],sr);
  }
  for(unsigned i=0;i<ns;++i)source[i].tick(input[i],qtake[i]);
  request_router.tick(qi,qr);response_router.tick(ri,ready);
 }
};
}
