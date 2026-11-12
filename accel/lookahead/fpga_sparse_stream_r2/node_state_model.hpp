#pragma once
#include "../fpga_sparse_stream/owner_model.hpp"
// New independent C++ cycle state machine. Only the synchronous FIFO primitive
// and plain payload types are reused; no R1 service-rate/calibration is inherited.
namespace r2_model {
using sparse_model::Fifo;using sparse_model::Candidate;using sparse_model::Response;using sparse_model::Line;using sparse_model::INF;
struct NodeStateCycle {
 bool clk=false,rst=false,iv=false,ir=false,fence=false,fence_done=false,ov=false,ordy=false;
 bool mem_valid=false,mem_ready=false,mem_write=false,rsp_valid=false,rsp_ready=false,idle=false,error=false;
 uint32_t node=0,onode=0,mem_line=0,state_base=0,node_count=0,argument=0;uint64_t operand=0;unsigned opcode=0,tag=0,otag=0,status=0,mem_id=0,rsp_id=0,owner_bits=3;
 std::array<uint32_t,4> old_record{};
 struct Request{uint32_t node=0;unsigned op=0;uint64_t value=0;uint32_t arg=0;unsigned tag=0;};
 struct Record{uint64_t label=0,meta=0;};
 struct Applied{Record old{},value{};unsigned status=0;bool changed=false;};
 uint32_t address(uint32_t n)const{return state_base+((((n>>(owner_bits+2))*2)+((n>>1)&1))<<owner_bits)+((n>>2)&((1u<<owner_bits)-1));}
 static Applied apply(const Request&r,const Line& l){
  Applied a;unsigned off=(r.node&1)*2;a.old=a.value={l[off],l[off+1]};uint32_t p=a.old.meta;unsigned version=((p>>12)+1)&65535;
  switch(r.op){
   case 0:a.status=1;break;
   case 1:a.status=!(a.old.meta>>32&1);a.value.meta|=1ull<<32;break;
   case 2:if((p>>28&1)&&(p&0xfffffff)==(r.arg&0xfffffff)){a.value.meta&=0xffffffff00000000ull;a.status=1;}break;
   case 3:if(r.value>=a.old.label)a.status=8;else{a.value.label=r.value;if(!(p>>28&1)||(p&4095)!=(r.value>>52)){a.value.meta=(a.old.meta&0xffffffff00000000ull)|(1u<<28)|(version<<12)|(r.value>>52);a.status=1;}}break;
   case 4:a.status=a.old.meta>>32&1;a.value.meta&=~(1ull<<32);break;
   case 5:a.value.label=0;a.value.meta=(a.old.meta&0xffffffff00000000ull)|0x10001000u;a.status=1;break;
   default:a.status=8;
  }
  a.changed=a.value.label!=a.old.label||a.value.meta!=a.old.meta;return a;
 }
 std::array<uint32_t,8> mem_data{},rsp_data{};
 uint32_t accepted=0,retired=0,merges=0,hits=0,misses=0,raw_stall=0;unsigned mshr_peak=0,dirty_peak=0;
 struct Cache {bool valid=false,dirty=false,busy=false;uint32_t tag=0;Line data{};};
 struct Miss {bool valid=false,sent=false,go=false;uint32_t line=0;unsigned slot=0;Request request{};};
 struct Write {bool valid=false,sent=false,ready=false;uint32_t line=0;Line data{};};
 struct Event {uint32_t node=0;unsigned tag=0,status=0;Record old{};};
 struct Stage {bool valid=false,eviction=false,dirty=false;unsigned slot=0,miss=0,write=0;Request cand{};uint32_t line=0,evict_line=0;};
 struct Core {std::array<Cache,128> cache{};std::array<Miss,32> misses{};std::array<Write,16> writes{};std::array<unsigned,32> replacement{};
  sparse_model::RequestFifo<Request> requests;Fifo<Response> responses;Fifo<Event> events;Stage stage;Line ram_q{},last_data{};bool last_valid=false,flushing=false,turn=false;unsigned last_slot=0,flush_index=0;
 } c;
 struct Wires {int hit=-1,matching=-1,fm=-1,fw=-1,victim=-1,im=-1,iw=-1;unsigned cm=0,cw=0;Applied hr{},fr{};Line base{},hitdata{},filldata{};bool advance=false,fillwait=false,filltake=false,qr=false,rr=false,dispatch=false,hitdispatch=false,missdispatch=false,flushdispatch=false,eventready=false;} w;
 bool last_clk=false,quiet_cached=false;
 static Line unpack(const std::array<uint32_t,8>& a){Line l{};for(unsigned i=0;i<4;++i)l[i]=uint64_t(a[2*i+1])<<32|a[2*i];return l;}
 void command(bool wr,uint32_t line,unsigned id,const Line& data){mem_valid=true;mem_write=wr;mem_line=line;mem_id=id;for(unsigned i=0;i<4;++i){mem_data[2*i]=data[i];mem_data[2*i+1]=data[i]>>32;}}
 void combin(){
#ifdef R2_IDLE_CACHE
  // Empty service has no in-flight timer or work. Cached combinational wires
  // remain valid until a request/response, reset, or fence changes the state.
  if(quiet_cached&&!rst&&!fence&&!fence_done)return;
#endif
  w=Wires{};auto q=c.requests.od;uint32_t line=address(q.node);
  for(unsigned i=0;i<32;++i){auto &m=c.misses[i];if(m.valid){++w.cm;if(m.line==line)w.matching=i;}else if(w.fm<0)w.fm=i;if(m.valid&&m.go&&!m.sent&&w.im<0){bool hazard=false;for(auto &b:c.writes)if(b.valid&&b.line==m.line){hazard=true;break;}if(!hazard)w.im=i;}}
  for(unsigned i=0;i<16;++i){auto &b=c.writes[i];if(b.valid)++w.cw;else if(w.fw<0)w.fw=i;if(b.valid&&b.ready&&!b.sent&&w.iw<0)w.iw=i;}
  unsigned set=(line>>owner_bits)&31;
  for(unsigned k=0;k<4;++k){unsigned s=k*32+set;auto &a=c.cache[s];if(a.valid&&!a.busy&&a.tag==line)w.hit=s;if(!a.valid&&!a.busy&&!(c.stage.valid&&c.stage.slot==s)&&w.victim<0)w.victim=s;}
  if(w.victim<0)for(unsigned k=0;k<4;++k){unsigned s=((c.replacement[set]+k)%4)*32+set;if(!c.cache[s].busy&&!(c.stage.valid&&c.stage.slot==s)&&w.victim<0)w.victim=s;}
  auto s=c.stage;w.base=c.last_valid&&c.last_slot==s.slot?c.last_data:c.ram_q;w.hitdata=w.base;
  w.hr=apply(s.cand,w.base);w.hitdata[(s.cand.node&1)*2]=w.hr.value.label;w.hitdata[(s.cand.node&1)*2+1]=w.hr.value.meta;
  auto response=c.responses.od;w.filldata=response.data;auto &miss=c.misses[response.id&31];
  w.fr=apply(miss.request,response.data);w.filldata[(miss.request.node&1)*2]=w.fr.value.label;w.filldata[(miss.request.node&1)*2+1]=w.fr.value.meta;
  w.eventready=c.events.ready(ordy);w.advance=!s.valid||s.eviction||w.eventready;
  w.fillwait=c.responses.ov&&response.id<32;w.filltake=w.fillwait&&!s.valid&&w.eventready;
  w.rr=response.id>=32||(!s.valid&&w.eventready);
  w.qr=!c.flushing&&!w.fillwait&&w.advance&&(w.matching<0&&(w.hit>=0||(w.fm>=0&&w.victim>=0&&(!c.cache[w.victim].dirty||w.fw>=0))));
  w.dispatch=c.requests.ov&&w.qr;w.hitdispatch=w.dispatch&&w.matching<0&&w.hit>=0;w.missdispatch=w.dispatch&&w.matching<0&&w.hit<0;
  w.flushdispatch=c.flushing&&c.flush_index<128&&c.cache[c.flush_index].dirty&&w.advance&&w.fw>=0;
  ir=c.requests.ready(w.qr)&&!fence;rsp_ready=c.responses.ready(w.rr);
  ov=c.events.ov;onode=c.events.od.node;otag=c.events.od.tag;status=c.events.od.status;old_record={uint32_t(c.events.od.old.label),uint32_t(c.events.od.old.label>>32),uint32_t(c.events.od.old.meta),uint32_t(c.events.od.old.meta>>32)};
  idle=!s.valid&&!c.flushing&&!c.requests.count&&!c.requests.ov&&!c.responses.count&&!c.responses.ov&&!w.cm&&!w.cw&&!mem_valid&&!c.events.count&&!c.events.ov;
  quiet_cached=idle&&!fence&&!fence_done;
 }
 void eval(){if(clk&&!last_clk)step();last_clk=clk;combin();}
 void step(){
#ifdef R2_IDLE_CACHE
  if(quiet_cached&&!rst&&!iv&&!rsp_valid&&!fence&&!fence_done)return;
#endif
  quiet_cached=false;
  if(rst){c=Core{};mem_valid=fence_done=error=false;accepted=retired=merges=hits=misses=raw_stall=0;mshr_peak=dirty_peak=0;return;}
  // Snapshot only values read across this edge, not entire FIFO/cache arrays.
  // Every cycle is still evaluated; this is host implementation optimization.
  const bool old_mem_valid=mem_valid;const auto z=w;const bool old_idle=idle;auto &n=c;
  const auto s=c.stage;const auto q=c.requests.od;const auto response=c.responses.od;
  const bool old_flushing=c.flushing,old_turn=c.turn,old_requests_ov=c.requests.ov,old_responses_ov=c.responses.ov,old_events_ov=c.events.ov;
  const unsigned old_flush_index=c.flush_index,old_responses_count=c.responses.count,old_events_count=c.events.count;
  const auto fill_miss=c.misses[response.id&31];
  const auto send_miss=z.im>=0?c.misses[z.im]:Miss{};
  const auto send_write=z.iw>=0?c.writes[z.iw]:Write{};
  const auto ack_write=response.id>=32&&response.id<48?c.writes[response.id-32]:Write{};
  const auto victim_cache=z.victim>=0?c.cache[z.victim]:Cache{};
  const auto flush_cache=c.cache[c.flush_index&127];
  const Line read_data=(z.hitdispatch||z.missdispatch||z.flushdispatch)?c.cache[z.flushdispatch?c.flush_index:z.hitdispatch?unsigned(z.hit):unsigned(z.victim)].data:Line{};

  bool hitwrite=s.valid&&!s.eviction&&z.advance&&z.hr.changed;
  bool event_v=(s.valid&&!s.eviction&&z.advance)||z.filltake;auto fillreq=fill_miss.request;
  Event event=z.filltake?Event{fillreq.node,fillreq.tag,z.fr.status,z.fr.old}:Event{s.cand.node,s.cand.tag,z.hr.status,z.hr.old};
  n.requests.step(iv&&!fence,{node,opcode,operand,argument,tag},z.qr);n.responses.step(rsp_valid,{rsp_id,unpack(rsp_data)},z.rr);n.events.step(event_v,event,ordy);
  if(iv&&ir){++accepted;if(node>=node_count)error=true;}if(old_requests_ov&&!z.qr)++raw_stall;mshr_peak=std::max(mshr_peak,z.cm);dirty_peak=std::max(dirty_peak,z.cw);
  if(z.hitdispatch||z.missdispatch||z.flushdispatch){unsigned addr=z.flushdispatch?old_flush_index:z.hitdispatch?z.hit:z.victim;n.ram_q=read_data;}
  if(hitwrite||z.filltake){unsigned slot=z.filltake?fill_miss.slot:s.slot;auto data=z.filltake?z.filldata:z.hitdata;n.cache[slot].data=data;n.last_valid=true;n.last_slot=slot;n.last_data=data;}
  if(!mem_valid||mem_ready){mem_valid=false;if(z.iw>=0&&(z.im<0||!old_turn)){auto b=send_write;command(true,b.line,32+z.iw,b.data);n.writes[z.iw].sent=true;n.turn=true;}else if(z.im>=0){command(false,send_miss.line,z.im,{});n.misses[z.im].sent=true;n.turn=false;}}
  if(old_responses_ov&&z.rr&&response.id>=32){unsigned i=response.id-32;if(i>=16||!ack_write.valid||!ack_write.sent)error=true;else{n.writes[i].valid=n.writes[i].sent=n.writes[i].ready=false;}}
  if(z.filltake){unsigned i=response.id;auto m=fill_miss;if(!m.valid||!m.sent)error=true;n.cache[m.slot].valid=true;n.cache[m.slot].busy=false;n.cache[m.slot].dirty=z.fr.changed!=0;n.misses[i].valid=n.misses[i].sent=n.misses[i].go=false;++retired;if(z.fr.status&8)error=true;}
  if(z.advance){
   n.stage.valid=false;
   if(s.valid){if(!s.eviction){++retired;if(z.hr.status&8)error=true;if(z.hr.changed)n.cache[s.slot].dirty=true;}else{if(s.dirty){n.writes[s.write].data=z.base;n.writes[s.write].ready=true;}if(!old_flushing)n.misses[s.miss].go=true;}}
   if(z.hitdispatch){n.stage.valid=true;n.stage.eviction=false;n.stage.slot=z.hit;n.stage.cand=q;n.stage.line=address(q.node);++hits;}
   if(z.missdispatch){
    auto v=victim_cache;auto &st=n.stage;st.valid=true;st.eviction=true;st.slot=z.victim;st.dirty=v.dirty;st.evict_line=v.tag;st.miss=z.fm;
    if(v.dirty){st.write=z.fw;n.writes[z.fw].valid=true;n.writes[z.fw].sent=n.writes[z.fw].ready=false;n.writes[z.fw].line=v.tag;}
    auto &m=n.misses[z.fm];m.valid=true;m.sent=m.go=false;m.line=address(q.node);m.slot=z.victim;m.request=q;
    n.cache[z.victim].valid=n.cache[z.victim].dirty=false;n.cache[z.victim].busy=true;n.cache[z.victim].tag=address(q.node);n.replacement[(address(q.node)>>owner_bits)&31]=((unsigned(z.victim)>>5)+1)&3;++misses;
   }
   if(z.flushdispatch){auto &st=n.stage;st.write=z.fw;n.writes[z.fw].valid=true;n.writes[z.fw].sent=n.writes[z.fw].ready=false;n.writes[z.fw].line=flush_cache.tag;st.valid=true;st.eviction=true;st.slot=old_flush_index;st.dirty=true;st.evict_line=flush_cache.tag;n.cache[old_flush_index].dirty=false;n.flush_index=old_flush_index+1;}
  }
  if(!fence)fence_done=false;
  if(fence&&!fence_done&&!old_flushing&&old_idle){n.flushing=true;n.flush_index=0;}
  if(old_flushing&&old_flush_index<128&&!flush_cache.dirty)n.flush_index=old_flush_index+1;
  // mem_valid is a register: use its PRE-edge value at the fence boundary.
  if(old_flushing&&old_flush_index==128&&!s.valid&&!z.cw&&!old_responses_count&&!old_responses_ov&&!old_events_count&&!old_events_ov&&!old_mem_valid){n.flushing=false;fence_done=true;}
 }
};
}
