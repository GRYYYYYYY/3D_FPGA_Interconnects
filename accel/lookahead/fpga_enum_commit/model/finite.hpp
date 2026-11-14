#pragma once
#include "../../fpga_decoupled_front/graph.hpp"
#include "../../fpga_sparse_stream_r2/pending17.hpp"
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
struct Directory {
 static constexpr unsigned CAP=524288;std::vector<Member>pool;std::vector<unsigned>free,head,tail;std::array<T,64>bits{};T upper=0;unsigned used=0,peak=0;std::array<unsigned,64>bank_used{},bank_peak{};
 Directory():pool(CAP),free(CAP),head(4096*64,NIL),tail(head.size(),NIL){clear();}
 void clear(){std::fill(head.begin(),head.end(),NIL);std::fill(tail.begin(),tail.end(),NIL);bits.fill(0);upper=used=0;bank_used.fill(0);for(unsigned i=0;i<CAP;++i)free[i]=i;}
 static unsigned bank(unsigned n){unsigned l=n/4;return 2*(l&31)+((l>>5)&1);}
 void put(unsigned node,unsigned arg){unsigned key=arg&4095,b=bank(node),h=key*64+b;check(used<CAP,"DIRECTORY_CAPACITY");check(bank_used[b]<CAP/64,"DIRECTORY_BANK_CAPACITY");auto p=free[b*(CAP/64)+bank_used[b]++];++used;peak=std::max(peak,used);bank_peak[b]=std::max(bank_peak[b],bank_used[b]);pool[p]={node,arg,NIL};if(head[h]==NIL)head[h]=p;else pool[tail[h]].next=p;tail[h]=p;bits[key/64]|=T(1)<<(key%64);upper|=T(1)<<(key/64);}
 unsigned min()const{check(upper,"DIRECTORY_EMPTY");unsigned g=__builtin_ctzll(upper);return g*64+__builtin_ctzll(bits[g]);}
 std::array<unsigned,64>take(unsigned key){std::array<unsigned,64>x;for(unsigned b=0;b<64;++b){unsigned h=key*64+b;x[b]=head[h];head[h]=tail[h]=NIL;}bits[key/64]&=~(T(1)<<(key%64));if(!bits[key/64])upper&=~(T(1)<<(key/64));return x;}
 Member release(unsigned p){check(p!=NIL&&used,"DIRECTORY_FREE");auto x=pool[p];unsigned b=bank(x.node);check(bank_used[b],"DIRECTORY_BANK_UNDERFLOW");free[b*(CAP/64)+--bank_used[b]]=p;--used;return x;}
};
enum Kind{INIT,ROW,EDGE,META,POP_READ,CAN_READ,CAN_WRITE,SCR_READ,SCR_WRITE,OUT_WRITE,COST_LOAD,KINDS};
struct Request{unsigned kind=0,id=0,gen=0,tag=0;T line=0,due=0,queued=0;};
struct Port {Fifo<Request,64>q;Fifo<Request,32>flight;Fifo<Request,4>back;uint32_t tags=0;unsigned credit_peak=0;T issues=0,responses=0,credit_stalls=0,queue_stalls=0,response_full=0;};
struct Token{unsigned state=0,node=0;T pair=0,due=0;bool graph=false,meta=false;};
struct Header{unsigned state=0,node=0,gen=0,sent=0,got=0,need=0;T pair=0,due=0;};
struct Meta{unsigned state=0,node=0,gen=0;T pair=0,due=0;};
struct Ready{unsigned node=0;T pair=0,begin=0,end=0,due=0;};
struct Desc{bool live=false;unsigned node=0,gen=0,inflight=0;T pair=0,next=0,pos=0,end=0;};
struct Slot{unsigned state=0,desc=0,gen=0;T beat=0;};
struct ExportBeat{unsigned line=0;PairLine data;T due=0;};
struct Candidate{unsigned node=0;T pair=0,due=0;};
struct Tx {
 enum State{FREE,DELAY,READ_REQ,READ_WAIT,APPLY,WRITE_REQ,WRITE_WAIT,PV,EVENT,RELEASE,PUBLISH};
 unsigned state=FREE,node=0,op=0,arg=0,gen=0,token=NIL,append=0,event_sector=0;T due=0,pv_capture_due=0,old_label=INF;bool pv_captured=false;bool changed=false,valid=false;PairLine input,labels,next;std::array<unsigned,4>oldpv{},newpv{};
};
struct Entry{unsigned line=0;uint8_t mask=0;PairLine value;};
struct Bank {
 std::array<Entry,4096>entry;std::array<uint8_t,1024>victim{};std::array<T,1024>set_until{};std::array<unsigned,4096>occupied{};unsigned used=0;
 Fifo<Candidate,16>candidate;Fifo<Fragment,16>fragment,merge,commit;std::array<Fragment,4>enum_pipe;unsigned enum_valid=0;bool enum_phase=false;Fifo<Fragment,1>enum_raw;Fifo<std::pair<unsigned,T>,2>atom;bool query_valid=false;Fragment query;
 std::array<unsigned,2048>spill_ids{};unsigned nspill=0,scan=0,enum_index=0,resident_pending=0;T enum_next=0;
 // Expand scratch and finalize merge each use one command, never simultaneously.
 unsigned scratch_state=0;Fragment scratch;bool first_spill=false;T scratch_due=0;
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
struct Stats{T candidates=0,parents=0,zeros=0,waves=0,expected_degree=0,expected_row=0,expected_edge=0,graph_admit=0,meta_admit=0,valid_target_events=0,output_improvements=0,pop_transactions=0,stale=0,spills=0,merges=0,canonical_lines=0,changed_lines=0,events=0;std::array<T,64>lane_emit{},lane_block{},lane_alloc{};std::array<std::array<T,32>,KINDS>traffic{};unsigned fork_peak=0,H_peak=0,E_peak=0,M_peak=0,slots_peak=0;};
struct Model {
 Graph&g;unsigned sample;std::string outdir;T t=0,sample_start=0,init_end=0;Directory directory;std::vector<T>label;std::vector<unsigned>pv;std::vector<PairLine>scratch_backing;std::vector<uint8_t>spilled,consumed;std::vector<T>output;std::vector<uint8_t>output_seen;std::vector<PairLine>device_output;std::vector<uint8_t>output_enqueued;unsigned output_acks=0;T export_start=0,export_end=0,output_stride=0;
 std::array<Port,32>ports;std::array<Token,128>tokens;std::array<Header,128>headers;std::array<Meta,128>metas;std::array<Fifo<Ready,16>,8>ready;std::array<Desc,256>desc;std::array<Slot,512>slots;std::array<Fifo<Candidate,2>,64>pipeline;std::array<unsigned,64>lane_rr{};std::array<unsigned,8>alloc_rr{},token_rr{};std::unique_ptr<std::array<Bank,64>>banks;
 std::array<unsigned,64>pop_head{};T labelbase,scratchbase,outputbase,costbase;unsigned Hlive=0,Elive=0,Mlive=0,Slive=0,Tlive=0,Plive=0,reserved_tokens=0,token_group_rr=0;unsigned wave=0,bucket=0,phase=0; //0 idle,1 expand,2 finalize
 std::array<bool,8>token_reserved_group{},token_publish_group{};std::array<bool,32>accepted_port{};std::array<bool,64>return_lane{},return_bank{};unsigned rotor=0;Stats stats;std::ofstream waves,checkpoints;unsigned recorded=0;bool jitter=false;T watchdog=10000000000ull;
 static unsigned bank_of_line(unsigned l){return 2*(l&31)+((l>>5)&1);}static unsigned set_of_line(unsigned l){return (l>>6)&1023;}
 Model(Graph&x,unsigned q,const std::string&d,bool j=false):g(x),sample(q),outdir(d),label(x.w.h.nodes,INF),pv(x.w.h.nodes),scratch_backing((x.w.h.nodes+3)/4),spilled(scratch_backing.size()),consumed(scratch_backing.size()),output(x.w.h.cells,INF),output_seen(x.w.h.cells),device_output((x.w.h.cells+3)/4),output_enqueued(device_output.size()),banks(new std::array<Bank,64>),waves(d+"/waves.csv"),checkpoints(d+"/progress.jsonl"),jitter(j){
 check(g.w.h.nodes<=4194304&&g.w.h.cells<=32768,"GRAPH_CAPACITY");labelbase=Graph::align(g.metabase+g.w.h.jobs*g.metastride);scratchbase=Graph::align(labelbase+scratch_backing.size());output_stride=Graph::align(device_output.size());outputbase=Graph::align(scratchbase+scratch_backing.size())+sample*output_stride;costbase=Graph::align(Graph::align(scratchbase+scratch_backing.size())+g.w.h.jobs*output_stride);pop_head.fill(NIL);waves<<"sample,wave,bucket,start,pop_expand_end,final_end,parents,candidates,spills,merges,commits,changed_lines,events,directory_used\n";
 }
 Bank&b(unsigned i){return (*banks)[i];}
 bool request(unsigned kind,unsigned id,unsigned gen,T line){unsigned p=line&31;auto&port=ports[p];if(accepted_port[p])return false;if(port.q.full()){++port.queue_stalls;return false;}if(port.tags==~uint32_t(0)){++port.credit_stalls;return false;}unsigned tag=__builtin_ctz(~port.tags);port.tags|=uint32_t(1)<<tag;port.credit_peak=std::max(port.credit_peak,unsigned(__builtin_popcount(port.tags)));port.q.push({kind,id,gen,tag,line,0,t});accepted_port[p]=true;return true;}
 bool memory_empty()const{for(auto&p:ports)if(!p.q.empty()||!p.flight.empty()||!p.back.empty()||p.tags)return false;return true;}
 bool canon_empty()const{for(auto&bk:*banks)if(bk.txmask)return false;return true;}
 unsigned reserve_token(){for(unsigned k=0;k<8;++k){unsigned group=(token_group_rr+k)%8;if(token_reserved_group[group])continue;for(unsigned i=group*16;i<group*16+16;++i)if(tokens[i].state==0){tokens[i]={};tokens[i].state=1;token_reserved_group[group]=true;++Tlive;++reserved_tokens;stats.fork_peak=std::max(stats.fork_peak,Tlive);token_group_rr=(group+1)%8;return i;}}return NIL;}
 void release_token(unsigned i){check(tokens[i].state&&Tlive,"TOKEN_RELEASE");tokens[i].state=0;--Tlive;}
 bool word_locked(Bank&bk,unsigned line){if(bk.last_released_line==line&&t<bk.release_block_until)return true;for(unsigned m=bk.txmask;m;m&=m-1)if(bk.tx[__builtin_ctz(m)].node/4==line)return true;return false;}
 unsigned free_tx(Bank&bk){for(unsigned i=0;i<8;++i)if(!(bk.txmask&(1u<<i))&&bk.reusable_at[i]<=t)return i;return NIL;}
 bool start_tx(unsigned bi,unsigned node,unsigned op,unsigned arg,const PairLine&v,unsigned tok=NIL){auto&bk=b(bi);unsigned i=free_tx(bk);if(i==NIL)return false;if(word_locked(bk,node/4)){++bk.word_stalls;return false;}auto&tx=bk.tx[i];unsigned generation=(tx.gen+1)&255;tx=Tx{};tx.gen=generation;tx.node=node;tx.op=op;tx.arg=arg;tx.input=v;tx.token=tok;tx.state=Tx::DELAY;tx.due=t+3;tx.pv_capture_due=t+1;bk.txmask|=1u<<i;bk.txpeak=std::max(bk.txpeak,unsigned(__builtin_popcount(bk.txmask)));return true;}
 void response(const Request&r){
  if(r.kind==OUT_WRITE){check(r.gen==sample&&r.id<device_output.size()&&output_enqueued[r.id]==1,"OUTPUT_ACK_BINDING");output_enqueued[r.id]=2;++output_acks;return;}if(r.kind==INIT||r.kind==COST_LOAD)return;
  if(r.kind==ROW){auto&h=headers[r.id];check(h.state&&h.gen==r.gen,"HEADER_GENERATION");++h.got;check(h.got<=h.need,"HEADER_DUPLICATE");h.due=t+1;return;}
  if(r.kind==EDGE){auto&s=slots[r.id];check(s.state==1&&s.gen==r.gen,"EDGE_GENERATION");auto&d=desc[s.desc];check(d.live&&d.gen==r.gen&&d.inflight,"DESC_RETURN");--d.inflight;s.state=2;return;}
  if(r.kind==META){auto&m=metas[r.id];check(m.state==2&&m.gen==r.gen,"META_GENERATION");m.state=3;m.due=t+1;return;}
  if(r.kind==POP_READ||r.kind==CAN_READ||r.kind==CAN_WRITE){unsigned bi=r.id/8,i=r.id%8;auto&tx=b(bi).tx[i];check(tx.state&&tx.gen==r.gen,"CANON_GENERATION");if(r.kind==CAN_WRITE){check(tx.state==Tx::WRITE_WAIT,"CANON_WRITE_STATE");unsigned l=tx.node/4;for(unsigned s=0;s<4&&l*4+s<label.size();++s)label[l*4+s]=tx.next.p[s];tx.state=Tx::PV;tx.due=t+1;}else{check(tx.state==Tx::READ_WAIT,"CANON_READ_STATE");unsigned l=tx.node/4;for(unsigned s=0;s<4;++s){tx.labels.p[s]=l*4+s<label.size()?label[l*4+s]:INF;}tx.state=Tx::APPLY;tx.due=t+1;}return;}
  auto&bk=b(r.id);check(bk.scratch_state&&unsigned(bk.scratch.line)==r.gen,"SCRATCH_GENERATION");
  if(r.kind==SCR_READ){check(bk.scratch_state==3||bk.scratch_state==8,"SCRATCH_READ_STATE");auto&old=scratch_backing[bk.scratch.line];for(unsigned s=0;s<4;++s)bk.scratch.data.p[s]=std::min(bk.scratch.data.p[s],old.p[s]);bk.scratch_state=bk.scratch_state==3?4:9;bk.scratch_due=t+1;}
  else{check(r.kind==SCR_WRITE&&bk.scratch_state==5,"SCRATCH_WRITE_STATE");scratch_backing[bk.scratch.line]=bk.scratch.data;if(bk.first_spill){spilled[bk.scratch.line]=1;check(bk.nspill<2048,"SPILL_ID_CAPACITY");bk.spill_ids[bk.nspill++]=bk.scratch.line;bk.spill_peak=std::max(bk.spill_peak,bk.nspill);}bk.scratch_state=0;}
 }
 void memory_begin(){token_reserved_group.fill(false);token_publish_group.fill(false);accepted_port.fill(false);return_lane.fill(false);return_bank.fill(false);for(unsigned k=0;k<32;++k){unsigned p=(rotor+k)%32;auto&port=ports[p];if(port.back.empty()||port.back.front().due>t)continue;auto&r=port.back.front();bool ok=true;unsigned lane=0,bi=0;if(r.kind==ROW||r.kind==META||r.kind==EDGE){lane=r.kind==EDGE?r.id/8:r.id%64;ok=!return_lane[lane];}else if(r.kind>=POP_READ&&r.kind<=CAN_WRITE){bi=r.id/8;ok=!return_bank[bi];}if(ok){if(r.kind==ROW||r.kind==META||r.kind==EDGE)return_lane[lane]=true;else if(r.kind>=POP_READ&&r.kind<=CAN_WRITE)return_bank[bi]=true;auto a=port.back.pop();response(a);}}
 }
 void memory_end(){for(unsigned p=0;p<32;++p){auto&port=ports[p];if(!port.flight.empty()&&port.flight.front().due<=t){if(port.back.full())++port.response_full;else{auto r=port.flight.pop();check(port.tags&(uint32_t(1)<<r.tag),"CREDIT_DOUBLE_RETURN");port.tags&=~(uint32_t(1)<<r.tag);r.due=t+2;port.back.push(r);++port.responses;}}if(!port.q.empty()&&port.q.front().queued+2<=t&&!port.flight.full()){auto r=port.q.pop();r.due=t+16+(jitter?(port.issues*17+p)%7:0);port.flight.push(r);++port.issues;++stats.traffic[r.kind][p];}}}
 void canonical(){
  for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(!bk.txmask)continue;
   // Exactly one held publication bundle. It cannot be bypassed by unchanged
   // lines or stale POPs. Last directory event and bundle completion use
   // separate edges, as ec_backend_owner.remaining_events is pre-edge state.
   if(bk.pub_slot!=NIL&&bk.pub_ready<=t){unsigned i=bk.pub_slot;auto&x=bk.tx[i];check(x.state==Tx::PUBLISH,"PUBLICATION_STATE");bool complete=false;
    if(x.op==2){if(!token_publish_group[x.token/16]){token_publish_group[x.token/16]=true;check(x.token!=NIL,"POP_TOKEN_RESERVATION");auto&tok=tokens[x.token];check(tok.state==1&&reserved_tokens,"POP_TOKEN_STATE");--reserved_tokens;if(x.valid){tok.node=x.node;tok.pair=x.old_label;tok.state=2;tok.due=t+1;++stats.parents;T a=g.row[x.node],z=g.row[x.node+1];stats.expected_degree+=z-a;stats.expected_row+=1+(x.node%4==3);if(a!=z)stats.expected_edge+=(z-1)/8-a/8+1;}else release_token(x.token);complete=true;}}
    else if(x.append){unsigned s=__builtin_ctz(x.append),node=x.node/4*4+s;unsigned arg=((x.newpv[s]&65535)<<12)|(x.next.p[s]>>52);directory.put(node,arg);x.append&=~(1u<<s);++bk.events;++stats.events;}
    else complete=true;
    if(complete){x.state=Tx::FREE;bk.txmask&=~(1u<<i);bk.reusable_at[i]=t+1;bk.last_released_line=x.node/4;bk.release_block_until=t+1;bk.pub_slot=NIL;++bk.retired;bk.last_retire=t;}
   }
   // One synchronous PV capture per bank/cycle, following the admitted read.
   unsigned captures=0;for(unsigned m=bk.txmask;m;m&=m-1){auto&x=bk.tx[__builtin_ctz(m)];if(x.state==Tx::DELAY&&!x.pv_captured&&x.pv_capture_due<=t){unsigned l=x.node/4;for(unsigned s=0;s<4;++s)x.oldpv[s]=l*4+s<pv.size()?pv[l*4+s]:0;x.pv_captured=true;++captures;}}
   check(captures<=1,"PV_READ_PORT_OVERBOOKED");
   for(unsigned m=bk.txmask;m;m&=m-1){auto&x=bk.tx[__builtin_ctz(m)];if(x.state==Tx::DELAY&&x.due<=t){check(x.pv_captured,"PV_NOT_CAPTURED");x.state=Tx::READ_REQ;}}
   // Separate persistent grant cursors, each advanced only on its actual grant.
   for(unsigned k=0;k<8;++k){unsigned i=(bk.request_cursor+k)%8;auto&x=bk.tx[i];if(x.due>t||(x.state!=Tx::READ_REQ&&x.state!=Tx::WRITE_REQ))continue;unsigned kind=x.state==Tx::WRITE_REQ?CAN_WRITE:(x.op==2?POP_READ:CAN_READ);if(request(kind,bi*8+i,x.gen,labelbase+x.node/4)){x.state=x.state==Tx::WRITE_REQ?Tx::WRITE_WAIT:Tx::READ_WAIT;bk.request_cursor=(i+1)%8;}break;}
   for(unsigned k=0;k<8;++k){unsigned i=(bk.apply_cursor+k)%8;auto&x=bk.tx[i];if(x.state!=Tx::APPLY||x.due>t)continue;x.next=x.labels;x.newpv=x.oldpv;x.append=0;x.old_label=x.labels.p[x.node&3];x.valid=false;
    for(unsigned s=0;s<4;++s){if(x.op!=7&&s!=(x.node&3))continue;pending17::Packed state{x.labels.p[s],x.oldpv[s]};auto old=pending17::Old{state.label,pending17::expand(state)};unsigned rc=pending17::packed_op(state,x.op==7?3:x.op,x.input.p[s],x.arg),rc2=pending17::old_op(old,x.op==7?3:x.op,x.input.p[s],x.arg);check(rc==rc2,"PENDING_EVENT_DIFFERENTIAL");pending17::check(old,state);x.next.p[s]=state.label;x.newpv[s]=state.pv;if(x.op==2)x.valid=rc==1;else if(rc&1)x.append|=1u<<s;}
    x.changed=x.next.p!=x.labels.p;if(x.op==7){++bk.commits;++stats.canonical_lines;if(x.changed){++bk.changed;++stats.changed_lines;}}if(x.op==2){++bk.pops;++stats.pop_transactions;if(!x.valid){++bk.stales;++stats.stale;}}x.state=x.changed?Tx::WRITE_REQ:Tx::PV;x.due=t+(x.changed?2:1);bk.apply_cursor=(i+1)%8;break;
   }
   for(unsigned k=0;k<8;++k){unsigned i=(bk.pv_cursor+k)%8;auto&x=bk.tx[i];if(x.state!=Tx::PV||x.due>t)continue;unsigned l=x.node/4;for(unsigned s=0;s<4&&l*4+s<pv.size();++s)pv[l*4+s]=x.newpv[s];x.state=Tx::EVENT;x.due=t+1;bk.pv_cursor=(i+1)%8;break;}
   if(bk.pub_slot==NIL)for(unsigned k=0;k<8;++k){unsigned i=(bk.pub_cursor+k)%8;auto&x=bk.tx[i];if(x.state!=Tx::EVENT||x.due>t)continue;bk.pub_slot=i;bk.pub_ready=t+1;x.state=Tx::PUBLISH;bk.pub_cursor=(i+1)%8;break;}
  }
 }
 void dispatch_pop(){if(phase!=1)return;for(unsigned k=0;k<64;++k){unsigned bi=(rotor+k)%64;auto&bk=b(bi);if(pop_head[bi]==NIL||free_tx(bk)==NIL)continue;auto member=directory.pool[pop_head[bi]];if(word_locked(bk,member.node/4)){++bk.word_stalls;continue;}auto tok=reserve_token();if(tok==NIL)break;check(start_tx(bi,member.node,2,member.arg,PairLine{},tok),"POP_ADMIT");directory.release(pop_head[bi]);pop_head[bi]=member.next;}}
 void metadata(){if(!Mlive)return;std::array<bool,8>busy{};for(unsigned k=0;k<128;++k){unsigned i=(k+rotor)%128;auto&m=metas[i];if(!m.state)continue;if(m.state==1){if(request(META,i,m.gen,g.metabase+sample*g.metastride+m.node/4))m.state=2;}else if(m.state==3&&m.due<=t){int c=g.w.cell[T(sample)*g.w.h.nodes+m.node];if(g.w.node[m.node].type==1&&c>=0){check(unsigned(c)<output.size(),"OUTPUT_CELL");if(busy[c&7])continue;busy[c&7]=true;++stats.valid_target_events;if(!output_seen[c]){output_seen[c]=1;++recorded;}if(m.pair<output[c]){output[c]=m.pair;++stats.output_improvements;}}m.state=0;--Mlive;}}}
 void front(){if(!Tlive&&!Hlive&&!Elive&&!Plive){bool all_empty=true;for(auto&q:ready)all_empty&=q.empty();if(all_empty)return;}
  // Router: real finite lane pipeline -> one write per destination bank/cycle.
  std::array<bool,64>wrote{};for(unsigned k=0;k<64;++k){unsigned l=(rotor+k)%64;auto&p=pipeline[l];if(!p.empty()&&p.front().due<=t){unsigned bi=bank_of_line(p.front().node/4);if(!wrote[bi]&&!b(bi).candidate.full()){auto x=p.pop();--Plive;x.due=t+1;b(bi).candidate.push(x);wrote[bi]=true;}else ++stats.lane_block[l];}}
  for(unsigned l=0;l<64;++l){if(pipeline[l].full())continue;for(unsigned k=0;k<4;++k){unsigned i=l*4+(lane_rr[l]+k)%4;auto&d=desc[i];if(!d.live)continue;int slot=-1;for(unsigned s=l*8;s<l*8+8;++s)if(slots[s].state==2&&slots[s].desc==i&&slots[s].beat==d.pos/8){slot=s;break;}if(slot<0)continue;auto e=g.edge[d.pos];T pair=g.pair(d.pair,e);pipeline[l].push({e&0xfffffff,pair,t+2});++Plive;++stats.candidates;++stats.lane_emit[l];++d.pos;lane_rr[l]=(i%4+1)%4;if(d.pos==d.end||d.pos%8==0){slots[slot].state=0;--Slive;}if(d.pos==d.end){check(!d.inflight,"PARENT_LATE_RESPONSE");d.live=false;--Elive;}break;}}
  // A single lane's eight slots; parent D1, shared physical credits.
  for(unsigned k=0;k<256;++k){unsigned i=(k+rotor)%256;auto&d=desc[i];if(!d.live||d.inflight||d.next>=(d.end+7)/8)continue;unsigned l=i/4,s=l*8;while(s<l*8+8&&slots[s].state)++s;if(s==l*8+8)continue;if(request(EDGE,s,d.gen,g.edgebase+d.next)){slots[s]={1,i,d.gen,d.next++};++d.inflight;++Slive;stats.slots_peak=std::max(stats.slots_peak,Slive);}}
  // Eight implementable group dispatchers, one successful parent per group/cycle.
  for(unsigned group=0;group<8;++group){auto&q=ready[group];if(q.empty()||q.front().due>t)continue;auto r=q.front();if(r.begin==r.end){q.pop();++stats.zeros;continue;}unsigned chosen=NIL;
   for(unsigned k=0;k<8&&chosen==NIL;++k){unsigned l=group*8+(alloc_rr[group]+k)%8;for(unsigned c=0;c<4;++c)if(!desc[l*4+c].live){chosen=l*4+c;break;}}
   if(chosen!=NIL){q.pop();auto&d=desc[chosen];unsigned gen=d.gen+1;d={true,r.node,gen,0,r.pair,r.begin/8,r.begin,r.end};++Elive;++stats.lane_alloc[chosen/4];alloc_rr[group]=(chosen/4%8+1)%8;}}
  // One H->ready and one fork->H/M admission per group per cycle.
  for(unsigned group=0;group<8;++group){unsigned base=group*16;bool pushed=false;for(unsigned k=0;k<16;++k){unsigned i=base+(k+rotor)%16;auto&h=headers[i];if(h.state&&h.got==h.need&&h.due<=t&&!ready[group].full()&&!pushed){ready[group].push({h.node,h.pair,g.row[h.node],g.row[h.node+1],t+1});h.state=0;--Hlive;pushed=true;}if(h.state&&h.sent<h.need){if(request(ROW,i,h.gen,g.rowbase+h.node/4+h.sent))++h.sent;}}
   bool graph=false,meta=false;for(unsigned k=0;k<16;++k){unsigned i=base+(token_rr[group]+k)%16;auto&tok=tokens[i];if(tok.state!=2||tok.due>t)continue;if(!tok.graph&&!graph){unsigned h=base;while(h<base+16&&headers[h].state)++h;if(h<base+16){auto&v=headers[h];unsigned gen=v.gen+1;v={1,tok.node,gen,0,0,unsigned(tok.node%4==3?2:1),tok.pair,t+1};tok.graph=true;graph=true;++Hlive;++stats.graph_admit;}}
    if(!tok.meta&&!meta){unsigned m=base;while(m<base+16&&metas[m].state)++m;if(m<base+16){auto&v=metas[m];unsigned gen=v.gen+1;v={1,tok.node,gen,tok.pair,t+1};tok.meta=true;meta=true;++Mlive;++stats.meta_admit;}}
    if(tok.graph&&tok.meta)release_token(i);
   }token_rr[group]=(token_rr[group]+1)%16;
  }
  stats.H_peak=std::max(stats.H_peak,Hlive);stats.E_peak=std::max(stats.E_peak,Elive);stats.M_peak=std::max(stats.M_peak,Mlive);
 }
 void accumulator(){if(phase!=1)return;for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(bk.candidate.empty()||bk.candidate.front().due>t)continue;auto c=bk.candidate.front();unsigned line=c.node/4,set=set_of_line(line);if(bk.set_until[set]>t){++bk.set_stalls;continue;}unsigned way=bk.victim[set];bool hit=false,empty=false;for(int w=3;w>=0;--w)if(!bk.entry[w*1024+set].mask){way=w;empty=true;}for(unsigned w=0;w<4;++w)if(bk.entry[w*1024+set].mask&&bk.entry[w*1024+set].line==line){way=w;hit=true;}auto&e=bk.entry[way*1024+set];if(!hit&&!empty&&bk.fragment.full())continue;
   bk.candidate.pop();if(!hit){if(!empty){bk.fragment.push({e.line,e.value,t+7,false});++bk.spills;++stats.spills;}else{check(bk.used<4096,"OCCUPIED_CAPACITY");bk.occupied[bk.used++]=way*1024+set;}e.line=line;e.mask=0;e.value=PairLine{};bk.victim[set]=(way+1)&3;}
   unsigned s=c.node&3;e.value.p[s]=std::min(e.value.p[s],c.pair);e.mask|=1u<<s;bk.set_until[set]=t+5;bk.accumulator_tail=t+5;++bk.accepted;
  }}
 void scratch_expand(){if(phase!=1)return;for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(!bk.scratch_state&&!bk.fragment.empty()&&bk.fragment.front().due<=t){bk.scratch=bk.fragment.pop();bk.first_spill=!spilled[bk.scratch.line];bk.scratch_state=1;bk.scratch_due=t+2;}
   if(bk.scratch_due>t)continue;
   if(bk.scratch_state==1){bk.scratch_state=bk.first_spill?4:2;bk.scratch_due=t+1;continue;}
   if(bk.scratch_state==2){if(request(SCR_READ,bi,bk.scratch.line,scratchbase+bk.scratch.line))bk.scratch_state=3;}
   else if(bk.scratch_state==4){if(request(SCR_WRITE,bi,bk.scratch.line,scratchbase+bk.scratch.line))bk.scratch_state=5;}
  }}
 void final_backend(){if(phase!=2)return;for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);
   if(!bk.atom.empty()&&bk.atom.front().second<=t){auto a=bk.atom.pop();consumed[a.first]=1;check(bk.resident_pending,"ATOM_RESIDENT_PENDING");--bk.resident_pending;}

   if(!bk.scratch_state&&!bk.merge.empty()&&bk.merge.front().due<=t){bk.scratch=bk.merge.pop();bk.scratch_state=7;bk.scratch_due=t+1;}
   if(bk.scratch_state==7&&bk.scratch_due<=t){if(request(SCR_READ,bi,bk.scratch.line,scratchbase+bk.scratch.line)){bk.scratch_state=8;++bk.merges;++stats.merges;}}
   bool qready=bk.query_valid&&bk.query.due<=t;
   if(qready&&!bk.query.resident&&consumed[bk.query.line]){bk.query_valid=false;qready=false;}
   bool qspill=qready&&(spilled[bk.query.line]||!bk.query.resident);
   if(qspill&&!bk.merge.full()){auto f=bk.query;f.due=t+1;bk.merge.push(f);bk.query_valid=false;qready=false;}
   bool fast=qready&&!qspill,merged=bk.scratch_state==9&&bk.scratch_due<=t;
   if(!bk.commit.full()&&!bk.atom.full()&&(fast||merged)){bool use_merge=merged&&(!fast||bk.arb_merge);Fragment f=use_merge?bk.scratch:bk.query;if(use_merge)bk.scratch_state=0;else bk.query_valid=false;f.due=t+2;bk.commit.push(f);bk.arb_merge=!use_merge;if(f.resident)bk.atom.push({f.line,t+1});else check(!consumed[f.line],"DUPLICATE_RESIDUAL_COMMIT");}
   auto incoming=enum_clock(bk,t,!bk.query_valid&&!bk.final_scan);if(incoming){bk.query=*incoming;bk.query.due=t+1;bk.query_valid=true;}
   if(bk.enum_index==bk.used&&!bk.resident_pending&&!bk.enum_valid&&bk.enum_raw.empty()&&bk.fragment.empty()&&!bk.query_valid&&bk.merge.empty()&&!bk.scratch_state&&bk.commit.empty()&&bk.atom.empty())bk.final_scan=true;
   if(bk.final_scan&&!bk.query_valid&&bk.scan<bk.nspill){unsigned line=bk.spill_ids[bk.scan++];bk.query={line,PairLine{},t+3,false};bk.query_valid=true;}
   if(!bk.commit.empty()&&bk.commit.front().due<=t){auto&f=bk.commit.front();if(start_tx(bi,f.line*4,7,0,f.data)){bk.commit.pop();++bk.commit_admissions;}}
  }}
 void step(){if(getenv("EC_DEBUG")&&t%100000==0){std::cerr<<"DEBUG t="<<t<<" phase="<<phase<<" token="<<Tlive<<" reserved="<<reserved_tokens<<" H="<<Hlive<<" E="<<Elive<<" M="<<Mlive<<" P="<<Plive<<" dir="<<directory.used<<" parents="<<stats.parents<<" cand="<<stats.candidates;for(unsigned bi=0;bi<64;++bi)if(pop_head[bi]!=NIL)std::cerr<<" pophead"<<bi<<"="<<pop_head[bi];for(unsigned gi=0;gi<8;++gi)if(!ready[gi].empty())std::cerr<<" ready"<<gi<<"="<<ready[gi].n;for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(bk.txmask||bk.used||bk.scratch_state||!bk.candidate.empty())std::cerr<<" bank"<<bi<<" tx="<<bk.txmask<<" used="<<bk.used<<" enum="<<bk.enum_index<<" rp="<<bk.resident_pending<<" can="<<bk.candidate.n<<" frag="<<bk.fragment.n<<" enum_pipe="<<bk.enum_valid<<" query="<<bk.query_valid<<" merge="<<bk.merge.n<<" commit="<<bk.commit.n<<" scratch="<<bk.scratch_state;};std::cerr<<std::endl;}check(t<watchdog,"CYCLE_WATCHDOG");memory_begin();
  // Rotate service-class priority; no extra physical enqueue ports are invented.
  unsigned order=rotor%4;for(unsigned k=0;k<4;++k){switch((order+k)%4){case 0:metadata();break;case 1:front();break;case 2:scratch_expand();final_backend();break;case 3:canonical();break;}}
  accumulator();dispatch_pop();memory_end();++t;++rotor;
 }
 bool expansion_done(){for(auto h:pop_head)if(h!=NIL)return false;if(!canon_empty()||reserved_tokens||Hlive||Elive)return false;for(auto&x:tokens)if(x.state==2&&!x.graph)return false;for(auto&q:ready)if(!q.empty())return false;for(auto&p:pipeline)if(!p.empty())return false;for(auto&bk:*banks){if(!bk.candidate.empty()||!bk.fragment.empty()||bk.scratch_state)return false;if(bk.accumulator_tail>t)return false;}return true;}
 bool final_done(){if(!canon_empty())return false;for(auto&bk:*banks)if(bk.enum_index!=bk.used||bk.resident_pending||!bk.final_scan||bk.scan!=bk.nspill||bk.scratch_state||(bk.enum_valid||!bk.enum_raw.empty())||!bk.fragment.empty()||bk.query_valid||!bk.atom.empty()||!bk.merge.empty()||!bk.commit.empty())return false;return true;}
 bool meta_done()const{if(Mlive)return false;for(auto&x:tokens)if(x.state&&(!x.meta||x.state==1))return false;return true;}
 void initialize(){sample_start=t;++t;++rotor;T minimum=t+16384;unsigned next=0;T nlines=scratch_backing.size();while(next<nlines||!memory_empty()||t<minimum){if(getenv("EC_DEBUG")&&t%10000==0)std::cerr<<"INITDBG t="<<t<<" next="<<next<<" nlines="<<nlines<<" q0="<<ports[0].q.n<<" flight0="<<ports[0].flight.n<<" back0="<<ports[0].back.n<<" tags0="<<ports[0].tags<<std::endl;memory_begin();for(unsigned p=0;p<32&&next<nlines;++p){if(request(INIT,0,0,labelbase+next))++next;else break;}memory_end();++t;++rotor;}for(unsigned k=0;k<(g.w.h.costs+3)/4;++k){while(true){memory_begin();bool ok=request(COST_LOAD,0,0,costbase+k);memory_end();++t;++rotor;if(ok)break;}}while(!memory_empty())step();init_end=t;}
 void run(unsigned targets){initialize();if(targets){unsigned src=g.w.job[sample].source;check(start_tx(bank_of_line(src/4),src,5,0,PairLine{}),"SEED_ADMIT");while(!canon_empty())step();}
  while(directory.upper){bucket=directory.min();pop_head=directory.take(bucket);++wave;++stats.waves;check(wave<1000000,"WAVE_LIMIT");T start=t,parents=stats.parents,candidates=stats.candidates,sp=stats.spills,mer=stats.merges,cl=stats.canonical_lines,ch=stats.changed_lines,ev=stats.events;
   phase=1;while(!expansion_done())step();T expand_end=t;phase=2;for(auto&bk:*banks){bk.enum_index=bk.scan=bk.resident_pending=0;bk.final_scan=false;bk.enum_next=t;bk.enum_valid=0;bk.enum_phase=false;}
   while(!final_done())step();
   // Finite bitmap clear uses one word/subbank/cycle, 256 clocks. No epoch shortcut.
   phase=0;for(unsigned i=0;i<256;++i)step();std::fill(spilled.begin(),spilled.end(),0);std::fill(consumed.begin(),consumed.end(),0);for(auto&bk:*banks){bk.used=bk.nspill=0;}
   waves<<sample<<','<<wave<<','<<bucket<<','<<start<<','<<expand_end<<','<<t<<','<<stats.parents-parents<<','<<stats.candidates-candidates<<','<<stats.spills-sp<<','<<stats.merges-mer<<','<<stats.canonical_lines-cl<<','<<stats.changed_lines-ch<<','<<stats.events-ev<<','<<directory.used<<'\n';waves.flush();
   checkpoints<<"{\"sample\":"<<sample<<",\"wave\":"<<wave<<",\"cycle\":"<<t<<",\"candidates\":"<<stats.candidates<<",\"directory_used\":"<<directory.used<<"}\n";checkpoints.flush();
   if(!directory.upper||directory.min()!=bucket){while(!meta_done())step();if(recorded==targets)break;}
  }
  phase=0;while(!meta_done()||!memory_empty()||Tlive)step();export_start=t;unsigned next=0;unsigned n=device_output.size();Fifo<ExportBeat,16>packed;
  while(next<n||!packed.empty()||!memory_empty()){
   memory_begin();
   // Eight synchronous output BRAM banks provide eight pairs/cycle = two beats.
   // Reserve finite packing storage before the read; read/export pipeline is two clocks.
   for(unsigned k=0;k<2&&!packed.empty()&&packed.front().due<=t;++k){auto&e=packed.front();if(!request(OUT_WRITE,e.line,sample,outputbase+e.line))break;check(!output_enqueued[e.line],"DUPLICATE_OUTPUT_WRITE");device_output[e.line]=e.data;output_enqueued[e.line]=1;packed.pop();}
   for(unsigned k=0;k<2&&next<n&&!packed.full();++k){ExportBeat e;e.line=next++;e.due=t+2;for(unsigned s=0;s<4;++s){unsigned c=e.line*4+s;e.data.p[s]=c<output.size()&&output_seen[c]?output[c]:0x7fc000007fc00000ull;}packed.push(e);}
   memory_end();++t;++rotor;
  }export_end=t;check(output_acks==n,"OUTPUT_ACK_CONSERVATION");

  T total_accepted=0,metadata_requests=0,row_requests=0,edge_requests=0;for(auto&bk:*banks)total_accepted+=bk.accepted;for(unsigned p=0;p<32;++p){metadata_requests+=stats.traffic[META][p];row_requests+=stats.traffic[ROW][p];edge_requests+=stats.traffic[EDGE][p];}check(total_accepted==stats.candidates&&stats.candidates==stats.expected_degree,"CANDIDATE_CONSERVATION");check(metadata_requests==stats.parents&&stats.graph_admit==stats.parents&&stats.meta_admit==stats.parents,"FORK_EXACTLY_ONCE");check(row_requests==stats.expected_row&&edge_requests==stats.expected_edge,"ALIGNED_REQUEST_CONSERVATION");check(!Hlive&&!Elive&&!Mlive&&!Slive&&!Plive&&!Tlive&&!reserved_tokens,"FINAL_FRONTEND_BUSY");for(auto&p:ports)check(p.issues==p.responses&&!p.tags,"FINAL_MEMORY_CONSERVATION");check(recorded==targets,"RECORDED_TARGETS");for(auto&bk:*banks){check(!bk.txmask,"FINAL_TX_BUSY");}
 }
 void save(){std::ofstream o(outdir+"/finite.json");o<<"{\"sample\":"<<sample<<",\"cycles\":"<<t<<",\"init_end\":"<<init_end<<",\"export_start\":"<<export_start<<",\"export_end\":"<<export_end<<",\"output_ACKs\":"<<output_acks<<",\"output_base_line\":"<<outputbase<<",\"output_sample_stride_lines\":"<<output_stride<<",\"cost_base_line\":"<<costbase<<",\"cost_table_lines\":"<<(g.w.h.costs+3)/4<<",\"parents\":"<<stats.parents<<",\"zero_degree\":"<<stats.zeros<<",\"candidates\":"<<stats.candidates<<",\"waves\":"<<stats.waves<<",\"spills\":"<<stats.spills<<",\"scratch_final_reads\":"<<stats.merges<<",\"canonical_lines\":"<<stats.canonical_lines<<",\"changed_lines\":"<<stats.changed_lines<<",\"events\":"<<stats.events<<",\"pop_transactions\":"<<stats.pop_transactions<<",\"stale\":"<<stats.stale<<",\"directory_peak\":"<<directory.peak<<",\"recorded\":"<<recorded<<",\"fork_H_E_M_slots_peak\":["<<stats.fork_peak<<','<<stats.H_peak<<','<<stats.E_peak<<','<<stats.M_peak<<','<<stats.slots_peak<<"],\"memory_kind_names\":[\"init\",\"row\",\"edge\",\"meta\",\"pop_read\",\"canonical_read\",\"canonical_write\",\"scratch_read\",\"scratch_write\",\"output_write\",\"cost_load\"],\"traffic\":[";
  for(unsigned k=0;k<KINDS;++k){if(k)o<<',';o<<'[';for(unsigned p=0;p<32;++p)o<<(p?",":"")<<stats.traffic[k][p];o<<']';}o<<"],\"lane_emit\":[";for(unsigned l=0;l<64;++l)o<<(l?",":"")<<stats.lane_emit[l];o<<"],\"bank_stats\":[";
  for(unsigned bi=0;bi<64;++bi){auto&bk=b(bi);if(bi)o<<',';o<<"{\"tx_peak\":"<<bk.txpeak<<",\"spill_id_peak\":"<<bk.spill_peak<<",\"spill\":"<<bk.spills<<",\"enum\":"<<bk.enum_launches<<",\"commit_admit\":"<<bk.commit_admissions<<",\"commit\":"<<bk.commits<<",\"events\":"<<bk.events<<",\"tx_retired\":"<<bk.retired<<",\"last_retire\":"<<bk.last_retire<<",\"word_stalls\":"<<bk.word_stalls<<",\"set_stalls\":"<<bk.set_stalls<<",\"fifo_peaks\":["<<bk.candidate.peak<<','<<bk.fragment.peak<<','<<4<<','<<bk.atom.peak<<','<<bk.merge.peak<<','<<bk.commit.peak<<"]}";}
  o<<"],\"port_stats\":[";for(unsigned p=0;p<32;++p){auto&x=ports[p];if(p)o<<',';o<<"{\"issued\":"<<x.issues<<",\"returned\":"<<x.responses<<",\"credit_peak\":"<<x.credit_peak<<",\"queue_peak\":"<<x.q.peak<<",\"return_peak\":"<<x.back.peak<<",\"credit_stall_attempts\":"<<x.credit_stalls<<",\"queue_stall_attempts\":"<<x.queue_stalls<<",\"response_full_cycles\":"<<x.response_full<<'}';}o<<"],\"directory_bank_peaks\":[";for(unsigned bi=0;bi<64;++bi)o<<(bi?",":"")<<directory.bank_peak[bi];o<<"],\"complete_finite_functional_model\":true,\"calibration\":\"not yet calibrated against new full RTL chain; stage latencies explicit conditional contract\",\"frequency_hz\":200000000,\"latency_ns\":80,\"gap_ns\":5,\"conditional_predicted_seconds\":"<<std::setprecision(15)<<double(t)/200000000<<",\"fpga_seconds\":null,\"board_measured\":false}\n";
 }
};
}
