#include "replay61.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
struct Trace {
 std::ofstream stim,expected,initial;unsigned wave=0;std::vector<la::Cost> mem;
 Trace(const std::string& dir,const la::Workload& w):stim(dir+"/stimulus.txt"),expected(dir+"/expected.hex"),initial(dir+"/initial.hex"),mem(8192,{INFINITY,INFINITY}){if(w.h.nodes>8192)throw std::runtime_error("trace RAM overflow");mem[w.job[0].source]={0,0};dump(initial);}
 void dump(std::ofstream& f){f<<std::hex<<std::setfill('0');for(unsigned l=0;l<2048;++l){for(int s=3;s>=0;--s)f<<std::setw(8)<<la61::bits(mem[l*4+s].delay)<<std::setw(8)<<la61::bits(mem[l*4+s].congestion);f<<'\n';}}
 void member(uint32_t,uint32_t){}
 void begin_wave(uint32_t,uint64_t,const std::vector<uint32_t>&,const std::vector<la::Cost>&){++wave;}
 void edge(size_t,uint32_t v,la::Cost p,uint64_t){if(wave>2)return;stim<<"0 "<<std::hex<<(v>>2)<<' '<<(v%4)<<' '<<std::setfill('0')<<std::setw(8)<<la61::bits(p.delay)<<std::setw(8)<<la61::bits(p.congestion)<<'\n';if(la61::less(p,mem[v]))mem[v]=p;}
 void flush(){if(wave>2)return;stim<<"1 0 0 0\n";dump(expected);}
 void end_wave(uint64_t,uint64_t){}
};
int main(int argc,char**argv){if(argc!=3)return 2;la::Workload w(argv[1]);la61::Prepared prep(w);la61::ScratchT<la61::DirectDirectory>s(w.h.nodes);std::vector<la::Cost> out(w.h.cells);Trace trace(argv[2],w);auto p=la61::search_replay<true>(w,0,prep.targets[0],20,s,out.data(),false,500000000,524288,trace);std::cout<<"q0 full reference status "<<p.status<<"; emitted complete waves 1 and 2; not complete RTL batch\n";return p.status;}
