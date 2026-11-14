#pragma once
#include "../../fpga_descriptor_front/services/transport_model.hpp"
namespace lf {
// Exact FIFO4 + registered-output three-stage 4x4 butterfly. No lookahead,
// virtual queues, bypass, or speculative simultaneous-full-FIFO admission.
template<class P>struct Radix {
 using R=dfservice::Routed<P>;using Inputs=std::array<std::optional<R>,64>;using Ready=std::array<bool,64>;
 std::array<std::array<dfservice::Queue<R,4>,64>,3>q{};
 std::array<Inputs,3>hold{};std::array<std::array<unsigned,64>,3>cursor{};
 std::array<std::array<uint64_t,64>,3>link{},blocked{},hol{};
 std::array<std::optional<P>,64>out{};
 static unsigned shuffle(unsigned j){return ((j<<2)&63)|(j>>4);}
 Ready ready()const{Ready r{};for(unsigned i=0;i<64;++i)r[i]=!q[0][i].full();return r;}
 bool idle()const{for(unsigned s=0;s<3;++s)for(unsigned i=0;i<64;++i)if(!q[s][i].empty()||hold[s][i])return false;return true;}
 // external_heads=true: stage0 FIFO is the caller's physical source FIFO;
 // returned bits pop that FIFO. Internal stage0 q is unused in that mode.
 Ready tick(const Inputs&in,const Ready&sink,bool external_heads=false){
  std::array<Inputs,3>heads{},incoming{};std::array<Ready,3>take{},ready_out{};
  for(unsigned s=0;s<3;++s)for(unsigned i=0;i<64;++i){
   if(s==0&&external_heads)heads[s][i]=in[i];else if(!q[s][i].empty())heads[s][i]=q[s][i].front();
   ready_out[s][i]=s==2?sink[i]:!q[s+1][shuffle(i)].full();
   if(s==0){if(!external_heads&&!q[0][i].full())incoming[0][i]=in[i];}
   else {unsigned prev=((i>>2)|(i<<4))&63;if(!q[s][i].full())incoming[s][i]=hold[s-1][prev];}
  }
  for(unsigned s=0;s<3;++s)for(unsigned o=0;o<64;++o){
   if(hold[s][o]&&ready_out[s][o])++link[s][o];
   if(hold[s][o]&&!ready_out[s][o]){++blocked[s][o];continue;}
   int chosen=-1;unsigned sw=o/4,d=o%4;
   for(unsigned k=0;k<4;++k){unsigned i=4*sw+((cursor[s][o]+k)&3);if(heads[s][i]&&((heads[s][i]->dest>>(4-2*s))&3)==d){chosen=int(i);break;}}
   hold[s][o].reset();if(chosen>=0){hold[s][o]=heads[s][chosen];take[s][chosen]=true;cursor[s][o]=(unsigned(chosen)+1)&3;}
  }
  for(unsigned s=0;s<3;++s)for(unsigned i=0;i<64;++i){
   if(heads[s][i]&&!take[s][i])++hol[s][i];
   if(!(s==0&&external_heads))q[s][i].tick(incoming[s][i],take[s][i]);
  }
  for(unsigned i=0;i<64;++i){out[i].reset();if(hold[2][i]){if(hold[2][i]->dest!=i)throw std::runtime_error("RADIX_ROUTE");out[i]=hold[2][i]->payload;}}
  return take[0];
 }
};
}
