#pragma once
#include "fabric_model.hpp"
namespace r2_model {
struct HierFabricCycle:FabricIO {
 unsigned L;std::vector<FabricCycle>local;FabricCycle central;
 HierFabricCycle(unsigned clients=41,unsigned ports=8):FabricIO(clients,ports),L((clients-1)/5),central(L+1,ports){if(clients!=5*L+1||L>32)throw std::runtime_error("hier dimensions");for(unsigned n=0;n<L;++n)local.emplace_back(5,1);}
 unsigned index(unsigned n,unsigned j)const{return j<4?j*L+n:4*L+1+n;}
 void combin(){
  central.rst=rst;central.mr=mr;central.sv=sv;central.si=si;central.sd=sd;
  for(unsigned n=0;n<L;++n){auto&l=local[n];l.rst=rst;
   for(unsigned j=0;j<5;++j){unsigned c=index(n,j);l.cv[j]=cv[c];l.cw[j]=cw[c];l.cl[j]=cl[c];l.ci[j]=ci[c];l.cd[j]=cd[c];l.rr[j]=rr[c];}
   l.combin();central.cv[n]=l.mv[0];central.cw[n]=l.mw[0];central.cl[n]=l.ml[0];central.ci[n]=l.mi[0];central.cd[n]=l.md[0];central.rr[n]=l.sr[0];
  }
  unsigned c=4*L;central.cv[L]=cv[c];central.cw[L]=cw[c];central.cl[L]=cl[c];central.ci[L]=ci[c];central.cd[L]=cd[c];central.rr[L]=rr[c];central.combin();
  cr[c]=central.cr[L];rv[c]=central.rv[L];ri[c]=central.ri[L];rd[c]=central.rd[L];idle=central.idle;error=central.error;
  for(unsigned n=0;n<L;++n){auto&l=local[n];l.mr[0]=central.cr[n];l.sv[0]=central.rv[n];l.si[0]=central.ri[n];l.sd[0]=central.rd[n];l.combin();idle&=l.idle;error|=l.error;
   for(unsigned j=0;j<5;++j){unsigned c=index(n,j);cr[c]=l.cr[j];rv[c]=l.rv[j];ri[c]=l.ri[j];rd[c]=l.rd[j];}
  }
  mv=central.mv;mw=central.mw;ml=central.ml;mi=central.mi;md=central.md;sr=central.sr;accepted=central.accepted;returned=central.returned;
 }
 void step(){central.step();for(auto&l:local)l.step();}
};
}
