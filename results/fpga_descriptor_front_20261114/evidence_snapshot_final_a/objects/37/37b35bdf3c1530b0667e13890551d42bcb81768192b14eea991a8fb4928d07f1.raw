#include "transport_adapter.hpp"
#include "../services/network_model.hpp"
#include <iostream>
#include <string>
static void must(bool x,const char*m){if(!x)throw std::runtime_error(m);}
static bool eq(const ec::Request&a,const ec::Request&b){return a.kind==b.kind&&a.id==b.id&&a.gen==b.gen&&a.line==b.line&&a.source==b.source&&a.cls==b.cls;}
template<class A,class B>void packets(const A&a,const B&b){must(bool(a)==bool(b),"VALID");if(a)must(eq(*a,*b),"PAYLOAD");}
int main(){try{auto ap=std::make_unique<ec::Transport>();auto op=std::make_unique<dfservice::MemoryNetwork<ec::Request>>(208,32);auto&a=*ap;auto&o=*op;a.jitter=true;uint64_t seed=42,total=0;auto rnd=[&](){seed^=seed<<13;seed^=seed>>7;seed^=seed<<17;return seed;};
 for(unsigned t=0;t<12000||!a.idle();++t){must(t<20000,"DRAIN_TIMEOUT");std::vector<std::optional<ec::Request>> input(208);std::vector<bool> ready(208),mr(32,true);std::vector<std::optional<unsigned>> response(32);
  for(unsigned s=0;s<208;++s){ready[s]=t>12000||((t*13+s*7)%37)>15;if(t<12000&&rnd()%9<5){ec::Request r;r.source=s;r.cls=ec::Transport::cls(s);r.kind=s%12;r.id=t*208+s;r.gen=t%256;r.line=(rnd()%4==0?0:rnd()%32);input[s]=r;}}
  for(unsigned p=0;p<32;++p){auto&port=a.ports[p];uint64_t earliest=~uint64_t(0);for(unsigned tag=0;tag<32;++tag)if(port.flight[tag]&&port.flight[tag]->due<=t&&port.flight[tag]->due<earliest){earliest=port.flight[tag]->due;response[p]=tag;}if(port.capture.full())response[p].reset();}
  a.begin(t,[&](const ec::Request&r){return ready[r.source];},[&](const ec::Request&,unsigned){++total;});for(unsigned s=0;s<208;++s)if(input[s])a.push(s,*input[s]);a.end();o.tick(input,ready,mr,response);
  for(unsigned s=0;s<208;++s){must(a.source[s].n==o.source[s].n,"SOURCE_COUNT");if(a.source[s].n)must(eq(a.source[s].front(),o.source[s].front()),"SOURCE_HEAD");packets(a.returns.out[s],o.response_router.out[s]);}
  for(unsigned i=0;i<128;++i)packets(a.requests.out[i],o.request_router.out[i]);
  for(unsigned p=0;p<32;++p){auto&x=a.ports[p];auto&y=o.port[p];must(bool(x.req)==bool(y.req),"REQ_VALID");if(x.req){must(x.req->tag==y.req->tag&&eq(x.req->packet,y.req->packet),"REQ_PAYLOAD");}must(x.credits()==y.credits(),"CREDITS");must(x.launch.n==o.request_slice[p].n&&x.capture.n==o.response_slice[p].n,"SLICE_COUNTS");must(x.back.n==y.back.n,"RETURN_COUNT");for(unsigned c=0;c<4;++c){must(x.q[c].n==y.q[c].n,"CLIENT_COUNT");packets(x.client[c],y.client[c]);}}
 }
 std::cout<<"PASS exact Transport adapter vs shared RTL-qualified MemoryNetwork; cycles>=12000 ports32 sources208 requests="<<total<<"\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
