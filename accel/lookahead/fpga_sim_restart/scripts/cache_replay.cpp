// Functional transaction replay ONLY. No elapsed software time is FPGA time.
#include "replay61.hpp"
#include <iostream>
#include <fstream>
#include <iomanip>
#include <array>
struct Line {uint32_t line=0;bool valid=false,dirty=false;std::array<la::Cost,4> data;};
struct Observer {
 std::vector<la::Cost> home; std::array<Line,8192> cache;std::array<unsigned,2048> rr{};
 unsigned owners,q;bool bypass;uint64_t events=0,hits=0,reads=0,writes=0,evictions=0,improvements=0,waves=0;
 const std::vector<la::Cost>& labels;
 Observer(size_t n,unsigned o,unsigned q_,bool f0,const std::vector<la::Cost>& l):home((n+3)/4*4,{INFINITY,INFINITY}),owners(o),q(q_),bypass(f0),labels(l){}
 void member(uint32_t,uint32_t){}
 void begin_wave(uint32_t,uint64_t,const std::vector<uint32_t>&,const std::vector<la::Cost>&){++waves;}
 void write(Line& e){if(e.valid&&e.dirty){++writes;for(unsigned s=0;s<4;++s)home[e.line*4+s]=e.data[s];e.dirty=false;}}
 void edge(size_t,uint32_t v,la::Cost p,uint64_t){
  ++events;auto line=v>>2,owner=line%owners,set=(line/owners)%32,base=(owner*32+set)*4;Line* e=nullptr;
  if(!bypass)for(unsigned w=0;w<4;++w)if(cache[base+w].valid&&cache[base+w].line==line)e=&cache[base+w];
  if(e)++hits;
  else{unsigned way=rr[owner*32+set];for(int w=3;w>=0;--w)if(!cache[base+w].valid)way=w;
   e=&cache[base+way];evictions+=e->valid;write(*e);*e={};e->valid=true;e->line=line;
   rr[owner*32+set]=(way+1)%4;++reads;for(unsigned s=0;s<4;++s)e->data[s]=home[line*4+s];}
  if(la61::less(p,e->data[v%4])){e->data[v%4]=p;e->dirty=true;++improvements;}
  if(bypass){write(*e);e->valid=false;}
 }
 void flush(){for(auto& e:cache){write(e);e.valid=false;}}
 void end_wave(uint64_t,uint64_t){if(memcmp(home.data(),labels.data(),labels.size()*8))throw std::runtime_error("full wave proposal/label mismatch");}
};
int main(int argc,char** argv){try{
 if(argc!=5)throw std::runtime_error("cache_replay INPUT owners F0|F1 OUTPUT");
 la::Workload w(argv[1]);la61::Prepared prep(w);la61::ScratchT<la61::DirectDirectory> s(w.h.nodes);
 la61::ScratchT<std::map<uint32_t,std::vector<uint32_t>>> ref(w.h.nodes);
 std::vector<la::Cost> out(w.h.jobs*w.h.cells),gold(w.h.cells);unsigned owners=std::stoul(argv[2]);if(owners!=1&&owners!=8&&owners!=64)throw std::runtime_error("owners");
 for(unsigned q=0;q<w.h.jobs;++q){
 Observer obs(w.h.nodes,owners,q,std::string(argv[3])=="F0",s.label);if(prep.targets[q])obs.home[w.job[q].source]={0,0};
 auto p=la61::search_replay<false>(w,q,prep.targets[q],20,s,out.data()+q*w.h.cells,false,500000000,524288,obs);
 auto check=la61::search<false>(w,q,prep.targets[q],20,ref,gold.data(),false,500000000,524288);
 bool eq=!memcmp(gold.data(),out.data()+q*w.h.cells,w.h.cells*8);
 std::cout<<"{\"qid\":"<<q<<",\"status\":"<<p.status<<",\"reference_status\":"<<check.status<<",\"output_equal\":"<<(eq?"true":"false")<<",\"events\":"<<obs.events<<",\"hits\":"<<obs.hits<<",\"reads32B\":"<<obs.reads<<",\"writes32B\":"<<obs.writes<<",\"evictions\":"<<obs.evictions<<",\"improvements\":"<<obs.improvements<<",\"waves\":"<<obs.waves<<",\"pending_peak\":"<<p.pending_peak<<",\"buckets_peak\":"<<p.bucket_peak<<"}\n"<<std::flush;
 if(p.status||check.status||!eq)return 3;
 }
 std::ofstream f(argv[4],std::ios::binary);la::write(f,out.data(),out.size());
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 10;}}
