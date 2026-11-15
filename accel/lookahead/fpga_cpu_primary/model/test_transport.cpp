#include "transport_adapter.hpp"
#include <iostream>
#include <map>
#include <vector>
static void require(bool v,const char*m){if(!v)throw std::runtime_error(m);}
int main(){try{
 for(auto mhz:{125.,200.,333.})for(bool stress:{false,true}){
  ec::Transport t;t.configure(mhz,160,10);t.jitter=stress;
  require(t.latency_cycles==uint64_t(std::ceil(160*mhz/1000)),"latency ceil");require(t.gap_cycles==uint64_t(std::ceil(10*mhz/1000)),"gap ceil");
  unsigned sent=0,got=0;uint64_t now=0,last=0;bool have=false;std::map<unsigned,uint64_t>issue_at;std::vector<unsigned>seen(160);
  for(;now<20000&&(sent<160||!t.idle());++now){
   t.begin(now,[&](const ec::Request&r){if(now>=100&&now<300)return false;require(r.id>=0xdead0000u&&r.id<0xdead00a0u,"full32 identity");unsigned i=r.id-0xdead0000u;require(!seen[i]++,"duplicate response");require(now>=issue_at.at(r.id)+t.latency_cycles,"response too early");require(r.gen==0x87654321u,"full32 generation");++got;return true;},[&](const ec::Request&r,unsigned p){require(p==0,"owner");if(have)require(now-last>=t.gap_cycles,"issue gap");if(stress)require((now+p)%19<14,"backpressure window");last=now;have=true;issue_at[r.id]=now;});
   if(sent<160&&t.push(176,{0,0xdead0000u+sent,0x87654321u,0,32ull*sent,0,now,176}))++sent;
   t.end();
  }
  require(sent==160&&got==160&&t.idle(),"drain");for(auto&p:t.ports)require(p.issues==p.responses&&!p.credits(),"credit conservation");
  std::cout<<"TRANSPORT_PASS mhz="<<mhz<<" stress="<<stress<<" latency="<<t.latency_cycles<<" gap="<<t.gap_cycles<<" cycles="<<now<<"\n";
 }
 bool rejected=false;try{ec::Transport t;t.configure(0,80,5);}catch(const std::exception&){rejected=true;}require(rejected,"invalid parameter rejection");
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
