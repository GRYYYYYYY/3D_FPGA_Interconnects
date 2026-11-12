#pragma once
#include "../fpga_sparse_stream/owner_model.hpp"
namespace r2_model {
using sparse_model::Line;using sparse_model::Fifo;using sparse_model::Candidate;using sparse_model::Response;
struct OwnerF0Cycle:sparse_model::OwnerModel{
 unsigned owner_bits=3; // Global line addresses; no cache indexing in F0.
 struct Miss{bool valid=false,sent=false,ready=false;uint32_t node=0;uint64_t candidate=0;Line data{};};
 struct Write{bool valid=false,sent=false;unsigned miss=0;Line data{};};
 struct Core{std::array<Miss,32> miss{};std::array<Write,16> write{};sparse_model::RequestFifo<Candidate> requests;Fifo<Response> responses;unsigned state=0,selected=0;Line fill_q{};} c;
 void combin(){bool collision=false;int fm=-1;for(unsigned i=0;i<32;++i){auto m=c.miss[i];collision|=m.valid&&m.node/4==c.requests.od.node/4;if(!m.valid&&fm<0)fm=i;}bool qr=c.state==0&&!c.responses.ov&&!update_valid&&fm>=0&&!collision;ir=c.requests.ready(qr)&&!fence;rsp_ready=c.responses.ready(c.state==0&&!update_valid);bool pending=false;for(auto m:c.miss)pending|=m.valid;for(auto w:c.write)pending|=w.valid;idle=c.state==0&&!c.requests.count&&!c.requests.ov&&!c.responses.count&&!c.responses.ov&&!pending&&!mem_valid&&!update_valid;}
 void eval(){if(clk&&!last_clk)step();last_clk=clk;combin();}
 void step(){
  if(rst){c=Core{};mem_valid=update_valid=fence_done=error=false;accepted=retired=merges=hits=misses=raw_stall=0;mshr_peak=dirty_peak=0;return;}
  // FIFO payload arrays are not copied each clock. Snapshot only the old
  // head values/valid bits; the miss/write arrays remain unchanged until the
  // corresponding decisions below have consumed their old values.
  auto &n=c;const auto q=c.requests.od;const auto r=c.responses.od;
  const bool qv=c.requests.ov,rv=c.responses.ov;
  const unsigned state=c.state,selected=c.selected;const Line fill=c.fill_q;
  int fm=-1,fw=-1,fetch=-1,write_cmd=-1,apply=-1;unsigned mc=0,wc=0;bool collision=false;
  for(unsigned i=0;i<32;++i){auto m=c.miss[i];if(m.valid){++mc;collision|=m.node/4==q.node/4;}else if(fm<0)fm=i;if(m.valid&&!m.sent&&fetch<0)fetch=i;if(m.valid&&m.ready&&apply<0)apply=i;}
  for(unsigned i=0;i<16;++i){auto w=c.write[i];if(w.valid)++wc;else if(fw<0)fw=i;if(w.valid&&!w.sent&&write_cmd<0)write_cmd=i;}
  bool event=update_valid,qr=state==0&&!rv&&!event&&fm>=0&&!collision,rr=state==0&&!event;
  n.requests.step(iv&&!fence,{node,pair},qr);n.responses.step(rsp_valid,{rsp_id,from(rsp_data)},rr);
  if(iv&&ir)++accepted;mshr_peak=std::max(mshr_peak,mc);dirty_peak=std::max(dirty_peak,wc);if(event&&update_ready)update_valid=false;
  if(!mem_valid||mem_ready){mem_valid=false;if(write_cmd>=0){auto w=c.write[write_cmd];command(true,c.miss[w.miss].node/4,32+write_cmd,w.data);n.write[write_cmd].sent=true;}else if(fetch>=0){command(false,c.miss[fetch].node/4,fetch,{});n.miss[fetch].sent=true;}}
  if(!fence)fence_done=false;else if(idle)fence_done=true;
  if(state==1)n.fill_q=c.miss[selected].data;
  switch(state){
  case 0:
   if(rv&&rr){
    if(r.id>=32){unsigned w=r.id-32;if(w>=16||!c.write[w].valid)error=true;else{unsigned m=c.write[w].miss;update_valid=true;update_line=c.miss[m].node/4;update_mask=1u<<(c.miss[m].node&3);n.miss[m].valid=n.miss[m].sent=false;n.write[w].valid=n.write[w].sent=false;++retired;}}
    else{n.miss[r.id].data=r.data;if(!c.miss[r.id].valid)error=true;else n.miss[r.id].ready=true;}
   }else if(qv&&qr){n.miss[fm]={true,false,false,q.node,q.pair,{}};++misses;}
   else if(apply>=0&&fw>=0&&!event){n.selected=apply;n.miss[apply].ready=false;n.state=1;}
   if(qv&&collision)++raw_stall;
   break;
  case 1:n.state=2;break;
  case 2:{auto m=c.miss[selected];if(m.candidate<fill[m.node&3]){n.write[fw]={true,false,selected,fill};n.write[fw].data[m.node&3]=m.candidate;}else{n.miss[selected].valid=n.miss[selected].sent=false;++retired;}n.state=0;}break;
  default:error=true;
  }
 }
};
}
