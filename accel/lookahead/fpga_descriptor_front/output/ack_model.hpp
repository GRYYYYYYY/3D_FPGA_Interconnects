#pragma once
#include <array>
#include <optional>
#include <vector>
#include <stdexcept>
namespace dfoutput {
// Generic metadata retained unchanged through two registered output holders.
// Observe out BEFORE tick: newly accepted source ACKs cannot retire this edge.
template<class Packet>struct AckCollector {
 unsigned cursor=0;std::array<std::optional<Packet>,2>out;
 std::array<int,2>grants(const std::vector<std::optional<Packet>>&in,const std::array<bool,2>&ready)const{
  if(in.size()!=32)throw std::runtime_error("OUTPUT_ACK_SOURCES");std::array<int,2>g{-1,-1};unsigned begin=cursor;
  for(unsigned lane=0;lane<2;++lane)if(!out[lane]||ready[lane]){
   for(unsigned k=0;k<32;++k){unsigned i=(begin+k)&31;if(in[i]&&int(i)!=g[0]){g[lane]=int(i);begin=(i+1)&31;break;}}
  }return g;
 }
 std::vector<bool>input_ready(const std::vector<std::optional<Packet>>&in,const std::array<bool,2>&ready)const{
  auto g=grants(in,ready);std::vector<bool>take(32,false);for(int i:g)if(i>=0)take[i]=true;return take;
 }
 void tick(const std::vector<std::optional<Packet>>&in,const std::array<bool,2>&ready){
  auto g=grants(in,ready);for(unsigned lane=0;lane<2;++lane)if(!out[lane]||ready[lane]){out[lane].reset();if(g[lane]>=0){out[lane]=in[g[lane]];cursor=(unsigned(g[lane])+1)&31;}}
 }
 bool idle()const{return !out[0]&&!out[1];}
};
}
