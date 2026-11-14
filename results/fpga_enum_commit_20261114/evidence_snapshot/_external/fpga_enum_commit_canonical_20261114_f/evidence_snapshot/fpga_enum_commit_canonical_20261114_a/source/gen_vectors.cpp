#include "pending17.hpp"
#include <array>
#include <vector>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
using namespace pending17;
struct Model {std::array<std::array<Packed,4>,64> state;};
void line(std::ostream&o,const std::array<uint64_t,4>&v){for(int s=3;s>=0;--s)o<<std::setw(16)<<v[s];}
int main(int argc,char**argv){if(argc!=2)return 1;for(unsigned bank=0;bank<2;++bank){Model m;std::ofstream f(std::string(argv[1])+"/bank"+std::to_string(bank)+".mem");unsigned count=0;
 auto emit=[&](unsigned word,unsigned sector,unsigned op,uint64_t value,std::array<uint64_t,4>lv,uint32_t arg){auto &x=m.state[word];auto old=x[sector].label;unsigned mask=0,status=0;std::array<uint64_t,4>labels;std::array<uint32_t,4>events;
  for(unsigned s=0;s<4;++s){Old a{x[s].label,expand(x[s])};if(op==7){if(both(a,x[s],3,lv[s],0)&1)mask|=1<<s;}else if(s==sector){status=both(a,x[s],op,value,arg);if(op!=2&&(status&1))mask|=1<<s;}labels[s]=x[s].label;events[s]=expand(x[s])&0xfffffff; // absent PV is0 but event_arguments preserve label bucket
   events[s]=((x[s].pv&65535)<<12)|(x[s].label>>52);
  }
  // Pack68 = four17-bit words, printed as17 nibbles using an unsigned128 intermediate.
  __uint128_t pv=0;for(unsigned s=0;s<4;++s)pv|=__uint128_t(x[s].pv)<<(s*17);
  f<<std::hex<<std::setfill('0')<<std::setw(6)<<((word<<8)|(bank<<7)|(3<<2)|sector)<<std::setw(1)<<op<<std::setw(16)<<value;line(f,lv);f<<std::setw(7)<<arg<<std::setw(16)<<old<<std::setw(1)<<unsigned(pv>>64)<<std::setw(16)<<uint64_t(pv)<<std::setw(1)<<status<<std::setw(1)<<mask;
  for(int s=3;s>=0;--s)f<<std::setw(7)<<events[s];line(f,labels);f<<'\n';++count;
 };
 std::array<uint64_t,4> lv;
 for(unsigned w=0;w<8;++w){for(unsigned s=0;s<4;++s)lv[s]=(uint64_t(0x410+w)<<52)|((uint64_t(bank*11+w+s+1))<<32)|1000;emit(w,0,7,0,lv,0);}
 // Hundreds of repeated slot and word lifecycles, same-bucket/migrating/no-op/POP/SEED.
 for(unsigned i=0;i<360;++i){unsigned w=(i<300?0:(i*17)%48),s=i%4;auto before=m.state[w][s];unsigned mode=i%9;
  uint64_t val=(uint64_t(0x200+(i%128))<<52)|uint64_t(100000-i);lv={val,val+1,val+2,val+3};
  if(mode==0)emit(w,s,3,before.label==INF?val:before.label-1,lv,0);
  else if(mode==1)emit(w,s,3,INF,lv,0);
  else if(mode==2)emit(w,s,2,0,lv,(expand(before)&0xfffffff)^1);
  else if(mode==3)emit(w,s,2,0,lv,expand(before)&0xfffffff);
  else if(mode==4)emit(w,s,3,val,lv,0);
  else if(mode==5)emit(w,s,7,0,lv,0);
  else if(mode==6)emit(w,s,5,0,lv,0);
  else if(mode==7)emit(w,s,3,0,lv,0);
  else emit(w,s,2,0,lv,expand(before)&0xfffffff);
 }
 std::ofstream final(std::string(argv[1])+"/bank"+std::to_string(bank)+"_final.mem");for(auto &x:m.state){std::array<uint64_t,4>labels;for(unsigned s=0;s<4;++s)labels[s]=x[s].label;final<<std::hex<<std::setfill('0');line(final,labels);final<<'\n';}
 std::cout<<"bank="<<bank<<" operations="<<count<<'\n';if(count!=368)return 1;
 }
}
