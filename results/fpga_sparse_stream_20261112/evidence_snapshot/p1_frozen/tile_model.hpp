#pragma once
#include "owner_model.hpp"
#include <cstring>
#include <limits>
namespace sparse_model {
inline uint64_t addpair(uint64_t a,uint64_t b){uint32_t ad=a>>32,ac=a,bd=b>>32,bc=b;float x,y,z,t;std::memcpy(&x,&ad,4);std::memcpy(&y,&bd,4);std::memcpy(&z,&ac,4);std::memcpy(&t,&bc,4);x=x+y;z=z+t;std::memcpy(&ad,&x,4);std::memcpy(&ac,&z,4);return uint64_t(ad)<<32|ac;}
struct Arithmetic{
 bool full=false,ov=false,ir=false;Candidate out{},in{};uint64_t cost=0;
 void combin(bool ordy){ir=!full||!ov||ordy;}
 void step(bool rst,bool iv,uint32_t node,uint64_t parent,uint64_t c,bool ordy){bool advance=!ov||ordy,ready=!full||advance;if(rst){full=ov=false;return;}if(advance){ov=full;if(full)out={in.node,addpair(in.pair,cost)};}if(ready){full=iv;if(iv){in={node,parent};cost=c;}}}
};
struct Front {
 enum{FREE,ROW,ROW_WAIT,ROW_NEXT,EDGE,EDGE_WAIT,EMIT,NEXT_WAIT};
 struct Ctx{unsigned state=FREE;uint32_t node=0,pos=0,last=0;uint64_t parent=0;Line beat{};};
 std::array<Ctx,4> ctx{};std::array<unsigned,4> state{};std::array<uint64_t,16> costs{};
 Arithmetic lane;bool pv=false,pr=false,ordy=false,mem_valid=false,mem_ready=false,rsp_valid=false,emitv=false,local_error=false;
 uint32_t pn=0,row_base=0,edge_base=0,mem_line=0;uint64_t pp=0;unsigned mem_id=0,rsp_id=0;Line rsp_data{};
 bool cost_we=false;unsigned cost_index=0;uint64_t cost_data=0;
 Candidate emitdata{};uint64_t emitcost=0;bool row_valid=false;uint32_t row_tag=0;Line row_cache{};unsigned rr=0;
 uint32_t parents=0,edge_beats=0,row_beats=0,candidates=0,unused=0;unsigned peak=0;
 int free_ctx=-1,fetch=-1,emit=-1;unsigned used=0;
 void combin(){free_ctx=fetch=emit=-1;used=0;for(unsigned c=0;c<4;++c){state[c]=ctx[c].state;if(ctx[c].state==FREE&&free_ctx<0)free_ctx=c;if(ctx[c].state!=FREE)++used;if((ctx[c].state==ROW||ctx[c].state==ROW_NEXT||ctx[c].state==EDGE)&&fetch<0)fetch=c;unsigned n=(rr+c)%4;if(ctx[n].state==EMIT&&emit<0)emit=n;}pr=free_ctx>=0;lane.combin(ordy);}
 bool idle()const{return !used&&!mem_valid&&!emitv&&!lane.full&&!lane.ov;}
 void step(bool rst){
  auto old=ctx;bool old_emitv=emitv;Candidate old_emit=emitdata;uint64_t old_cost=emitcost;bool ready=lane.ir;auto old_cache=row_cache;bool old_valid=row_valid;uint32_t old_tag=row_tag;
  lane.step(rst,old_emitv,old_emit.node,old_emit.pair,old_cost,ordy);
  if(cost_we)costs[cost_index]=cost_data;
  if(rst){ctx={};mem_valid=emitv=row_valid=local_error=false;rr=parents=edge_beats=row_beats=candidates=unused=peak=0;return;}
  peak=std::max(peak,used);
  if(pv&&pr){ctx[free_ctx].state=ROW;ctx[free_ctx].node=pn;ctx[free_ctx].parent=pp;++parents;}
  if(!old_emitv||ready){emitv=false;if(emit>=0){auto c=old[emit];uint64_t word=c.beat[(c.pos&7)/2];uint32_t desc=word>>((c.pos&1)*32);emitv=true;emitdata={desc&0xfffffff,c.parent};emitcost=costs[desc>>28];++candidates;rr=(emit+1)&3;ctx[emit].pos=c.pos+1;if(c.pos+1==c.last)ctx[emit].state=FREE;else if((c.pos&7)==7)ctx[emit].state=EDGE;}}
  auto decode=[&](unsigned id,const Line &line){auto c=old[id];uint64_t a=line[c.node&3];ctx[id].pos=a;if(a>>32)local_error=true;if((c.node&3)==3)ctx[id].state=ROW_NEXT;else{uint64_t b=line[(c.node&3)+1];ctx[id].last=b;if((b>>32)||b<a)local_error=true;ctx[id].state=a==b?FREE:EDGE;}};
  if(!mem_valid||mem_ready){mem_valid=false;if(fetch>=0){auto c=old[fetch];if(c.state==EDGE){mem_valid=true;mem_line=edge_base+(c.pos>>3);mem_id=8+fetch;ctx[fetch].state=EDGE_WAIT;++edge_beats;}else if(c.state==ROW_NEXT){mem_valid=true;mem_line=row_base+(c.node>>2)+1;mem_id=4+fetch;ctx[fetch].state=NEXT_WAIT;++row_beats;}else if(old_valid&&old_tag==row_base+(c.node>>2))decode(fetch,old_cache);else{mem_valid=true;mem_line=row_base+(c.node>>2);mem_id=fetch;ctx[fetch].state=ROW_WAIT;++row_beats;}}}
  if(rsp_valid){unsigned s=rsp_id&3;auto c=old[s];if(rsp_id/4==2){ctx[s].beat=rsp_data;ctx[s].state=EMIT;unused+=(c.pos&7)+((c.last>>3)==(c.pos>>3)?8-(c.last&7):0);}else if(rsp_id/4==1){ctx[s].last=rsp_data[0];if((rsp_data[0]>>32)||uint32_t(rsp_data[0])<c.pos)local_error=true;ctx[s].state=uint32_t(rsp_data[0])==c.pos?FREE:EDGE;}else{row_valid=true;row_tag=row_base+(c.node>>2);row_cache=rsp_data;decode(s,rsp_data);}}
 }
};
struct Changed {
 std::array<unsigned,512> ids{};std::array<bool,512> marked{};unsigned wr=0,rd=0,index=0,peak=0,todo=0,base=0;bool busy=false,ov=false,error=false;
 bool ev=false,er=false,commit=false,ack=false;uint32_t line=0;unsigned mask=0;
 void combin(){er=!busy&&!commit;}
 void step(bool rst){if(rst){marked.fill(false);wr=rd=peak=todo=base=0;busy=ov=error=false;return;}bool old_busy=busy,old_ov=ov;unsigned oldwr=wr,oldrd=rd,oldindex=index;bool take=commit&&(!old_ov||ack)&&oldrd<oldwr;if(take)index=ids[oldrd];if(!commit&&!old_busy&&oldwr==oldrd&&!old_ov)wr=rd=0;if(ev&&er){busy=true;todo=mask;base=(line>>3)*4;}if(old_busy){if(!todo)busy=false;else{unsigned s=__builtin_ctz(todo);if(marked[base+s])todo&=~(1u<<s);else if(oldwr<512){ids[oldwr]=base+s;marked[base+s]=true;wr=oldwr+1;todo&=~(1u<<s);peak=std::max(peak,wr);}else error=true;}}if(take)rd=oldrd+1;if(commit&&(!old_ov||ack))ov=take;if(old_ov&&ack)marked[oldindex]=false;}
};
struct Bank {
 enum{IDLE,INIT,INITMEM,INITWAIT,SEED,POPHEAD,POPSTART,POPMEMBER,POPMETA,POPVALID,POPLABEL,POPEMIT,COMMIT,CREAD,CWAIT,CMETA,CWRITE,APPEND,ALLOC,TAILREAD,TAILWRITE,PUBLISH,CACK,CLOSE,CLOSEIDX,CLOSELABEL,CLOSEEMIT,CACKWAIT};
 struct Registers{unsigned state=IDLE,free_count=1024,closed_wr=0,closed_rd=0,initidx=0,idx=0,key=0;uint64_t label_q=0,dir_q=0,member_q=0,tail_value=0,new_label=0;uint32_t pending_q=0,pointer=0,allocated=0,tail_ptr=0;unsigned free_q=0,closed_q=0,version=0;} r;
 std::array<uint64_t,512> labels{};std::array<uint32_t,512> pending{};std::array<uint64_t,4096> directory{};std::array<uint64_t,1024> members{};std::array<unsigned,1024> free_ids{};std::array<unsigned,512> closed{};std::array<bool,512> closed_mark{};std::array<uint64_t,64> bitmap{};uint64_t groups=0;
 unsigned number=0,command=0,bucket=0;uint32_t source=0;bool done=false,error=false,pv=false,pr=false,cv=false,ca=false,close_valid=false,close_ready=false,mem_valid=false,mem_ready=false,mem_write=false,rsp_valid=false;
 uint32_t pn=0,close_node=0,mem_line=0;uint64_t pp=0,close_pair=0;unsigned ci=0;Line mem_data{},rsp_data{};
 uint32_t active_count=0,commit_count=0,closed_count=0,stale_count=0;unsigned member_peak=0;
 unsigned global(unsigned idx)const{return (idx/4)*32+number*4+idx%4;}
 unsigned minimum()const{if(!groups)return 0;unsigned g=__builtin_ctzll(groups);return g*64+__builtin_ctzll(bitmap[g]);}
 bool has(unsigned key)const{return bitmap[key/64]>>(key%64)&1;}
 void step(bool rst){
  const Registers o=r;auto &n=r;bool old_pv=pv,old_close=close_valid,old_mem=mem_valid;
  n.label_q=labels[o.idx];n.pending_q=pending[o.idx];n.dir_q=directory[o.key];n.member_q=members[o.pointer&1023];n.free_q=free_ids[(o.free_count-1)&1023];n.closed_q=closed[o.closed_rd&511];
  if(rst){r=Registers{};done=error=pv=close_valid=ca=mem_valid=false;bitmap.fill(0);groups=0;closed_mark.fill(false);member_peak=active_count=commit_count=closed_count=stale_count=0;return;}
  ca=false;if(old_mem&&mem_ready)mem_valid=false;if(old_pv&&pr)pv=false;if(old_close&&close_ready)close_valid=false;if(!command)done=false;
  switch(o.state){
  case IDLE:if(command&&!done){switch(command){case 1:n.initidx=n.closed_wr=n.closed_rd=0;bitmap.fill(0);groups=0;closed_mark.fill(false);n.free_count=1024;n.state=INIT;break;case 2:n.key=bucket;n.state=POPHEAD;break;case 3:n.state=COMMIT;break;case 4:n.closed_rd=0;n.state=CLOSE;break;default:error=true;}}break;
  case INIT:free_ids[o.initidx]=o.initidx;if(o.initidx<512){labels[o.initidx]=global(o.initidx)==source?0:INF;pending[o.initidx]=0;}if(o.initidx==1023){n.initidx=0;n.state=INITMEM;}else ++n.initidx;break;
  case INITMEM:if(!old_mem){mem_valid=mem_write=true;mem_line=o.initidx*8+number;mem_data.fill(INF);for(unsigned i=0;i<4;++i)if(o.initidx*32+number*4+i==source)mem_data[i]=0;n.state=INITWAIT;}break;
  case INITWAIT:if(rsp_valid){if(o.initidx==127){n.idx=(source/32)*4+source%4;n.state=SEED;}else{++n.initidx;n.state=INITMEM;}}break;
  case SEED:if((source>>2)%8==number){n.key=0;n.version=1;n.new_label=0;n.state=APPEND;}else{n.state=IDLE;done=true;}break;
  case POPHEAD:n.state=POPSTART;break;
  case POPSTART:if(!has(o.key)){done=true;n.state=IDLE;}else{n.pointer=o.dir_q>>32;bitmap[o.key/64]&=~(1ull<<(o.key%64));if(!bitmap[o.key/64])groups&=~(1ull<<(o.key/64));n.state=POPMEMBER;}break;
  case POPMEMBER:if(o.pointer==0xffffffffu){n.state=IDLE;done=true;}else n.state=POPMETA;break;
  case POPMETA:n.idx=(o.member_q>>32)&511;n.version=o.member_q>>48;n.tail_ptr=o.member_q;free_ids[o.free_count&1023]=o.pointer&1023;n.free_count=o.free_count+1;n.state=POPVALID;break;
  case POPVALID:n.state=POPLABEL;break;
  case POPLABEL:if(!(o.pending_q>>28&1)||((o.pending_q>>12)&65535)!=o.version||(o.pending_q&4095)!=o.key){++stale_count;n.pointer=o.tail_ptr;n.state=POPMEMBER;}else{pending[o.idx]=0;if(!closed_mark[o.idx]){if(o.closed_wr==512)error=true;else{closed[o.closed_wr]=o.idx;closed_mark[o.idx]=true;++n.closed_wr;}}pv=true;pn=global(o.idx);pp=o.label_q;n.state=POPEMIT;}break;
  case POPEMIT:if(old_pv&&pr){++active_count;n.pointer=o.tail_ptr;n.state=POPMEMBER;}break;
  case COMMIT:if(cv){n.idx=ci;n.state=CREAD;}else{done=true;n.state=IDLE;}break;
  case CREAD:if(!old_mem){mem_valid=true;mem_write=false;mem_line=global(o.idx)/4;n.state=CWAIT;}break;
  case CWAIT:if(rsp_valid){n.new_label=rsp_data[o.idx&3];n.state=CMETA;}break;
  case CMETA:n.state=CWRITE;break;
  case CWRITE:if(o.new_label>=o.label_q)error=true;labels[o.idx]=o.new_label;++commit_count;n.key=o.new_label>>52;n.version=(((o.pending_q>>12)&65535)+1)&65535;n.state=(o.pending_q>>28&1)&&(o.pending_q&4095)==(o.new_label>>52)?CACK:APPEND;break;
  case APPEND:if(!o.free_count)error=true;else n.state=ALLOC;break;
  case ALLOC:n.allocated=o.free_q;n.free_count=o.free_count-1;n.tail_ptr=o.dir_q;n.pointer=o.dir_q;n.tail_value=o.dir_q;member_peak=std::max(member_peak,1025-o.free_count);n.state=has(o.key)?TAILREAD:PUBLISH;break;
  case TAILREAD:n.state=TAILWRITE;break;
  case TAILWRITE:members[o.tail_ptr&1023]=(o.member_q&0xffffffff00000000ull)|o.allocated;n.state=PUBLISH;break;
  case PUBLISH:members[o.allocated&1023]=uint64_t(o.version)<<48|uint64_t(o.idx)<<32|0xffffffffu;directory[o.key]=(has(o.key)?o.tail_value&0xffffffff00000000ull:uint64_t(o.allocated)<<32)|o.allocated;bitmap[o.key/64]|=1ull<<(o.key%64);groups|=1ull<<(o.key/64);pending[o.idx]=(1u<<28)|(o.version<<12)|o.key;n.state=CACK;break;
  case CACK:if(command==1){done=true;n.state=IDLE;}else{ca=true;n.state=CACKWAIT;}break;
  case CACKWAIT:n.state=COMMIT;break;
  case CLOSE:if(o.closed_rd==o.closed_wr){n.closed_wr=0;done=true;n.state=IDLE;}else n.state=CLOSEIDX;break;
  case CLOSEIDX:n.idx=o.closed_q;n.state=CLOSELABEL;break;
  case CLOSELABEL:n.state=CLOSEEMIT;break;
  case CLOSEEMIT:if(!old_close){close_valid=true;close_node=global(o.idx);close_pair=o.label_q;}else if(close_ready){close_valid=false;closed_mark[o.idx]=false;++n.closed_rd;++closed_count;n.state=CLOSE;}break;
  default:error=true;
  }
 }
};
struct TileModel {
 bool clk=false,rst=false,start=false,done=false,error=false,last_clk=false;
 uint32_t source=0,row_base=0,edge_base=0,cost_base=0,cell_base=0,targets=0;unsigned cell_count=0,cost_count=0,output_index=0;uint64_t output_pair=0;
 uint32_t mem_valid=0,mem_ready=0,mem_write=0,rsp_valid=0,rsp_ready=0;
 std::array<uint32_t,25> mem_line{};std::array<uint32_t,5> mem_id{},rsp_id{};std::array<uint32_t,200> mem_data{},rsp_data{};
 unsigned issued=0,accepted=0,committed=0,owner_error=0;std::array<uint32_t,8> commit_nodes{},active_counts{},commit_counts{};
 uint32_t wave=0;unsigned phase=0;
 enum{IDLE,RESET_JOB,LOAD_COST,COST_WAIT,COST_WORDS,INIT,GAP,SELECT,POP,DRAIN,FENCE,COMMIT,DECIDE,CLOSE,FINISH};
 std::array<OwnerModel,8> owners;std::array<Bank,8> banks;std::array<Front,8> fronts;std::array<Changed,8> changed;std::array<Fifo<Candidate>,8> route;
 std::array<unsigned,8> route_rr{},qc{},rc{};std::array<int,8> selection{};
 unsigned command=0,bucket=0,cost_pos=0,cost_index=0;uint64_t cost_data=0;bool cost_we=false,cost_loaded=false;
 Line cost_beat{},ctl_data{},cell_cache{};bool ctl_valid=false,ctl_write=false,cell_cache_valid=false,local_error=false;
 uint32_t ctl_line=0,recorded=0,cell_cache_tag=0,held_node=0;unsigned output_init=0,close_state=0,target_cell=0;uint64_t held_pair=0,target_pair=0,output_q=0;
 std::array<uint64_t,64> outputs{};uint64_t output_valid=0;
 unsigned next_min=4095;bool any_min=false;int close_chosen=-1;bool router_idle=true,all_bank_done=false,all_front_idle=false,all_owner_done=false,all_queue_idle=false;
 TileModel(){for(unsigned i=0;i<8;++i)banks[i].number=i;}
 static unsigned idget(const std::array<uint32_t,5>& a,unsigned c){unsigned bit=c*6,w=bit/32,s=bit%32,v=a[w]>>s;if(s>26)v|=a[w+1]<<(32-s);return v&63;}
 void outset(unsigned c,bool valid,bool write,unsigned line,unsigned id,const Line& data){if(valid)mem_valid|=1u<<c;if(write)mem_write|=1u<<c;mem_line[c]=line;unsigned bit=c*6,w=bit/32,s=bit%32;mem_id[w]|=(id&63)<<s;if(s>26)mem_id[w+1]|=(id&63)>>(32-s);for(unsigned j=0;j<4;++j){mem_data[c*8+j*2]=data[j];mem_data[c*8+j*2+1]=data[j]>>32;}}
 Line response(unsigned c){Line l{};for(unsigned j=0;j<4;++j)l[j]=uint64_t(rsp_data[c*8+j*2+1])<<32|rsp_data[c*8+j*2];return l;}
 void combin(){
  next_min=4095;any_min=false;close_chosen=-1;router_idle=true;all_bank_done=all_front_idle=all_owner_done=all_queue_idle=true;
  mem_valid=mem_write=rsp_ready=issued=accepted=committed=owner_error=0;mem_id.fill(0);error=local_error;
  for(unsigned i=0;i<8;++i){auto &b=banks[i];auto &f=fronts[i];auto &o=owners[i];auto &q=changed[i];
   q.commit=phase==COMMIT;q.combin();o.fence=phase==FENCE;o.update_ready=q.er;o.combin();f.combin();
   if(b.groups){any_min=true;next_min=std::min(next_min,b.minimum());}if(b.close_valid&&close_chosen<0)close_chosen=i;
   all_bank_done&=b.done;all_front_idle&=f.idle();all_owner_done&=o.fence_done;all_queue_idle&=!q.busy;router_idle&=route[i].count==0&&!route[i].ov;
   error|=b.error||o.error||q.error||f.local_error;if(o.error)owner_error|=1u<<i;
  }
  for(unsigned owner=0;owner<8;++owner){selection[owner]=-1;for(unsigned k=0;k<8;++k){unsigned lane=(route_rr[owner]+k)%8;if(fronts[lane].lane.ov&&((fronts[lane].lane.out.node>>2)&7)==owner&&selection[owner]<0)selection[owner]=lane;}}
  for(auto &f:fronts)f.ordy=false;
  for(unsigned i=0;i<8;++i)if(selection[i]>=0)fronts[selection[i]].ordy=route[i].ready(owners[i].ir);
  for(unsigned i=0;i<8;++i){auto &b=banks[i];auto &f=fronts[i];auto &o=owners[i];auto &q=changed[i];f.combin();
   b.command=command;b.bucket=bucket;b.source=source;b.pr=f.pr;b.cv=q.ov;b.ci=q.index;b.close_ready=phase==CLOSE&&close_state==0&&close_chosen==int(i);b.mem_ready=mem_ready>>(16+i)&1;b.rsp_valid=rsp_valid>>(16+i)&1;b.rsp_data=response(16+i);
   f.pv=b.pv;f.pn=b.pn;f.pp=b.pp;f.row_base=row_base;f.edge_base=edge_base;f.cost_we=cost_we;f.cost_index=cost_index;f.cost_data=cost_data;f.mem_ready=mem_ready>>(8+i)&1;f.rsp_valid=rsp_valid>>(8+i)&1;f.rsp_id=idget(rsp_id,8+i)&15;f.rsp_data=response(8+i);
   o.iv=route[i].ov;o.node=route[i].od.node;o.pair=route[i].od.pair;o.mem_ready=mem_ready>>i&1;o.rsp_valid=rsp_valid>>i&1;o.rsp_id=idget(rsp_id,i);for(unsigned j=0;j<8;++j)o.rsp_data[j]=rsp_data[i*8+j];
   q.ev=o.update_valid;q.line=o.update_line;q.mask=o.update_mask;q.ack=b.ca;
   outset(i,o.mem_valid,o.mem_write,o.mem_line,o.mem_id,OwnerModel::from(o.mem_data));outset(8+i,f.mem_valid,false,f.mem_line,f.mem_id,{});outset(16+i,b.mem_valid,b.mem_write,b.mem_line,0,b.mem_data);
   if(o.rsp_ready)rsp_ready|=1u<<i;rsp_ready|=1u<<(8+i);rsp_ready|=1u<<(16+i);
   if(f.lane.ov&&f.ordy)issued|=1u<<i;if(o.iv&&o.ir)accepted|=1u<<i;if(b.ca)committed|=1u<<i;commit_nodes[i]=b.global(q.index);active_counts[i]=b.active_count;commit_counts[i]=b.commit_count;
   qc[i]=o.c.requests.count+o.c.requests.ov;rc[i]=o.c.responses.count+o.c.responses.ov;
  }
  outset(24,ctl_valid,ctl_write,ctl_line,0,ctl_data);rsp_ready|=1u<<24;
 }
 void eval(){if(clk&&!last_clk)step();last_clk=clk;combin();}
 void step(){
  bool reset_job=rst||phase==RESET_JOB;unsigned oldphase=phase;bool oldctl=ctl_valid;unsigned old_cs=close_state;uint64_t old_outq=output_q;output_pair=outputs[output_index];output_q=outputs[target_cell];
  std::array<bool,8> ready,put;std::array<Candidate,8> data;
  for(unsigned i=0;i<8;++i){ready[i]=owners[i].ir;put[i]=selection[i]>=0;if(put[i])data[i]=fronts[selection[i]].lane.out;}
  if(rst){phase=IDLE;command=0;done=local_error=cost_loaded=cost_we=ctl_valid=false;wave=0;output_valid=0;close_state=0;cell_cache_valid=false;}
  else{
   cost_we=false;if(oldctl&&(mem_ready>>24&1))ctl_valid=false;
   switch(oldphase){
   case IDLE:if(start){done=false;wave=recorded=0;output_valid=0;output_init=0;cell_cache_valid=false;close_state=0;phase=RESET_JOB;if(cell_count>64||!cell_count||cost_count>16||!cost_count||source>=4096)local_error=true;}break;
   case RESET_JOB:if(cost_loaded){command=1;phase=INIT;}else{cost_pos=0;phase=LOAD_COST;}break;
   case LOAD_COST:if(!oldctl){ctl_valid=true;ctl_write=false;ctl_line=cost_base+(cost_pos>>2);ctl_data={};phase=COST_WAIT;}break;
   case COST_WAIT:if(rsp_valid>>24&1){cost_beat=response(24);phase=COST_WORDS;}break;
   case COST_WORDS:{unsigned pos=cost_pos;cost_we=true;cost_index=pos;cost_data=cost_beat[pos&3];++cost_pos;if(pos+1==cost_count){cost_loaded=true;command=1;phase=INIT;}else if((pos&3)==3)phase=LOAD_COST;}break;
   case INIT:if(output_init<cell_count)outputs[output_init++]=0x7fc000007fc00000ull;if(all_bank_done){command=0;phase=GAP;}break;
   case GAP:phase=SELECT;break;
   case SELECT:if(!any_min||!targets)phase=FINISH;else{bucket=next_min;command=2;++wave;phase=POP;}break;
   case POP:if(all_bank_done){command=0;phase=DRAIN;}break;
   case DRAIN:if(all_front_idle&&router_idle)phase=FENCE;break;
   case FENCE:if(all_owner_done&&all_queue_idle){command=3;phase=COMMIT;}break;
   case COMMIT:if(all_bank_done){command=0;phase=DECIDE;}break;
   case DECIDE:if(any_min&&next_min==bucket)phase=SELECT;else{command=4;close_state=0;phase=CLOSE;}break;
   case CLOSE:switch(old_cs){
    case 0:if(close_chosen>=0){held_node=banks[close_chosen].close_node;held_pair=banks[close_chosen].close_pair;close_state=1;}else if(all_bank_done){command=0;phase=recorded==targets?FINISH:GAP;}break;
    case 1:if(cell_cache_valid&&cell_cache_tag==cell_base+(held_node>>2))close_state=3;else if(!oldctl){ctl_valid=true;ctl_write=false;ctl_line=cell_base+(held_node>>2);close_state=2;}break;
    case 2:if(rsp_valid>>24&1){cell_cache=response(24);cell_cache_tag=cell_base+(held_node>>2);cell_cache_valid=true;close_state=3;}break;
    case 3:{uint64_t meta=cell_cache[held_node&3];if(!(meta>>32)||uint32_t(meta)==0xffffffffu)close_state=0;else{if(uint32_t(meta)>=cell_count)local_error=true;target_cell=meta&63;target_pair=held_pair;close_state=4;}}break;
    case 4:close_state=5;break;
    case 5:if(!(output_valid>>target_cell&1)||target_pair<old_outq)outputs[target_cell]=target_pair;if(!(output_valid>>target_cell&1))++recorded;output_valid|=1ull<<target_cell;close_state=0;break;
    default:local_error=true;
   }break;
   case FINISH:done=true;phase=IDLE;break;
   default:local_error=true;
   }
  }
  for(unsigned i=0;i<8;++i){bool fire=put[i]&&route[i].ready(ready[i]);if(reset_job){route[i]=Fifo<Candidate>{};route_rr[i]=0;}else{route[i].step(put[i],data[i],ready[i]);if(fire)route_rr[i]=(route_rr[i]+1)&7;}owners[i].rst=reset_job;owners[i].step();changed[i].step(reset_job);fronts[i].step(reset_job);banks[i].step(reset_job);}
 }
 decltype(banks[0].labels) &sparse_tile__DOT__banks__BRA__0__KET____DOT__bank__DOT__labels=banks[0].labels;
 decltype(changed[0].wr) &sparse_tile__DOT__banks__BRA__0__KET____DOT__changes__DOT__wr=changed[0].wr;
 decltype(changed[0].ids) &sparse_tile__DOT__banks__BRA__0__KET____DOT__changes__DOT__ids=changed[0].ids;
 decltype(owners[0].retired) &sparse_tile__DOT__banks__BRA__0__KET____DOT__dummy1=owners[0].retired;
 decltype(qc[0]) &sparse_tile__DOT__banks__BRA__0__KET____DOT__owner__DOT__qc=qc[0];
 decltype(rc[0]) &sparse_tile__DOT__banks__BRA__0__KET____DOT__owner__DOT__rc=rc[0];
 decltype(changed[0].peak) &sparse_tile__DOT__banks__BRA__0__KET____DOT__changed_peak=changed[0].peak;
 decltype(banks[0].member_peak) &sparse_tile__DOT__banks__BRA__0__KET____DOT__member_peak=banks[0].member_peak;
 decltype(fronts[0].state) &sparse_tile__DOT__banks__BRA__0__KET____DOT__front__DOT__state=fronts[0].state;
 decltype(banks[1].labels) &sparse_tile__DOT__banks__BRA__1__KET____DOT__bank__DOT__labels=banks[1].labels;
 decltype(changed[1].wr) &sparse_tile__DOT__banks__BRA__1__KET____DOT__changes__DOT__wr=changed[1].wr;
 decltype(changed[1].ids) &sparse_tile__DOT__banks__BRA__1__KET____DOT__changes__DOT__ids=changed[1].ids;
 decltype(owners[1].retired) &sparse_tile__DOT__banks__BRA__1__KET____DOT__dummy1=owners[1].retired;
 decltype(qc[1]) &sparse_tile__DOT__banks__BRA__1__KET____DOT__owner__DOT__qc=qc[1];
 decltype(rc[1]) &sparse_tile__DOT__banks__BRA__1__KET____DOT__owner__DOT__rc=rc[1];
 decltype(changed[1].peak) &sparse_tile__DOT__banks__BRA__1__KET____DOT__changed_peak=changed[1].peak;
 decltype(banks[1].member_peak) &sparse_tile__DOT__banks__BRA__1__KET____DOT__member_peak=banks[1].member_peak;
 decltype(fronts[1].state) &sparse_tile__DOT__banks__BRA__1__KET____DOT__front__DOT__state=fronts[1].state;
 decltype(banks[2].labels) &sparse_tile__DOT__banks__BRA__2__KET____DOT__bank__DOT__labels=banks[2].labels;
 decltype(changed[2].wr) &sparse_tile__DOT__banks__BRA__2__KET____DOT__changes__DOT__wr=changed[2].wr;
 decltype(changed[2].ids) &sparse_tile__DOT__banks__BRA__2__KET____DOT__changes__DOT__ids=changed[2].ids;
 decltype(owners[2].retired) &sparse_tile__DOT__banks__BRA__2__KET____DOT__dummy1=owners[2].retired;
 decltype(qc[2]) &sparse_tile__DOT__banks__BRA__2__KET____DOT__owner__DOT__qc=qc[2];
 decltype(rc[2]) &sparse_tile__DOT__banks__BRA__2__KET____DOT__owner__DOT__rc=rc[2];
 decltype(changed[2].peak) &sparse_tile__DOT__banks__BRA__2__KET____DOT__changed_peak=changed[2].peak;
 decltype(banks[2].member_peak) &sparse_tile__DOT__banks__BRA__2__KET____DOT__member_peak=banks[2].member_peak;
 decltype(fronts[2].state) &sparse_tile__DOT__banks__BRA__2__KET____DOT__front__DOT__state=fronts[2].state;
 decltype(banks[3].labels) &sparse_tile__DOT__banks__BRA__3__KET____DOT__bank__DOT__labels=banks[3].labels;
 decltype(changed[3].wr) &sparse_tile__DOT__banks__BRA__3__KET____DOT__changes__DOT__wr=changed[3].wr;
 decltype(changed[3].ids) &sparse_tile__DOT__banks__BRA__3__KET____DOT__changes__DOT__ids=changed[3].ids;
 decltype(owners[3].retired) &sparse_tile__DOT__banks__BRA__3__KET____DOT__dummy1=owners[3].retired;
 decltype(qc[3]) &sparse_tile__DOT__banks__BRA__3__KET____DOT__owner__DOT__qc=qc[3];
 decltype(rc[3]) &sparse_tile__DOT__banks__BRA__3__KET____DOT__owner__DOT__rc=rc[3];
 decltype(changed[3].peak) &sparse_tile__DOT__banks__BRA__3__KET____DOT__changed_peak=changed[3].peak;
 decltype(banks[3].member_peak) &sparse_tile__DOT__banks__BRA__3__KET____DOT__member_peak=banks[3].member_peak;
 decltype(fronts[3].state) &sparse_tile__DOT__banks__BRA__3__KET____DOT__front__DOT__state=fronts[3].state;
 decltype(banks[4].labels) &sparse_tile__DOT__banks__BRA__4__KET____DOT__bank__DOT__labels=banks[4].labels;
 decltype(changed[4].wr) &sparse_tile__DOT__banks__BRA__4__KET____DOT__changes__DOT__wr=changed[4].wr;
 decltype(changed[4].ids) &sparse_tile__DOT__banks__BRA__4__KET____DOT__changes__DOT__ids=changed[4].ids;
 decltype(owners[4].retired) &sparse_tile__DOT__banks__BRA__4__KET____DOT__dummy1=owners[4].retired;
 decltype(qc[4]) &sparse_tile__DOT__banks__BRA__4__KET____DOT__owner__DOT__qc=qc[4];
 decltype(rc[4]) &sparse_tile__DOT__banks__BRA__4__KET____DOT__owner__DOT__rc=rc[4];
 decltype(changed[4].peak) &sparse_tile__DOT__banks__BRA__4__KET____DOT__changed_peak=changed[4].peak;
 decltype(banks[4].member_peak) &sparse_tile__DOT__banks__BRA__4__KET____DOT__member_peak=banks[4].member_peak;
 decltype(fronts[4].state) &sparse_tile__DOT__banks__BRA__4__KET____DOT__front__DOT__state=fronts[4].state;
 decltype(banks[5].labels) &sparse_tile__DOT__banks__BRA__5__KET____DOT__bank__DOT__labels=banks[5].labels;
 decltype(changed[5].wr) &sparse_tile__DOT__banks__BRA__5__KET____DOT__changes__DOT__wr=changed[5].wr;
 decltype(changed[5].ids) &sparse_tile__DOT__banks__BRA__5__KET____DOT__changes__DOT__ids=changed[5].ids;
 decltype(owners[5].retired) &sparse_tile__DOT__banks__BRA__5__KET____DOT__dummy1=owners[5].retired;
 decltype(qc[5]) &sparse_tile__DOT__banks__BRA__5__KET____DOT__owner__DOT__qc=qc[5];
 decltype(rc[5]) &sparse_tile__DOT__banks__BRA__5__KET____DOT__owner__DOT__rc=rc[5];
 decltype(changed[5].peak) &sparse_tile__DOT__banks__BRA__5__KET____DOT__changed_peak=changed[5].peak;
 decltype(banks[5].member_peak) &sparse_tile__DOT__banks__BRA__5__KET____DOT__member_peak=banks[5].member_peak;
 decltype(fronts[5].state) &sparse_tile__DOT__banks__BRA__5__KET____DOT__front__DOT__state=fronts[5].state;
 decltype(banks[6].labels) &sparse_tile__DOT__banks__BRA__6__KET____DOT__bank__DOT__labels=banks[6].labels;
 decltype(changed[6].wr) &sparse_tile__DOT__banks__BRA__6__KET____DOT__changes__DOT__wr=changed[6].wr;
 decltype(changed[6].ids) &sparse_tile__DOT__banks__BRA__6__KET____DOT__changes__DOT__ids=changed[6].ids;
 decltype(owners[6].retired) &sparse_tile__DOT__banks__BRA__6__KET____DOT__dummy1=owners[6].retired;
 decltype(qc[6]) &sparse_tile__DOT__banks__BRA__6__KET____DOT__owner__DOT__qc=qc[6];
 decltype(rc[6]) &sparse_tile__DOT__banks__BRA__6__KET____DOT__owner__DOT__rc=rc[6];
 decltype(changed[6].peak) &sparse_tile__DOT__banks__BRA__6__KET____DOT__changed_peak=changed[6].peak;
 decltype(banks[6].member_peak) &sparse_tile__DOT__banks__BRA__6__KET____DOT__member_peak=banks[6].member_peak;
 decltype(fronts[6].state) &sparse_tile__DOT__banks__BRA__6__KET____DOT__front__DOT__state=fronts[6].state;
 decltype(banks[7].labels) &sparse_tile__DOT__banks__BRA__7__KET____DOT__bank__DOT__labels=banks[7].labels;
 decltype(changed[7].wr) &sparse_tile__DOT__banks__BRA__7__KET____DOT__changes__DOT__wr=changed[7].wr;
 decltype(changed[7].ids) &sparse_tile__DOT__banks__BRA__7__KET____DOT__changes__DOT__ids=changed[7].ids;
 decltype(owners[7].retired) &sparse_tile__DOT__banks__BRA__7__KET____DOT__dummy1=owners[7].retired;
 decltype(qc[7]) &sparse_tile__DOT__banks__BRA__7__KET____DOT__owner__DOT__qc=qc[7];
 decltype(rc[7]) &sparse_tile__DOT__banks__BRA__7__KET____DOT__owner__DOT__rc=rc[7];
 decltype(changed[7].peak) &sparse_tile__DOT__banks__BRA__7__KET____DOT__changed_peak=changed[7].peak;
 decltype(banks[7].member_peak) &sparse_tile__DOT__banks__BRA__7__KET____DOT__member_peak=banks[7].member_peak;
 decltype(fronts[7].state) &sparse_tile__DOT__banks__BRA__7__KET____DOT__front__DOT__state=fronts[7].state;
};
}
