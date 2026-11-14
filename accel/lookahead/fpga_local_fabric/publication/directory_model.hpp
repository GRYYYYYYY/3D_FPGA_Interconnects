#pragma once
#include "../../fpga_descriptor_front/services/directory_model.hpp"
#include "../../fpga_descriptor_front/services/transport_model.hpp"
namespace lf {
using dfservice::DirCommand;using dfservice::DirResponse;
struct DirectoryPipeline {
 static constexpr unsigned NIL=8192,CAP=8192;
 using Heads=dfservice::DirectoryBank::Heads;using Member=dfservice::DirectoryBank::Member;
 std::array<Heads,4096>heads{};std::array<Member,8192>members{};std::array<unsigned,8192>free{};std::array<uint64_t,64>bitmap{};
 struct Stage{DirCommand c;Heads read_heads,new_heads;uint64_t read_bits=0,new_bits=0;unsigned ptr=0,oldtail=NIL;};
 std::array<std::optional<Stage>,4>pipe{};dfservice::Queue<DirResponse,8>responses;
 enum{INIT,IDLE,READ,CAPTURE,DONE};unsigned state=INIT,init=0,used=0,peak=0,reservations=0;uint64_t upper=0;bool cooldown=false,last_valid=false;
 unsigned last_bucket=0;Heads last_heads;uint64_t last_bits=0;
 DirCommand cmd;Heads hr;Member mr;uint64_t br=0;unsigned group=0;
 bool initialized()const{return state!=INIT;}
 bool empty()const{return upper==0;}
 bool pipe_empty()const{for(auto&x:pipe)if(x)return false;return true;}
 bool ready()const{return state==IDLE&&pipe_empty()&&reservations==0;}
 bool append_ready()const{return state==IDLE&&!cooldown&&used<CAP&&reservations<8;}
 const DirResponse*response()const{return responses.empty()?nullptr:&responses.front();}
 void tick(std::optional<DirCommand> input={},bool rr=false){
  const bool fire=input&&(input->op==0?append_ready():ready());
  const bool take=rr&&!responses.empty();const unsigned oldused=used;
  if(state==INIT){free[init]=init;if(init<4096)heads[init]={};if(init<64)bitmap[init]=0;if(++init==8192)state=IDLE;return;}
  // Reads occur at acceptance BEFORE concurrent write commits (read-first).
  std::optional<Stage> incoming;
  if(fire&&input->op==0){Stage x;x.c=*input;x.read_heads=heads[x.c.bucket];x.read_bits=bitmap[x.c.bucket/64];x.ptr=free[8191-used];incoming=x;}
  std::optional<DirResponse> response_in;
  if(pipe[3]){auto&x=*pipe[3];response_in=DirResponse{0,0,x.c.bucket,0,0,x.ptr,NIL};}
  std::optional<Stage> decoded;
  if(pipe[0]){auto x=*pipe[0];Heads h=last_valid&&last_bucket==x.c.bucket?last_heads:x.read_heads;uint64_t bits=last_valid&&last_bucket/64==x.c.bucket/64?last_bits:x.read_bits;
   x.new_heads={h.head==NIL?x.ptr:h.head,x.ptr};x.new_bits=bits|(uint64_t(1)<<(x.c.bucket%64));x.oldtail=h.tail;decoded=x;}
  if(pipe[2]){auto&x=*pipe[2];if(x.oldtail!=NIL)members[x.oldtail].next=x.ptr;}
  if(pipe[1]){auto&x=*pipe[1];heads[x.c.bucket]=x.new_heads;members[x.ptr]={x.c.node,x.c.arg,NIL};bitmap[x.c.bucket/64]=x.new_bits;upper|=uint64_t(1)<<(x.c.bucket/64);last_valid=true;last_bucket=x.c.bucket;last_heads=x.new_heads;last_bits=x.new_bits;}
  switch(state){
   case IDLE:if(fire&&input->op!=0){cmd=*input;group=cmd.op==3?dfservice::DirectoryBank::first(upper):cmd.bucket/64;
    hr=heads[cmd.bucket];br=bitmap[group];if(cmd.ptr<CAP)mr=members[cmd.ptr];last_valid=false;state=READ;}break;
   case READ:if(cmd.op==3){response_in=DirResponse{3,upper?0u:1u,group*64+dfservice::DirectoryBank::first(br),0,0,NIL,NIL};state=DONE;}else state=CAPTURE;break;
   case CAPTURE:if(cmd.op==1){heads[cmd.bucket]={};bitmap[group]=br&~(uint64_t(1)<<(cmd.bucket%64));if(!bitmap[group])upper&=~(uint64_t(1)<<group);response_in=DirResponse{1,0,cmd.bucket,0,0,hr.head,NIL};}
    else{bool good=cmd.ptr<CAP&&used;response_in=DirResponse{2,good?0u:2u,cmd.bucket,mr.node,mr.arg,cmd.ptr,mr.next};if(good){free[CAP-used]=cmd.ptr;--used;}}state=DONE;break;
   case DONE:if(take)state=IDLE;break;
  }
  pipe[3]=pipe[2];pipe[2]=pipe[1];pipe[1]=decoded;pipe[0]=incoming;
  if(incoming){used=oldused+1;peak=std::max(peak,used);}cooldown=incoming.has_value();
  if(response_in&&responses.full())throw std::runtime_error("RESERVED_DIRECTORY_RESPONSE_OVERFLOW");
  responses.tick(response_in,take);reservations+=unsigned(fire);reservations-=unsigned(take);
 }
};
// Baseline serialized bank is unchanged; pipeline selected explicitly by config.
struct DirectoryUnit {
 bool pipelined=false;dfservice::DirectoryBank old;DirectoryPipeline pipe;
 unsigned used=0,peak=0;
 bool ready()const{return pipelined?pipe.ready():old.ready();}
 bool append_ready()const{return pipelined?pipe.append_ready():old.ready();}
 bool initialized()const{return pipelined?pipe.initialized():old.initialized();}
 bool empty()const{return pipelined?pipe.empty():old.empty();}
 const DirResponse*response()const{return pipelined?pipe.response():old.response();}
 void tick(std::optional<DirCommand>c={},bool rr=false){if(pipelined){pipe.tick(c,rr);used=pipe.used;peak=pipe.peak;}else{old.tick(c,rr);used=old.used;peak=old.peak;}}
};
}
