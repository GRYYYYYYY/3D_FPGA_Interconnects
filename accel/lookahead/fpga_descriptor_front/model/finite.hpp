#pragma once
#include "../../fpga_decoupled_front/graph.hpp"
#include "../../fpga_sparse_stream_r2/pending17.hpp"
#include "../descriptor/packed.hpp"
#include "directory_adapter.hpp"
#include "transport_adapter.hpp"
#include "../output/output_model.hpp"
#include "../output/ack_model.hpp"
#include "../services/transport_model.hpp"
#include <array>
#include <fstream>
#include <memory>
#include <filesystem>
#include <iostream>
#include <limits>
#include <cassert>
#include <numeric>
#include <iomanip>
#include <optional>
namespace ec {
using T=uint64_t;constexpr T INF=pending17::INF;constexpr unsigned NIL=~0u;
inline void check(bool x,const char*s){if(!x)throw std::runtime_error(s);}
template<class X,unsigned N>struct Fifo {std::array<X,N>a{};unsigned head=0,n=0,peak=0;bool empty()const{return !n;}bool full()const{return n==N;}X&front(){check(n,"FIFO_EMPTY");return a[head];}const X&front()const{check(n,"FIFO_EMPTY");return a[head];}void push(const X&x){check(n<N,"FIFO_OVERFLOW");a[(head+n)%N]=x;++n;peak=std::max(peak,n);}X pop(){X x=front();head=(head+1)%N;--n;return x;}void clear(){head=n=0;}};
struct PairLine {std::array<T,4> p{INF,INF,INF,INF};};
struct Fragment {unsigned line=0;PairLine data;T due=0;bool resident=false;};
struct Member{unsigned node=0,arg=0,next=NIL;};
enum Kind{INIT,ROW,EDGE,META,POP_READ,CAN_READ,CAN_WRITE,SCR_READ,SCR_WRITE,OUT_WRITE,COST_LOAD,DESC_READ,KINDS};
struct Token{unsigned state=0,node=0;T pair=0,due=0;bool graph=false,meta=false;unsigned gen=0;T reusable=0,retire_due=0;dfdesc::Decoded decoded{};};
struct Header{unsigned state=0,node=0,gen=0,sent=0,got=0,need=0;T pair=0,due=0;};
struct Meta{unsigned state=0,node=0,gen=0;T pair=0,due=0;};
struct Ready{unsigned node=0;T pair=0,begin=0,end=0,due=0;};
struct Desc{bool live=false;unsigned node=0,gen=0,inflight=0;T pair=0,next=0,pos=0,end=0,due=0,reusable=0;};
struct Slot{unsigned state=0,desc=0,gen=0;T beat=0,due=0,reusable=0;};
struct ExportBeat{unsigned line=0;PairLine data;T due=0;};
struct Candidate{unsigned node=0;T pair=0,due=0;};
struct Tx {
 enum State{FREE,DELAY,READ_REQ,READ_WAIT,APPLY,WRITE_REQ,WRITE_WAIT,PV,EVENT,RELEASE,PUBLISH};
 unsigned state=FREE,node=0,op=0,arg=0,gen=0,token=NIL,append=0,event_sector=0;T due=0,pv_capture_due=0,old_label=INF;bool pv_captured=false;bool changed=false,valid=false;PairLine input,labels,next;std::array<unsigned,4>oldpv{},newpv{};
};
struct PopDelivery{unsigned token=0,node=0;T pair=0,due=0;bool valid=false;};
struct TargetDelivery{unsigned cell=0;T pair=0,due=0;};
struct Reservation{unsigned bank=0,token=NIL;T due=0;};
struct TxInput{unsigned node=0,op=0,arg=0,token=NIL;PairLine data;T due=0;};
struct Entry{unsigned line=0;uint8_t mask=0;PairLine value;};
struct Bank {
 std::array<Entry,4096>entry;std::array<uint8_t,1024>victim{};std::array<T,1024>set_until{};std::array<unsigned,4096>occupied{};unsigned used=0;
 Fifo<Candidate,16>candidate;Fifo<Fragment,16>fragment,merge,commit;std::array<Fragment,4>enum_pipe;unsigned enum_valid=0;bool enum_phase=false;Fifo<Fragment,1>enum_raw;Fifo<std::pair<unsigned,T>,2>atom;bool query_valid=false;Fragment query;
 std::array<unsigned,2048>spill_ids{};unsigned nspill=0,scan=0,enum_index=0,resident_pending=0;T enum_next=0;
 // Expand scratch and finalize merge each use one command, never simultaneously.
 unsigned scratch_state=0;Fragment scratch;bool first_spill=false;T scratch_due=0;
 Fifo<TxInput,2> op_input;Fifo<Candidate,2> candidate_input;unsigned adapter_state=0;bool adapter_event=false;unsigned adapter_sector=0;T adapter_due=0;
 std::array<Tx,8>tx;unsigned txmask=0,request_cursor=0,apply_cursor=0,pv_cursor=0,pub_cursor=0,pub_slot=NIL;T pub_ready=0;std::array<T,8>reusable_at{};unsigned last_released_line=NIL;T release_block_until=0;bool arb_merge=false;
 T accepted=0,retired=0,spills=0,merges=0,commits=0,changed=0,events=0,pops=0,stales=0,enum_launches=0,commit_admissions=0,word_stalls=0,set_stalls=0;
 unsigned txpeak=0,spill_peak=0;T last_retire=0,accumulator_tail=0;bool final_scan=false;
};
// Shared full-model and RTL-calibration enum control. FIFO includes its synchronous
// output stage in the configured 16 live words; two clocks put->handshake.
inline std::optional<Fragment> enum_clock(Bank&bk,T t,bool sink_ready){
 bool fifo_ir=!bk.fragment.full();std::optional<Fragment> out;
 if(sink_ready&&!bk.fragment.empty()&&bk.fragment.front().due<=t)out=bk.fragment.pop();
 bool advance=bk.enum_raw.empty()||fifo_ir;
 if(!bk.enum_raw.empty()&&fifo_ir){auto f=bk.enum_raw.pop();f.due=t+2;bk.fragment.push(f);}
 bool step=!(bk.enum_valid&8)||advance;
 if(step){unsigned old=bk.enum_valid;if(old&8){check(bk.enum_raw.empty(),"ENUM_RAW_OVERWRITE");bk.enum_raw.push(bk.enum_pipe[3]);}
  for(unsigned k=3;k>0;--k)bk.enum_pipe[k]=bk.enum_pipe[k-1];bool launch=!bk.enum_phase&&bk.enum_index<bk.used;
  if(launch){auto&e=bk.entry[bk.occupied[bk.enum_index++]];check(e.mask,"EMPTY_ENUM");bk.enum_pipe[0]={e.line,e.value,0,true};e.mask=0;++bk.resident_pending;++bk.enum_launches;}
  bk.enum_valid=((old<<1)&15)|unsigned(launch);bk.enum_phase=!bk.enum_phase;
 }
 return out;
}
struct Stats{T candidates=0,parents=0,zeros=0,waves=0,expected_degree=0,expected_row=0,expected_edge=0,graph_admit=0,meta_admit=0,valid_target_events=0,output_improvements=0,pop_transactions=0,stale=0,spills=0,merges=0,canonical_lines=0,changed_lines=0,events=0;std::array<T,64>lane_emit{},lane_block{},lane_alloc{};std::array<std::array<T,32>,KINDS>traffic{};unsigned fork_peak=0,H_peak=0,E_peak=0,M_peak=0,slots_peak=0,descriptor_peak=0,ready_peak=0;};
struct Model {
 Graph&g;unsigned sample;std::string configuration;bool fused;unsigned groups,lanes,group_slots;dfdesc::Admission admission;dfdesc::Image image;dfoutput::Service output_service;std::vector<std::optional<dfoutput::Update>>output_inputs;std::string outdir;T t=0,sample_start=0,init_end=0;Directory directory;std::vector<T>label;std::vector<unsigned>pv;std::vector<PairLine>scratch_backing;std::vector<uint8_t>spilled,consumed;std::vector<PairLine>device_output;std::vector<uint8_t>output_enqueued;unsigned output_acks=0,output_ack_peak=0;dfoutput::AckCollector<Request> output_ack_collector;std::vector<std::optional<Request>>output_ack_inputs=std::vector<std::optional<Request>>(32);T output_ack_stall_cycles=0;T export_start=0,export_end=0,output_stride=0;
 Transport transport;std::array<Transport::Port,32>&ports=transport.ports;std::array<Token,128>tokens;std::array<Header,128>headers;std::array<Meta,128>metas;std::array<Fifo<Ready,16>,16>ready;std::array<Desc,256>desc;std::array<Slot,512>slots;std::array<std::array<Candidate,6>,64>pipeline;std::array<unsigned,64>pipe_valid{};std::array<Fifo<Candidate,4>,64>candidate_source;std::array<std::optional<Candidate>,64>candidate_hold;std::array<unsigned,64>candidate_rr{};std::array<unsigned,64>lane_rr{};std::array<std::optional<Request>,208> local_request_hold{};std::array<std::optional<Request>,48> front_request_context{},front_return_context{};std::array<std::optional<Candidate>,64> front_candidate_context{};std::array<std::optional<TargetDelivery>,16>target_context{};std::array<std::optional<PopDelivery>,16>pop_context{};std::array<std::optional<Reservation>,16>reserve_launch{},reserve_capture{};std::array<bool,64>bank_reserving{};std::array<unsigned,16> edge_h{},target_h{};std::array<T,16>edge_h_due{},target_h_due{};std::array<unsigned,64>operand_h{};
 std::array<unsigned,16>alloc_rr{},token_rr{},edge_rr{},header_rr{},meta_rr{};std::array<T,128>header_reuse{},meta_reuse{};std::unique_ptr<std::array<Bank,64>>banks;
 std::array<unsigned,64>pop_head{};T labelbase,scratchbase,outputbase,costbase;unsigned Hlive=0,Elive=0,Mlive=0,Slive=0,Tlive=0,Plive=0,reserved_tokens=0,token_group_rr=0;T expand_cycles=0,final_cycles=0;std::array<std::array<T,8>,2>wall_observer{};std::array<std::array<std::array<T,65>,6>,16>occupancy{};std::array<std::array<T,8>,64> wave_bank_hist{};std::array<T,64>wave_bank_lastbusy{};struct CriticalTail{unsigned wave=0,bank=0;T lastbusy=0;std::array<T,8>hist{};};std::vector<CriticalTail>critical_tails;std::array<T,65>emit_population_hist{};std::array<T,208>logical_request_stalls{};std::array<T,64>pending_full_cycles{},pub_cycles{},scratch_cycles{};std::array<T,16>group_req_hold_cycles{},group_return_hold_cycles{};unsigned wave=0,bucket=0,phase=0; //0 idle,1 expand,2 finalize
 std::array<bool,16>token_reserved_group{},token_publish_group{},group_target_used{};unsigned pop_admissions=0;std::array<bool,8>output_busy{};T output_conflicts=0;std::array<bool,32>accepted_port{};std::array<bool,64>return_lane{},return_bank{};unsigned rotor=0;Stats stats;std::ofstream waves,checkpoints,wave_services;unsigned recorded=0;bool jitter=false;T watchdog=10000000000ull;
 static unsigned bank_of_line(unsigned l){return 2*(l&31)+((l>>5)&1);}static unsigned set_of_line(unsigned l){return (l>>6)&1023;}
 Model(Graph&x,unsigned q,const std::string&d,const std::string&cfg="C0",bool j=false):g(x),sample(q),configuration(cfg),fused(cfg=="F1"||cfg=="F3"),groups(cfg=="F2"||cfg=="F3"?16:8),lanes(64/groups),group_slots(128/groups),admission(x),image(x,q,admission),output_service(groups,12),output_inputs(groups),outdir(d),label(x.w.h.nodes,INF),pv(x.w.h.nodes),scratch_backing((x.w.h.nodes+3)/4),spilled(scratch_backing.size()),consumed(scratch_backing.size()),device_output((x.w.h.cells+3)/4),output_enqueued(device_output.size()),banks(new std::array<Bank,64>),waves(d+"/waves.csv"),checkpoints(d+"/progress.jsonl"),wave_services(d+"/wave_services.jsonl"),jitter(j){
 check(g.w.h.nodes<=4194304&&g.w.h.cells<=32768,"GRAPH_CAPACITY");check(cfg=="C0"||cfg=="F1"||cfg=="F2"||cfg=="F3","CONFIGURATION");labelbase=Graph::align(image.layout.end_bytes/32);scratchbase=Graph::align(labelbase+scratch_backing.size());output_stride=Graph::align(device_output.size());outputbase=Graph::align(scratchbase+scratch_backing.size())+sample*output_stride;costbase=Graph::align(Graph::align(scratchbase+scratch_backing.size())+g.w.h.jobs*output_stride);edge_h.fill(NIL);target_h.fill(NIL);operand_h.fill(NIL);pop_head.fill(NIL);waves<<"sample,wave,bucket,start,pop_expand_end,final_end,parents,candidates,spills,merges,commits,changed_lines,events,directory_used\n";
 }
 Bank&b(unsigned i){return (*banks)[i];}
 unsigned source_of(unsigned kind,unsigned id,T line)const{
  if(kind==EDGE)return id/(8*lanes);if(kind==ROW||kind==DESC_READ)return 16+id/group_slots;if(kind==META)return 32+id/group_slots;
  if(kind==POP_READ||kind==CAN_READ||kind==CAN_WRITE)return 48+id/8;if(kind==SCR_READ||kind==SCR_WRITE)return 112+id;return 176+(line&31);
 }
 bool request(unsigned kind,unsigned id,unsigned gen,T line){unsigned source=source_of(kind,id,line);if(source>=112)return transport.push(source,{kind,id,gen,0,line,0,t,source});if(local_request_hold[source]){++logical_request_stalls[source];return false;}local_request_hold[source]=Request{kind,id,gen,0,line,t+1,t,source};return true;}
 bool memory_empty()const{if(!output_ack_collector.idle())return false;for(auto&h:local_request_hold)if(h)return false;for(auto&h:front_request_context)if(h)return false;for(auto&h:front_return_context)if(h)return false;return transport.idle();}
 bool canon_empty()const{for(auto&bk:*banks)if(bk.txmask||!bk.op_input.empty())return false;return true;}
 unsigned reserve_token(){
  if(pop_admissions==8)return NIL;
  for(unsigned k=0;k<groups;++k){unsigned group=(token_group_rr+k)%groups;if(token_reserved_group[group])continue;
   for(unsigned i=group*group_slots;i<(group+1)*group_slots;++i)if(!tokens[i].state&&tokens[i].reusable<=t){unsigned gen=tokens[i].gen+1;tokens[i]=Token{};tokens[i].gen=gen;tokens[i].state=1;token_reserved_group[group]=true;++pop_admissions;++Tlive;++reserved_tokens;stats.fork_peak=std::max(stats.fork_peak,Tlive);token_group_rr=(group+1)%groups;return i;}}
  return NIL;
 }
 void release_token(unsigned i){check(tokens[i].state&&Tlive,"TOKEN_RELEASE");tokens[i].state=0;tokens[i].reusable=t+1;--Tlive;}
 bool word_locked(Bank&bk,unsigned line){if(bk.last_released_line==line&&t<bk.release_block_until)return true;for(unsigned m=bk.txmask;m;m&=m-1)if(bk.tx[__builtin_ctz(m)].node/4==line)return true;return false;}
 unsigned free_tx(Bank&bk){for(unsigned i=0;i<8;++i)if(!(bk.txmask&(1u<<i))&&bk.reusable_at[i]<=t)return i;return NIL;}
 bool enqueue_tx(unsigned bi,unsigned node,unsigned op,unsigned arg,const PairLine&v,unsigned tok=NIL){auto&bk=b(bi);if(bk.op_input.full())return false;bk.op_input.push({node,op,arg,tok,v,t+1});return true;}
 void admit_tx(){for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(!bk.op_input.empty()&&bk.op_input.front().due<=t){auto x=bk.op_input.front();if(start_tx(bi,x.node,x.op,x.arg,x.data,x.token))bk.op_input.pop();}}}
 bool start_tx(unsigned bi,unsigned node,unsigned op,unsigned arg,const PairLine&v,unsigned tok=NIL){auto&bk=b(bi);unsigned i=free_tx(bk);if(i==NIL)return false;if(word_locked(bk,node/4)){++bk.word_stalls;return false;}auto&tx=bk.tx[i];unsigned generation=(tx.gen+1)&255;tx=Tx{};tx.gen=generation;tx.node=node;tx.op=op;tx.arg=arg;tx.input=v;tx.token=tok;tx.state=Tx::DELAY;tx.due=t+2;tx.pv_capture_due=t+1;bk.txmask|=1u<<i;bk.txpeak=std::max(bk.txpeak,unsigned(__builtin_popcount(bk.txmask)));return true;}
 void response(const Request&r){
  if(r.kind==OUT_WRITE){check(r.gen==sample&&r.id<device_output.size()&&output_enqueued[r.id]==1,"OUTPUT_ACK_BINDING");output_enqueued[r.id]=2;++output_acks;return;}if(r.kind==INIT||r.kind==COST_LOAD)return;
  if(r.kind==DESC_READ){auto&tok=tokens[r.id];check(tok.state==3&&tok.gen==r.gen,"DESC_GENERATION");tok.decoded=image.get(tok.node);tok.state=4;tok.due=t+1;return;}
  if(r.kind==ROW){auto&h=headers[r.id];check(h.state&&h.gen==r.gen,"HEADER_GENERATION");++h.got;check(h.got<=h.need,"HEADER_DUPLICATE");h.due=t+1;return;}
  if(r.kind==EDGE){auto&s=slots[r.id];check(s.state==1&&s.gen==r.gen,"EDGE_GENERATION");auto&d=desc[s.desc];check(d.live&&d.gen==r.gen&&d.inflight,"DESC_RETURN");--d.inflight;d.due=std::max(d.due,t+1);s.state=2;s.due=t+1;return;}
  if(r.kind==META){auto&m=metas[r.id];check(m.state==2&&m.gen==r.gen,"META_GENERATION");m.state=3;m.due=t+1;return;}
  if(r.kind==POP_READ||r.kind==CAN_READ||r.kind==CAN_WRITE){unsigned bi=r.id/8,i=r.id%8;auto&tx=b(bi).tx[i];check(tx.state&&tx.gen==r.gen,"CANON_GENERATION");if(r.kind==CAN_WRITE){check(tx.state==Tx::WRITE_WAIT,"CANON_WRITE_STATE");unsigned l=tx.node/4;for(unsigned s=0;s<4&&l*4+s<label.size();++s)label[l*4+s]=tx.next.p[s];tx.state=Tx::PV;tx.due=t+1;}else{check(tx.state==Tx::READ_WAIT,"CANON_READ_STATE");unsigned l=tx.node/4;for(unsigned s=0;s<4;++s){tx.labels.p[s]=l*4+s<label.size()?label[l*4+s]:INF;}tx.state=Tx::APPLY;tx.due=t+1;}return;}
  auto&bk=b(r.id);check(bk.scratch_state&&unsigned(bk.scratch.line)==r.gen,"SCRATCH_GENERATION");
  if(r.kind==SCR_READ){check(bk.scratch_state==3||bk.scratch_state==8,"SCRATCH_READ_STATE");auto&old=scratch_backing[bk.scratch.line];for(unsigned s=0;s<4;++s)bk.scratch.data.p[s]=std::min(bk.scratch.data.p[s],old.p[s]);bk.scratch_state=bk.scratch_state==3?4:9;bk.scratch_due=t+1;}
  else{check(r.kind==SCR_WRITE&&bk.scratch_state==5,"SCRATCH_WRITE_STATE");scratch_backing[bk.scratch.line]=bk.scratch.data;if(bk.first_spill){spilled[bk.scratch.line]=1;check(bk.nspill<2048,"SPILL_ID_CAPACITY");bk.spill_ids[bk.nspill++]=bk.scratch.line;bk.spill_peak=std::max(bk.spill_peak,bk.nspill);}bk.scratch_state=0;bk.scratch_due=t+1;}
 }
 void memory_begin(){
  token_reserved_group.fill(false);token_publish_group.fill(false);output_busy.fill(false);pop_admissions=0;return_lane.fill(false);return_bank.fill(false);directory.begin(t);
  for(unsigned source=0;source<48;++source)if(front_return_context[source]&&front_return_context[source]->due<=t){response(*front_return_context[source]);front_return_context[source].reset();}
  for(unsigned group=0;group<groups;++group)if(pop_context[group]&&pop_context[group]->due<=t){auto x=*pop_context[group];auto&tok=tokens[x.token];check(tok.state==1&&reserved_tokens,"POP_TOKEN_STATE");--reserved_tokens;
   if(x.valid){tok.node=x.node;tok.pair=x.pair;tok.state=2;tok.due=t+1;++stats.parents;T a=g.row[x.node],z=g.row[x.node+1];stats.expected_degree+=z-a;stats.expected_row+=1+(x.node%4==3);if(a!=z)stats.expected_edge+=(z-1)/8-a/8+1;}else release_token(x.token);pop_context[group].reset();}
  for(unsigned group=0;group<groups;++group){output_inputs[group].reset();if(target_context[group]&&target_context[group]->due<=t){auto x=*target_context[group];output_inputs[group]=dfoutput::Update{x.cell,x.pair};}}
  std::array<bool,8> output_ready{};output_ready.fill(true);auto output_events=output_service.tick(output_inputs,output_ready);
  for(unsigned group=0;group<groups;++group)if(output_events.accepted[group])target_context[group].reset();else if(output_inputs[group])++output_conflicts;
  for(auto&event:output_events.completion)if(event){++stats.valid_target_events;recorded+=event->first;stats.output_improvements+=event->improved;}
  std::array<bool,2> ack_ready{true,true};unsigned ack_live=0;for(auto&r:output_ack_collector.out)if(r){response(*r);++ack_live;}output_ack_peak=std::max(output_ack_peak,ack_live);
  for(unsigned p=0;p<32;++p){output_ack_inputs[p].reset();auto&r=transport.returns.out[176+p];if(r&&r->kind==OUT_WRITE)output_ack_inputs[p]=r;}
  auto ack_accept=output_ack_collector.input_ready(output_ack_inputs,ack_ready);for(unsigned p=0;p<32;++p)if(output_ack_inputs[p]&&!ack_accept[p])++output_ack_stall_cycles;
  transport.jitter=jitter;transport.begin(t,[&](const Request&r){if(r.kind==OUT_WRITE)return bool(ack_accept[r.source-176]);if(r.source<48){if(front_return_context[r.source])return false;auto x=r;x.due=t+1;front_return_context[r.source]=x;}else response(r);return true;},[&](const Request&r,unsigned p){++stats.traffic[r.kind][p];});
  output_ack_collector.tick(output_ack_inputs,ack_ready);
  for(unsigned source=0;source<48;++source)if(front_request_context[source]&&front_request_context[source]->due<=t&&transport.push(source,*front_request_context[source]))front_request_context[source].reset();
  for(unsigned source=0;source<208;++source)if(local_request_hold[source]&&local_request_hold[source]->due<=t){if(source<48){if(!front_request_context[source]){auto x=*local_request_hold[source];x.due=t+1;front_request_context[source]=x;local_request_hold[source].reset();}}else if(transport.push(source,*local_request_hold[source]))local_request_hold[source].reset();}
 }
 void memory_end(){transport.end();directory.wave_tick();directory.end();}
 void canonical(){
  for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(!bk.txmask)continue;
   // Exactly one held publication bundle. It cannot be bypassed by unchanged
   // lines or stale POPs. Last directory event and bundle completion use
   // separate edges, as ec_backend_owner.remaining_events is pre-edge state.
   if(bk.adapter_state==4&&bk.adapter_due<=t)bk.adapter_state=0;
   if(bk.pub_slot!=NIL&&bk.pub_ready<=t){unsigned i=bk.pub_slot;auto&x=bk.tx[i];check(x.state==Tx::PUBLISH,"PUBLICATION_STATE");
    if(bk.adapter_state==0){bk.adapter_event=x.op!=2&&x.append;bk.adapter_sector=bk.adapter_event?__builtin_ctz(x.append):0;bk.adapter_state=1;bk.adapter_due=t+1;}
    else if(bk.adapter_state==1&&bk.adapter_due<=t){
     if(bk.adapter_event){unsigned sec=bk.adapter_sector,node=x.node/4*4+sec;unsigned arg=((x.newpv[sec]&65535)<<12)|(x.next.p[sec]>>52);if(directory.start_append(node,arg))bk.adapter_state=2;}
     else {bool consumed=true;if(x.op==2){unsigned group=x.token/group_slots;consumed=!pop_context[group];if(consumed){check(x.token!=NIL,"POP_TOKEN_RESERVATION");pop_context[group]=PopDelivery{x.token,x.node,x.old_label,t+1,x.valid};}}if(consumed){bk.adapter_state=3;bk.adapter_due=t+1;}}
    }else if(bk.adapter_state==2){if(directory.finish_append(bi)){bk.adapter_state=3;bk.adapter_due=t+1;}}
    else if(bk.adapter_state==3&&bk.adapter_due<=t){
     if(bk.adapter_event){x.append&=~(1u<<bk.adapter_sector);++bk.events;++stats.events;}
     else{x.state=Tx::FREE;bk.txmask&=~(1u<<i);bk.reusable_at[i]=t+1;bk.last_released_line=x.node/4;bk.release_block_until=t+1;bk.pub_slot=NIL;++bk.retired;bk.last_retire=t;}
     bk.adapter_state=4;bk.adapter_due=t+1;
    }
   }
   // One synchronous PV capture per bank/cycle, following the admitted read.
   unsigned captures=0;for(unsigned m=bk.txmask;m;m&=m-1){auto&x=bk.tx[__builtin_ctz(m)];if(x.state==Tx::DELAY&&!x.pv_captured&&x.pv_capture_due<=t){unsigned l=x.node/4;for(unsigned s=0;s<4;++s)x.oldpv[s]=l*4+s<pv.size()?pv[l*4+s]:0;x.pv_captured=true;++captures;}}
   check(captures<=1,"PV_READ_PORT_OVERBOOKED");
   for(unsigned m=bk.txmask;m;m&=m-1){auto&x=bk.tx[__builtin_ctz(m)];if(x.state==Tx::DELAY&&x.due<=t){check(x.pv_captured,"PV_NOT_CAPTURED");x.state=Tx::READ_REQ;}}
   // Separate persistent grant cursors, each advanced only on its actual grant.
   for(unsigned k=0;k<8;++k){unsigned i=(bk.request_cursor+k)%8;auto&x=bk.tx[i];if(x.due>t||(x.state!=Tx::READ_REQ&&x.state!=Tx::WRITE_REQ))continue;unsigned kind=x.state==Tx::WRITE_REQ?CAN_WRITE:(x.op==2?POP_READ:CAN_READ);if(request(kind,bi*8+i,x.gen,labelbase+x.node/4)){x.state=x.state==Tx::WRITE_REQ?Tx::WRITE_WAIT:Tx::READ_WAIT;bk.request_cursor=(i+1)%8;}break;}
   for(unsigned k=0;k<8;++k){unsigned i=(bk.apply_cursor+k)%8;auto&x=bk.tx[i];if(x.state!=Tx::APPLY||x.due>t)continue;x.next=x.labels;x.newpv=x.oldpv;x.append=0;x.old_label=x.labels.p[x.node&3];x.valid=false;
    for(unsigned s=0;s<4;++s){if(x.op!=7&&s!=(x.node&3))continue;pending17::Packed state{x.labels.p[s],x.oldpv[s]};auto old=pending17::Old{state.label,pending17::expand(state)};unsigned rc=pending17::packed_op(state,x.op==7?3:x.op,x.input.p[s],x.arg),rc2=pending17::old_op(old,x.op==7?3:x.op,x.input.p[s],x.arg);check(rc==rc2,"PENDING_EVENT_DIFFERENTIAL");pending17::check(old,state);x.next.p[s]=state.label;x.newpv[s]=state.pv;if(x.op==2)x.valid=rc==1;else if(rc&1)x.append|=1u<<s;}
    x.changed=x.next.p!=x.labels.p;if(x.op==7){++bk.commits;++stats.canonical_lines;if(x.changed){++bk.changed;++stats.changed_lines;}}if(x.op==2){++bk.pops;++stats.pop_transactions;if(!x.valid){++bk.stales;++stats.stale;}}x.state=x.changed?Tx::WRITE_REQ:Tx::PV;x.due=t+1;bk.apply_cursor=(i+1)%8;break;
   }
   for(unsigned k=0;k<8;++k){unsigned i=(bk.pv_cursor+k)%8;auto&x=bk.tx[i];if(x.state!=Tx::PV||x.due>t)continue;unsigned l=x.node/4;for(unsigned s=0;s<4&&l*4+s<pv.size();++s)pv[l*4+s]=x.newpv[s];x.state=Tx::EVENT;x.due=t+1;bk.pv_cursor=(i+1)%8;break;}
   if(bk.pub_slot==NIL)for(unsigned k=0;k<8;++k){unsigned i=(bk.pub_cursor+k)%8;auto&x=bk.tx[i];if(x.state!=Tx::EVENT||x.due>t)continue;bk.pub_slot=i;bk.pub_ready=t+1;x.state=Tx::PUBLISH;bk.pub_cursor=(i+1)%8;break;}
  }
 }
 void dispatch_pop(){if(phase!=1)return;
  unsigned admitted=0,allocated=0;
  for(unsigned group=0;group<groups;++group){
   if(reserve_capture[group]&&reserve_capture[group]->due<=t&&admitted<8){auto r=*reserve_capture[group];auto&member=directory.member[r.bank];check(member.has_value(),"RESERVE_MEMBER_LOST");if(enqueue_tx(r.bank,member->node,2,member->arg,PairLine{},r.token)){member.reset();reserve_capture[group].reset();bank_reserving[r.bank]=false;++admitted;}}
   if(reserve_launch[group]&&reserve_launch[group]->due<=t&&!reserve_capture[group]&&allocated<8){unsigned tok=NIL;for(unsigned i=group*group_slots;i<(group+1)*group_slots;++i)if(!tokens[i].state&&tokens[i].reusable<=t){tok=i;break;}if(tok!=NIL){unsigned gen=(tokens[tok].gen+1)&255;tokens[tok]=Token{};tokens[tok].gen=gen;tokens[tok].state=1;++allocated;++Tlive;++reserved_tokens;stats.fork_peak=std::max(stats.fork_peak,Tlive);reserve_capture[group]=Reservation{reserve_launch[group]->bank,tok,t+1};reserve_launch[group].reset();}}
  }
  unsigned requests=0;for(unsigned k=0;k<64&&requests<8;++k){unsigned bi=(rotor+k)%64;if(!directory.member[bi]||directory.member_due[bi]>t||bank_reserving[bi])continue;unsigned chosen=NIL;for(unsigned j=0;j<groups;++j){unsigned group=(token_group_rr+j)%groups;if(!reserve_launch[group]){chosen=group;break;}}if(chosen==NIL)break;reserve_launch[chosen]=Reservation{bi,NIL,t+1};bank_reserving[bi]=true;token_group_rr=(chosen+1)%groups;++requests;}
  directory.fetch_members();
 }
 bool allocate_E(unsigned group,const Ready&r){
  if(r.begin==r.end){++stats.zeros;return true;}
  unsigned chosen=NIL;
  for(unsigned k=0;k<lanes&&chosen==NIL;++k){unsigned l=group*lanes+(alloc_rr[group]+k)%lanes;for(unsigned c=0;c<4;++c)if(!desc[l*4+c].live&&desc[l*4+c].reusable<=t){chosen=l*4+c;break;}}
  if(chosen==NIL)return false;
  auto&d=desc[chosen];unsigned gen=(d.gen+1)&255;d={true,r.node,gen,0,r.pair,r.begin/8,r.begin,r.end,t+1,0};++Elive;++stats.lane_alloc[chosen/4];alloc_rr[group]=(chosen/4%lanes+1)%lanes;return true;
 }
 void metadata(){
  if(fused){
   for(unsigned group=0;group<groups;++group){unsigned base=group*group_slots,held=target_h[group],selected=NIL;
    for(unsigned k=0;k<group_slots;++k){unsigned i=base+(meta_rr[group]+k)%group_slots;auto&tok=tokens[i];if(i!=held&&tok.state==5&&!tok.meta&&tok.due<=t){selected=i;break;}}
    bool consumed=false;if(held!=NIL&&target_h_due[group]<=t){auto&tok=tokens[held];if(!tok.decoded.valid||!target_context[group]){if(tok.decoded.valid)target_context[group]=TargetDelivery{tok.decoded.cell,tok.pair,t+1};tok.meta=true;tok.retire_due=t+1;++stats.meta_admit;meta_rr[group]=(held-base+1)%group_slots;consumed=true;}}
    if(held==NIL||consumed){target_h[group]=selected;target_h_due[group]=t+1;}
   }
   return;
  }
  if(!Mlive)return;
  for(unsigned group=0;group<groups;++group){unsigned base=group*group_slots;bool retired=false;
   for(unsigned k=0;k<group_slots;++k){unsigned i=base+(meta_rr[group]+k)%group_slots;auto&m=metas[i];if(!m.state||m.due>t)continue;
    if(m.state==1){if(request(META,i,m.gen,g.metabase+sample*g.metastride+m.node/4)){m.state=2;meta_rr[group]=(i-base+1)%group_slots;}}
    else if(m.state==3&&!retired){int c=g.w.cell[T(sample)*g.w.h.nodes+m.node];if(g.w.node[m.node].type==1&&c>=0){if(target_context[group])continue;target_context[group]=TargetDelivery{unsigned(c),m.pair,t+1};}m.state=0;meta_reuse[i]=t+1;--Mlive;retired=true;}
   }
  }
 }
 void route_candidates(){
  // Preedge source/holding/FIFO state; elastic holding replacement allowed.
  std::array<bool,64> used_lane{};
  for(unsigned bi=0;bi<64;++bi){bool can_fill=!candidate_hold[bi]||(!b(bi).candidate.full()&&candidate_hold[bi]->due<=t);
   if(candidate_hold[bi]&&can_fill){auto x=*candidate_hold[bi];x.due=t+1;b(bi).candidate.push(x);candidate_hold[bi].reset();}
   if(can_fill)for(unsigned k=0;k<64;++k){unsigned lane=(candidate_rr[bi]+k)%64;auto&q=candidate_source[lane];if(used_lane[lane]||q.empty()||q.front().due>t||bank_of_line(q.front().node/4)!=bi)continue;auto x=q.pop();used_lane[lane]=true;x.due=t+1;candidate_hold[bi]=x;candidate_rr[bi]=(lane+1)%64;break;}
  }
 }
 void front(){
  std::array<bool,64> source_full{};for(unsigned l=0;l<64;++l)source_full[l]=candidate_source[l].full();
  std::array<bool,16> ready_space{};for(unsigned group=0;group<groups;++group)ready_space[group]=ready[group].n<group_slots;
  route_candidates();
  for(unsigned l=0;l<64;++l){
   bool context_ready=!front_candidate_context[l]||!source_full[l];
   if(front_candidate_context[l]&&!source_full[l]){auto x=*front_candidate_context[l];x.due=t+1;candidate_source[l].push(x);front_candidate_context[l].reset();}
   unsigned old=pipe_valid[l];std::array<bool,6>r{};r[5]=!(old&32)||context_ready;for(int k=4;k>=0;--k)r[k]=!(old&(1u<<k))||r[k+1];
   if(old&32){if(context_ready){auto x=pipeline[l][5];x.due=t+1;front_candidate_context[l]=x;--Plive;}else ++stats.lane_block[l];}
   for(int k=5;k>0;--k)if(r[k]){pipeline[l][k]=pipeline[l][k-1];pipe_valid[l]=(pipe_valid[l]&~(1u<<k))|((old&(1u<<(k-1)))<<1);}
   unsigned selected=operand_h[l],slot=NIL;
   if(selected==NIL)for(unsigned k=0;k<4;++k){unsigned i=l*4+(lane_rr[l]+k)%4;auto&d=desc[i];if(!d.live||d.due>t)continue;for(unsigned j=l*8;j<l*8+8;++j)if(slots[j].state==2&&slots[j].due<=t&&slots[j].desc==i&&slots[j].beat==d.pos/8){selected=i;slot=j;break;}if(selected!=NIL)break;}
   else for(unsigned j=l*8;j<l*8+8;++j)if(slots[j].state==2&&slots[j].desc==selected&&slots[j].beat==desc[selected].pos/8){slot=j;break;}
   if(!r[0]&&selected!=NIL)operand_h[l]=selected;
   if(r[0]){pipe_valid[l]&=~1u;if(selected!=NIL){check(slot!=NIL,"OPERAND_HELD_SLOT");auto&d=desc[selected];auto e=g.edge[d.pos];T pair=g.pair(d.pair,e);pipeline[l][0]={e&0xfffffff,pair,0};pipe_valid[l]|=1;++Plive;++stats.candidates;++stats.lane_emit[l];++d.pos;lane_rr[l]=(selected%4+1)%4;operand_h[l]=NIL;
     if(d.pos==d.end||d.pos%8==0){slots[slot].state=0;slots[slot].reusable=t+1;--Slive;}if(d.pos==d.end){check(!d.inflight,"PARENT_LATE_RESPONSE");d.live=false;d.reusable=t+1;--Elive;}
    }}
  }
  for(unsigned group=0;group<groups;++group){unsigned chosen=NIL,slot=NIL;
   for(unsigned k=0;k<lanes&&chosen==NIL;++k){unsigned l=group*lanes+(edge_rr[group]+k)%lanes;unsigned free=l*8;while(free<l*8+8&&(slots[free].state||slots[free].reusable>t))++free;if(free==l*8+8)continue;
    for(unsigned c=0;c<4;++c){unsigned i=l*4+c;auto&d=desc[i];if(d.live&&d.due<=t&&!d.inflight&&d.next<(d.end+7)/8){chosen=i;slot=free;break;}}}
   if(chosen!=NIL){auto&d=desc[chosen];if(request(EDGE,slot,d.gen,g.edgebase+d.next)){slots[slot]={1,chosen,d.gen,d.next++,0,0};++d.inflight;++Slive;stats.slots_peak=std::max(stats.slots_peak,Slive);edge_rr[group]=(chosen/4%lanes+1)%lanes;}}
  }
  if(fused){
   for(unsigned group=0;group<groups;++group){unsigned base=group*group_slots,held=edge_h[group],selected=NIL,decoded=NIL,retired=NIL;
    for(unsigned k=0;k<group_slots;++k){unsigned i=base+(token_rr[group]+k)%group_slots;auto&tok=tokens[i];if(tok.state==5&&!tok.graph&&tok.due<=t&&i!=held&&selected==NIL)selected=i;}
    for(unsigned i=base;i<base+group_slots;++i){auto&tok=tokens[i];if(tok.state==4&&tok.due<=t&&decoded==NIL)decoded=i;if(tok.state==5&&tok.graph&&tok.meta&&tok.retire_due<=t&&retired==NIL)retired=i;}
    bool consumed=false;if(held!=NIL&&edge_h_due[group]<=t){auto&tok=tokens[held];auto x=tok.decoded;if(allocate_E(group,{tok.node,tok.pair,x.begin,x.end,0})){tok.graph=true;tok.retire_due=t+1;--Hlive;consumed=true;token_rr[group]=(held-base+1)%group_slots;}}
    if(held==NIL||consumed){edge_h[group]=selected;edge_h_due[group]=t+1;}
    if(decoded!=NIL){tokens[decoded].state=5;tokens[decoded].due=t+1;}
    if(retired!=NIL)release_token(retired);
    for(unsigned k=0;k<group_slots;++k){unsigned i=base+(header_rr[group]+k)%group_slots;auto&tok=tokens[i];if(tok.state==2&&tok.due<=t){if(request(DESC_READ,i,tok.gen,image.line(tok.node))){tok.state=3;++Hlive;++stats.graph_admit;stats.H_peak=std::max(stats.H_peak,Hlive);header_rr[group]=(i-base+1)%group_slots;}break;}}
   }
  }else{
   for(unsigned group=0;group<groups;++group){auto&q=ready[group];if(!q.empty()&&q.front().due<=t&&allocate_E(group,q.front()))q.pop();}
   for(unsigned group=0;group<groups;++group){unsigned base=group*group_slots;bool pushed=false;
    for(unsigned k=0;k<group_slots;++k){unsigned i=base+(header_rr[group]+k)%group_slots;auto&h=headers[i];if(!h.state||h.due>t)continue;
     if(h.got==h.need&&ready_space[group]&&!pushed){ready[group].push({h.node,h.pair,g.row[h.node],g.row[h.node+1],t+1});h.state=0;header_reuse[i]=t+1;--Hlive;pushed=true;}
     if(h.state&&h.sent<h.need&&request(ROW,i,h.gen,g.rowbase+h.node/4+h.sent)){++h.sent;header_rr[group]=(i-base+1)%group_slots;}
    }
    bool graph=false,meta=false;
    for(unsigned k=0;k<group_slots;++k){unsigned i=base+(token_rr[group]+k)%group_slots;auto&tok=tokens[i];if(tok.state!=2||tok.due>t)continue;
     if(!tok.graph&&!graph){unsigned h=base;while(h<base+group_slots&&(headers[h].state||header_reuse[h]>t))++h;if(h<base+group_slots){auto&v=headers[h];unsigned gen=(v.gen+1)&255;v={1,tok.node,gen,0,0,unsigned(tok.node%4==3?2:1),tok.pair,t+1};tok.graph=true;graph=true;++Hlive;++stats.graph_admit;}}
     if(!tok.meta&&!meta){unsigned m=base;while(m<base+group_slots&&(metas[m].state||meta_reuse[m]>t))++m;if(m<base+group_slots){auto&v=metas[m];unsigned gen=(v.gen+1)&255;v={1,tok.node,gen,tok.pair,t+1};tok.meta=true;meta=true;++Mlive;++stats.meta_admit;}}
     if(tok.graph&&tok.meta){release_token(i);token_rr[group]=(i-base+1)%group_slots;}
    }
   }
  }
  stats.H_peak=std::max(stats.H_peak,Hlive);stats.E_peak=std::max(stats.E_peak,Elive);stats.M_peak=std::max(stats.M_peak,Mlive);
 }
 void candidate_context(){for(auto&bk:*banks){if(!bk.candidate_input.full()&&!bk.candidate.empty()&&bk.candidate.front().due<=t){auto c=bk.candidate.pop();c.due=t+1;bk.candidate_input.push(c);}}}
 void accumulator(){if(phase!=1)return;for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(bk.candidate_input.empty()||bk.candidate_input.front().due>t)continue;auto c=bk.candidate_input.front();unsigned line=c.node/4,set=set_of_line(line);if(bk.set_until[set]>t){++bk.set_stalls;continue;}unsigned way=bk.victim[set];bool hit=false,empty=false;for(int w=3;w>=0;--w)if(!bk.entry[w*1024+set].mask){way=w;empty=true;}for(unsigned w=0;w<4;++w)if(bk.entry[w*1024+set].mask&&bk.entry[w*1024+set].line==line){way=w;hit=true;}auto&e=bk.entry[way*1024+set];if(!hit&&!empty&&bk.fragment.full())continue;
   bk.candidate_input.pop();if(!hit){if(!empty){bk.fragment.push({e.line,e.value,t+7,false});++bk.spills;++stats.spills;}else{check(bk.used<4096,"OCCUPIED_CAPACITY");bk.occupied[bk.used++]=way*1024+set;}e.line=line;e.mask=0;e.value=PairLine{};bk.victim[set]=(way+1)&3;}
   unsigned s=c.node&3;e.value.p[s]=std::min(e.value.p[s],c.pair);e.mask|=1u<<s;bk.set_until[set]=t+5;bk.accumulator_tail=t+5;++bk.accepted;
  }}
 void scratch_expand(){if(phase!=1)return;for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(!bk.scratch_state&&bk.scratch_due<=t&&!bk.fragment.empty()&&bk.fragment.front().due<=t){bk.scratch=bk.fragment.pop();bk.first_spill=!spilled[bk.scratch.line];bk.scratch_state=1;bk.scratch_due=t+2;}
   if(bk.scratch_due>t)continue;
   if(bk.scratch_state==1){bk.scratch_state=bk.first_spill?4:2;bk.scratch_due=t+1;continue;}
   if(bk.scratch_state==2){if(request(SCR_READ,bi,bk.scratch.line,scratchbase+bk.scratch.line))bk.scratch_state=3;}
   else if(bk.scratch_state==4){if(request(SCR_WRITE,bi,bk.scratch.line,scratchbase+bk.scratch.line))bk.scratch_state=5;}
  }}
 void final_backend(){if(phase!=2)return;for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);bool merge_full=bk.merge.full(),atom_full=bk.atom.full();
   if(!bk.atom.empty()&&bk.atom.front().second<=t){auto a=bk.atom.pop();consumed[a.first]=1;check(bk.resident_pending,"ATOM_RESIDENT_PENDING");--bk.resident_pending;}

   if(!bk.scratch_state&&bk.scratch_due<=t&&!bk.merge.empty()&&bk.merge.front().due<=t){bk.scratch=bk.merge.pop();bk.scratch_state=7;bk.scratch_due=t+1;}
   if(bk.scratch_state==7&&bk.scratch_due<=t){if(request(SCR_READ,bi,bk.scratch.line,scratchbase+bk.scratch.line)){bk.scratch_state=8;++bk.merges;++stats.merges;}}
   bool qready=bk.query_valid&&bk.query.due<=t;
   if(qready&&!bk.query.resident&&consumed[bk.query.line]){bk.query_valid=false;qready=false;}
   bool qspill=qready&&(spilled[bk.query.line]||!bk.query.resident);
   if(qspill&&!merge_full){auto f=bk.query;f.due=t+1;bk.merge.push(f);bk.query_valid=false;qready=false;}
   bool fast=qready&&!qspill,merged=bk.scratch_state==9&&bk.scratch_due<=t;
   if(!bk.commit.full()&&!atom_full&&(fast||merged)){bool use_merge=merged&&(!fast||bk.arb_merge);Fragment f=use_merge?bk.scratch:bk.query;if(use_merge)bk.scratch_state=0;else bk.query_valid=false;f.due=t+2;bk.commit.push(f);bk.arb_merge=!use_merge;if(f.resident)bk.atom.push({f.line,t+1});else check(!consumed[f.line],"DUPLICATE_RESIDUAL_COMMIT");}
   auto incoming=enum_clock(bk,t,!bk.query_valid&&!bk.final_scan);if(incoming){bk.query=*incoming;bk.query.due=t+1;bk.query_valid=true;}
   if(bk.enum_index==bk.used&&!bk.resident_pending&&!bk.enum_valid&&bk.enum_raw.empty()&&bk.fragment.empty()&&!bk.query_valid&&bk.merge.empty()&&!bk.scratch_state&&bk.commit.empty()&&bk.atom.empty())bk.final_scan=true;
   if(bk.final_scan&&!bk.query_valid&&bk.scan<bk.nspill){unsigned line=bk.spill_ids[bk.scan++];bk.query={line,PairLine{},t+3,false};bk.query_valid=true;}
   if(!bk.commit.empty()&&bk.commit.front().due<=t){auto&f=bk.commit.front();if(enqueue_tx(bi,f.line*4,7,0,f.data)){bk.commit.pop();++bk.commit_admissions;}}
  }}
 void observe(T emitted0,T retired0,T candidates_before){
  check(stats.candidates-candidates_before<=64,"LANE_ISSUE_WIDTH");++emit_population_hist[stats.candidates-candidates_before];
  std::array<std::array<unsigned,6>,16> counts{};
  for(unsigned i=0;i<128;++i){unsigned gr=i/group_slots;counts[gr][0]+=tokens[i].state!=0;counts[gr][1]+=fused?(tokens[i].state>=3):(headers[i].state!=0);counts[gr][2]+=metas[i].state!=0;}
  for(unsigned i=0;i<256;++i)counts[i/(lanes*4)][4]+=desc[i].live;
  for(unsigned i=0;i<512;++i)counts[i/(lanes*8)][5]+=slots[i].state!=0;
  for(unsigned gr=0;gr<groups;++gr){if(fused){for(unsigned i=gr*group_slots;i<(gr+1)*group_slots;++i)counts[gr][3]+=tokens[i].state==5&&!tokens[i].graph;}else counts[gr][3]=ready[gr].n;
   for(unsigned k=0;k<6;++k){check(counts[gr][k]<=64,"GROUP_OCCUPANCY_CAPACITY");++occupancy[gr][k][counts[gr][k]];}
   group_req_hold_cycles[gr]+=bool(local_request_hold[gr])||bool(local_request_hold[16+gr]);group_return_hold_cycles[gr]+=bool(front_return_context[gr])||bool(front_return_context[16+gr]);}
  unsigned total_D=0,total_ready=0;for(unsigned gr=0;gr<groups;++gr){total_D+=counts[gr][1];total_ready+=counts[gr][3];}stats.descriptor_peak=std::max(stats.descriptor_peak,fused?total_D:0);stats.ready_peak=std::max(stats.ready_peak,total_ready);
  for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);pending_full_cycles[bi]+=bk.txmask==255;pub_cycles[bi]+=bk.pub_slot!=NIL;scratch_cycles[bi]+=bk.scratch_state!=0;}
  if(phase==1){++expand_cycles;unsigned label=7;if(stats.lane_emit[0]>emitted0)label=0;else if(pipe_valid[0]||front_candidate_context[0]||!candidate_source[0].empty())label=1;else if(counts[0][4])label=2;else if(counts[0][1])label=3;else if(counts[0][0])label=4;else if(b(0).scratch_state)label=5;else if(!directory.pops_empty())label=6;++wall_observer[0][label];}
  else if(phase==2||phase==3){++final_cycles;for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);unsigned label=7;
    if(bk.last_retire==t)label=0;else if(bk.pub_slot!=NIL)label=1;else if(bk.txmask==255)label=2;else if(bk.scratch_state)label=3;else if(!bk.commit.empty()||!bk.op_input.empty())label=4;else if(bk.enum_index<bk.used||bk.enum_valid)label=5;else if(phase==2)label=6;
    if(bi==0)++wall_observer[1][label];++wave_bank_hist[bi][label];
    if(phase==2&&(bk.txmask||!bk.op_input.empty()||bk.enum_index!=bk.used||bk.resident_pending||!bk.final_scan||bk.scan!=bk.nspill||bk.scratch_state||bk.enum_valid||!bk.enum_raw.empty()||!bk.fragment.empty()||bk.query_valid||!bk.atom.empty()||!bk.merge.empty()||!bk.commit.empty()||bk.last_retire==t))wave_bank_lastbusy[bi]=t;
   }}
 }
 void step(){if(getenv("EC_DEBUG")&&t%100000==0){std::cerr<<"DEBUG t="<<t<<" phase="<<phase<<" token="<<Tlive<<" reserved="<<reserved_tokens<<" H="<<Hlive<<" E="<<Elive<<" M="<<Mlive<<" P="<<Plive<<" dir="<<directory.used<<" parents="<<stats.parents<<" cand="<<stats.candidates;for(unsigned bi=0;bi<64;++bi)if(pop_head[bi]!=NIL)std::cerr<<" pophead"<<bi<<"="<<pop_head[bi];for(unsigned gi=0;gi<groups;++gi)if(!ready[gi].empty())std::cerr<<" ready"<<gi<<"="<<ready[gi].n;for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(bk.txmask||bk.used||bk.scratch_state||!bk.candidate.empty())std::cerr<<" bank"<<bi<<" tx="<<bk.txmask<<" used="<<bk.used<<" enum="<<bk.enum_index<<" rp="<<bk.resident_pending<<" can="<<bk.candidate.n<<" frag="<<bk.fragment.n<<" enum_pipe="<<bk.enum_valid<<" query="<<bk.query_valid<<" merge="<<bk.merge.n<<" commit="<<bk.commit.n<<" scratch="<<bk.scratch_state;};std::cerr<<std::endl;}check(t<watchdog,"CYCLE_WATCHDOG");T observed_emit0=stats.lane_emit[0],observed_retire0=b(0).retired,candidates_before=stats.candidates;memory_begin();
  // Rotate service-class priority; no extra physical enqueue ports are invented.
  unsigned order=rotor%4;for(unsigned k=0;k<4;++k){switch((order+k)%4){case 0:metadata();break;case 1:front();break;case 2:scratch_expand();final_backend();break;case 3:canonical();break;}}
  candidate_context();accumulator();dispatch_pop();admit_tx();observe(observed_emit0,observed_retire0,candidates_before);memory_end();++t;++rotor;
 }
 bool expansion_done(){if(!directory.pops_empty())return false;if(!canon_empty()||reserved_tokens||Hlive||Elive)return false;for(auto&x:tokens)if(x.state==2&&!x.graph)return false;for(auto&q:ready)if(!q.empty())return false;if(Plive)return false;for(auto&h:front_candidate_context)if(h)return false;for(auto&q:candidate_source)if(!q.empty())return false;for(auto&h:candidate_hold)if(h)return false;for(auto&bk:*banks){if(!bk.candidate.empty()||!bk.candidate_input.empty()||!bk.fragment.empty()||bk.scratch_state)return false;if(bk.accumulator_tail>t)return false;}return true;}
 bool final_done(){if(!canon_empty()||!directory.idle())return false;for(auto&bk:*banks)if(bk.enum_index!=bk.used||bk.resident_pending||!bk.final_scan||bk.scan!=bk.nspill||bk.scratch_state||(bk.enum_valid||!bk.enum_raw.empty())||!bk.fragment.empty()||bk.query_valid||!bk.atom.empty()||!bk.merge.empty()||!bk.commit.empty())return false;return true;}
 bool meta_done()const{if(Mlive||!output_service.idle())return false;for(auto&h:target_context)if(h)return false;for(auto&x:tokens)if(x.state&&(!x.meta||x.state==1))return false;return true;}
 void initialize(){sample_start=t;++t;++rotor;T minimum=t+16384;unsigned next=0;T nlines=scratch_backing.size();while(next<nlines||!memory_empty()||t<minimum){if(getenv("EC_DEBUG")&&t%10000==0)std::cerr<<"INITDBG t="<<t<<" next="<<next<<" nlines="<<nlines<<" q0="<<ports[0].q[0].n<<" flight0="<<ports[0].credits()<<" back0="<<ports[0].back.n<<" tags0="<<ports[0].credits()<<std::endl;memory_begin();for(unsigned p=0;p<32&&next<nlines;++p){if(request(INIT,0,0,labelbase+next))++next;else break;}memory_end();++t;++rotor;}for(unsigned k=0;k<(g.w.h.costs+3)/4;++k){while(true){memory_begin();bool ok=request(COST_LOAD,0,0,costbase+k);memory_end();++t;++rotor;if(ok)break;}}while(!memory_empty())step();init_end=t;}
 void run(unsigned targets){initialize();if(targets){unsigned src=g.w.job[sample].source;check(enqueue_tx(bank_of_line(src/4),src,5,0,PairLine{}),"SEED_ADMIT");while(!canon_empty())step();}
  directory.start_wave();while(!directory.wave_done())step();
  while(directory.selected!=4096){bucket=directory.selected;directory.start_take();while(!directory.wave_done())step();++wave;++stats.waves;check(wave<1000000,"WAVE_LIMIT");auto traffic_before=stats.traffic;auto requests_before=transport.accepted;auto returns_before=transport.delivered;auto stalls_before=transport.source_stalls;auto lane_before=stats.lane_emit;wave_bank_hist={};wave_bank_lastbusy.fill(0);
   T start=t,parents=stats.parents,candidates=stats.candidates,sp=stats.spills,mer=stats.merges,cl=stats.canonical_lines,ch=stats.changed_lines,ev=stats.events;
   phase=1;while(!expansion_done())step();step();step();T expand_end=t;phase=2;for(auto&bk:*banks){bk.enum_index=bk.scan=bk.resident_pending=0;bk.final_scan=false;bk.enum_next=t;bk.enum_valid=0;bk.enum_phase=false;}
   while(!final_done())step();step();
   // Finite bitmap clear uses one word/subbank/cycle, 256 clocks. No epoch shortcut.
   phase=3;for(unsigned i=0;i<256;++i)step();phase=0;std::fill(spilled.begin(),spilled.end(),0);std::fill(consumed.begin(),consumed.end(),0);for(auto&bk:*banks){bk.used=bk.nspill=0;}
   waves<<sample<<','<<wave<<','<<bucket<<','<<start<<','<<expand_end<<','<<t<<','<<stats.parents-parents<<','<<stats.candidates-candidates<<','<<stats.spills-sp<<','<<stats.merges-mer<<','<<stats.canonical_lines-cl<<','<<stats.changed_lines-ch<<','<<stats.events-ev<<','<<directory.used<<'\n';waves.flush();
   unsigned critical=0;for(unsigned bi=1;bi<64;++bi)if(wave_bank_lastbusy[bi]>wave_bank_lastbusy[critical])critical=bi;critical_tails.push_back({wave,critical,wave_bank_lastbusy[critical],wave_bank_hist[critical]});
   wave_services<<"{\"wave\":"<<wave<<",\"groups\":[";
   for(unsigned gr=0;gr<groups;++gr){wave_services<<(gr?",":"")<<'[';for(unsigned kind=0;kind<3;++kind){unsigned src=gr+kind*16;wave_services<<(kind?",":"")<<'['<<transport.accepted[src]-requests_before[src]<<','<<transport.delivered[src]-returns_before[src]<<','<<transport.source_stalls[src]-stalls_before[src]<<']';}wave_services<<']';}
   wave_services<<"],\"traffic_by_kind_port\":[";for(unsigned kind=0;kind<KINDS;++kind){wave_services<<(kind?",":"")<<'[';for(unsigned port=0;port<32;++port)wave_services<<(port?",":"")<<stats.traffic[kind][port]-traffic_before[kind][port];wave_services<<']';}wave_services<<"],\"lane_emits\":[";for(unsigned lane=0;lane<64;++lane)wave_services<<(lane?",":"")<<stats.lane_emit[lane]-lane_before[lane];wave_services<<"]}\n";wave_services.flush();
   checkpoints<<"{\"sample\":"<<sample<<",\"wave\":"<<wave<<",\"cycle\":"<<t<<",\"candidates\":"<<stats.candidates<<",\"directory_used\":"<<directory.used<<"}\n";checkpoints.flush();
   directory.start_wave();while(!directory.wave_done())step();if(directory.selected!=bucket){while(!meta_done())step();if(recorded==targets)break;}

  }
  phase=0;while(!meta_done()||!memory_empty()||Tlive)step();export_start=t;unsigned next=0;unsigned n=device_output.size();Fifo<ExportBeat,16>packed;
  // Registered exporter start acceptance: no RAM read on this edge.
  memory_begin();memory_end();++t;++rotor;
  while(next<n||!packed.empty()||!memory_empty()){
   memory_begin();unsigned packing_space=16-packed.n;
   // Eight synchronous output BRAM banks provide eight pairs/cycle = two beats.
   // Reserve finite packing storage before the read; read/export pipeline is two clocks.
   for(unsigned k=0;k<2&&!packed.empty()&&packed.front().due<=t;++k){auto&e=packed.front();if(!request(OUT_WRITE,e.line,sample,outputbase+e.line))break;check(!output_enqueued[e.line],"DUPLICATE_OUTPUT_WRITE");device_output[e.line]=e.data;output_enqueued[e.line]=1;packed.pop();}
   for(unsigned k=0;k<2&&k<packing_space&&next<n;++k){ExportBeat e;e.line=next++;e.due=t+2;for(unsigned s=0;s<4;++s){unsigned c=e.line*4+s;e.data.p[s]=c<g.w.h.cells?output_service.get(c):0x7fc000007fc00000ull;}packed.push(e);}
   memory_end();++t;++rotor;
  }
  // done registers one edge after the last accepted export ACK.
  memory_begin();memory_end();++t;++rotor;export_end=t;check(output_acks==n,"OUTPUT_ACK_CONSERVATION");

  T total_accepted=0,metadata_requests=0,row_requests=0,edge_requests=0,descriptor_requests=0;for(auto&bk:*banks)total_accepted+=bk.accepted;for(unsigned p=0;p<32;++p){descriptor_requests+=stats.traffic[DESC_READ][p];metadata_requests+=stats.traffic[META][p];row_requests+=stats.traffic[ROW][p];edge_requests+=stats.traffic[EDGE][p];}check(total_accepted==stats.candidates&&stats.candidates==stats.expected_degree,"CANDIDATE_CONSERVATION");check((fused?descriptor_requests==stats.parents&&metadata_requests==0:metadata_requests==stats.parents&&descriptor_requests==0)&&stats.graph_admit==stats.parents&&stats.meta_admit==stats.parents,"FORK_EXACTLY_ONCE");check(row_requests==(fused?0:stats.expected_row)&&edge_requests==stats.expected_edge,"ALIGNED_REQUEST_CONSERVATION");check(!Hlive&&!Elive&&!Mlive&&!Slive&&!Plive&&!Tlive&&!reserved_tokens,"FINAL_FRONTEND_BUSY");for(auto&p:ports)check(p.issues==p.responses&&!p.credits(),"FINAL_MEMORY_CONSERVATION");check(recorded==targets,"RECORDED_TARGETS");check(output_service.admitted==output_service.retired&&output_service.retired==stats.valid_target_events&&output_service.first_count==recorded,"OUTPUT_RAM_COMPLETION_CONSERVATION");for(auto&bk:*banks){check(!bk.txmask,"FINAL_TX_BUSY");}
 }
 void save(){std::ofstream o(outdir+"/finite.json");o<<"{\"configuration\":\""<<configuration<<"\",\"groups\":"<<groups<<",\"lanes_per_group\":"<<lanes<<",\"descriptor_bytes\":"<<image.formatbytes<<",\"sample\":"<<sample<<",\"cycles\":"<<t<<",\"init_end\":"<<init_end<<",\"export_start\":"<<export_start<<",\"export_end\":"<<export_end<<",\"output_ACKs\":"<<output_acks<<",\"output_ACK_peak_per_cycle\":"<<output_ack_peak<<",\"output_ACK_rejected_source_cycles\":"<<output_ack_stall_cycles<<",\"output_base_line\":"<<outputbase<<",\"output_sample_stride_lines\":"<<output_stride<<",\"cost_base_line\":"<<costbase<<",\"cost_table_lines\":"<<(g.w.h.costs+3)/4<<",\"parents\":"<<stats.parents<<",\"zero_degree\":"<<stats.zeros<<",\"candidates\":"<<stats.candidates<<",\"waves\":"<<stats.waves<<",\"spills\":"<<stats.spills<<",\"scratch_final_reads\":"<<stats.merges<<",\"canonical_lines\":"<<stats.canonical_lines<<",\"changed_lines\":"<<stats.changed_lines<<",\"events\":"<<stats.events<<",\"pop_transactions\":"<<stats.pop_transactions<<",\"stale\":"<<stats.stale<<",\"directory_peak\":"<<directory.peak<<",\"recorded\":"<<recorded<<",\"fork_H_E_M_slots_peak\":["<<stats.fork_peak<<','<<stats.H_peak<<','<<stats.E_peak<<','<<stats.M_peak<<','<<stats.slots_peak<<"],\"descriptor_slots_peak\":"<<stats.descriptor_peak<<",\"ready_peak\":"<<stats.ready_peak<<",\"memory_kind_names\":[\"init\",\"row\",\"edge\",\"meta\",\"pop_read\",\"canonical_read\",\"canonical_write\",\"scratch_read\",\"scratch_write\",\"output_write\",\"cost_load\",\"descriptor\"],\"traffic\":[";
  for(unsigned k=0;k<KINDS;++k){if(k)o<<',';o<<'[';for(unsigned p=0;p<32;++p)o<<(p?",":"")<<stats.traffic[k][p];o<<']';}o<<"],\"lane_emit\":[";for(unsigned l=0;l<64;++l)o<<(l?",":"")<<stats.lane_emit[l];o<<"],\"lane_block\":[";for(unsigned l=0;l<64;++l)o<<(l?",":"")<<stats.lane_block[l];o<<"],\"lane_alloc\":[";for(unsigned l=0;l<64;++l)o<<(l?",":"")<<stats.lane_alloc[l];o<<"],\"bank_stats\":[";
  for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(bi)o<<',';o<<"{\"tx_peak\":"<<bk.txpeak<<",\"spill_id_peak\":"<<bk.spill_peak<<",\"spill\":"<<bk.spills<<",\"enum\":"<<bk.enum_launches<<",\"commit_admit\":"<<bk.commit_admissions<<",\"commit\":"<<bk.commits<<",\"events\":"<<bk.events<<",\"tx_retired\":"<<bk.retired<<",\"last_retire\":"<<bk.last_retire<<",\"word_stalls\":"<<bk.word_stalls<<",\"pending_full_cycles\":"<<pending_full_cycles[bi]<<",\"publication_cycles\":"<<pub_cycles[bi]<<",\"scratch_busy_cycles\":"<<scratch_cycles[bi]<<",\"input_candidate_peak\":"<<bk.candidate_input.peak<<",\"input_op_peak\":"<<bk.op_input.peak<<",\"set_stalls\":"<<bk.set_stalls<<",\"fifo_peaks\":["<<bk.candidate.peak<<','<<bk.fragment.peak<<','<<4<<','<<bk.atom.peak<<','<<bk.merge.peak<<','<<bk.commit.peak<<"]}";}
  o<<"],\"port_stats\":[";for(unsigned p=0;p<32;++p){auto&x=ports[p];if(p)o<<',';o<<"{\"issued\":"<<x.issues<<",\"returned\":"<<x.responses<<",\"credit_peak\":"<<x.credit_peak<<",\"queue_peak\":"<<std::max({x.q[0].peak,x.q[1].peak,x.q[2].peak,x.q[3].peak})<<",\"return_peak\":"<<x.back.peak<<",\"credit_stall_attempts\":"<<x.credit_stalls<<",\"queue_stall_attempts\":"<<x.queue_stalls<<",\"response_full_cycles\":"<<x.response_full<<",\"return_HOL_cycles\":"<<x.return_hol<<'}';}o<<"],\"directory_bank_peaks\":[";for(unsigned bi=0;bi<64;++bi)o<<(bi?",":"")<<directory.bank_peak[bi];o<<"],\"phase_cycles\":{\"init\":"<<init_end<<",\"pop_expand\":"<<expand_cycles<<",\"finalize\":"<<final_cycles<<",\"export\":"<<export_end-export_start<<",\"other\":"<<t-init_end-expand_cycles-final_cycles-(export_end-export_start)<<"},\"fixed_observer_wall_cycles\":[";for(unsigned phase=0;phase<2;++phase){o<<(phase?",":"")<<'[';for(unsigned k=0;k<8;++k)o<<(k?",":"")<<wall_observer[phase][k];o<<']';}o<<"],\"output_bank_conflicts\":"<<output_conflicts<<",\"output_RAM_admitted\":"<<output_service.admitted<<",\"output_RAM_retired\":"<<output_service.retired<<",\"output_RAM_first\":"<<output_service.first_count<<",\"group_stats\":[";
  for(unsigned gr=0;gr<groups;++gr){if(gr)o<<',';o<<"{\"group\":"<<gr<<",\"request_hold_cycles\":"<<group_req_hold_cycles[gr]<<",\"return_hold_cycles\":"<<group_return_hold_cycles[gr]<<",\"service_sources\":[";for(unsigned k=0;k<3;++k){unsigned src=gr+16*k;if(k)o<<',';o<<"{\"source\":"<<src<<",\"accepted\":"<<transport.accepted[src]<<",\"returned\":"<<transport.delivered[src]<<",\"request_stalls\":"<<transport.source_stalls[src]<<",\"logical_request_stalls\":"<<logical_request_stalls[src]<<",\"return_stalls\":"<<transport.return_stalls[src]<<",\"source_fifo_peak\":"<<transport.source[src].peak<<'}';}o<<"],\"occupancy_histograms\":[";for(unsigned k=0;k<6;++k){o<<(k?",":"")<<'[';for(unsigned n=0;n<65;++n)o<<(n?",":"")<<occupancy[gr][k][n];o<<']';}o<<"]}";}
  o<<"],\"emit_population_histogram\":[";for(unsigned n=0;n<=64;++n)o<<(n?",":"")<<emit_population_hist[n];o<<"],\"critical_final_bank_observers\":[";for(unsigned n=0;n<critical_tails.size();++n){auto&c=critical_tails[n];o<<(n?",":"")<<"{\"wave\":"<<c.wave<<",\"bank\":"<<c.bank<<",\"last_busy_cycle\":"<<c.lastbusy<<",\"exclusive_histogram\":[";for(unsigned k=0;k<8;++k)o<<(k?",":"")<<c.hist[k];o<<"]}";}
  o<<"],\"complete_finite_functional_model\":true,\"calibration\":\"not yet calibrated against new full RTL chain; stage latencies explicit conditional contract\",\"frequency_hz\":200000000,\"latency_ns\":80,\"gap_ns\":5,\"conditional_predicted_seconds\":"<<std::setprecision(15)<<double(t)/200000000<<",\"fpga_seconds\":null,\"board_measured\":false}\n";
 }
};
}
