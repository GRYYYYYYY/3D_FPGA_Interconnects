// Verilator4 legacy callback used only by assertion diagnostics; clocks are explicit.
double sc_time_stamp(){return 0;}
#include "Vowner_changed_tb.h"
#include "verilated.h"
using Vsparse_owner=Vowner_changed_tb;
#include <array>
#include <vector>
#include <map>
#include <set>
#include <random>
#include <fstream>
#include <iostream>
#include <stdexcept>
using Line=std::array<uint64_t,4>;
struct Pending{bool write;uint32_t address,id;Line data;uint64_t due;};
int main(int argc,char**argv){try{
 Verilated::commandArgs(argc,argv);Vsparse_owner d;std::mt19937 gen(42);std::map<uint32_t,Line> memory,expected;std::vector<Pending> pending;std::set<uint32_t> marks;uint64_t tick=0;const uint64_t inf=0x7f8000007f800000ull;
 auto get=[&](uint32_t a){if(a%8||a/8>=768)throw std::runtime_error("finite memory range");if(!memory.count(a))memory[a]={inf,inf,inf,inf};return memory[a];};
 uint64_t eviction_writes=0,events=0,unique_total=0;
 auto cycle=[&](){d.clk=0;d.eval();d.clk=1;d.eval();++tick;};
 d.commit_phase=d.commit_ready=d.commit_ack=0;d.ack_index=0;d.rst=1;d.iv=d.fence=d.rsp_valid=d.mem_ready=0;d.update_ready=0;cycle();cycle();d.rst=0;
 unsigned maxout=0;std::ofstream log(argc>1?argv[1]:"owner_cycles.csv");log<<"cycle,wave,sent,accepted,retired,outstanding,mshr_peak,dirty_peak\n";
 for(unsigned wave=0;wave<2;++wave){
  auto base=memory;marks.clear();std::vector<std::pair<uint32_t,uint64_t>> requests;
  for(unsigned i=0;i<2400;++i){uint32_t line=(i<256?i%32:gen()%768)*8;uint32_t node=line*4+(gen()%4);uint64_t cost=(uint64_t(0x3f800000+gen()%200)<<32)|(0x3f800000+gen()%200);requests.push_back({node,cost});if(!expected.count(line))expected[line]=get(line);expected[line][node%4]=std::min(expected[line][node%4],cost);}
  unsigned sent=0;bool done=false;int response=-1;bool held=false;uint32_t held_line=0,held_id=0;Line held_data{};bool held_write=false;
  for(unsigned steps=0;steps<1000000;++steps){
   d.clk=0;d.iv=sent<requests.size();if(d.iv){d.node=requests[sent].first;d.pair=requests[sent].second;}d.fence=sent==requests.size();d.mem_ready=pending.size()<64&&(gen()%5!=0);d.update_ready=gen()%4!=0;
   if(response<0)for(int i=int(pending.size())-1;i>=0;--i)if(pending[i].due<=tick){response=i;break;}
   d.rsp_valid=response>=0;if(response>=0){auto &p=pending[response];d.rsp_id=p.id;for(unsigned s=0;s<4;++s){d.rsp_data[2*s]=p.data[s];d.rsp_data[2*s+1]=p.data[s]>>32;}}
   d.eval();
   if(held){if(!d.mem_valid||d.mem_line!=held_line||d.mem_id!=held_id||d.mem_write!=held_write)throw std::runtime_error("command instability");for(unsigned s=0;s<4;++s)if((uint64_t(d.mem_data[s*2+1])<<32|d.mem_data[s*2])!=held_data[s])throw std::runtime_error("payload instability");}
   held=d.mem_valid&&!d.mem_ready;if(held){held_line=d.mem_line;held_id=d.mem_id;held_write=d.mem_write;for(unsigned s=0;s<4;++s)held_data[s]=uint64_t(d.mem_data[s*2+1])<<32|d.mem_data[s*2];}
   if(d.iv&&d.ir)++sent;
   if(d.update_valid&&d.update_ready)for(unsigned s=0;s<4;++s)if(d.update_mask&(1<<s)){marks.insert(d.update_line*4+s);++events;}
   bool pop=response>=0&&d.rsp_ready;
   if(pop){auto p=pending[response];if(p.write)memory[p.address]=p.data;}
   if(d.mem_valid&&d.mem_ready){Line data=get(d.mem_line);if(d.mem_write){if(!d.fence)++eviction_writes;for(unsigned s=0;s<4;++s)data[s]=uint64_t(d.mem_data[2*s+1])<<32|d.mem_data[2*s];}else for(auto p:pending)if(p.write&&p.address==d.mem_line&&!(pop&&p.id==pending[response].id))throw std::runtime_error("unacknowledged write RAW");pending.push_back({bool(d.mem_write),d.mem_line,d.mem_id,data,tick+120+gen()%80});}
   if(pop){pending.erase(pending.begin()+response);response=-1;}maxout=std::max<unsigned>(maxout,pending.size());
   d.clk=1;d.eval();++tick;if(d.error)throw std::runtime_error("DUT error");
   if(tick%100==0)log<<tick<<','<<wave<<','<<sent<<','<<d.accepted<<','<<d.retired<<','<<pending.size()<<','<<unsigned(d.mshr_peak)<<','<<unsigned(d.dirty_peak)<<'\n';
   if(d.fence_done){if(!pending.empty()||d.accepted!=d.retired)throw std::runtime_error("early fence");done=true;break;}
  }
  if(!done)throw std::runtime_error("watchdog");
  std::set<uint32_t> changed;
  for(unsigned l=0;l<768;++l){unsigned a=l*8;Line e=expected.count(a)?expected[a]:Line{inf,inf,inf,inf};if(get(a)!=e)throw std::runtime_error("full memory mismatch line "+std::to_string(a));Line b=base.count(a)?base[a]:Line{inf,inf,inf,inf};for(unsigned s=0;s<4;++s)if(e[s]<b[s])changed.insert(a*4+s);}
  if(changed!=marks)throw std::runtime_error("changed set mismatch");
  // Read final IDs only after the complete write-ACK fence. Clear each mark
  // several cycles after issue, representing a delayed label/metadata commit ACK.
  std::set<uint32_t> queued;std::vector<std::pair<unsigned,uint64_t>> acks;
  auto marked=[&](unsigned idx){return (d.marked_debug[idx/32]>>(idx%32))&1u;};
  d.iv=d.rsp_valid=0;d.commit_phase=1;d.commit_ready=1;
  bool drained=false;
  for(unsigned k=0;k<100000;++k){
   d.clk=0;d.commit_ack=0;d.eval();
   if(d.commit_valid&&d.commit_ready){unsigned idx=d.commit_index,n=((idx>>2)<<5)|(idx&3);if(!marked(idx)||!queued.insert(n).second)throw std::runtime_error("missing membership or duplicate queued ID");acks.push_back({idx,tick+7+idx%5});}
   int ack=-1;for(unsigned j=0;j<acks.size();++j)if(acks[j].second<=tick){ack=j;break;}
   unsigned idx=0;if(ack>=0){idx=acks[ack].first;d.ack_index=idx;d.commit_ack=1;}
   for(auto a:acks)if(!marked(a.first))throw std::runtime_error("membership cleared before commit ACK");
   d.eval();d.clk=1;d.eval();++tick;
   if(ack>=0){if(marked(idx))throw std::runtime_error("membership not cleared at commit ACK");acks.erase(acks.begin()+ack);}
   for(auto a:acks)if(!marked(a.first))throw std::runtime_error("membership cleared by unrelated ACK");
   if(!d.occupancy&&!d.commit_valid&&acks.empty()){drained=true;break;}
  }
  if(!drained||queued!=changed)throw std::runtime_error("persistent changed queue vs baseline mismatch");
  unique_total+=queued.size();d.commit_phase=d.commit_ready=d.commit_ack=0;
  for(unsigned k=0;k<128;++k)if(d.marked_debug[k])throw std::runtime_error("membership retained after full commit");
  d.fence=0;d.iv=0;d.rsp_valid=0;cycle();cycle();
 }
 std::cout<<"OWNER_CHANGED_PASS eviction_writes="<<eviction_writes<<" events="<<events<<" unique="<<unique_total<<" cycles="<<tick<<" mshr_peak="<<unsigned(d.mshr_peak)<<" dirty_peak="<<unsigned(d.dirty_peak)<<" outstanding_peak="<<maxout<<" merges="<<d.merges<<" accepted="<<d.accepted<<" retired="<<d.retired<<'\n';
 if(d.mshr_peak<2||maxout<2||!d.merges||eviction_writes<128||events<=unique_total)throw std::runtime_error("concurrency not exercised");
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
