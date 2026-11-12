#pragma once
#include "node_state_model.hpp"
#include "support_models.hpp"
namespace r2_model {
struct ExternalBankCycle {
 enum{IDLE,INIT,SEED,POP_HEAD,POP_DIR,POP_READ,POP_CAPTURE,POP_DRAIN,COMMIT,FENCE,MIN_WORD,MIN_END};
 enum{FREE,POP_SEND,POP_WAIT,PROP_SEND,PROP_WAIT,COMMIT_SEND,COMMIT_WAIT,PUBLISH_READY,PUBLISH_WAIT,CLEAR_SEND,CLEAR_WAIT,SEED_SEND,SEED_WAIT};
 struct Ctx {unsigned state=FREE;uint32_t node=0,arg=0;uint64_t pair=0;};std::array<Ctx,32>ctx{};
 struct Append{bool valid=false,present=false;unsigned context=0,id=0,key=0,version=0;uint32_t node=0;}append;
 NodeStateCycle cache;ExternalChanged changed;Fifo<PopEvent>parents;Fifo<unsigned,1024>pool;
 std::array<uint64_t,4096>directory{};std::array<uint64_t,1024>header{};std::array<uint32_t,1024>next{};std::array<uint64_t,64>bitmap{};
 uint64_t groups=0,directory_q=0,header_q=0,last_dir=0,selected_word=0;uint32_t next_q=0,pointer=~0u;unsigned key=0,last_key=0,selected_group=0;
 bool last_valid=false,done=false,has_bucket=false,local_error=false,error=false,ca=false,sv=false,arb_hold=false,arb_selected=false,arb_turn=false,state_fence=false;
 unsigned state=IDLE,number=0,command=0,bucket=0,min_bucket=0;uint32_t source=0,node_count=0,state_base=0,commit_node=0;bool upstream_fenced=false;
 uint32_t sn=0,sarg=0;uint64_t sval=0;unsigned sop=0,sid=0;
 bool pr=false,ev=false,er=false,mark_idle=false;uint32_t event_line=0;unsigned event_mask=0;
 bool mem_valid=false,mem_ready=false,mem_write=false,rsp_valid=false;uint32_t mem_line=0;unsigned mem_id=0,rsp_id=0;Line mem_data{},rsp_data{};
 unsigned pool_init=0,init_sent=0,init_acked=0;uint16_t init_busy=0;
 uint32_t active_count=0,commit_count=0,stale_count=0;unsigned member_peak=0;
 int free_context=-1,send_context=-1,prop_context=-1,publish_context=-1,init_free=-1;unsigned live_count=0,pop_count=0;
 bool selected=false,sr=false,bank_response=false,parent_iv=false,pop_capture=false,append_select=false,cr=false;PopEvent parent_data{};
 void combin(){
  free_context=send_context=prop_context=publish_context=-1;live_count=pop_count=0;
  for(unsigned i=0;i<32;++i){auto c=ctx[i];if(c.state==FREE&&free_context<0)free_context=i;if(c.state!=FREE)++live_count;if(c.state==POP_SEND||c.state==POP_WAIT)++pop_count;
   if((c.state==POP_SEND||c.state==COMMIT_SEND||c.state==CLEAR_SEND||c.state==SEED_SEND)&&send_context<0)send_context=i;
   if(c.state==PROP_SEND&&prop_context<0)prop_context=i;if(c.state==PUBLISH_READY&&publish_context<0)publish_context=i;
  }
  init_free=init_busy==65535?-1:__builtin_ctz(unsigned(~init_busy)&65535);
  selected=arb_hold?arb_selected:(changed.mv&&(!sv||arb_turn));
  cache.iv=selected?changed.mv:sv;cache.node=selected?changed.mn:sn;cache.opcode=selected?1:sop;cache.operand=selected?0:sval;cache.argument=selected?0:sarg;cache.tag=(selected?32:0)|(selected?changed.mid:sid);cache.fence=state_fence;cache.state_base=state_base;cache.node_count=node_count;cache.ordy=true;cache.combin();
  sr=!selected&&cache.ir;bank_response=cache.ov&&cache.otag<32;
  changed.ev=ev;changed.line=event_line;changed.mask=event_mask;changed.commit=state==COMMIT;cr=state==COMMIT&&free_context>=0;changed.cr=cr;changed.mr=selected&&cache.ir;changed.rv=cache.ov&&cache.otag>=32;changed.rid=cache.otag&31;changed.rn=cache.onode;changed.first=cache.status&1;changed.combin();
  er=changed.er;mark_idle=changed.mark_idle;error=local_error||changed.error||cache.error;
  parent_iv=bank_response&&ctx[cache.otag&31].state==POP_WAIT&&(cache.status&1);parent_data={cache.onode,uint64_t(cache.old_record[1])<<32|cache.old_record[0]};
  append_select=publish_context>=0&&pool.ov;
  pop_capture=state==POP_CAPTURE&&free_context>=0&&parents.count+parents.ov+pop_count<64&&pool.ready(append_select);
 }
 void step(bool rst){
  cache.rst=rst;
  if(rst){cache.step();changed.edge(true);parents={};pool={};ctx={};append={};state=IDLE;done=has_bucket=local_error=sv=arb_hold=arb_turn=arb_selected=state_fence=last_valid=mem_valid=ca=false;min_bucket=0;bitmap={};groups=0;pointer=~0u;key=0;mem_id=0;mem_write=false;mem_line=0;mem_data={};commit_node=active_count=commit_count=stale_count=member_peak=0;pool_init=init_sent=init_acked=init_busy=0;return;}
  const auto oldctx=ctx;const auto a=append;unsigned oldstate=state;bool oldsv=sv,oldmem=mem_valid,oldlast=last_valid;auto oldlastkey=last_key;auto oldlastdir=last_dir;auto olddirq=directory_q;auto oldheader=header_q;auto oldnext=next_q;auto oldpointer=pointer;auto oldkey=key;auto oldgroups=groups;auto oldword=selected_word;auto oldselectedgroup=selected_group;
  auto oldinit=init_sent,oldacked=init_acked,oldpoolinit=pool_init;auto oldbusy=init_busy;unsigned oldpoolcount=pool.count+pool.ov,oldpoolout=pool.od;bool poolir=pool.ready(append_select);
  bool response=bank_response;unsigned response_id=cache.otag&31,response_status=cache.status;uint32_t response_node=cache.onode,response_pending=cache.old_record[2];bool cache_done=cache.fence_done;bool oldmarkidle=mark_idle;bool oldcv=changed.cv;uint32_t changednode=changed.node;bool parent_empty=parents.count==0&&!parents.ov;
  bool niv=cache.iv,nir=cache.ir;
  bool oldpresent=(bitmap[a.key/64]>>(a.key%64))&1; (void)oldpresent;
  bool fwd=oldlast&&oldlastkey==a.key,present=fwd||a.present;uint64_t previous=fwd?oldlastdir:olddirq;uint64_t published=(present?(previous&0xffffffff00000000ull):uint64_t(a.id)<<32)|a.id;
  // Synchronous RAM reads sample old contents before writes at this edge.
  if(append_select||oldstate==POP_HEAD)directory_q=directory[append_select?oldctx[publish_context].pair>>52:oldkey];
  if(!a.valid){header_q=header[oldpointer&1023];next_q=next[oldpointer&1023];}
  if(a.valid){directory[a.key]=published;header[a.id]=uint64_t(a.version)<<32|a.node;next[a.id]=~0u;if(present)next[unsigned(previous)&1023]=a.id;}
  parents.step(parent_iv,parent_data,pr);
  pool.step((oldstate==INIT&&oldpoolinit<1024)||pop_capture,oldstate==INIT?oldpoolinit:oldpointer&1023,append_select);
  changed.edge(false);cache.step();
  if(niv){if(nir){arb_hold=false;arb_turn=!selected;}else{arb_hold=true;arb_selected=selected;}}
  ca=false;append.valid=false;
  if(oldstate!=INIT)member_peak=std::max(member_peak,1024-oldpoolcount);
  // Readiness was checked before parents.step; POP credit guarantees capacity.
  if(command==0)done=false;if(oldmem&&mem_ready)mem_valid=false;if(oldsv&&sr)sv=false;
  if((!oldsv||sr)&&send_context>=0){auto c=oldctx[send_context];sv=true;sid=send_context;sn=c.node;sval=c.pair;sarg=c.arg;
   switch(c.state){case POP_SEND:sop=2;ctx[send_context].state=POP_WAIT;break;case COMMIT_SEND:sop=3;ctx[send_context].state=COMMIT_WAIT;break;case CLEAR_SEND:sop=4;ctx[send_context].state=CLEAR_WAIT;break;case SEED_SEND:sop=5;ctx[send_context].state=SEED_WAIT;break;default:local_error=true;}
  }
  if(response){if((response_status&8)||oldctx[response_id].node!=response_node)local_error=true;
   switch(oldctx[response_id].state){
    case POP_WAIT:ctx[response_id].state=FREE;if(response_status&1)++active_count;else ++stale_count;break;
    case COMMIT_WAIT:ctx[response_id].arg=((((response_pending>>12)+1)&65535)<<12)|(oldctx[response_id].pair>>52);ctx[response_id].state=(response_status&1)?PUBLISH_READY:CLEAR_SEND;break;
    case CLEAR_WAIT:if(!(response_status&1))local_error=true;ctx[response_id].state=FREE;ca=true;commit_node=response_node;++commit_count;break;
    case SEED_WAIT:ctx[response_id].state=PUBLISH_READY;ctx[response_id].arg=0x1000;break;
    default:local_error=true;
   }
  }
  if(append_select){auto c=oldctx[publish_context];unsigned k=c.pair>>52;append={true,bool(bitmap[k/64]>>(k%64)&1),unsigned(publish_context),oldpoolout,k,c.arg>>12,c.node};ctx[publish_context].state=PUBLISH_WAIT;}else if(publish_context>=0&&!pool.ov)local_error=true;
  if(a.valid){bitmap[a.key/64]|=1ull<<(a.key%64);groups|=1ull<<(a.key/64);last_valid=true;last_key=a.key;last_dir=published;ctx[a.context].state=oldstate==SEED?FREE:CLEAR_SEND;}
  if(oldstate==COMMIT){
   if(oldcv&&cr){ctx[free_context].node=changednode;ctx[free_context].state=PROP_SEND;}
   if((!oldmem||mem_ready)&&prop_context>=0){mem_valid=true;mem_write=false;mem_line=oldctx[prop_context].node>>2;mem_id=prop_context;ctx[prop_context].state=PROP_WAIT;}
   if(rsp_valid){if(rsp_id>=32||oldctx[rsp_id&31].state!=PROP_WAIT)local_error=true;else{ctx[rsp_id].pair=rsp_data[oldctx[rsp_id].node&3];ctx[rsp_id].state=COMMIT_SEND;}}
  }
  unsigned gpb=(node_count+31)>>5,init_total=gpb*3;
  switch(oldstate){
   case IDLE:if(command&&!done)switch(command){
    case 1:state=INIT;bitmap={};groups=0;last_valid=false;pool_init=init_sent=init_acked=init_busy=0;break;
    case 2:key=bucket;last_valid=false;state=POP_HEAD;break;case 3:state=COMMIT;break;case 4:done=true;break;
    case 5:has_bucket=oldgroups!=0;selected_group=oldgroups?__builtin_ctzll(oldgroups):63;state=MIN_WORD;break;case 6:state=FENCE;break;default:local_error=true;
   }break;
   case INIT:
    if(oldpoolinit<1024&&poolir)pool_init=oldpoolinit+1;
    if((!oldmem||mem_ready)&&oldinit<init_total&&init_free>=0){mem_valid=mem_write=true;mem_id=init_free;init_busy|=1u<<init_free;init_sent=oldinit+1;
     if(oldinit<gpb){mem_line=oldinit*8+number;mem_data.fill(INF);for(unsigned s=0;s<4;++s)if((oldinit*32+number*4+s)==source)mem_data[s]=0;}
     else{mem_line=state_base+(oldinit-gpb)*8+number;mem_data={INF,0,INF,0};}
    }
    if(rsp_valid){if(rsp_id>=16||!(oldbusy>>rsp_id&1))local_error=true;else{init_busy&=~(1u<<rsp_id);init_acked=oldacked+1;}}
    if(oldpoolinit==1024&&oldacked==init_total&&!oldbusy&&!oldmem){state=SEED;if(((source>>2)&7)==number)ctx[0]={SEED_SEND,source,0,0};}break;
   case SEED:if(live_count==0&&!oldsv&&!a.valid){state_fence=true;if(cache_done){state_fence=false;done=true;state=IDLE;}}break;
   case POP_HEAD:state=POP_DIR;break;
   case POP_DIR:{bool has=bitmap[oldkey/64]>>(oldkey%64)&1;pointer=has?olddirq>>32:~0u;bitmap[oldkey/64]&=~(1ull<<(oldkey%64));if(!bitmap[oldkey/64])groups&=~(1ull<<(oldkey/64));state=POP_READ;break;}
   case POP_READ:state=oldpointer==~0u?POP_DRAIN:POP_CAPTURE;break;
   case POP_CAPTURE:if(pop_capture){ctx[free_context].node=oldheader;ctx[free_context].arg=((oldheader>>32)<<12)|oldkey;ctx[free_context].state=POP_SEND;pointer=oldnext;state=POP_READ;}break;
   case POP_DRAIN:if(live_count==0&&!oldsv&&parent_empty){done=true;state=IDLE;}break;
   case COMMIT:if(!oldcv&&live_count==0&&!oldsv&&!a.valid&&!oldmem){state_fence=true;if(cache_done){state_fence=false;done=true;state=IDLE;}}break;
   case FENCE:if(upstream_fenced&&oldmarkidle){state_fence=true;if(cache_done){state_fence=false;done=true;state=IDLE;}}break;
   case MIN_WORD:selected_word=bitmap[oldselectedgroup];state=MIN_END;break;
   case MIN_END:min_bucket=(oldselectedgroup<<6)|(oldword?__builtin_ctzll(oldword):63);has_bucket&=oldword!=0;done=true;state=IDLE;break;
   default:local_error=true;
  }
 }
};
}
