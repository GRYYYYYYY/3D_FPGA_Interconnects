#include "Vwave_inf_owner.h"
#include "verilated.h"
#include <array>
#include <vector>
#include <deque>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <cstring>
#include <random>
static constexpr uint64_t INF=0x7f8000007f800000ull;
struct Event{uint32_t node;uint64_t pair;};
struct Row{std::array<uint64_t,4> p={INF,INF,INF,INF};};
struct Frag{uint32_t line,mask;Row row;};
static void require(bool p,const char*s){if(!p)throw std::runtime_error(s);}
template<class T>void read(std::istream&f,T&x){f.read((char*)&x,sizeof(x));require(bool(f),"truncated input");}
int main(int argc,char**argv){try{
 require(argc==4,"usage real-wave.bin|directed cycles.csv output.csv");
 constexpr size_t CAP=1<<20; // finite testbench canonical/scratch capacity, independent of cache
 std::vector<Row> expected(CAP),scratch(CAP),before(CAP);std::vector<uint8_t> touched(CAP);
 std::vector<uint32_t> lines;std::array<std::vector<Event>,2> events;
 auto add=[&](Event e){unsigned line=e.node>>2;require(line<CAP,"backing overflow");
  if(!touched[line]){lines.push_back(line);touched[line]=1;}
  expected[line].p[e.node&3]=std::min(expected[line].p[e.node&3],e.pair);
  events[(line>>5)&1].push_back(e);
 };
 if(std::string(argv[1])=="empty"){
 }else if(std::string(argv[1])=="capacity4096"||std::string(argv[1])=="capacity4097"){
  unsigned count=std::string(argv[1])=="capacity4096"?4096:4097;
  for(unsigned i=0;i<count;++i)for(unsigned b=0;b<2;++b)add({(i*64+b*32)*4,0x3f80000040000000ull});
 }else if(std::string(argv[1])=="directed"){
  // Consecutive same-row RAW, 5 colliding tags, both subbanks, all sectors,
  // equal-delay whole-pair ties and long output backpressure.
  std::mt19937 rng(1729);
  for(unsigned i=0;i<12000;++i){unsigned b=i&1,slot=(i<2048)?0:(rng()%12),line=b*32+slot*64*1024;
    add({line*4+(i%4),uint64_t(0x3f800000+(rng()%16))<<32 | (0x40000000+(rng()%128))});}
 }else{
  std::ifstream f(argv[1],std::ios::binary);uint64_t h[6];for(auto&x:h)read(f,x);require(h[0]==0x5741564541434331ull,"magic");
  for(uint64_t i=0;i<h[4];++i){Event e;read(f,e.node);read(f,e.pair);add(e);}
  for(uint64_t i=0;i<h[5];++i){uint32_t line,mask;read(f,line);read(f,mask);require(line<CAP,"golden backing overflow");
    for(auto&x:before[line].p)read(f,x);Row final;for(auto&x:final.p)read(f,x);
    for(unsigned k=0;k<4;++k)require(std::min(before[line].p[k],expected[line].p[k])==final.p[k],"independent recorded final mismatch");}
 }
 Vwave_inf_owner d;d.clk=0;d.reset=1;d.in_valid=0;d.flush=0;d.frag_ready=0;
 for(int i=0;i<3;++i){d.clk=0;d.eval();d.clk=1;d.eval();}d.reset=0;
 std::array<size_t,2> pos{};std::array<std::deque<Frag>,2> fifo;unsigned rr=0,busy=0;uint64_t requests=0,merges=0,peak=0,duals=0,first=0,last=0;
 std::ofstream log(argv[2]);log<<"cycle,accept_mask,retire0,retire1,fragment_mask,q0,q1,service_busy,requests32B\n";
 bool finished=false;
 for(uint64_t cycle=0;cycle<1000000;++cycle){
   d.clk=0;d.in_valid=0;d.in_node=0;for(int i=0;i<4;++i)d.in_pair[i]=0;
   for(unsigned b=0;b<2;++b)if(pos[b]<events[b].size()){
     auto e=events[b][pos[b]];d.in_valid|=1<<b;d.in_node|=uint64_t(e.node)<<(b*32);d.in_pair[b*2]=e.pair;d.in_pair[b*2+1]=e.pair>>32;
   }
   d.flush=pos[0]==events[0].size()&&pos[1]==events[1].size();
   d.frag_ready=0;for(unsigned b=0;b<2;++b)if(fifo[b].size()<8&&cycle%37<29)d.frag_ready|=1<<b;
   d.eval();unsigned a=d.in_valid&d.in_ready,fg=d.frag_valid&d.frag_ready;
   for(unsigned b=0;b<2;++b){if(a>>b&1){++pos[b];if(!first)first=cycle;last=cycle;}
     if(fg>>b&1){Frag f;f.line=uint32_t(d.frag_line>>(b*32));f.mask=d.frag_mask>>(b*4)&15;require(f.line<CAP,"RTL fragment address overflow");
       for(unsigned k=0;k<4;++k)f.row.p[k]=uint64_t(d.frag_pairs[b*8+k*2])|uint64_t(d.frag_pairs[b*8+k*2+1])<<32;
       fifo[b].push_back(f);peak=std::max<uint64_t>(peak,fifo[b].size());}
   }
   duals+=a==3;
   if(busy)--busy;
   if(!busy){for(unsigned k=0;k<2;++k){unsigned b=(rr+k)&1;if(fifo[b].empty())continue;Frag f=fifo[b].front();fifo[b].pop_front();
      for(unsigned k=0;k<4;++k)if(f.mask>>k&1)scratch[f.line].p[k]=std::min(scratch[f.line].p[k],f.row.p[k]);
      rr=b^1;busy=20;requests+=4;++merges;break;}}
   log<<cycle<<','<<a<<','<<uint32_t(d.retired)<<','<<uint32_t(d.retired>>32)<<','<<fg<<','<<fifo[0].size()<<','<<fifo[1].size()<<','<<busy<<','<<requests<<'\n';
   d.clk=1;d.eval();
   if(d.done==3&&fifo[0].empty()&&fifo[1].empty()&&!busy){finished=true;break;}
 }
 require(finished,"timeout");require(uint32_t(d.accepted)==events[0].size()&&uint32_t(d.accepted>>32)==events[1].size(),"accept count");require(d.retired==d.accepted,"retirement drain");
 std::ofstream out(argv[3]);out<<"line,sector,actual,expected\n";
 for(auto line:lines)for(unsigned k=0;k<4;++k){auto a=std::min(before[line].p[k],scratch[line].p[k]);auto e=std::min(before[line].p[k],expected[line].p[k]);out<<line<<','<<k<<','<<a<<','<<e<<'\n';require(a==e,"complete pair differential");}
 std::cout<<"{\"passed\":true,\"accepted\":"<<pos[0]+pos[1]<<",\"dual_accept_cycles\":"<<duals<<",\"accept_span_cycles\":"<<last-first+1<<",\"spill_fragments\":"<<uint32_t(d.spill_count)+uint32_t(d.spill_count>>32)<<",\"total_fragments\":"<<merges<<",\"queue_peak\":"<<peak<<",\"scratch_requests32B\":"<<requests<<",\"enumerated_slots\":"<<uint32_t(d.enumerated)+uint32_t(d.enumerated>>32)<<",\"board_measured\":false}"<<std::endl;
}catch(std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
