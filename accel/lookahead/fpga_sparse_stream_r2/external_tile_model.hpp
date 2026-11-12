#pragma once
#include "external_bank_model.hpp"
#include "owner_pipeline_model.hpp"
#include "../fpga_sparse_stream/tile_model.hpp"
namespace r2_model {
struct ExternalTileModel {
 bool clk=false,last_clk=false,rst=false,start=false,done=false,error=false;
 uint32_t node_count=0,state_base=0,row_base=0,edge_base=0,cost_base=0,job_base=0;unsigned jobs=0,cell_count=0,cost_count=0;
 unsigned physical_valid=0,physical_ready=0,physical_write=0,physical_rsp_valid=0,physical_rsp_ready=0;uint64_t physical_id=0,physical_rsp_id=0;
 std::array<uint32_t,8> physical_line{};std::array<uint32_t,64>physical_data{},physical_rsp_data{};
 unsigned issued=0,accepted=0,committed=0,owner_error=0,phase=0,qid=0;uint32_t wave=0;std::array<uint32_t,8>commit_nodes{},active_counts{},commit_counts{};uint64_t mshr_peaks=0,dirty_peaks=0;
 unsigned r2_external_tile__DOT__bank_error=0,r2_external_tile__DOT__meta_error=0,r2_external_tile__DOT__reduce_error=0,r2_external_tile__DOT__fabric_error=0,r2_external_tile__DOT__front_error=0,r2_external_tile__DOT__queue_error=0;
 std::array<ExternalBankCycle,8>banks;std::array<OwnerCycle,8>owners;std::array<sparse_model::Front,8>fronts;std::array<Metadata,8>meta;std::array<PopFork,8>forks;std::array<CellReducer,8>reducers;
 Router8<PopEvent>router;Router8<CellEvent>cellrouter;Control8 control;Minimum8 minimum;FabricCycle fabric{41,8};
 unsigned command=7,command_epoch=0,bucket=0,bucket_epoch=0;uint32_t source=0,targets=0,cell_base=0,output_base=0;
 std::array<bool,8>reset_seen{},leaf_cost_we{},cost_seen{},local_reset{};std::array<unsigned,8>leaf_cost_index{};std::array<uint64_t,8>leaf_cost_data{};
 bool cost_we=false,ctl_valid=false,ctl_write=false,export_en=false,local_error=false;unsigned cost_index=0,cost_pos=0,ctl_id=0,export_index=0,output_sent=0,output_acked=0;uint16_t write_busy=0;uint64_t cost_data=0;Line cost_beat{},ctl_data{};std::array<uint64_t,8>export_hold{};uint32_t ctl_line=0;
 std::array<uint32_t,4>record_a{};std::array<uint32_t,2>record_b{};uint32_t recorded=0;unsigned after_neutral=0,closure_drain=0,held_minimum=0;
 ExternalTileModel(){for(unsigned i=0;i<8;++i)banks[i].number=i;}
 void request(unsigned c,bool v,bool wr,uint32_t line,unsigned id,const Line&data){fabric.cv[c]=v;fabric.cw[c]=wr;fabric.cl[c]=line;fabric.ci[c]=id;fabric.cd[c]=data;}
 static Line unpack(const std::array<uint32_t,8>&x){Line a{};for(unsigned i=0;i<4;++i)a[i]=uint64_t(x[2*i+1])<<32|x[2*i];return a;}
 void combin(){
  control.op=command;control.epoch=command_epoch;fabric.rst=rst;
  error=local_error;issued=accepted=committed=owner_error=0;mshr_peaks=dirty_peaks=0;r2_external_tile__DOT__bank_error=r2_external_tile__DOT__meta_error=r2_external_tile__DOT__reduce_error=r2_external_tile__DOT__front_error=0;r2_external_tile__DOT__queue_error=0;
  for(unsigned i=0;i<8;++i){unsigned op=control.leaf_op[i];local_reset[i]=rst||op==7;auto &b=banks[i];auto&o=owners[i];auto&f=fronts[i];auto&m=meta[i];auto&re=reducers[i];auto&fork=forks[i];
   b.command=(op==1||op==2||op==3||op==5||op==6)?op:0;b.bucket=bucket;b.source=source;b.node_count=node_count;b.state_base=state_base;b.upstream_fenced=o.fence_done;
   b.ev=o.c.events.ov;b.event_line=o.c.events.od.line;b.event_mask=o.c.events.od.mask;b.combin();
   o.update_ready=b.er;o.fence=op==6;o.combin();
   f.row_base=row_base;f.edge_base=edge_base;f.cost_we=leaf_cost_we[i];f.cost_index=leaf_cost_index[i];f.cost_data=leaf_cost_data[i];f.combin();
   m.base=cell_base;m.cells=cell_count;m.qid=qid;m.epoch=bucket_epoch;m.combin();
   fork.iv=b.parents.ov;fork.input=b.parents.od;fork.ar=f.pr;fork.br=m.ir;fork.combin();b.pr=fork.ir;
   f.pv=fork.av;f.pn=fork.input.node;f.pp=fork.input.pair;m.iv=fork.bv;m.input=fork.input;
   re.init=op==1;re.entries=(cell_count+7)>>3;re.qid=qid;re.epoch=bucket_epoch;re.export_en=export_en;re.export_index=export_index;re.combin();
   router.iv[i]=f.lane.ov;router.input[i]={f.lane.out.node,f.lane.out.pair};router.ordy[i]=o.ir;
   cellrouter.iv[i]=m.ov;cellrouter.input[i]=m.output;cellrouter.ordy[i]=re.ir;
  }
  router.combin();cellrouter.combin();
  for(unsigned i=0;i<8;++i){auto &b=banks[i];auto &o=owners[i];auto &f=fronts[i];auto&m=meta[i];auto&re=reducers[i];
   f.ordy=router.ir[i];f.combin();o.iv=router.q[i].ov;o.node=router.q[i].od.node;o.pair=router.q[i].od.pair;m.ordy=cellrouter.ir[i];
   re.iv=cellrouter.q[i].ov;auto e=cellrouter.q[i].od;re.index=e.cell>>3;re.pair=e.pair;re.event_qid=e.qid;re.event_epoch=e.epoch;
   request(i,o.mem_valid,o.mem_write,o.mem_line,o.mem_id,unpack(o.mem_data));fabric.rr[i]=o.rsp_ready;
   request(8+i,f.mem_valid,false,f.mem_line,f.mem_id,{});fabric.rr[8+i]=true;
   request(16+i,b.mem_valid,b.mem_write,b.mem_line,b.mem_id,b.mem_data);fabric.rr[16+i]=true;
   request(24+i,m.mem_valid,false,m.mem_line,m.mem_id,{});fabric.rr[24+i]=true;
   request(33+i,b.cache.mem_valid,b.cache.mem_write,b.cache.mem_line,b.cache.mem_id,unpack(b.cache.mem_data));fabric.rr[33+i]=b.cache.rsp_ready;
   auto op=control.leaf_op[i];control.done[i]=op==7?reset_seen[i]:op==0?!b.done:op==1?(b.done&&re.init_done):op==4?(f.idle()&&forks[i].idle()):op==6?(o.fence_done&&b.mark_idle&&b.done):b.done;
   minimum.keys[i]=(b.has_bucket?0:4096)|b.min_bucket;minimum.valid[i]=op==5&&b.done;minimum.epochs[i]=control.leaf_epoch[i];
   active_counts[i]=b.active_count;commit_counts[i]=b.commit_count;commit_nodes[i]=b.commit_node;
   if(f.lane.ov&&f.ordy)issued|=1u<<i;if(o.iv&&o.ir)accepted|=1u<<i;if(b.ca)committed|=1u<<i;
   if(o.error)owner_error|=1u<<i;if(b.error)r2_external_tile__DOT__bank_error|=1u<<i;if(f.local_error)r2_external_tile__DOT__front_error|=1u<<i;if(m.error)r2_external_tile__DOT__meta_error|=1u<<i;if(re.error)r2_external_tile__DOT__reduce_error|=1u<<i;
   error|=o.error||b.error||f.local_error||m.error||re.error;mshr_peaks|=uint64_t(o.mshr_peak)<<(6*i);dirty_peaks|=uint64_t(o.dirty_peak)<<(5*i);
  }
  request(32,ctl_valid,ctl_write,ctl_line,ctl_id,ctl_data);fabric.rr[32]=true;
  for(unsigned p=0;p<8;++p){fabric.mr[p]=physical_ready>>p&1;fabric.sv[p]=physical_rsp_valid>>p&1;fabric.si[p]=physical_rsp_id>>(p*6)&63;for(unsigned s=0;s<4;++s)fabric.sd[p][s]=uint64_t(physical_rsp_data[p*8+s*2+1])<<32|physical_rsp_data[p*8+s*2];}
  fabric.combin();physical_valid=physical_write=physical_rsp_ready=0;physical_id=0;
  for(unsigned p=0;p<8;++p){physical_valid|=unsigned(fabric.mv[p])<<p;physical_write|=unsigned(fabric.mw[p])<<p;physical_rsp_ready|=unsigned(fabric.sr[p])<<p;physical_line[p]=fabric.ml[p];physical_id|=uint64_t(fabric.mi[p])<<(p*6);for(unsigned s=0;s<4;++s){physical_data[p*8+s*2]=fabric.md[p][s];physical_data[p*8+s*2+1]=fabric.md[p][s]>>32;}}
  for(unsigned i=0;i<8;++i){auto &o=owners[i];auto&f=fronts[i];auto&b=banks[i];auto&m=meta[i];o.mem_ready=fabric.cr[i];o.rsp_valid=fabric.rv[i];o.rsp_id=fabric.ri[i];f.mem_ready=fabric.cr[8+i];f.rsp_valid=fabric.rv[8+i];f.rsp_id=fabric.ri[8+i];f.rsp_data=fabric.rd[8+i];b.mem_ready=fabric.cr[16+i];b.rsp_valid=fabric.rv[16+i];b.rsp_id=fabric.ri[16+i];b.rsp_data=fabric.rd[16+i];m.mem_ready=fabric.cr[24+i];m.rsp_valid=fabric.rv[24+i];m.rsp_id=fabric.ri[24+i];m.rsp_data=fabric.rd[24+i];b.cache.mem_ready=fabric.cr[33+i];b.cache.rsp_valid=fabric.rv[33+i];b.cache.rsp_id=fabric.ri[33+i];
   for(unsigned s=0;s<4;++s){o.rsp_data[s*2]=fabric.rd[i][s];o.rsp_data[s*2+1]=fabric.rd[i][s]>>32;b.cache.rsp_data[s*2]=fabric.rd[33+i][s];b.cache.rsp_data[s*2+1]=fabric.rd[33+i][s]>>32;}
  }
  r2_external_tile__DOT__fabric_error=fabric.error;error|=fabric.error;
 }
 void neutral(unsigned destination){command=0;command_epoch=(command_epoch+1)&255;after_neutral=destination;phase=6;}
 void launch(unsigned operation,unsigned waiting){command=operation;command_epoch=(command_epoch+1)&255;phase=waiting;}
 void controller(){
  if(rst){phase=0;command=7;command_epoch=0;done=local_error=cost_we=ctl_valid=export_en=false;ctl_id=wave=qid=bucket_epoch=write_busy=output_sent=output_acked=closure_drain=0;return;}
  unsigned oldphase=phase,oldsent=output_sent,oldacked=output_acked;uint16_t oldbusy=write_busy;bool oldctl=ctl_valid;unsigned freewrite=oldbusy==65535?32:__builtin_ctz(unsigned(~oldbusy)&65535);cost_we=false;
  if(oldctl&&fabric.cr[32])ctl_valid=false;
  if(oldphase>=30&&oldphase<=37&&fabric.rv[32]){unsigned id=fabric.ri[32];if(id>=16||!(oldbusy>>id&1))local_error=true;else{write_busy&=~(1u<<id);output_acked=oldacked+1;}}
  switch(oldphase){
   case 0:if(start){done=false;cost_pos=qid=0;phase=1;if(!jobs||jobs>64||!cell_count||cell_count>32768||!cost_count||cost_count>16)local_error=true;}break;
   case 1:if(!oldctl){ctl_valid=true;ctl_write=false;ctl_id=0;ctl_line=cost_base+(cost_pos>>2);ctl_data={};phase=2;}break;
   case 2:if(fabric.rv[32]){cost_beat=fabric.rd[32];phase=3;}break;
   case 3:{unsigned oldpos=cost_pos;cost_we=true;cost_index=oldpos;cost_data=cost_beat[oldpos&3];++cost_pos;if(oldpos+1==cost_count)phase=4;else if((oldpos&3)==3)phase=1;break;}
   case 4:{bool all=true;for(auto v:cost_seen)all&=v;if(!oldctl&&all){ctl_valid=true;ctl_write=false;ctl_id=0;ctl_line=job_base+qid;phase=5;}break;}
   case 5:if(fabric.rv[32]){auto d=fabric.rd[32];source=d[0];targets=d[0]>>32;cell_base=d[1];output_base=d[1]>>32;wave=bucket_epoch=0;if(source>=node_count||targets>cell_count)local_error=true;launch(7,7);}break;
   case 6:if(control.complete())phase=after_neutral;break;
   case 7:if(control.complete())neutral(8);break;
   case 8:launch(1,9);break;case 9:if(control.complete())neutral(10);break;case 10:launch(5,11);break;
   case 11:if(control.complete()&&minimum.ov&&minimum.epoch==command_epoch){if(!wave){if((minimum.key&4096)||!targets)neutral(30);else{bucket=minimum.key&4095;bucket_epoch=(bucket_epoch+1)&65535;neutral(12);}}else if(!(minimum.key&4096)&&(minimum.key&4095)==bucket)neutral(12);else{held_minimum=minimum.key;closure_drain=0;phase=23;}}break;
   case 12:launch(2,13);++wave;break;case 13:if(control.complete())neutral(14);break;case 14:launch(4,15);break;case 15:if(control.complete()&&router.idle())neutral(16);break;case 16:launch(6,17);break;case 17:if(control.complete())neutral(18);break;case 18:launch(3,19);break;case 19:if(control.complete())neutral(10);break;
   case 23:{bool all=cellrouter.idle()&&fabric.idle;for(unsigned i=0;i<8;++i)all&=meta[i].idle()&&reducers[i].idle();if(all){if(closure_drain==7)phase=24;else ++closure_drain;}else closure_drain=0;break;}
   case 24:if(recorded>targets)local_error=true;else if(recorded==targets||(held_minimum&4096))neutral(30);else{bucket=held_minimum&4095;bucket_epoch=(bucket_epoch+1)&65535;neutral(12);}break;
   case 30:output_sent=output_acked=write_busy=export_index=0;export_en=true;phase=31;break;case 31:phase=32;break;case 32:phase=33;break;
   case 33:for(unsigned i=0;i<8;++i)export_hold[i]=reducers[i].export_pair;phase=34;break;
   case 34:case 35:if((!oldctl||fabric.cr[32])&&freewrite<16){ctl_valid=ctl_write=true;ctl_id=freewrite;ctl_line=output_base+oldsent;for(unsigned i=0;i<4;++i)ctl_data[i]=export_hold[i+(oldphase==35?4:0)];write_busy|=1u<<freewrite;output_sent=oldsent+1;if(oldsent+1==((cell_count+3)>>2)){export_en=false;phase=37;}else if(oldphase==34)phase=35;else{++export_index;phase=31;}}break;
   case 37:if(oldacked==oldsent&&!oldbusy&&!oldctl&&fabric.idle){if(qid+1==jobs){done=true;phase=0;}else{++qid;phase=4;}}break;
   default:local_error=true;
  }
 }
 void step(){
  const auto olda=record_a;const auto oldb=record_b;auto oldcostwe=cost_we;auto oldcostindex=cost_index;auto oldcostdata=cost_data;bool globalreset=rst||command==7;
  for(unsigned i=0;i<4;++i)record_a[i]=reducers[2*i].recorded+reducers[2*i+1].recorded;for(unsigned i=0;i<2;++i)record_b[i]=olda[2*i]+olda[2*i+1];
  controller();recorded=oldb[0]+oldb[1];
  for(unsigned i=0;i<8;++i){auto op=control.leaf_op[i];bool oldwe=leaf_cost_we[i];unsigned oldindex=leaf_cost_index[i];leaf_cost_we[i]=oldcostwe&&(op==7||op==0);if(leaf_cost_we[i]){leaf_cost_index[i]=oldcostindex;leaf_cost_data[i]=oldcostdata;}if(rst||start)cost_seen[i]=false;else if(oldwe&&oldindex==cost_count-1)cost_seen[i]=true;reset_seen[i]=op==7;
   banks[i].step(local_reset[i]);owners[i].rst=local_reset[i];owners[i].step();fronts[i].step(local_reset[i]);meta[i].step(local_reset[i]);forks[i].step(local_reset[i]);reducers[i].step(local_reset[i]);
  }
  router.step(globalreset);cellrouter.step(globalreset);fabric.step();control.step(rst);minimum.step(rst);
 }
 void eval(){if(clk&&!last_clk)step();last_clk=clk;combin();}
};
}
