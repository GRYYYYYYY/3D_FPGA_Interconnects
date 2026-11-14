#include "directory_model.hpp"
#include <fstream>
#include <iostream>
#include <map>
#include <deque>
#include <cassert>
int main(int argc,char**argv){if(argc!=2)return 2;std::ofstream f(argv[1]);lf::DirectoryPipeline d;uint64_t cycle=0;unsigned accepted=0,acked=0;std::map<unsigned,lf::DirectoryPipeline::Member>oracle;std::array<std::deque<unsigned>,4096>lists;
 auto bucket=[](unsigned i){switch(i%7){case 0:case 1:case 3:return 0u;case 2:return 1u;case 4:return 64u;case 5:return 4095u;default:return 63u;}};
 auto step=[&](std::optional<lf::DirCommand> c={},bool rr=false){auto x=c?*c:lf::DirCommand{};lf::DirResponse r=d.response()?*d.response():lf::DirResponse{};
 f<<std::hex<<unsigned(c.has_value())<<' '<<x.op<<' '<<x.bucket<<' '<<x.node<<' '<<x.arg<<' '<<x.ptr<<' '<<rr<<' '<<(x.op==0?d.append_ready():d.ready())<<' '<<bool(d.response())<<' '<<r.op<<' '<<r.status<<' '<<r.bucket<<' '<<r.node<<' '<<r.arg<<' '<<r.ptr<<' '<<r.next<<' '<<d.used<<' '<<d.upper<<'\n';d.tick(c,rr);assert(++cycle<400000);};
 while(!d.initialized())step();assert(cycle==8192);
 auto txn=[&](lf::DirCommand c){while(!d.ready())step({},true);step(c,false);while(!d.response())step({},false);auto r=*d.response();for(unsigned k=0;k<3;++k)step({},false);assert(r.op==c.op&&r.status<=1);
 if(c.op==1){auto&l=lists[c.bucket];assert(r.ptr==(l.empty()?8192:l.front()));l.clear();}
 if(c.op==2){auto m=oracle.at(c.ptr);assert(r.node==m.node&&r.arg==m.arg&&r.next==m.next);oracle.erase(c.ptr);}
 if(c.op==3){unsigned b=0;while(b<4096&&lists[b].empty())++b;assert(b==4096?r.status==1:!r.status&&r.bucket==b);}
 step({},true);return r;};
 for(unsigned round=0;round<2;++round){accepted=acked=0;
  while(accepted<8192||acked<8192){bool rr=cycle%61<39;std::optional<lf::DirCommand>in;if(accepted<8192)in=lf::DirCommand{0,bucket(accepted),accepted,0xbeef0000u|accepted,8192};bool accept=in&&d.append_ready();
   if(rr&&d.response()){auto r=*d.response();assert(!r.status&&r.op==0&&r.ptr<8192&&!oracle.count(r.ptr)&&r.bucket==bucket(acked));auto&l=lists[r.bucket];if(!l.empty())oracle[l.back()].next=r.ptr;l.push_back(r.ptr);oracle[r.ptr]={acked,0xbeef0000u|acked,8192};++acked;}
   step(in,rr);accepted+=accept;
  }
  while(!d.ready())step({},true);assert(d.used==8192);for(unsigned i=0;i<20;++i){assert(!d.append_ready());step(lf::DirCommand{0,0,999,999,8192},true);}
  for(unsigned b=0;b<4096;++b)if(!lists[b].empty()){txn({3});unsigned ptr=txn({1,b}).ptr;while(ptr!=8192)ptr=txn({2,0,0,0,ptr}).next;}
  txn({3});assert(d.used==0&&oracle.empty());
 }
 for(unsigned i=0;i<8;++i)step({},true);std::cout<<"DIRECTORY_MODEL_ORACLE_PASS cycles="<<cycle<<" append=16384 peak="<<d.peak<<'\n';
}
