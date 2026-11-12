#include "Vsparse_bank_pipe.h"
#include "verilated.h"
#include <array>
#include <vector>
#include <set>
#include <random>
#include <fstream>
#include <iostream>
#include <stdexcept>
using Line=std::array<uint64_t,4>;
struct Pending{unsigned line,id;bool wr;Line data;uint64_t due;};
int main(int argc,char**argv){try{
 Verilated::commandArgs(argc,argv);Vsparse_bank_pipe d;std::array<Line,1024> memory{};std::vector<Pending> pending;int response=-1;uint64_t cycle=0;std::mt19937 rng(20261112);std::ofstream log(argv[1]);log<<"cycle,command,issued,ack,pop,outstanding\n";
 d.rst=1;d.command=0;d.source=0;d.cv=0;d.pr=1;d.close_ready=1;d.mem_ready=0;d.rsp_valid=0;
 auto clock=[&](){d.clk=0;d.eval();d.clk=1;d.eval();++cycle;};clock();clock();d.rst=0;
 auto global=[](unsigned idx){return ((idx>>2)<<5)|(idx&3);};
 unsigned maxstreak=0,streak=0,total_ack=0,total_pop=0,total_stale=0;
 auto run=[&](unsigned op,unsigned key,unsigned limit,uint64_t value,std::set<unsigned> expected_pop){
  d.command=op;d.bucket=key;std::set<unsigned> acked,popped;unsigned sent=0;bool done=false;
  if(op==3)for(unsigned i=1;i<=limit;++i){unsigned n=global(i);memory[n/4][n%4]=value;}
  for(unsigned step=0;step<100000;++step){
   d.clk=0;d.cv=op==3&&sent<limit;d.ci=sent+1;d.pr=rng()%5!=0;d.mem_ready=pending.size()<64;
   if(response<0)for(int i=int(pending.size())-1;i>=0;--i)if(pending[i].due<=cycle){response=i;break;}
   d.rsp_valid=response>=0;if(response>=0){auto &p=pending[response];d.rsp_id=p.id;for(unsigned s=0;s<4;++s){d.rsp_data[2*s]=p.data[s];d.rsp_data[2*s+1]=p.data[s]>>32;}}
   d.eval();bool issue=d.cv&&d.issue_ready;if(issue)++sent;
   if(d.ca){if(!acked.insert(d.commit_index).second||d.commit_index==0||d.commit_index>limit)throw std::runtime_error("commit ACK duplicate/wrong ID");++streak;++total_ack;maxstreak=std::max(maxstreak,streak);}else streak=0;
   if(d.pv&&d.pr){if(!popped.insert(d.pn).second)throw std::runtime_error("duplicate POP");if(d.pp!=memory[d.pn/4][d.pn%4])throw std::runtime_error("POP pair != committed proposal");++total_pop;}
   if(response>=0){auto &p=pending[response];if(p.wr)memory[p.line]=p.data;}
   if(d.mem_valid&&d.mem_ready){if(d.mem_line>=1024)throw std::runtime_error("bounded memory");for(auto &p:pending)if(p.id==d.mem_id)throw std::runtime_error("duplicate ID");Line data=memory[d.mem_line];if(d.mem_write)for(unsigned s=0;s<4;++s)data[s]=uint64_t(d.mem_data[2*s+1])<<32|d.mem_data[2*s];pending.push_back({d.mem_line,d.mem_id,bool(d.mem_write),data,cycle+4+(op==3?0:rng()%13)});}
   if(response>=0){pending.erase(pending.begin()+response);response=-1;}
   log<<cycle<<','<<op<<','<<issue<<','<<unsigned(d.ca)<<','<<unsigned(d.pv&&d.pr)<<','<<pending.size()<<'\n';
   d.clk=1;d.eval();++cycle;if(d.error)throw std::runtime_error("bank error op="+std::to_string(op));
   if(d.done){if(!pending.empty())throw std::runtime_error("done before ACK drain");done=true;break;}
  }
  if(!done)throw std::runtime_error("watchdog");if(op==3&&acked.size()!=limit)throw std::runtime_error("missing commit ACK");if(op==2&&popped!=expected_pop)throw std::runtime_error("POP membership mismatch");
  d.command=0;d.cv=0;d.rsp_valid=0;clock();clock();
 };
 run(1,0,0,0,{});run(2,0,0,0,{0});
 run(3,0,511,0x3f80000040000000ull,{});unsigned peak=d.member_peak;
 run(3,0,511,0x3f8000003f800000ull,{});if(d.member_peak!=peak)throw std::runtime_error("same-bucket congestion duplicated membership");
 run(3,0,16,0x3f0000003f800000ull,{});run(5,0,0,0,{});if(!d.has_bucket||d.min_bucket!=0x3f0)throw std::runtime_error("minimum lower bucket");
 std::set<unsigned> lower,upper;for(unsigned i=1;i<=511;++i)(i<=16?lower:upper).insert(global(i));
 run(2,0x3f0,0,0,lower);run(5,0,0,0,{});if(d.min_bucket!=0x3f8)throw std::runtime_error("minimum upper bucket");run(2,0x3f8,0,0,upper);
 run(5,0,0,0,{});if(d.has_bucket||d.stale_count!=16)throw std::runtime_error("stale filter/empty snapshot");
 if(maxstreak<64)throw std::runtime_error("commit pipeline II1 not sustained");
 std::cout<<"BANK_PIPE_PASS cycles="<<cycle<<" commits="<<total_ack<<" pops="<<total_pop<<" stale="<<d.stale_count<<" max_commit_streak="<<maxstreak<<" member_peak="<<d.member_peak<<'\n';
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
