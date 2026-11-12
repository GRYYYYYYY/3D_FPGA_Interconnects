#pragma once
#include <array>
#include <cstdint>
#include <algorithm>
// Independent cycle model of the new registered cache service. No RTL simulator,
// historical timing coefficients, or externally supplied frontier is called here.
namespace sparse_model {
using Line=std::array<uint64_t,4>;
constexpr uint64_t INF=0x7f8000007f800000ull;
template<class T,unsigned N=64>struct Fifo{
 std::array<T,N> ram{};unsigned wp=0,rp=0,count=0;bool ov=false;T od{};
 bool ready(bool ordy)const{
#ifdef R2_REGISTERED_READY
 return count+ov<N;
#else
 return count+ov<N||(ov&&ordy);
#endif
 }
 void step(bool iv,const T& data,bool ordy){bool put=iv&&ready(ordy),take=(!ov||ordy)&&count;T read=ram[rp];if(put){ram[wp]=data;wp=(wp+1)%N;}if(take){od=read;rp=(rp+1)%N;}count+=put;count-=take;if(!ov||ordy)ov=take;}
};
// Optional FF stage after the synchronous RAM, with the original total
// admission capacity. No additional queue entries are supplied by the model.
template<class T,unsigned N=64>struct PipelineFifo {
 Fifo<T,N> ram;unsigned count=0;bool ov=false;T od{};
 bool ready(bool ordy)const{
#ifdef R2_REGISTERED_READY
  return count+ov<N;
#else
  return count+ov<N||(ov&&ordy);
#endif
 }
 void step(bool iv,const T&data,bool ordy){
  const bool put=iv&&ready(ordy),advance=!ov||ordy;
  const bool v=ram.ov;const T q=ram.od;
  ram.step(put,data,advance);
  if(advance){ov=v;if(v)od=q;}
  count=ram.count+ram.ov;
 }
};
#ifdef R2_REQUEST_STAGE
 template<class T,unsigned N=64>using RequestFifo=PipelineFifo<T,N>;
#else
 template<class T,unsigned N=64>using RequestFifo=Fifo<T,N>;
#endif
struct Candidate{uint32_t node=0;uint64_t pair=0;};struct Response{unsigned id=0;Line data{};};
struct OwnerModel{
 bool clk=false,rst=false,iv=false,ir=false,fence=false,fence_done=false,update_valid=false,update_ready=false;
 bool mem_valid=false,mem_ready=false,mem_write=false,rsp_valid=false,rsp_ready=false,idle=false,error=false;
 uint32_t node=0,update_line=0,mem_line=0;uint64_t pair=0;unsigned update_mask=0,mem_id=0,rsp_id=0;
 std::array<uint32_t,8> mem_data{},rsp_data{};
 uint32_t accepted=0,retired=0,merges=0,hits=0,misses=0,raw_stall=0;unsigned mshr_peak=0,dirty_peak=0;
 enum{IDLE,TAG,READ,APPLY,ALLOC,FILL,EVENT,FLUSH,FREAD,FWRITE,WAIT};
 struct Cache{bool valid=false,dirty=false,busy=false;uint32_t tag=0;Line data{};};
 struct Miss{bool valid=false,sent=false;uint32_t line=0,count=0;unsigned way=0;Line cand{INF,INF,INF,INF};};
 struct Write{bool valid=false,sent=false;uint32_t line=0;Line data{};};
 struct Core{
  std::array<Cache,128> cache{};std::array<Miss,32> miss{};std::array<Write,16> write{};
  Fifo<Candidate> requests;Fifo<Response> responses;
  unsigned state=IDLE,resume=IDLE,slot=0,fillid=0,flush_index=0;bool flushing=false;
  uint32_t cur_node=0,cur_line=0;uint64_t cur_pair=0;Line ram_q{},filldata{};
 } c;
 bool last_clk=false;
 static Line from(const std::array<uint32_t,8>& w){Line l{};for(unsigned s=0;s<4;++s)l[s]=uint64_t(w[2*s+1])<<32|w[2*s];return l;}
 void command(bool write,uint32_t line,unsigned id,const Line& l){mem_valid=true;mem_write=write;mem_line=line;mem_id=id;for(unsigned s=0;s<4;++s){mem_data[2*s]=l[s];mem_data[2*s+1]=l[s]>>32;}}
 void combin(){bool rr=(c.responses.od.id>=32||c.state==IDLE||c.state==WAIT)&&!update_valid;ir=c.requests.ready(c.state==IDLE&&!c.responses.ov&&!c.flushing&&!update_valid)&&!fence;rsp_ready=c.responses.ready(rr);bool any=false;for(auto m:c.miss)any|=m.valid;for(auto w:c.write)any|=w.valid;idle=c.state==IDLE&&!c.requests.ov&&!c.requests.count&&!c.responses.ov&&!c.responses.count&&!any&&!mem_valid&&!update_valid;}
 void eval(){if(clk&&!last_clk)step();last_clk=clk;combin();}
 void step(){
  if(rst){c=Core{};fence_done=update_valid=mem_valid=error=false;accepted=retired=merges=hits=misses=raw_stall=0;mshr_peak=dirty_peak=0;return;}
  const Core old=c;auto &n=c;
  int matching=-1,hit=-1,fm=-1,fw=-1,victim=-1,im=-1,iw=-1;unsigned cm=0,cw=0;
  for(unsigned k=0;k<32;++k){auto m=old.miss[k];if(m.valid){++cm;if(m.line==old.cur_line)matching=k;}else if(fm<0)fm=k;bool hazard=false;for(auto w:old.write)hazard|=w.valid&&w.line==m.line;if(m.valid&&!m.sent&&!hazard&&im<0)im=k;}
  for(unsigned k=0;k<16;++k){auto w=old.write[k];if(w.valid)++cw;else if(fw<0)fw=k;if(w.valid&&!w.sent&&iw<0)iw=k;}
  for(unsigned w=0;w<4;++w){unsigned s=w*32+((old.cur_line>>3)&31);auto cc=old.cache[s];if(cc.valid&&cc.tag==old.cur_line)hit=s;if(!cc.valid&&!cc.busy&&victim<0)victim=s;}
  if(victim<0)for(unsigned w=0;w<4;++w){unsigned s=w*32+((old.cur_line>>3)&31);if(!old.cache[s].busy&&victim<0)victim=s;}
  bool event=update_valid,qr=old.state==IDLE&&!old.responses.ov&&!old.flushing&&!event;
  bool rr=(old.responses.od.id>=32||old.state==IDLE||old.state==WAIT)&&!event;
  n.requests.step(iv&&!fence,{node,pair},qr);n.responses.step(rsp_valid,{rsp_id,from(rsp_data)},rr);
  if(iv&&ir&&!fence)++accepted;mshr_peak=std::max(mshr_peak,cm);dirty_peak=std::max(dirty_peak,cw);
  if(event&&update_ready)update_valid=false;
  if(!mem_valid||mem_ready){mem_valid=false;if(iw>=0){auto w=old.write[iw];command(true,w.line,32+iw,w.data);n.write[iw].sent=true;}else if(im>=0){command(false,old.miss[im].line,im,{});n.miss[im].sent=true;}}
  if(!fence)fence_done=false;
  if(old.responses.ov&&rr&&old.responses.od.id>=32){unsigned id=old.responses.od.id-32;if(id>=16||!old.write[id].valid)error=true;else n.write[id].valid=n.write[id].sent=false;}
  if(old.state==READ||old.state==FREAD)n.ram_q=old.cache[old.slot].data;
  auto fill=[&](unsigned resume){n.fillid=old.responses.od.id;n.filldata=old.responses.od.data;if(n.fillid>=32||!old.miss[n.fillid].valid)error=true;n.resume=resume;n.state=FILL;};
  auto publish=[&](uint32_t line,unsigned mask,unsigned resume){update_valid=true;update_line=line;update_mask=mask;n.resume=resume;n.state=EVENT;};
  switch(old.state){
  case IDLE:
   if(old.responses.ov&&!event){if(old.responses.od.id<32)fill(IDLE);}
   else if(old.requests.ov&&qr){n.cur_node=old.requests.od.node;n.cur_line=n.cur_node>>2;n.cur_pair=old.requests.od.pair;n.state=TAG;}
   else if(fence&&!old.requests.count&&!old.requests.ov&&!cm&&!event&&!old.flushing&&!fence_done){n.flushing=true;n.flush_index=0;n.state=FLUSH;}
   else if(old.flushing&&!cw&&!mem_valid&&!event){n.flushing=false;fence_done=true;}break;
  case WAIT:if(old.responses.ov&&rr&&old.responses.od.id<32)fill(TAG);else if(!old.responses.ov)n.state=TAG;break;
  case TAG:
   if(matching>=0){auto &m=n.miss[matching];unsigned s=old.cur_node&3;m.cand[s]=std::min(m.cand[s],old.cur_pair);++m.count;++merges;n.state=IDLE;}
   else if(hit>=0&&!old.cache[hit].busy){n.slot=hit;++hits;n.state=READ;}
   else if(fm>=0&&victim>=0&&(!old.cache[victim].dirty||fw>=0)){n.slot=victim;n.state=READ;}
   else{++raw_stall;n.state=WAIT;}break;
  case READ:n.state=hit>=0?APPLY:ALLOC;break;
  case APPLY:{unsigned s=old.cur_node&3;if(old.cur_pair<old.ram_q[s]){n.cache[old.slot].data=old.ram_q;n.cache[old.slot].data[s]=old.cur_pair;n.cache[old.slot].dirty=true;publish(old.cur_line,1u<<s,IDLE);}else n.state=IDLE;++retired;}break;
  case ALLOC:
   if(fm<0||(old.cache[old.slot].dirty&&fw<0)){error=true;break;}
   if(old.cache[old.slot].dirty)n.write[fw]={true,false,old.cache[old.slot].tag,old.ram_q};
   n.miss[fm]={true,false,old.cur_line,1,old.slot,{INF,INF,INF,INF}};n.miss[fm].cand[old.cur_node&3]=old.cur_pair;
   n.cache[old.slot].valid=n.cache[old.slot].dirty=false;n.cache[old.slot].busy=true;n.cache[old.slot].tag=old.cur_line;++misses;n.state=IDLE;break;
  case FILL:{auto m=old.miss[old.fillid];auto &cc=n.cache[m.way];cc.data=old.filldata;unsigned mask=0;for(unsigned s=0;s<4;++s)if(m.cand[s]<old.filldata[s]){cc.data[s]=m.cand[s];mask|=1u<<s;}cc.valid=true;cc.busy=false;cc.dirty=mask!=0;n.miss[old.fillid].valid=n.miss[old.fillid].sent=false;retired+=m.count;if(mask)publish(m.line,mask,old.resume);else n.state=old.resume;}break;
  case EVENT:if(event&&update_ready)n.state=old.resume;break;
  case FLUSH:if(old.flush_index==128)n.state=IDLE;else if(!old.cache[old.flush_index].dirty)++n.flush_index;else if(fw>=0){n.slot=old.flush_index;n.state=FREAD;}break;
  case FREAD:n.state=FWRITE;break;
  case FWRITE:if(fw<0)error=true;else{n.write[fw]={true,false,old.cache[old.slot].tag,old.ram_q};n.cache[old.slot].dirty=false;++n.flush_index;n.state=FLUSH;}break;
  default:error=true;
  }
 }
};
}
