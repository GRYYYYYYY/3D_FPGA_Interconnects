// Verilator4 legacy callback used only by assertion diagnostics; clocks are explicit.
double sc_time_stamp(){return 0;}
#include "Vr2_node_state.h"
#include "verilated.h"
#include <array>
#include <vector>
#include <random>
#include <fstream>
#include <iostream>
#include <stdexcept>
#ifndef STATE_OWNER_BITS
#define STATE_OWNER_BITS 3
#endif
constexpr unsigned STATE_B=STATE_OWNER_BITS;
using Line=std::array<uint64_t,4>;
struct Record{uint64_t label=0x7f8000007f800000ull;uint32_t pending=0,flags=0;};
struct Expected{bool live=false;unsigned node=0,status=0;Record old;};
struct Pending{bool wr;unsigned line,id;Line data;uint64_t due;};
int main(int argc,char**argv){try{
 Verilated::commandArgs(argc,argv);Vr2_node_state d;const unsigned N=1u<<22;const uint64_t INF=0x7f8000007f800000ull;
 std::vector<Line> memory(N/2,Line{INF,0,INF,0});std::vector<Record> ref(N);std::array<Expected,64> scoreboard{};std::vector<Pending> pending;
 std::vector<unsigned> nodes;for(unsigned i=0;i<765;++i)nodes.push_back(i*4096+(i%32));nodes.push_back(4102607);nodes.push_back(4166723);nodes.push_back(N-1);
 std::mt19937 rng(20261112);uint64_t tick=0,reads=0,writes=0,returned=0;unsigned sent=0,peak=0;int response=-1;bool input_held=false;unsigned input_tag=0;
 std::ofstream log(argv[1]);log<<"cycle,sent,returned,cache_retired,read_commands,write_commands,outstanding,mshr,dirty\n";
 d.rst=1;d.iv=d.fence=d.rsp_valid=d.mem_ready=0;d.ordy=0;d.state_base=0;d.node_count=N;
 auto clock=[&](){d.clk=0;d.eval();d.clk=1;d.eval();++tick;};clock();clock();d.rst=0;bool success=false;
 bool held=false;unsigned held_line=0,held_id=0;bool held_write=false;Line held_payload{};
 for(unsigned step=0;step<3000000;++step){
  d.clk=0;d.iv=0;
  if(!input_held&&sent<nodes.size()*10){for(unsigned id=0;id<64;++id)if(!scoreboard[id].live){input_tag=id;input_held=true;unsigned phase=sent/nodes.size(),node=nodes[sent%nodes.size()];d.node=node;d.tag=id;d.argument=ref[node].pending;d.operand=0;
   switch(phase){case 0:case 2:d.opcode=1;break;case 1:d.opcode=3;d.operand=0x4000000040000000ull;break;case 3:d.opcode=3;d.operand=0x400000003f800000ull;break;case 4:case 7:d.opcode=2;break;case 5:d.opcode=3;d.operand=0x3f80000000000000ull;break;case 6:d.opcode=2;d.argument=0x10001400;break;case 8:d.opcode=4;break;default:d.opcode=0;break;}break;}
  }
  d.iv=input_held;d.fence=sent==nodes.size()*10;d.mem_ready=pending.size()<64&&rng()%5!=0;d.ordy=rng()%4!=0&&(tick%200)<165;
  if(response<0)for(int i=int(pending.size())-1;i>=0;--i)if(pending[i].due<=tick){response=i;break;}
  d.rsp_valid=response>=0;if(response>=0){auto &p=pending[response];d.rsp_id=p.id;for(unsigned s=0;s<4;++s){d.rsp_data[2*s]=p.data[s];d.rsp_data[2*s+1]=p.data[s]>>32;}}
  d.eval();
  if(held){if(!d.mem_valid||d.mem_line!=held_line||d.mem_id!=held_id||d.mem_write!=held_write)throw std::runtime_error("command instability");for(unsigned s=0;s<4;++s)if((uint64_t(d.mem_data[2*s+1])<<32|d.mem_data[2*s])!=held_payload[s])throw std::runtime_error("payload instability");}
  held=d.mem_valid&&!d.mem_ready;if(held){held_line=d.mem_line;held_id=d.mem_id;held_write=d.mem_write;for(unsigned s=0;s<4;++s)held_payload[s]=uint64_t(d.mem_data[2*s+1])<<32|d.mem_data[2*s];}
  if(d.iv&&d.ir){auto &e=scoreboard[input_tag];if(e.live)throw std::runtime_error("client tag reuse");e.live=true;e.node=d.node;e.old=ref[d.node];auto &v=ref[d.node];e.status=0;
   switch(d.opcode){case 0:e.status=1;break;case 1:e.status=!(v.flags&1);v.flags|=1;break;case 2:if((v.pending>>28&1)&&((v.pending&0xfffffff)==(d.argument&0xfffffff))){v.pending=0;e.status=1;}break;case 3:if(d.operand>=v.label)throw std::runtime_error("test nonimprovement");v.label=d.operand;if(!(v.pending>>28&1)||(v.pending&4095)!=(d.operand>>52)){v.pending=(1u<<28)|((((v.pending>>12)+1)&65535)<<12)|(d.operand>>52);e.status=1;}break;case 4:e.status=v.flags&1;v.flags&=~1u;break;default:throw std::runtime_error("test opcode");}
   ++sent;input_held=false;
  }
  if(d.ov&&d.ordy){auto &e=scoreboard[d.otag];Record actual{uint64_t(d.old_record[1])<<32|d.old_record[0],d.old_record[2],d.old_record[3]};if(!e.live||e.node!=d.onode||e.status!=d.status||actual.label!=e.old.label||actual.pending!=e.old.pending||actual.flags!=e.old.flags)throw std::runtime_error("node response mismatch tag="+std::to_string(d.otag)+" node="+std::to_string(d.onode)+" returned="+std::to_string(returned));e.live=false;++returned;}
  bool pop=response>=0&&d.rsp_ready;if(pop){auto &p=pending[response];if(p.wr)memory[p.line]=p.data;}
  if(d.mem_valid&&d.mem_ready){if(d.mem_line>=N/2)throw std::runtime_error("finite backing range");for(auto &p:pending)if(p.id==d.mem_id)throw std::runtime_error("physical ID reuse");Line data=memory[d.mem_line];if(d.mem_write){++writes;for(unsigned s=0;s<4;++s)data[s]=uint64_t(d.mem_data[2*s+1])<<32|d.mem_data[2*s];}else{++reads;for(unsigned i=0;i<pending.size();++i)if(pending[i].wr&&pending[i].line==d.mem_line&&!(pop&&int(i)==response))throw std::runtime_error("unacknowledged dirty RAW");}
   pending.push_back({bool(d.mem_write),d.mem_line,d.mem_id,data,tick+120+rng()%80});
  }
  if(pop){pending.erase(pending.begin()+response);response=-1;}peak=std::max<unsigned>(peak,pending.size());
  log<<tick<<','<<sent<<','<<returned<<','<<d.retired<<','<<reads<<','<<writes<<','<<pending.size()<<','<<unsigned(d.mshr_peak)<<','<<unsigned(d.dirty_peak)<<'\n';
  d.clk=1;d.eval();++tick;if(d.error)throw std::runtime_error("DUT error");if(d.fence_done){if(!pending.empty()||sent!=returned||d.accepted!=d.retired)throw std::runtime_error("early fence");success=true;break;}
 }
 if(!success)throw std::runtime_error("watchdog");
 for(unsigned line=0;line<N/2;++line)for(unsigned sector=0;sector<2;++sector){unsigned n=((line>>(STATE_B+1))<<(STATE_B+2))|((line&((1u<<STATE_B)-1))<<2)|(((line>>STATE_B)&1)<<1)|sector;auto &v=ref[n];if(memory[line][2*sector]!=v.label||memory[line][2*sector+1]!=(uint64_t(v.flags)<<32|v.pending))throw std::runtime_error("full backing mismatch node="+std::to_string(n));}
 if(reads<1000||writes<1000||d.mshr_peak<2||peak<2)throw std::runtime_error("working set/concurrency not exercised");
 std::cout<<"NODE_STATE_PASS address_nodes="<<N<<" highest_node="<<N-1<<" operations="<<returned<<" cycles="<<tick<<" reads="<<reads<<" writes="<<writes<<" mshr="<<unsigned(d.mshr_peak)<<" dirty="<<unsigned(d.dirty_peak)<<" outstanding="<<peak<<'\n';
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
