#pragma once
#include "../fpga_sparse_stream/owner_model.hpp"
#include <vector>
#include <stdexcept>
namespace r2_model {
using sparse_model::Fifo;using sparse_model::Line;
struct FabricRequest {bool write=false;uint32_t line=0;unsigned id=0;Line data{};};
struct FabricReturn {unsigned client=0,id=0;Line data{};};
// Independent finite synchronous FIFO/tag/arbitration model of r2_shared_fabric.
// Public fields are per-port, avoiding RTL packed-bus representation dependence.
struct FabricIO {
 unsigned C,P;bool rst=false,idle=false,error=false;uint32_t accepted=0,returned=0;
 std::vector<uint8_t> cv,cr,cw,rv,rr,mv,mr,mw,sv,sr;std::vector<uint32_t>cl,ml;std::vector<unsigned>ci,ri,mi,si;std::vector<Line>cd,rd,md,sd;
 explicit FabricIO(unsigned clients,unsigned ports):C(clients),P(ports),cv(C),cr(C),cw(C),rv(C),rr(C),mv(P),mr(P),mw(P),sv(P),sr(P),cl(C),ml(P),ci(C),ri(C),mi(P),si(P),cd(C),rd(C),md(P),sd(P){}
};
struct FabricCycle:FabricIO {
 std::vector<Fifo<FabricRequest,4>>q;std::vector<uint64_t>busy;std::vector<std::array<unsigned,64>> client,local;
 std::vector<unsigned>arb,return_arb;std::vector<uint8_t>bv,consume;std::vector<FabricReturn>b,next;std::vector<int>selected,tag;std::vector<uint8_t>qr,next_rv;
 explicit FabricCycle(unsigned clients=33,unsigned ports=8):FabricIO(clients,ports),q(C),busy(P),client(P),local(P),arb(P),return_arb(C),bv(P),consume(P),b(P),next(C),selected(P),tag(P),qr(C),next_rv(C){if(C>64||P>32||!P||(P&(P-1)))throw std::runtime_error("fabric dimensions");}
 void combin(){
  std::fill(qr.begin(),qr.end(),false);std::fill(consume.begin(),consume.end(),false);std::fill(next_rv.begin(),next_rv.end(),false);idle=true;
  std::array<uint64_t,32>eligible{};std::array<uint32_t,64>returns{};
  for(unsigned c=0;c<C;++c)if(q[c].ov)eligible[q[c].od.line&(P-1)]|=1ull<<c;
  for(unsigned p=0;p<P;++p)if(bv[p])returns[b[p].client]|=1u<<p;
  for(unsigned p=0;p<P;++p){uint64_t after=eligible[p]&(~0ull<<arb[p]);uint64_t choice=after?after:eligible[p];selected[p]=choice?__builtin_ctzll(choice):-1;tag[p]=busy[p]==~0ull?-1:__builtin_ctzll(~busy[p]);
   if((!mv[p]||mr[p])&&tag[p]>=0&&selected[p]>=0)qr[selected[p]]=true;
   idle&=!busy[p]&&!mv[p]&&!bv[p];
  }
  for(unsigned c=0;c<C;++c){next[c]={};uint32_t after=returns[c]&(~0u<<return_arb[c]),choice=after?after:returns[c];
   if(choice){unsigned k=__builtin_ctz(choice);next_rv[c]=true;next[c]=b[k];consume[k]=!rv[c]||rr[c];}
   cr[c]=q[c].ready(qr[c]);idle&=!q[c].ov&&!q[c].count&&!rv[c];
  }
  for(unsigned p=0;p<P;++p)sr[p]=!bv[p]||consume[p];
 }
 void step(){
  if(rst){for(auto &x:q)x={};std::fill(busy.begin(),busy.end(),0);std::fill(arb.begin(),arb.end(),0);std::fill(return_arb.begin(),return_arb.end(),0);std::fill(mv.begin(),mv.end(),false);std::fill(bv.begin(),bv.end(),false);std::fill(rv.begin(),rv.end(),false);accepted=returned=0;error=false;return;}
  // Snapshot queue outputs before the RAM read and enqueue on this edge.
  // Queues are updated after port decisions, so these outputs remain stable.
  for(unsigned p=0;p<P;++p){bool take=sr[p]&&sv[p];FabricReturn response;
   if(take){if(!(busy[p]>>si[p]&1))error=true;response={client[p][si[p]],local[p][si[p]],sd[p]};}
   if(!mv[p]||mr[p]){mv[p]=false;if(tag[p]>=0&&selected[p]>=0){auto x=q[selected[p]].od;mv[p]=true;mw[p]=x.write;ml[p]=x.line;md[p]=x.data;mi[p]=tag[p];busy[p]|=1ull<<tag[p];client[p][tag[p]]=selected[p];local[p][tag[p]]=x.id;arb[p]=selected[p]==int(C-1)?0:selected[p]+1;++accepted;}}
   if(sr[p]){bv[p]=sv[p];if(take){b[p]=response;busy[p]&=~(1ull<<si[p]);++returned;}}
  }
  for(unsigned c=0;c<C;++c){q[c].step(cv[c],{cw[c],cl[c],ci[c],cd[c]},qr[c]);if(!rv[c]||rr[c]){rv[c]=next_rv[c];ri[c]=next[c].id;rd[c]=next[c].data;if(next_rv[c])return_arb[c]=(return_arb[c]+1)&(P-1);}}
 }
};
}
