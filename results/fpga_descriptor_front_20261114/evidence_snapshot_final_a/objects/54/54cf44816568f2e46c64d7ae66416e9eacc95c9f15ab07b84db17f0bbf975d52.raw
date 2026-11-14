#include "directory_model.hpp"
#include <fstream>
#include <iostream>
#include <memory>
#include <random>
#include <cassert>
using namespace dfservice;
int main(int argc,char**argv){if(argc!=2)return 2;std::ofstream f(argv[1]);auto banks=std::make_unique<std::array<DirectoryBank,64>>();MinimumCollector col;unsigned cycle=0,queries=0;std::mt19937 rng(811);
 auto step=[&](uint64_t ext=0,unsigned bucket=0,unsigned generation=0,bool start=false,bool rr=false){std::array<bool,64>br{};std::array<std::optional<unsigned>,64>rsp;uint64_t cr=0,rv=0;unsigned sum=0;
 for(unsigned b=0;b<64;++b){auto&u=(*banks)[b];br[b]=u.ready();if(br[b])cr|=uint64_t(1)<<b;if(auto r=u.response()){rv|=uint64_t(1)<<b;rsp[b]=r->status?4096:r->bucket;}sum+=u.used;}
 auto cmd=col.commands(),ack=col.accepts();auto out=col.output();bool active=col.state!=MinimumCollector::IDLE;
 f<<std::hex<<ext<<' '<<bucket<<' '<<generation<<' '<<start<<' '<<rr<<' '<<col.ready(br)<<' '<<bool(out)<<' '<<out.value_or(4096)<<' '<<cmd<<' '<<ack<<' '<<cr<<' '<<rv<<' '<<sum<<'\n';
 col.tick(start,br,rsp,rr);
 for(unsigned b=0;b<64;++b){std::optional<DirCommand>c;if(cmd>>b&1)c=DirCommand{3};else if(ext>>b&1)c=DirCommand{0,(bucket+b*37)&4095,generation*64+b,(generation<<12)|((bucket+b*37)&4095)};(*banks)[b].tick(c,active?bool(ack>>b&1):true);}
 ++cycle;};
 auto allready=[&](){for(auto&b:*banks)if(!b.ready())return false;return true;};
 while(!allready())step();assert(cycle==8192);
 for(unsigned q=0;q<32;++q){if(q){uint64_t mask=(uint64_t(rng())<<32)|rng();unsigned key=rng()%4096;step(mask,key,q);while(!allready())step();}
  unsigned oracle=4096;for(auto&b:*banks)if(!b.empty())oracle=std::min(oracle,unsigned(DirectoryBank::first(b.upper)*64+DirectoryBank::first(b.bitmap[DirectoryBank::first(b.upper)])));
  step(0,0,0,true,false);while(!col.output())step();assert(*col.output()==oracle);for(unsigned n=0;n<q%7;++n)step();step(0,0,0,false,true);++queries;
 }
 for(unsigned i=0;i<5;++i)step();std::cout<<"MIN_COLLECT_MODEL_PASS cycles="<<cycle<<" queries="<<queries<<" banks=64\n";
}
