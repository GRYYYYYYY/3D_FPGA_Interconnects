#include "directory_model.hpp"
#include <fstream>
#include <iostream>
#include <map>
#include <deque>
#include <cassert>
using namespace dfservice;
int main(int argc,char**argv){
 if(argc!=2)return 2;
 std::ofstream f(argv[1]);DirectoryBank d;uint64_t cycle=0,commands=0,blocked=0;
 std::map<unsigned,DirectoryBank::Member> oracle;std::array<std::deque<unsigned>,4096> lists;
 auto step=[&](std::optional<DirCommand> c={},bool rr=false){DirCommand x=c?*c:DirCommand{};auto r=d.rsp;
 f<<std::hex<<unsigned(c.has_value())<<' '<<x.op<<' '<<x.bucket<<' '<<x.node<<' '<<x.arg<<' '<<x.ptr<<' '<<rr<<' '<<d.ready()<<' '<<d.rv<<' '<<r.op<<' '<<r.status<<' '<<r.bucket<<' '<<r.node<<' '<<r.arg<<' '<<r.ptr<<' '<<r.next<<' '<<d.used<<' '<<d.upper<<'\n';
 d.tick(c,rr);++cycle;};
 auto txn=[&](DirCommand c){while(!d.ready())step({},true);auto start=cycle;step(c,false);while(!d.rv){step({},false);assert(cycle-start<10);}auto r=d.rsp;
 for(unsigned k=0;k<(commands*17)%5;++k){auto old=d.rsp;step({},false);assert(d.rv&&d.rsp.ptr==old.ptr&&d.rsp.arg==old.arg);++blocked;}
 assert(r.op==c.op);
 if(c.op==0){if(oracle.size()==8192){assert(r.status==2);}else{assert(!r.status&&r.ptr<8192&&!oracle.count(r.ptr));auto&l=lists[c.bucket];if(!l.empty())oracle[l.back()].next=r.ptr;l.push_back(r.ptr);oracle[r.ptr]={c.node,c.arg,8192};}}
 if(c.op==1){auto&l=lists[c.bucket];assert(!r.status&&r.ptr==(l.empty()?8192:l.front()));l.clear();}
 if(c.op==2){if(c.ptr>=8192||oracle.empty())assert(r.status==2);else{auto x=oracle.at(c.ptr);assert(!r.status&&r.node==x.node&&r.arg==x.arg&&r.next==x.next);oracle.erase(c.ptr);}}
 if(c.op==3){unsigned b=0;while(b<4096&&lists[b].empty())++b;if(b==4096)assert(r.status==1);else assert(!r.status&&r.bucket==b);}
 step({},true);++commands;return r;
 };
 while(!d.initialized())step();
 assert(cycle==8192);txn({3});
 for(unsigned i=0;i<8192;++i){unsigned b=i%5==0?(i*67)%4096:17;txn({0,b,i+100,(i<<12)|b});}
 assert(d.used==8192);txn({0,17,999,17});txn({3});
 for(unsigned b=0;b<4096;++b){if(lists[b].empty())continue;txn({3});auto r=txn({1,b});unsigned p=r.ptr;
  // Detach then append again to identical bucket before consuming old list.
  if(d.used<8192)txn({0,b,900000+b,0x80000000u|b});
  while(p!=8192){auto m=txn({2,0,0,0,p});p=m.next;}
 }
 for(unsigned b=0;b<4096;++b){if(lists[b].empty())continue;unsigned p=txn({1,b}).ptr;while(p!=8192)p=txn({2,0,0,0,p}).next;}
 assert(d.used==0&&oracle.empty());txn({3});txn({2,0,0,0,8192});
 // Sparse min boundaries and high payload bits.
 for(unsigned b:{0u,63u,64u,127u,2047u,2048u,4095u})txn({0,b,0xf1234567u,0xabcde000u|b});
 for(unsigned b:{0u,63u,64u,127u,2047u,2048u,4095u}){txn({3});unsigned p=txn({1,b}).ptr;txn({2,0,0,0,p});}
 txn({3});for(unsigned i=0;i<8;++i)step({},true);
 std::cout<<"DIRECTORY_MODEL_PASS cycles="<<cycle<<" commands="<<commands<<" blocked_response_cycles="<<blocked<<" peak="<<d.peak<<"\n";
}
