#pragma once
#include "owner_model.hpp"
// New independent C++ cycle state machine. Only the synchronous FIFO primitive
// and plain payload types are reused; no R1 service-rate/calibration is inherited.
namespace r2_model {
using sparse_model::Fifo;using sparse_model::Candidate;using sparse_model::Response;using sparse_model::Line;using sparse_model::INF;
struct OwnerCycle {
 bool clk=false,rst=false,iv=false,ir=false,fence=false,fence_done=false,update_valid=false,update_ready=false;
 bool mem_valid=false,mem_ready=false,mem_write=false,rsp_valid=false,rsp_ready=false,idle=false,error=false;
 uint32_t node=0,update_line=0,mem_line=0;uint64_t pair=0;unsigned update_mask=0,mem_id=0,rsp_id=0;
 std::array<uint32_t,8> mem_data{},rsp_data{};
 uint32_t accepted=0,retired=0,merges=0,hits=0,misses=0,raw_stall=0;unsigned mshr_peak=0,dirty_peak=0,owner_bits=3;
 struct Cache {bool valid=false,dirty=false,busy=false;uint32_t tag=0;Line data{};};
 struct Miss {bool valid=false,sent=false,go=false;uint32_t line=0,count=0;unsigned slot=0;Line candidates{INF,INF,INF,INF};};
 struct Write {bool valid=false,sent=false,ready=false;uint32_t line=0;Line data{};};
 struct Event {uint32_t line=0;unsigned mask=0;};
 struct Stage {bool valid=false,eviction=false,dirty=false;unsigned slot=0,miss=0,write=0;Candidate cand{};uint32_t line=0,evict_line=0;};
 struct Core {std::array<Cache,128> cache{};std::array<Miss,32> misses{};std::array<Write,16> writes{};std::array<unsigned,32> replacement{};
  Fifo<Candidate> requests;Fifo<Response> responses;Fifo<Event> events;Stage stage;Line ram_q{},last_data{};bool last_valid=false,flushing=false,turn=false;unsigned last_slot=0,flush_index=0;
 } c;
 struct Wires {int hit=-1,matching=-1,fm=-1,fw=-1,victim=-1,im=-1,iw=-1;unsigned cm=0,cw=0,hitmask=0,fillmask=0;Line base{},hitdata{},filldata{};bool advance=false,fillwait=false,filltake=false,qr=false,rr=false,dispatch=false,hitdispatch=false,missdispatch=false,flushdispatch=false,eventready=false;} w;
 bool last_clk=false;
 static Line unpack(const std::array<uint32_t,8>& a){Line l{};for(unsigned i=0;i<4;++i)l[i]=uint64_t(a[2*i+1])<<32|a[2*i];return l;}
 void command(bool wr,uint32_t line,unsigned id,const Line& data){mem_valid=true;mem_write=wr;mem_line=line;mem_id=id;for(unsigned i=0;i<4;++i){mem_data[2*i]=data[i];mem_data[2*i+1]=data[i]>>32;}}
 void combin(){
  w=Wires{};auto q=c.requests.od;uint32_t line=q.node>>2;
  for(unsigned i=0;i<32;++i){auto &m=c.misses[i];if(m.valid){++w.cm;if(m.line==line)w.matching=i;}else if(w.fm<0)w.fm=i;bool hazard=false;for(auto &b:c.writes)hazard|=b.valid&&b.line==m.line;if(m.valid&&m.go&&!m.sent&&!hazard&&w.im<0)w.im=i;}
  for(unsigned i=0;i<16;++i){auto &b=c.writes[i];if(b.valid)++w.cw;else if(w.fw<0)w.fw=i;if(b.valid&&b.ready&&!b.sent&&w.iw<0)w.iw=i;}
  unsigned set=(line>>owner_bits)&31;
  for(unsigned k=0;k<4;++k){unsigned s=k*32+set;auto &a=c.cache[s];if(a.valid&&!a.busy&&a.tag==line)w.hit=s;if(!a.valid&&!a.busy&&!(c.stage.valid&&c.stage.slot==s)&&w.victim<0)w.victim=s;}
  if(w.victim<0)for(unsigned k=0;k<4;++k){unsigned s=((c.replacement[set]+k)%4)*32+set;if(!c.cache[s].busy&&!(c.stage.valid&&c.stage.slot==s)&&w.victim<0)w.victim=s;}
  auto s=c.stage;w.base=c.last_valid&&c.last_slot==s.slot?c.last_data:c.ram_q;w.hitdata=w.base;
  if(s.cand.pair<w.base[s.cand.node&3]){w.hitdata[s.cand.node&3]=s.cand.pair;w.hitmask=1u<<(s.cand.node&3);}
  auto response=c.responses.od;w.filldata=response.data;auto &miss=c.misses[response.id&31];
  for(unsigned i=0;i<4;++i)if(miss.candidates[i]<response.data[i]){w.filldata[i]=miss.candidates[i];w.fillmask|=1u<<i;}
  w.eventready=c.events.ready(update_ready);w.advance=!s.valid||s.eviction||!w.hitmask||w.eventready;
  w.fillwait=c.responses.ov&&response.id<32;w.filltake=w.fillwait&&!s.valid&&(!w.fillmask||w.eventready);
  w.rr=response.id>=32||(!s.valid&&(!w.fillmask||w.eventready));
  w.qr=!c.flushing&&!w.fillwait&&w.advance&&(w.matching>=0||w.hit>=0||(w.fm>=0&&w.victim>=0&&(!c.cache[w.victim].dirty||w.fw>=0)));
  w.dispatch=c.requests.ov&&w.qr;w.hitdispatch=w.dispatch&&w.matching<0&&w.hit>=0;w.missdispatch=w.dispatch&&w.matching<0&&w.hit<0;
  w.flushdispatch=c.flushing&&c.flush_index<128&&c.cache[c.flush_index].dirty&&w.advance&&w.fw>=0;
  ir=c.requests.ready(w.qr)&&!fence;rsp_ready=c.responses.ready(w.rr);
  update_valid=c.events.ov;update_line=c.events.od.line;update_mask=c.events.od.mask;
  idle=!s.valid&&!c.flushing&&!c.requests.count&&!c.requests.ov&&!c.responses.count&&!c.responses.ov&&!w.cm&&!w.cw&&!mem_valid&&!c.events.count&&!c.events.ov;
 }
 void eval(){if(clk&&!last_clk)step();last_clk=clk;combin();}
 void step(){
  if(rst){c=Core{};mem_valid=fence_done=error=false;accepted=retired=merges=hits=misses=raw_stall=0;mshr_peak=dirty_peak=0;return;}
  const bool old_mem_valid=mem_valid;const Core old=c;const auto z=w;const bool old_idle=idle;auto &n=c;auto s=old.stage;auto q=old.requests.od;auto response=old.responses.od;
  bool hitwrite=s.valid&&!s.eviction&&z.advance&&z.hitmask;
  bool event_v=hitwrite||(z.filltake&&z.fillmask);Event event=z.filltake?Event{old.misses[response.id&31].line,z.fillmask}:Event{s.line,z.hitmask};
  n.requests.step(iv&&!fence,{node,pair},z.qr);n.responses.step(rsp_valid,{rsp_id,unpack(rsp_data)},z.rr);n.events.step(event_v,event,update_ready);
  if(iv&&ir)++accepted;if(old.requests.ov&&!z.qr)++raw_stall;mshr_peak=std::max(mshr_peak,z.cm);dirty_peak=std::max(dirty_peak,z.cw);
  if(z.hitdispatch||z.missdispatch||z.flushdispatch){unsigned addr=z.flushdispatch?old.flush_index:z.hitdispatch?z.hit:z.victim;n.ram_q=old.cache[addr].data;}
  if(hitwrite||z.filltake){unsigned slot=z.filltake?old.misses[response.id&31].slot:s.slot;auto data=z.filltake?z.filldata:z.hitdata;n.cache[slot].data=data;n.last_valid=true;n.last_slot=slot;n.last_data=data;}
  if(!mem_valid||mem_ready){mem_valid=false;if(z.iw>=0&&(z.im<0||!old.turn)){auto b=old.writes[z.iw];command(true,b.line,32+z.iw,b.data);n.writes[z.iw].sent=true;n.turn=true;}else if(z.im>=0){command(false,old.misses[z.im].line,z.im,{});n.misses[z.im].sent=true;n.turn=false;}}
  if(old.responses.ov&&z.rr&&response.id>=32){unsigned i=response.id-32;if(i>=16||!old.writes[i].valid||!old.writes[i].sent)error=true;else{n.writes[i].valid=n.writes[i].sent=n.writes[i].ready=false;}}
  if(z.filltake){unsigned i=response.id;auto m=old.misses[i];if(!m.valid||!m.sent)error=true;n.cache[m.slot].valid=true;n.cache[m.slot].busy=false;n.cache[m.slot].dirty=z.fillmask!=0;n.misses[i].valid=n.misses[i].sent=n.misses[i].go=false;retired+=m.count;}
  if(z.advance){
   n.stage.valid=false;
   if(s.valid){if(!s.eviction){++retired;if(z.hitmask)n.cache[s.slot].dirty=true;}else{if(s.dirty){n.writes[s.write].data=z.base;n.writes[s.write].ready=true;}if(!old.flushing)n.misses[s.miss].go=true;}}
   if(z.hitdispatch){n.stage.valid=true;n.stage.eviction=false;n.stage.slot=z.hit;n.stage.cand=q;n.stage.line=q.node>>2;++hits;}
   if(z.missdispatch){
    auto v=old.cache[z.victim];auto &st=n.stage;st.valid=true;st.eviction=true;st.slot=z.victim;st.dirty=v.dirty;st.evict_line=v.tag;st.miss=z.fm;
    if(v.dirty){st.write=z.fw;n.writes[z.fw].valid=true;n.writes[z.fw].sent=n.writes[z.fw].ready=false;n.writes[z.fw].line=v.tag;}
    auto &m=n.misses[z.fm];m.valid=true;m.sent=m.go=false;m.line=q.node>>2;m.slot=z.victim;m.count=1;m.candidates.fill(INF);m.candidates[q.node&3]=q.pair;
    n.cache[z.victim].valid=n.cache[z.victim].dirty=false;n.cache[z.victim].busy=true;n.cache[z.victim].tag=q.node>>2;n.replacement[(q.node>>(owner_bits+2))&31]=((unsigned(z.victim)>>5)+1)&3;++misses;
   }
   if(z.flushdispatch){auto &st=n.stage;st.write=z.fw;n.writes[z.fw].valid=true;n.writes[z.fw].sent=n.writes[z.fw].ready=false;n.writes[z.fw].line=old.cache[old.flush_index].tag;st.valid=true;st.eviction=true;st.slot=old.flush_index;st.dirty=true;st.evict_line=old.cache[old.flush_index].tag;n.cache[old.flush_index].dirty=false;n.flush_index=old.flush_index+1;}
  }
  if(z.dispatch&&z.matching>=0){auto &m=n.misses[z.matching];m.candidates[q.node&3]=std::min(m.candidates[q.node&3],q.pair);++m.count;++merges;}
  if(!fence)fence_done=false;
  if(fence&&!fence_done&&!old.flushing&&old_idle){n.flushing=true;n.flush_index=0;}
  if(old.flushing&&old.flush_index<128&&!old.cache[old.flush_index].dirty)n.flush_index=old.flush_index+1;
  // mem_valid is a register: use its PRE-edge value at the fence boundary.
  if(old.flushing&&old.flush_index==128&&!s.valid&&!z.cw&&!old.responses.count&&!old.responses.ov&&!old.events.count&&!old.events.ov&&!old_mem_valid){n.flushing=false;fence_done=true;}
 }
};
}
