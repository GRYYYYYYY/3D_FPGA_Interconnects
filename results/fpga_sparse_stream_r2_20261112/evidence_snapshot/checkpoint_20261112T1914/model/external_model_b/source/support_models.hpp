#pragma once
#include "fabric_model.hpp"
namespace r2_model {
struct PopEvent{uint32_t node=0;uint64_t pair=0;};
struct CellEvent{unsigned qid=0,epoch=0,cell=0;uint64_t pair=0;};
struct PopFork {
 bool a=false,b=false,iv=false,ir=false,av=false,bv=false,ar=false,br=false;PopEvent input{};unsigned accepted=0;
 void combin(){av=iv&&!a;bv=iv&&!b;ir=(a||ar)&&(b||br);}
 void step(bool rst){if(rst){a=b=false;accepted=0;return;}if(iv&&ir){a=b=false;++accepted;}else{if(av&&ar)a=true;if(bv&&br)b=true;}}
 bool idle()const{return !iv&&!a&&!b;}
};
// All four sectors have independent finite queues. Atomic mark results are held
// in reserved mailboxes until the finite changed worklist accepts the ID.
struct ExternalChanged {
 std::array<Fifo<uint32_t>,4> q;Fifo<uint32_t,512> list;
 uint32_t live=0,sent=0,ready=0;std::array<uint32_t,32>cn{};unsigned rotate=0;
 bool ev=false,er=false,commit=false,cv=false,cr=false,mv=false,mr=false,rv=false,first=false,mark_idle=false,error=false;
 uint32_t line=0,node=0,mn=0,rn=0;unsigned mask=0,mid=0,rid=0,peak=0,marks=0,duplicates=0,unique=0;
 int free_ctx=-1,sector=-1,publish=-1;std::array<bool,4>qr{};bool list_ready=false;
 void combin(){
  free_ctx=live==~0u?-1:__builtin_ctz(~live);publish=(live&ready)?__builtin_ctz(live&ready):-1;sector=-1;qr.fill(false);
  for(unsigned i=0;i<4;++i){unsigned k=(rotate+i)&3;if(q[k].ov){sector=k;break;}}
  if((!mv||mr)&&free_ctx>=0&&sector>=0&&!commit)qr[sector]=true;
  er=!commit;for(unsigned i=0;i<4;++i)if(mask>>i&1)er&=q[i].ready(qr[i]);
  cv=list.ov;node=list.od;list_ready=list.ready(cr&&commit);mark_idle=!mv&&!live;for(auto &x:q)mark_idle&=!x.ov&&!x.count;
 }
 void step(bool rst){
  if(rst){q={};list={};live=sent=ready=rotate=peak=marks=duplicates=unique=0;mv=error=false;return;}
  auto oldlive=live,oldsent=sent,oldready=ready;peak=std::max(peak,list.count+list.ov);
  for(unsigned s=0;s<4;++s)q[s].step(ev&&er&&(mask>>s&1),line*4+s,qr[s]);
  list.step(publish>=0,publish>=0?cn[publish]:0,cr&&commit);
  if(mv&&mr)sent|=1u<<mid;
  if(!mv||mr){mv=false;if(free_ctx>=0&&sector>=0&&!commit){mv=true;mid=free_ctx;/* input saved below before FIFO step */live|=1u<<free_ctx;sent&=~(1u<<free_ctx);ready&=~(1u<<free_ctx);rotate=(sector+1)&3;++marks;}}
  if(rv){unsigned bit=1u<<rid;if(!(oldlive&bit)||!(oldsent&bit)||(oldready&bit)||cn[rid]!=rn)error=true;else if(first)ready|=bit;else{live&=~bit;sent&=~bit;++duplicates;}}
  if(publish>=0&&list_ready){live&=~(1u<<publish);sent&=~(1u<<publish);ready&=~(1u<<publish);++unique;}
  if(publish>=0&&!list_ready&&!commit)error=true;
 }
 // The queue RAM output is sampled before any clocked action in the bank.
 void edge(bool rst){uint32_t selected=sector>=0?q[sector].od:0;bool take=(!mv||mr)&&free_ctx>=0&&sector>=0&&!commit;unsigned id=free_ctx;step(rst);if(!rst&&take){mn=selected;cn[id]=selected;}}
};
struct CellReducer {
 struct Item{bool seen=false;uint64_t pair=0;};std::array<Item,4096>memory{};Item ram{},last{};unsigned addr=0,last_addr=0,init_index=0;
 bool sv=false,last_valid=false,initializing=false,init_done=false,error=false,init=false,iv=false,ir=false,export_en=false;
 unsigned entries=0,index=0,export_index=0,qid=0,epoch=0,event_qid=0,event_epoch=0;uint64_t pair=0,spair=0,export_pair=0;
 uint32_t recorded=0,retired=0,forwarded=0;
 void combin(){ir=init_done&&!initializing&&!init&&!export_en;}
 bool idle()const{return !sv&&!initializing;}
 void step(bool rst){auto oldram=ram,base=(last_valid&&last_addr==addr)?last:ram;auto value=Item{true,(!base.seen||spair<base.pair)?spair:base.pair};bool oldinit=initializing,oldsv=sv,oldlv=last_valid;unsigned oldaddr=addr;
  if((iv&&ir)||export_en)ram=memory[iv&&ir?index:export_index];export_pair=oldram.seen?oldram.pair:0x7fc000007fc00000ull;
  if(oldinit&&init_index<entries)memory[init_index]={};else if(oldsv)memory[oldaddr]=value;
  if(rst){sv=last_valid=initializing=init_done=error=false;init_index=recorded=retired=forwarded=0;return;}
  sv=iv&&ir;last_valid=oldsv;
  if(init&&!init_done&&!oldinit){initializing=true;init_index=0;recorded=0;}
  if(oldinit){if(init_index==entries){initializing=false;init_done=true;}else ++init_index;}
  if(iv&&ir){addr=index;spair=pair;if(index>=entries||qid!=event_qid||epoch!=event_epoch)error=true;}
  if(oldsv){if(!base.seen)++recorded;if(oldlv&&last_addr==oldaddr)++forwarded;last_addr=oldaddr;last=value;++retired;}
 }
};
struct Metadata {
 struct Ctx{bool live=false,sent=false,ready=false;PopEvent pop;unsigned qid=0,epoch=0,cell=0;bool target=false;};std::array<Ctx,16>ctx{};
 bool iv=false,ir=false,ov=false,ordy=false,mem_valid=false,mem_ready=false,rsp_valid=false,rsp_ready=true,error=false;
 PopEvent input{};CellEvent output{};unsigned qid=0,epoch=0,cells=0,mem_id=0,rsp_id=0;uint32_t base=0,mem_line=0;Line rsp_data{};
 int free_ctx=-1,send=-1,emit=-1;unsigned peak=0,used=0,rotate=0,accepted=0,reads=0,targets=0,skipped=0;
 void combin(){free_ctx=send=emit=-1;used=0;for(unsigned i=0;i<16;++i){auto c=ctx[i];if(!c.live&&free_ctx<0)free_ctx=i;if(c.live){++used;if(!c.sent&&send<0)send=i;}}for(unsigned i=0;i<16;++i){unsigned k=(rotate+i)&15;if(ctx[k].live&&ctx[k].ready){emit=k;break;}}ir=free_ctx>=0;}
 bool idle()const{return !used&&!mem_valid&&!ov;}
 void step(bool rst){
  if(rst){ctx={};mem_valid=ov=error=false;peak=rotate=accepted=reads=targets=skipped=0;return;}auto old=ctx;peak=std::max(peak,used);
  if(iv&&ir){ctx[free_ctx]={true,false,false,input,qid,epoch,0,false};++accepted;}
  if(!mem_valid||mem_ready){mem_valid=false;if(send>=0){mem_valid=true;mem_line=base+(old[send].pop.node>>2);mem_id=send;ctx[send].sent=true;++reads;}}
  if(rsp_valid){if(rsp_id>=16||!old[rsp_id&15].live||!old[rsp_id&15].sent||old[rsp_id&15].ready)error=true;else{auto m=rsp_data[old[rsp_id].pop.node&3];ctx[rsp_id].ready=true;ctx[rsp_id].target=(m>>32)!=0;ctx[rsp_id].cell=m;}}
  if(!ov||ordy){ov=false;if(emit>=0){auto c=old[emit];ctx[emit].live=ctx[emit].ready=false;rotate=(emit+1)&15;if(!c.target||c.cell==~0u)++skipped;else{ov=true;output={c.qid,c.epoch,c.cell,c.pop.pair};++targets;if(c.cell>=cells)error=true;}}}
 }
};

template<class T>struct Router8 {
 std::array<Fifo<T>,8>q;std::array<unsigned,8>rotate{};std::array<bool,8>iv{},ir{},ordy{};std::array<T,8>input{};std::array<int,8>selection{};
 static unsigned destination(const PopEvent&e){return (e.node>>2)&7;}
 static unsigned destination(const CellEvent&e){return e.cell&7;}
 void combin(){ir.fill(false);for(unsigned b=0;b<8;++b){selection[b]=-1;for(unsigned p=0;p<8;++p){unsigned l=(rotate[b]+p)&7;if(iv[l]&&destination(input[l])==b){selection[b]=l;ir[l]=q[b].ready(ordy[b]);break;}}}}
 bool idle()const{for(auto &f:q)if(f.ov||f.count)return false;return true;}
 void step(bool rst){if(rst){q={};rotate={};return;}for(unsigned b=0;b<8;++b){bool put=selection[b]>=0;T data=put?input[selection[b]]:T{};bool accepted=put&&q[b].ready(ordy[b]);q[b].step(put,data,ordy[b]);if(accepted)rotate[b]=(rotate[b]+1)&7;}}
};
struct Control8 {
 unsigned op=7,epoch=0,root_op=7,root_epoch=0;std::array<unsigned,2>branch_op{7,7},branch_epoch{},group_epoch{};std::array<bool,2>group_done{};
 std::array<bool,8>done{},ack{};std::array<unsigned,8>leaf_op{7,7,7,7,7,7,7,7},leaf_epoch{},ack_epoch{};
 bool complete()const{return group_done[0]&&group_done[1]&&group_epoch[0]==epoch&&group_epoch[1]==epoch;}
 void step(bool rst){if(rst){root_op=7;root_epoch=0;branch_op={7,7};branch_epoch={};leaf_op.fill(7);leaf_epoch={};ack={};group_done={};group_epoch={};ack_epoch={};return;}
  auto old=*this;root_op=op;root_epoch=epoch;
  for(unsigned g=0;g<2;++g){bool all=true;for(unsigned i=g*4;i<g*4+4;++i)all&=done[i];if(all||old.branch_op[g]==0||old.branch_op[g]==7){branch_op[g]=old.root_op;branch_epoch[g]=old.root_epoch;}}
  for(unsigned i=0;i<8;++i){if(old.branch_epoch[i/4]!=old.leaf_epoch[i]&&(done[i]||old.leaf_op[i]==0)){leaf_op[i]=old.branch_op[i/4];leaf_epoch[i]=old.branch_epoch[i/4];}ack[i]=done[i];ack_epoch[i]=old.leaf_epoch[i];}
  for(unsigned g=0;g<2;++g){group_epoch[g]=old.ack_epoch[g*4];bool all=true;for(unsigned i=g*4;i<g*4+4;++i)all&=old.ack[i]&&old.ack_epoch[i]==old.ack_epoch[g*4];group_done[g]=all;}
 }
};
struct Minimum8 {
 std::array<unsigned,8>keys{},epochs{};std::array<bool,8>valid{};
 std::array<unsigned,4>a{},ae{};std::array<bool,4>av{};std::array<unsigned,2>b{},be{};std::array<bool,2>bv{};bool ov=false;unsigned key=8191,epoch=0;
 void step(bool rst){if(rst){av={};bv={};ov=false;key=8191;epoch=0;return;}auto old=*this;
  for(unsigned i=0;i<4;++i){a[i]=std::min(keys[2*i],keys[2*i+1]);ae[i]=epochs[2*i];av[i]=valid[2*i]&&valid[2*i+1]&&epochs[2*i]==epochs[2*i+1];}
  for(unsigned i=0;i<2;++i){b[i]=std::min(old.a[2*i],old.a[2*i+1]);be[i]=old.ae[2*i];bv[i]=old.av[2*i]&&old.av[2*i+1]&&old.ae[2*i]==old.ae[2*i+1];}
  key=std::min(old.b[0],old.b[1]);epoch=old.be[0];ov=old.bv[0]&&old.bv[1]&&old.be[0]==old.be[1];
 }
};
}
