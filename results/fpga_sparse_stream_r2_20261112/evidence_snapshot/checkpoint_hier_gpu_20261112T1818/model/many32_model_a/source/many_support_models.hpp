#pragma once
#include "support_models.hpp"
#include "hier_fabric_model.hpp"
namespace r2_model {
template<class T,unsigned I,unsigned O>struct RouterMany {
 std::array<Fifo<T>,O>q;std::array<unsigned,O>rotate{};std::array<bool,I>iv{},ir{};std::array<bool,O>ordy{};std::array<T,I>input{};std::array<int,O>selection{};
 static unsigned destination(const PopEvent&e){return (e.node>>2)&(O-1);}
 static unsigned destination(const CellEvent&e){return e.cell&(O-1);}
 void combin(){ir.fill(false);for(unsigned b=0;b<O;++b){selection[b]=-1;for(unsigned p=0;p<I;++p){unsigned l=(rotate[b]+p)&(I-1);if(iv[l]&&destination(input[l])==b){selection[b]=l;ir[l]=q[b].ready(ordy[b]);break;}}}}
 bool idle()const{for(auto&f:q)if(f.ov||f.count)return false;return true;}
 void step(bool rst){if(rst){q={};rotate={};return;}for(unsigned b=0;b<O;++b){bool put=selection[b]>=0;T data=put?input[selection[b]]:T{};bool accepted=put&&q[b].ready(ordy[b]);q[b].step(put,data,ordy[b]);if(accepted)rotate[b]=(rotate[b]+1)&(I-1);}}
};
template<unsigned L>struct ControlMany {
 static constexpr unsigned G=L/4;
 unsigned op=7,epoch=0,root_op=7,root_epoch=0;std::array<unsigned,G>branch_op{},branch_epoch{},group_epoch{};std::array<bool,G>group_done{};
 std::array<bool,L>done{},ack{};std::array<unsigned,L>leaf_op{},leaf_epoch{},ack_epoch{};
 ControlMany(){branch_op.fill(7);leaf_op.fill(7);}
 bool complete()const{for(unsigned g=0;g<G;++g)if(!group_done[g]||group_epoch[g]!=epoch)return false;return true;}
 void step(bool rst){if(rst){root_op=7;root_epoch=0;branch_op.fill(7);branch_epoch={};leaf_op.fill(7);leaf_epoch={};ack={};group_done={};group_epoch={};ack_epoch={};return;}
  auto old=*this;root_op=op;root_epoch=epoch;
  for(unsigned g=0;g<G;++g){bool all=true;for(unsigned i=g*4;i<g*4+4;++i)all&=done[i];if(all||old.branch_op[g]==0||old.branch_op[g]==7){branch_op[g]=old.root_op;branch_epoch[g]=old.root_epoch;}}
  for(unsigned i=0;i<L;++i){if(old.branch_epoch[i/4]!=old.leaf_epoch[i]&&(done[i]||old.leaf_op[i]==0)){leaf_op[i]=old.branch_op[i/4];leaf_epoch[i]=old.branch_epoch[i/4];}ack[i]=done[i];ack_epoch[i]=old.leaf_epoch[i];}
  for(unsigned g=0;g<G;++g){group_epoch[g]=old.ack_epoch[g*4];bool all=true;for(unsigned i=g*4;i<g*4+4;++i)all&=old.ack[i]&&old.ack_epoch[i]==old.ack_epoch[g*4];group_done[g]=all;}
 }
};
template<unsigned L>struct MinimumMany {
 std::array<unsigned,L>keys{},epochs{};std::array<bool,L>valid{};
 std::array<unsigned,2*L>k{},e{};std::array<bool,2*L>v{};bool ov=false;unsigned key=8191,epoch=0;
 void step(bool rst){if(rst){k.fill(8191);e={};v={};ov=false;key=8191;epoch=0;return;}
  for(unsigned i=0;i<L;++i){k[L+i]=keys[i];e[L+i]=epochs[i];v[L+i]=valid[i];}
  // Ascending heap indices read children before those children are updated.
  for(unsigned i=1;i<L;++i){k[i]=std::min(k[2*i],k[2*i+1]);e[i]=e[2*i];v[i]=v[2*i]&&v[2*i+1]&&e[2*i]==e[2*i+1];}
  ov=v[1];key=k[1];epoch=e[1];
 }
};
}
