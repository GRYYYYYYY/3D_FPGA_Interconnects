#include <array>
#include <bitset>
#include <vector>
#include <random>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <algorithm>
#include <type_traits>
#include "hier_fabric_model.hpp"
#ifndef INDEPENDENT_MODEL
#include "Vr2_shared_fabric.h"
#include "verilated.h"
#endif
using Line=std::array<uint64_t,4>;
#ifndef FABRIC_C
#define FABRIC_C 33
#define FABRIC_P 8
#endif
constexpr unsigned C=FABRIC_C,P=FABRIC_P;
#ifdef INDEPENDENT_MODEL
using Device=r2_model::HierFabricCycle;
#else
struct Device:r2_model::HierFabricCycle {
 Vr2_shared_fabric d;
 Device(unsigned c=FABRIC_C,unsigned p=FABRIC_P):r2_model::HierFabricCycle(c,p){}
 template<class W>static void bits(W& w,unsigned at,unsigned width,uint64_t v){
  if constexpr(std::is_integral<W>::value){for(unsigned i=0;i<width;++i){uint64_t mask=uint64_t(1)<<(at+i);w=(w&~mask)|(((v>>i)&1)?mask:0);}}
  else for(unsigned i=0;i<width;++i){auto mask=uint32_t(1)<<(at+i)%32;w[(at+i)/32]=(w[(at+i)/32]&~mask)|(((v>>i)&1)?mask:0);}
 }
 template<class W>static uint64_t get(const W&w,unsigned at,unsigned width){uint64_t v=0;
  if constexpr(std::is_integral<W>::value){for(unsigned i=0;i<width;++i)v|=uint64_t(w>>(at+i)&1)<<i;}
  else for(unsigned i=0;i<width;++i)v|=uint64_t(w[(at+i)/32]>>((at+i)%32)&1)<<i;return v;
 }
 void combin(){d.clk=0;d.rst=rst;d.mr=d.sv=0;
  for(unsigned c=0;c<C;++c){bits(d.cv,c,1,cv[c]);bits(d.cw,c,1,cw[c]);bits(d.rr,c,1,rr[c]);d.cl[c]=cl[c];bits(d.ci,c*6,6,ci[c]);for(unsigned s=0;s<4;++s)bits(d.cd,c*256+s*64,64,cd[c][s]);}
  for(unsigned p=0;p<P;++p){d.mr|=unsigned(mr[p])<<p;d.sv|=unsigned(sv[p])<<p;bits(d.si,p*6,6,si[p]);for(unsigned s=0;s<4;++s)bits(d.sd,p*256+s*64,64,sd[p][s]);}
  d.eval();for(unsigned c=0;c<C;++c){cr[c]=get(d.cr,c,1);rv[c]=get(d.rv,c,1);ri[c]=get(d.ri,c*6,6);for(unsigned s=0;s<4;++s)rd[c][s]=get(d.rd,c*256+s*64,64);}
  for(unsigned p=0;p<P;++p){mv[p]=d.mv>>p&1;mw[p]=d.mw>>p&1;ml[p]=get(d.ml,p*32,32);mi[p]=get(d.mi,p*6,6);sr[p]=d.sr>>p&1;for(unsigned s=0;s<4;++s)md[p][s]=get(d.md,p*256+s*64,64);}
  error=d.error;idle=d.idle;accepted=d.accepted;returned=d.returned;
 }
 void step(){d.clk=1;d.eval();}
};
#endif

struct Pending{unsigned id;Line data;uint64_t due;};
static Line read_data(unsigned line){return {0x123456789abcdef0ull^line,line*0x12345ull,0x8765432100000000ull|line,~uint64_t(line)};}
int main(int argc,char**argv){try{
 Device d(C,P);std::mt19937 rng(221112);std::array<uint64_t,C>live{};std::array<unsigned,C>sent{},retired{};std::array<std::array<Line,64>,C>expected{};
 std::array<std::vector<Pending>,P>pending;std::array<int,P>response;response.fill(-1);uint64_t tick=0,total_sent=0,total_retired=0;unsigned peak=0;
 std::ofstream log(argv[1]);log<<"cycle,inputs,outputs,physical_accepted,physical_returned,outstanding,request_mask,response_mask\n";
 d.rst=true;for(unsigned i=0;i<2;++i){d.combin();d.step();++tick;}d.rst=false;bool success=false;
 for(unsigned step=0;step<1000000;++step){
  for(unsigned c=0;c<C;++c){d.rr[c]=(rng()%7)!=0&&(tick%401<330||c%3);if(!d.cv[c]&&sent[c]<1000&&live[c]!=~0ull&&rng()%3){unsigned id=__builtin_ctzll(~live[c]);d.cv[c]=true;d.ci[c]=id;live[c]|=1ull<<id;d.cl[c]=(rng()%512)*P+((sent[c]%3)?rng()%P:0);d.cw[c]=sent[c]%2;d.cd[c]={c,sent[c],id,0xfedcba9876000000ull|c};expected[c][id]=d.cw[c]?d.cd[c]:read_data(d.cl[c]);}}
  for(unsigned p=0;p<P;++p){d.mr[p]=pending[p].size()<64&&rng()%4&&tick%157<139;if(response[p]<0)for(int i=int(pending[p].size())-1;i>=0;--i)if(pending[p][i].due<=tick){response[p]=i;break;}d.sv[p]=response[p]>=0;if(d.sv[p]){auto x=pending[p][response[p]];d.si[p]=x.id;d.sd[p]=x.data;}}
  d.combin();std::bitset<C> im,om;std::array<bool,C>take{};
  for(unsigned c=0;c<C;++c){take[c]=d.cv[c]&&d.cr[c];if(take[c]){++sent[c];++total_sent;im[c]=1;}if(d.rv[c]&&d.rr[c]){unsigned id=d.ri[c];if(!(live[c]>>id&1)||d.rd[c]!=expected[c][id])throw std::runtime_error("client response mismatch");live[c]&=~(1ull<<id);++retired[c];++total_retired;om[c]=1;}}
  unsigned outstanding=0;
  for(unsigned p=0;p<P;++p){bool pop=d.sv[p]&&d.sr[p];if(d.mv[p]&&d.mr[p]){if(d.ml[p]%P!=p)throw std::runtime_error("striping");for(auto x:pending[p])if(x.id==d.mi[p])throw std::runtime_error("tag reuse");pending[p].push_back({d.mi[p],d.mw[p]?d.md[p]:read_data(d.ml[p]),tick+60+rng()%60});}if(pop){pending[p].erase(pending[p].begin()+response[p]);response[p]=-1;}outstanding+=pending[p].size();}
  peak=std::max(peak,outstanding);log<<tick<<','<<total_sent<<','<<total_retired<<','<<d.accepted<<','<<d.returned<<','<<outstanding<<','<<im<<','<<om<<'\n';
  if(d.error)throw std::runtime_error("DUT error");if(total_retired==C*1000&&d.idle){success=true;break;}
  d.step();++tick;for(unsigned c=0;c<C;++c)if(take[c])d.cv[c]=false;
 }
 if(!success)throw std::runtime_error("watchdog");std::cout<<"FABRIC_PASS clients="<<C<<" ports="<<P<<" commands="<<total_retired<<" cycles="<<tick<<" peak="<<peak<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
