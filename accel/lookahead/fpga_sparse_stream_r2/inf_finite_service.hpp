#pragma once
#include <array>
#include <vector>
#include <deque>
#include <algorithm>
#include <fstream>
#include <queue>
#include <stdexcept>
// Executable finite scheduling contract, NOT RTL-calibrated performance.
// 64 ordered front-end contexts, one candidate/cycle/context; 32 shared physical
// ports, 32 credits/port, 80ns latency (16 cycles at assumed 200MHz).
// The offline scheduler reserves ports conservatively in trace submission order.
// It never assigns traffic to an extra port or assumes arbitrary overlap.
struct InfFiniteService {
 using T=uint64_t;static constexpr unsigned B=64,S=1024,N=1<<22,L=N/4;
 struct Entry {uint32_t line=0;uint8_t mask=0;};
 struct Bank {std::array<Entry,4096> e{};std::array<uint8_t,S> victim{};std::array<T,S> set_done{};T next=0,pv=0,meta=0;std::deque<T> fragments;std::vector<unsigned> spilled;};
 std::array<Bank,B> banks;std::array<T,32> port_next{};std::array<std::deque<T>,32> credits;
 std::array<T,B> front{};std::vector<T> line_ack,pending_word;std::vector<uint8_t> spilled,seen;
 std::array<std::array<T,32>,12> traffic{};std::array<T,12> onchip{};T cycle=0,arrival=0,edge_ready=0,parent_done=0,total_candidates=0;unsigned current_front=0,front_turn=0,edge_in_row=0;
 unsigned gap=1,nodes;T accepted=0,retired=0,spills=0,commits=0,intersection=0;unsigned peak_spill=0,peak_frag=0,peak_credit=0;
 std::ofstream log;std::string dir;
 enum {LABEL_INIT,POP_LABEL,CSR_ROW,CSR_EDGE,NODE_META,SCRATCH_READ,SCRATCH_WRITE,LABEL_READ,LABEL_WRITE,OUTPUT_READ,OUTPUT_WRITE,COST_LOAD};
 static unsigned bank(unsigned line){return (line&31)*2+((line>>5)&1);}
 T mem(unsigned b,T at,unsigned kind){unsigned p=b/2;auto&q=credits[p];T t=std::max(at,port_next[p]);while(!q.empty()&&q.front()<=t)q.pop_front();if(q.size()==32){t=std::max(t,q.front());q.pop_front();while(!q.empty()&&q.front()<=t)q.pop_front();}T ack=t+16;port_next[p]=t+gap;q.push_back(ack);peak_credit=std::max<unsigned>(peak_credit,q.size());++traffic[kind][p];return ack;}
 T drain()const {T t=cycle;for(auto&q:credits)if(!q.empty())t=std::max(t,q.back());for(auto&b:banks)t=std::max(t,b.next);return t;}
 InfFiniteService(unsigned n,const std::string&d):line_ack(L),pending_word(L),spilled(L),seen(L),nodes(n),dir(d),log(d+"/finite_service_cycles.csv"){if(n>N)throw std::runtime_error("MAX_N_REJECT");log<<"sample,wave,start,end,candidates,spill_fragments,unique_commits,intersection\n";if(const char*p=getenv("INF_GAP"))gap=std::stoul(p);}
 void init(){cycle=drain();T start=cycle;for(unsigned l=0;l<(nodes+3)/4;++l)mem(bank(l),start,LABEL_INIT);for(unsigned b=0;b<B;++b){banks[b].pv=start+16384;onchip[0]+=16384;}cycle=std::max(drain(),start+16384);mem(0,cycle,COST_LOAD);mem(0,cycle,COST_LOAD);cycle=drain();}
 void begin(){cycle=drain()+1;for(unsigned b=0;b<B;++b){banks[b].next=cycle;banks[b].spilled.clear();banks[b].fragments.clear();}front.fill(cycle);front_turn=0;accepted=retired=spills=commits=intersection=0;std::fill(seen.begin(),seen.end(),0);}
 // POP uses old label and whole pending-word lock. Directory member service and
 // pending read/clear share explicit per-bank issue slots; no version-only presence.
 void pop(unsigned node,bool valid,bool target){auto l=node/4,b=bank(l);auto&bk=banks[b];T t=std::max({cycle,pending_word[l],bk.pv});t=mem(b,t,POP_LABEL);bk.pv=t+2;pending_word[l]=t+2;onchip[1]+=valid?2:1;onchip[2]+=2;if(target){t=mem(b,t+2,NODE_META);t=mem(b,t,OUTPUT_READ);t=mem(b,t,OUTPUT_WRITE);}bk.next=std::max(bk.next,t+2);}
 void parent(unsigned node){if(front_turn==0){cycle=drain();front.fill(cycle);}current_front=front_turn++%64;arrival=front[current_front];unsigned b=bank(node/4);arrival=mem(b,arrival,CSR_ROW);arrival=mem(b,arrival,NODE_META);edge_in_row=0;parent_done=arrival;}
 void candidate(unsigned node,T /*pair*/){unsigned l=node/4,b=bank(l),set=(l>>6)&1023;auto&bk=banks[b];if(edge_in_row%8==0)edge_ready=mem(current_front,arrival,CSR_EDGE);++edge_in_row;T t=std::max({arrival,edge_ready,bk.next,bk.set_done[set]});unsigned way=bk.victim[set];bool hit=false,empty=false;
  for(int w=3;w>=0;--w)if(!bk.e[w*S+set].mask){way=w;empty=true;}
  for(unsigned w=0;w<4;++w)if(bk.e[w*S+set].mask&&bk.e[w*S+set].line==l){way=w;hit=true;}
  auto&e=bk.e[way*S+set];if(!hit&&e.mask){while(!bk.fragments.empty()&&bk.fragments.front()<=t)bk.fragments.pop_front();if(bk.fragments.size()==8){t=std::max(t,bk.fragments.front());bk.fragments.pop_front();}auto old=e.line;T s=std::max(t+4,line_ack[old]);onchip[3]+=2; // bitmap read and update
   if(spilled[old])s=mem(b,s,SCRATCH_READ);else {if(bk.spilled.size()==2048)throw std::runtime_error("SPILL_LIST_OVERFLOW");bk.spilled.push_back(old);spilled[old]=1;peak_spill=std::max<unsigned>(peak_spill,bk.spilled.size());++onchip[4];}
   s=mem(b,s,SCRATCH_WRITE);line_ack[old]=s;bk.fragments.push_back(s);peak_frag=std::max<unsigned>(peak_frag,bk.fragments.size());++spills;
  }
  if(!hit){e={l,0};bk.victim[set]=(way+1)&3;}e.mask|=1u<<(node&3);bk.set_done[set]=t+5;bk.next=t+1;arrival=t+1;front[current_front]=arrival;parent_done=std::max(parent_done,t+5);++accepted;++retired;++total_candidates;onchip[5]+=4;onchip[6]+=hit?2:5; // 4 meta reads, payload reads/writes
 }
 template<class Active,class CSR,class W,class Labels>void expand(const Active&active,const CSR&csr,const W&w,const Labels&label){
  struct Context {T time;unsigned id,phase,node;T edge,end;bool operator<(const Context&o)const{return time!=o.time?time>o.time:id>o.id;}};
  std::priority_queue<Context> ready;size_t next_parent=0;cycle=drain();
  auto load=[&](unsigned id,T t){if(next_parent<active.size){auto n=active.a[next_parent++];ready.push({t,id,0,n,csr.row[n],csr.row[n+1]});}};
  for(unsigned i=0;i<64;++i)load(i,cycle);
  while(!ready.empty()){
   auto c=ready.top();ready.pop();unsigned b=bank(c.node/4);
   if(c.phase==0){c.time=mem(b,c.time,CSR_ROW);c.phase=1;ready.push(c);continue;}
   if(c.phase==1){c.time=mem(b,c.time,NODE_META);c.phase=2;ready.push(c);continue;}
   if(c.edge==c.end){load(c.id,c.time);continue;}
   if(c.phase==2){c.time=mem(c.id,c.time,CSR_EDGE);c.phase=3;ready.push(c);continue;}
   auto desc=csr.edge[c.edge],node=desc&0xfffffff,l=node/4,db=bank(l),set=(l>>6)&1023;auto&bk=banks[db];T eligible=std::max({c.time,bk.next,bk.set_done[set]});
   while(!bk.fragments.empty()&&bk.fragments.front()<=eligible)bk.fragments.pop_front();
   if(bk.fragments.size()==8)eligible=std::max(eligible,bk.fragments.front());
   if(eligible>c.time){c.time=eligible;ready.push(c);continue;}
   auto cost=w.cost[desc>>28],parent=label[c.node];la::Cost pair={parent.delay+cost.delay,parent.congestion+cost.congestion};
   current_front=c.id;arrival=edge_ready=c.time;edge_in_row=1;candidate(node,pack(pair));
   ++c.edge;c.time=arrival;if((c.edge-csr.row[c.node])%8==0)c.phase=2;ready.push(c);
  }
 }
 template<class Labels,class Props>void finish(unsigned sample,unsigned wave,unsigned, const Labels&label,const Props&prop){T start=cycle;cycle=drain();for(auto&bk:banks)for(auto t:bk.set_done)cycle=std::max(cycle,t);T fence=cycle;
  for(unsigned b=0;b<B;++b){auto&bk=banks[b];T t=fence;auto commit=[&](unsigned l,bool resident){if(seen[l])throw std::runtime_error("DUPLICATE_COMMIT");seen[l]=1;++commits;unsigned count=0;for(unsigned s=0;s<4&&l*4+s<nodes;++s)if(less(prop[l*4+s],label[l*4+s]))++count;t=std::max(t,line_ack[l]);if(spilled[l]){t=mem(b,t,SCRATCH_READ);intersection+=resident;}t=mem(b,t,LABEL_READ);t=std::max({t,pending_word[l],bk.pv})+2;++onchip[7]; // one whole68bit read
    if(count){t=mem(b,t,LABEL_WRITE);t+=1;onchip[8]++;onchip[9]+=count;t+=count; /* ack then pending+directory atomic retirement */}
    pending_word[l]=t;bk.pv=t;spilled[l]=0;t+=1;};
   for(auto&e:bk.e)if(e.mask){t+=3;onchip[10]+=3;commit(e.line,true);e.mask=0;}
   for(auto l:bk.spilled){++t;++onchip[4];if(!seen[l])commit(l,false);}
   // Clear finite 16384bit map as256x64bit words; no epoch wrap shortcut.
   t+=256;onchip[3]+=256;cycle=std::max(cycle,t);bk.next=t;
  }
  cycle=drain()+1;log<<sample<<','<<wave<<','<<start<<','<<cycle<<','<<accepted<<','<<spills<<','<<commits<<','<<intersection<<'\n';
 }
 void save(){std::ofstream f(dir+"/finite_service.json");f<<"{\"scope\":\"new conservative finite event schedule, not RTL calibrated or complete-kernel clock qualified\",\"cycles\":"<<cycle<<",\"assumed_MHz\":200,\"latency_ns\":80,\"issue_gap_ns\":"<<5*gap<<",\"fpga_seconds\":null,\"board_measured\":false,\"candidates\":"<<total_candidates<<",\"peak_spill_list\":"<<peak_spill<<",\"peak_fragment_queue\":"<<peak_frag<<",\"peak_port_credits\":"<<peak_credit<<",\"traffic32B_by_operation_by_physical_port\":[";
  for(unsigned k=0;k<12;++k){if(k)f<<',';f<<'[';for(unsigned p=0;p<32;++p)f<<(p?",":"")<<traffic[k][p];f<<']';}f<<"],\"onchip_operations\":[";for(unsigned k=0;k<12;++k)f<<(k?",":"")<<onchip[k];f<<"]}\n";
 }
};
