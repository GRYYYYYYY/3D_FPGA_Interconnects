// Stage B relaxed screen. Finite pending/port/parent/frontend services are real
// event schedules. Accumulator/routing/finalize timing is deliberately omitted:
// this is NOT a complete finite architecture model or an FPGA performance claim.
#include "pending17.hpp"
#include <algorithm>
#include <array>
#include <cstdint>
#include <deque>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <vector>
#include <tuple>
using T=uint64_t;
void require(bool b,const char* s){if(!b)throw std::runtime_error(s);}
template<class V>void read(std::ifstream& f,V& v){require(bool(f.read((char*)&v,sizeof v)),"truncated trace");}
struct Pop{uint32_t node,arg,pv,valid,target,parent;T label;};
struct Edge{uint32_t node;T pair;};
struct Parent{uint32_t node;T label;std::vector<Edge> edges;};
struct Line{std::array<T,4> before,after;std::array<uint32_t,4> pv;};
struct Trace{
 T sample,wave,bucket,candidates;std::vector<Pop> pops;std::vector<Parent> parents;std::map<unsigned,Line> lines;
 explicit Trace(const char* path){std::ifstream f(path,std::ios::binary);T h[8];read(f,h);require(h[0]==0x5053545241434531ull,"trace magic");sample=h[1];wave=h[2];bucket=h[3];candidates=h[6];require(h[4]<=524288&&h[5]<=524288,"directory/active capacity");pops.resize(h[4]);parents.resize(h[5]);
  for(auto& p:pops){read(f,p.node);read(f,p.arg);read(f,p.pv);read(f,p.valid);read(f,p.target);read(f,p.parent);read(f,p.label);}
  T count=0;for(auto& p:parents){uint32_t n;read(f,p.node);read(f,n);read(f,p.label);p.edges.resize(n);count+=n;for(auto& e:p.edges){read(f,e.node);read(f,e.pair);}}require(count==candidates,"edge count");
  for(T i=0;i<h[7];++i){unsigned l;Line x;read(f,l);read(f,x.before);read(f,x.pv);read(f,x.after);require(lines.emplace(l,x).second,"duplicate trace line");}require(f.peek()==EOF,"trailing trace");
 }
};
unsigned bank(unsigned node){unsigned l=node/4;return (l&31)*2+((l>>5)&1);}
struct Event{T at,seq;std::function<void()> fn;bool operator<(const Event& o)const{return at!=o.at?at>o.at:seq>o.seq;}};
struct Screen{
 Trace& tr;unsigned K;bool streaming;T now=0,seq=0;std::priority_queue<Event> events;
 struct Request{unsigned kind;std::function<void()> done;};
 struct Port{std::deque<Request> queue;std::array<bool,32> tags{};unsigned used=0,peak=0,queue_peak=0,rotate=0;bool armed=false;T next=0,issued=0,returned=0,credit_stall=0,queue_stall=0;std::array<T,5> kinds{};};
 std::array<Port,32> ports;
 struct Bank{std::deque<unsigned> input;std::set<unsigned> words;unsigned used=0,peak=0;bool armed=false;T next=0,accept=0,retire=0,word_stall=0,context_stall=0,token_stall=0,first_accept=~T(0),last_accept=0,first_retire=~T(0),last_retire=0;};
 std::array<Bank,64> banks;
 std::map<unsigned,pending17::Packed> state;
 std::deque<std::tuple<unsigned,unsigned,T>> blocked;bool blocked_armed=false;
 std::deque<unsigned> tokens;unsigned token_peak=0,front_used=0,front_peak=0;std::vector<unsigned> free_front;
 T pop_end=0,front_start=~T(0),front_end=0,edge_emits=0,front_wait=0,front_emit=0,front_no_parent=0,word_conflicts=0,edge_reads=0,parents_done=0,token_emits=0;
 std::map<unsigned,std::array<T,4>> proposals;std::array<T,64> candidate_banks{};std::array<T,65536> set_access{};
 std::ofstream log;unsigned latency=16;bool jitter=false;T stall_tokens_until=0;
 Screen(Trace& t,unsigned k,bool stream,const char* path):tr(t),K(k),streaming(stream),log(path){
  log<<"cycle,phase,bank_or_context,item\n";
  for(unsigned i=0;i<tr.pops.size();++i){auto p=tr.pops[i];require(p.node<(1u<<22),"MAX_N");banks[bank(p.node)].input.push_back(i);state.emplace(p.node,pending17::Packed{p.label,p.pv});}
  for(unsigned i=0;i<64;++i)free_front.push_back(63-i);
  for(auto& [l,x]:tr.lines)proposals[l]={pending17::INF,pending17::INF,pending17::INF,pending17::INF};
 }
 void later(T at,std::function<void()> fn){require(at>=now,"time reversal");require(events.size()<8192,"event capacity violated");events.push({at,seq++,std::move(fn)});}
 void port_arm(unsigned p){auto& a=ports[p];if(a.armed||a.queue.empty())return;if(a.used==32){++a.credit_stall;return;}a.armed=true;later(std::max(now,a.next),[this,p]{issue(p);});}
 void issue(unsigned p){auto& a=ports[p];a.armed=false;require(!a.queue.empty()&&a.used<32,"port issue");auto r=std::move(a.queue.front());a.queue.pop_front();unsigned tag=a.rotate;while(a.tags[tag])tag=(tag+1)%32;a.rotate=(tag+1)%32;a.tags[tag]=true;++a.used;a.peak=std::max(a.peak,a.used);++a.issued;++a.kinds[r.kind];a.next=now+1;
  T delay=latency+(jitter?(a.issued*17+p*7)%23:0);
  later(now+delay,[this,p,tag,r=std::move(r)]()mutable{auto& a=ports[p];require(a.tags[tag]&&a.used,"tag mismatch");a.tags[tag]=false;--a.used;++a.returned;r.done();port_arm(p);});port_arm(p);
 }
 void memory(unsigned p,unsigned kind,std::function<void()> done){auto& a=ports[p];if(a.queue.size()==64){++a.queue_stall;later(now+1,[this,p,kind,done=std::move(done)]()mutable{memory(p,kind,std::move(done));});return;}a.queue.push_back({kind,std::move(done)});a.queue_peak=std::max<unsigned>(a.queue_peak,a.queue.size());port_arm(p);}
 void bank_arm(unsigned b){auto& a=banks[b];if(a.armed||a.input.empty())return;if(a.used==K){++a.context_stall;return;}unsigned l=tr.pops[a.input.front()].node/4;if(a.words.count(l)){++a.word_stall;return;}a.armed=true;later(std::max(now,a.next),[this,b]{accept(b);});}
 void accept(unsigned b){auto& a=banks[b];a.armed=false;auto i=a.input.front();a.input.pop_front();auto p=tr.pops[i];require(a.used<K&&a.words.insert(p.node/4).second,"word reservation");++a.used;a.peak=std::max(a.peak,a.used);++a.accept;a.first_accept=std::min(a.first_accept,now);a.last_accept=now;a.next=now+1;
  // Canonical read; no write is needed for POP. Context holds whole word through retirement.
  memory(b/2,0,[this,b,i]{later(now+2,[this,b,i]{retire(b,i);});});bank_arm(b);
 }
 void wake_blocked(){
  if(blocked_armed||blocked.empty())return;blocked_armed=true;later(std::max(now+1,stall_tokens_until),[this]{blocked_armed=false;auto [b,i,start]=blocked.front();blocked.pop_front();banks[b].token_stall+=now-start;retire(b,i);wake_blocked();});
 }
 void retire(unsigned b,unsigned i){auto& a=banks[b];auto p=tr.pops[i];
  // Slot must be available before changing pending. No failed/stale POP emits a token.
  if(p.valid&&streaming&&(tokens.size()==64||now<stall_tokens_until)){blocked.push_back({b,i,now});require(blocked.size()<=64*K,"blocked context capacity");wake_blocked();return;}
  auto& x=state.at(p.node);require(x.label==p.label&&x.pv==p.pv,"POP order/state");auto result=pending17::packed_op(x,2,0,p.arg);require(bool(result)==bool(p.valid),"POP oracle");
  ++a.retire;a.first_retire=std::min(a.first_retire,now);a.last_retire=now;--a.used;require(a.words.erase(p.node/4)==1,"release reservation");pop_end=now;
  if(p.valid){require(p.parent<tr.parents.size()&&tr.parents[p.parent].label==p.label,"snapshot");require(tokens.size()<(streaming?64:524288),"parent capacity");tokens.push_back(p.parent);++token_emits;token_peak=std::max<unsigned>(token_peak,tokens.size());if(streaming)load_front();}
  bank_arm(b);
  if(!streaming){bool all=true;for(auto& z:banks)all&=z.input.empty()&&z.used==0;if(all)load_front();}
 }
 void load_front(){while(!free_front.empty()&&!tokens.empty()&&now>=stall_tokens_until){auto id=free_front.back();free_front.pop_back();auto parent=tokens.front();tokens.pop_front();++front_used;front_peak=std::max(front_peak,front_used);front_start=std::min(front_start,now);log<<now<<",parent,"<<id<<','<<parent<<'\n';
   auto start=now;unsigned p=bank(tr.parents[parent].node)/2;
   memory(p,1,[this,id,parent,start,p]{front_wait+=now-start;auto start2=now;memory(p,2,[this,id,parent,start2]{front_wait+=now-start2;edge_request(id,parent,0);});});
  }
 }
 void edge_request(unsigned id,unsigned parent,unsigned pos){if(pos==tr.parents[parent].edges.size()){--front_used;free_front.push_back(id);++parents_done;front_end=now;load_front();return;}
  auto start=now;++edge_reads;memory(id/2,3,[this,id,parent,pos,start]{front_wait+=now-start;emit(id,parent,pos,0);});
 }
 void emit(unsigned id,unsigned parent,unsigned pos,unsigned inbeat){auto e=tr.parents[parent].edges[pos];auto& v=proposals.at(e.node/4)[e.node&3];v=std::min(v,e.pair);++edge_emits;++front_emit;++candidate_banks[bank(e.node)];++set_access[bank(e.node)*1024+((e.node>>8)&1023)];
  // Deliberate optimistic relaxation: no candidate router, accumulator set hazard,
  // scratch, FP32 latency, output RMW or finalize delay. It cannot qualify performance.
  later(now+1,[this,id,parent,pos,inbeat]{if(pos+1==tr.parents[parent].edges.size()||inbeat==7)edge_request(id,parent,pos+1);else emit(id,parent,pos+1,inbeat+1);});
 }
 void run(){for(unsigned b=0;b<64;++b)bank_arm(b);while(!events.empty()){auto e=events.top();events.pop();now=e.at;e.fn();require(now<100000000,"watchdog");}
  require(tokens.empty()&&!front_used&&parents_done==tr.parents.size(),"fence parent drain");require(edge_emits==tr.candidates,"candidate conservation");
  for(auto& a:ports)require(!a.used&&a.queue.empty()&&a.issued==a.returned,"port drain");
  for(auto& a:banks)require(a.used==0&&a.input.empty()&&a.words.empty()&&a.accept==a.retire,"pending drain");
  // Independent final whole-pair output comparison. This backing is an oracle,
  // not a simulated graph-sized on-chip accumulator.
  for(auto& [l,x]:tr.lines)for(unsigned k=0;k<4;++k){auto actual=std::min(proposals.at(l)[k],x.before[k]);require(actual==x.after[k],"full-wave proposal/label differential");}
 }
 void save(const char* path){std::ofstream o(path);o<<"{\"scope\":\"stage B relaxed POP/front screen; accumulator, scratch, output and finalize timing omitted; not complete kernel\",\"pending_contexts_per_subbank\":"<<K<<",\"frontend_contexts\":64,\"streaming\":"<<(streaming?"true":"false")<<",\"cycles\":"<<now<<",\"pop_end\":"<<pop_end<<",\"frontend_start\":"<<(front_start==~T(0)?0:front_start)<<",\"frontend_end\":"<<front_end<<",\"frontend_wait_context_cycles\":"<<front_wait<<",\"frontend_emit_context_cycles\":"<<front_emit<<",\"edge_reads\":"<<edge_reads<<",\"candidates\":"<<edge_emits<<",\"parent_tokens\":"<<token_emits<<",\"parent_fifo_peak\":"<<token_peak<<",\"frontend_context_peak\":"<<front_peak<<",\"output_exact\":true,\"fpga_seconds\":null,\"board_measured\":false,\"ports\":[";
  for(unsigned p=0;p<32;++p){auto& a=ports[p];o<<(p?",":"")<<"{\"issued\":"<<a.issued<<",\"returned\":"<<a.returned<<",\"credit_peak\":"<<a.peak<<",\"request_fifo_peak\":"<<a.queue_peak<<",\"credit_full_observations\":"<<a.credit_stall<<",\"request_full_retry_cycles\":"<<a.queue_stall<<"}";}o<<"],\"banks\":[";
  for(unsigned b=0;b<64;++b){auto& a=banks[b];o<<(b?",":"")<<"{\"accepted\":"<<a.accept<<",\"retired\":"<<a.retire<<",\"context_peak\":"<<a.peak<<",\"same_word_observations\":"<<a.word_stall<<",\"context_full_observations\":"<<a.context_stall<<",\"parent_full_context_cycles\":"<<a.token_stall<<",\"accept_span\":"<<(a.accept?a.last_accept-a.first_accept+1:0)<<",\"retire_span\":"<<(a.retire?a.last_retire-a.first_retire+1:0)<<",\"candidates\":"<<candidate_banks[b]<<"}";}o<<"]}\n";
 }
};
int main(int argc,char**argv){try{require(argc>=5,"usage trace contexts stream outprefix [jitter] [token_block_cycles]");Trace t(argv[1]);std::string p=argv[4];Screen s(t,std::stoul(argv[2]),std::stoul(argv[3]),(p+".csv").c_str());s.jitter=argc>5&&std::stoul(argv[5]);s.stall_tokens_until=argc>6?std::stoull(argv[6]):0;s.run();s.save((p+".json").c_str());std::cout<<"SCREEN_PASS cycles="<<s.now<<" candidates="<<s.edge_emits<<'\n';}catch(std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
