#include "../../fpga_decoupled_front/graph.hpp"
#define main prior_screen_main
#include "../../fpga_pending_stream/screen.cpp"
#undef main
// Stage 1 FRONTEND ONLY. Valid POP boundary, ideal candidate sink. Not a complete model.
struct FrontModel {
 bool balanced=false,grouped=false;unsigned dispatch=0,alloc_rr=0;
 std::array<T,64> lane_alloc{},lane_occupancy{},lane_slot_pressure{},lane_credit_denied{},lane_queue_wait{},lane_slot_occupancy{};
 std::array<std::array<T,9>,64> lane_slot_hist{};
 static constexpr unsigned H=128,E=256,M=128,L=64,S=512;
 struct Header{bool live=false;unsigned parent=0,gen=0;unsigned sent=0,got=0,need=0;bool meta_done=false;};
 struct Desc{bool live=false;unsigned parent=0,gen=0,inflight=0;T next=0,pos=0,end=0;};
 struct Slot{unsigned state=0,id=0,gen=0;T beat=0;}; // reserved=1, returned=2
 struct Meta{bool live=false,sent=false,ready=false;unsigned parent=0,gen=0;};
 struct Fork{unsigned parent;bool graph=false,meta=false;};
 struct Req{unsigned kind,id,gen,tag;T line,beat=0,due=0;};
 struct Port{std::deque<Req> q,flight,back;std::array<bool,32> tags{};T issue=0,returned=0,stall=0;unsigned peak=0;};
 Graph& g;Trace& tr;char variant;unsigned depth;T t=0,emitted=0,outputs=0,first_seen=0,parents_done=0,edge_req=0,row_req=0,meta_req=0;
 std::array<Header,H> headers;std::array<Desc,E> desc;std::array<Slot,S> slots;std::array<Meta,M> meta;std::array<Port,32> ports;
 std::deque<Fork> fork;std::deque<unsigned> ready;std::vector<T> target;std::vector<bool> seen;
 std::array<unsigned,L> rr{};std::array<std::deque<std::pair<T,Edge>>,L> pipe;
 std::array<T,L> lane_emit{},lane_empty{},lane_block{};std::array<std::array<T,32>,3> traffic{};
 std::array<std::array<T,513>,6> occupancy{};
 std::array<T,32> credit_stall{},queue_stall{},return_full{};
 std::array<std::array<T,65>,32> queue_hist{},flight_hist{},credit_hist{},return_hist{};
 T first_wait=0,continuation_wait=0,last_input=0,last_parent=0,last_candidate=0,last_meta=0,last_response=0;
 std::array<T,8> stalls{};std::array<unsigned,7> peaks{};size_t input=0;unsigned cursor=0;bool jitter=false;
 FrontModel(Graph& graph,Trace& trace,char v,bool j=false):g(graph),tr(trace),variant(v),depth(v=='C'?2:1),target(g.w.h.cells,pending17::INF),seen(target.size()),jitter(j){
  require(g.w.h.cells<=32768,"BRAM output capacity");
  for(auto& p:tr.parents){require(p.edges.size()==g.row[p.node+1]-g.row[p.node],"prepared degree mismatch");}
 }
 bool header_ready(unsigned p){for(auto& h:headers)if(h.live&&h.parent==p)return h.got==h.need;return false;}
 bool request(unsigned kind,unsigned id,unsigned gen,T line,T beat=0){auto& p=ports[line&31];unsigned tag=0;while(tag<32&&p.tags[tag])++tag;if(p.q.size()==64||tag==32){credit_stall[line&31]+=tag==32;queue_stall[line&31]+=p.q.size()==64;++p.stall;return false;}p.tags[tag]=true;p.q.push_back({kind,id,gen,tag,line,beat,0});return true;}
 void tick(){
  // Physical interfaces: one request + one response/port/cycle; reserve tags before enqueue.
  for(unsigned b=0;b<32;++b){auto& p=ports[b];if(!p.q.empty()){auto q=p.q.front();p.q.pop_front();q.due=t+16+(jitter?(p.issue*17+b)%13:0);p.flight.push_back(q);++p.issue;++traffic[q.kind][b];}
   auto it=std::find_if(p.flight.begin(),p.flight.end(),[&](auto q){return q.due<=t;});
   if(it!=p.flight.end()&&p.back.size()==4)++return_full[b];
   if(it!=p.flight.end()&&p.back.size()<4){p.back.push_back(*it);require(p.tags[it->tag],"tag mismatch");p.tags[it->tag]=false;p.flight.erase(it);++p.returned;}
   p.peak=std::max<unsigned>(p.peak,std::count(p.tags.begin(),p.tags.end(),true));
  }
  // Abstract response-buffer bypass when empty (not registered RTL calibration), at most one payload write per logical lane per cycle.
  std::array<bool,L> wrote{};
  for(unsigned k=0;k<32;++k){auto& p=ports[(k+cursor)%32];if(p.back.empty())continue;auto q=p.back.front();unsigned lane=q.kind==1?q.id/8:q.id%L;if(wrote[lane]){++stalls[0];continue;}wrote[lane]=true;p.back.pop_front();last_response=t;
   if(q.kind==0){auto& h=headers[q.id];require(h.live&&h.gen==q.gen,"header generation");++h.got;require(h.got<=h.need,"header duplicate");}
   else if(q.kind==1){auto& s=slots[q.id];require(s.state==1&&s.gen==q.gen&&s.beat==q.beat,"slot generation");auto& d=desc[s.id];require(d.live&&d.gen==q.gen&&d.inflight,"descriptor generation");--d.inflight;s.state=2;}
   else{auto& m=meta[q.id];require(m.live&&m.gen==q.gen,"metadata generation");m.ready=true;if(variant=='A')for(auto& h:headers)if(h.live&&h.parent==m.parent)h.meta_done=true;}
  }++cursor;
  // Descriptor-cycles, overlapping across lanes/parents; never sum as wall time.
  for(auto& d:desc)if(d.live){bool present=false;for(auto& s:slots)if(s.state==2&&s.id==unsigned(&d-desc.data())&&s.beat==d.pos/8)present=true;
   if(!present){++lane_queue_wait[unsigned(&d-desc.data())/4];if(d.pos==g.row[tr.parents[d.parent].node])++first_wait;else ++continuation_wait;}}

  // Eight finite BRAM output banks. Whole-pair forwarding semantics; one update/bank/cycle.
  std::array<bool,8> outbusy{};
  for(auto& m:meta)if(m.live&&m.ready){auto& p=tr.parents[m.parent];int c=g.w.cell[tr.sample*g.w.h.nodes+p.node];if(g.w.node[p.node].type==1&&c>=0){if(outbusy[c&7]){++stalls[1];continue;}outbusy[c&7]=true;target[c]=std::min(target[c],p.label);if(!seen[c]){seen[c]=true;++first_seen;}++outputs;}m.live=false;last_meta=t;}
  for(unsigned i=0;i<M;++i){auto& m=meta[i];if(m.live&&!m.sent&&(variant!='A'||header_ready(m.parent))){auto n=tr.parents[m.parent].node;if(request(2,i,m.gen,g.metabase+tr.sample*g.metastride+n/4)){m.sent=true;++meta_req;}}}
  // Actual two-stage pair pipeline model; every arithmetic value comes from operands/cost.
  for(unsigned l=0;l<L;++l){if(!pipe[l].empty()&&pipe[l].front().first<=t){pipe[l].pop_front();}bool found=false;
   for(unsigned k=0;k<4;++k){unsigned i=l*4+(rr[l]+k)%4;auto& d=desc[i];if(!d.live)continue;int slot=-1;for(unsigned s=l*8;s<l*8+8;++s)if(slots[s].state==2&&slots[s].id==i&&slots[s].beat==d.pos/8){slot=s;break;}if(slot<0)continue;
    if(pipe[l].size()==2){++lane_block[l];break;}auto& p=tr.parents[d.parent];auto descriptor=g.edge[d.pos];Edge e{descriptor&0xfffffff,g.pair(p.label,descriptor)};auto& expected=p.edges[d.pos-g.row[p.node]];require(e.node==expected.node&&e.pair==expected.pair,"real FP32 candidate differential");pipe[l].push_back({t+2,e});++emitted;last_candidate=t;++lane_emit[l];++d.pos;rr[l]=(i%4+1)%4;found=true;
    if(d.pos==d.end||d.pos%8==0)slots[slot].state=0;
    if(d.pos==d.end){require(!d.inflight,"late edge at retire");d.live=false;++parents_done;last_parent=t;}break;
   }if(!found)++lane_empty[l];
  }
  // First beat prefetch is allowed immediately upon E allocation, before lane selection.
  for(unsigned i=0;i<E;++i){auto& d=desc[i];if(!d.live||d.next>=(d.end+7)/8||d.inflight==depth)continue;unsigned lane=i/4,s=lane*8;while(s<lane*8+8&&slots[s].state)++s;if(s==lane*8+8){++stalls[2];++lane_slot_pressure[lane];continue;}
   if(request(1,s,d.gen,g.edgebase+d.next,d.next)){slots[s]={1,i,d.gen,d.next};++d.next;++d.inflight;++edge_req;}else ++lane_credit_denied[lane];}
  // H -> bounded ready FIFO. No header context may prefetch an edge without E ownership.
  unsigned header_ready_count=0;for(auto& h:headers)if((!dispatch||header_ready_count<dispatch)&&h.live&&h.got==h.need&&(variant!='A'||h.meta_done)){if(ready.size()==128){++stalls[3];break;}ready.push_back(h.parent);h.live=false;++header_ready_count;}
  std::array<bool,8> group_used{};unsigned dispatched=0;while(!ready.empty()&&(!dispatch||dispatched<dispatch)){unsigned i=E;
   if(balanced){for(unsigned k=0;k<L&&i==E;++k){unsigned l=(alloc_rr+k)%L;for(unsigned j=0;j<4;++j)if((!grouped||!group_used[l/8])&&!desc[l*4+j].live){i=l*4+j;break;}}}
   else{ i=0;while(i<E&&(desc[i].live||(grouped&&group_used[(i/4)/8])))++i;}if(i==E){++stalls[4];break;}auto p=ready.front();ready.pop_front();++dispatched;auto n=tr.parents[p].node;T a=g.row[n],b=g.row[n+1];if(a==b){++parents_done;last_parent=t;continue;}auto gen=desc[i].gen+1;desc[i]={true,p,gen,0,a/8,a,b};++lane_alloc[i/4];group_used[(i/4)/8]=true;if(balanced)alloc_rr=(i/4+1)%L;}
  for(unsigned i=0;i<H;++i){auto& h=headers[i];if(h.live&&h.sent<h.need){auto n=tr.parents[h.parent].node;T line=n/4+h.sent;if(request(0,i,h.gen,g.rowbase+line)){++h.sent;++row_req;}}}
  unsigned graph_admitted=0,meta_admitted=0;for(auto& f:fork){if(!f.graph&&(!dispatch||graph_admitted<dispatch)){unsigned i=0;while(i<H&&headers[i].live)++i;if(i<H){unsigned gen=headers[i].gen+1;headers[i]={true,f.parent,gen,0,0,unsigned(tr.parents[f.parent].node%4==3?2:1)};f.graph=true;++graph_admitted;}}
   if(!f.meta&&(!dispatch||meta_admitted<dispatch)){unsigned i=0;while(i<M&&meta[i].live)++i;if(i<M){unsigned gen=meta[i].gen+1;meta[i]={true,false,false,f.parent,gen};f.meta=true;++meta_admitted;}}}
  while(!fork.empty()&&fork.front().graph&&fork.front().meta)fork.pop_front();
  // Environment supplies at most 32 valid POP snapshots/cycle; finite fork capacity.
  for(unsigned n=0;n<(dispatch?dispatch:32)&&input<tr.parents.size()&&fork.size()<128;++n) {fork.push_back({unsigned(input++),false,false});last_input=t;}if(fork.size()==128)++stalls[5];if(ready.empty())++stalls[6];
  unsigned hs=0,es=0,ms=0,ss=0;for(auto x:headers)hs+=x.live;for(unsigned i=0;i<E;++i){es+=desc[i].live;lane_occupancy[i/4]+=desc[i].live;}for(auto x:meta)ms+=x.live;for(unsigned l=0;l<L;++l){unsigned used=0;for(unsigned s=l*8;s<l*8+8;++s)used+=slots[s].state!=0;ss+=used;lane_slot_occupancy[l]+=used;++lane_slot_hist[l][used];}std::array<unsigned,7> occ{hs,es,ms,ss,unsigned(fork.size()),unsigned(ready.size()),0};for(unsigned i=0;i<7;++i)peaks[i]=std::max(peaks[i],occ[i]);
  for(unsigned i=0;i<6;++i)++occupancy[i][occ[i]];
  for(unsigned b=0;b<32;++b){auto& p=ports[b];++queue_hist[b][p.q.size()];++flight_hist[b][p.flight.size()];++return_hist[b][p.back.size()];++credit_hist[b][std::count(p.tags.begin(),p.tags.end(),true)];}
  ++t;
 }
 void run(){while(true){tick();require(t<20000000,"watchdog");bool done=parents_done==tr.parents.size()&&input==tr.parents.size()&&fork.empty()&&ready.empty();for(auto& m:meta)done&=!m.live;for(auto& p:ports)done&=p.q.empty()&&p.flight.empty()&&p.back.empty();for(auto& p:pipe)done&=p.empty();if(done)break;}
  require(emitted==tr.candidates,"candidate conservation");require(meta_req==tr.parents.size(),"metadata once");for(auto& p:ports)require(p.issue==p.returned&&std::count(p.tags.begin(),p.tags.end(),true)==0,"port conservation");
  std::vector<T> expected(g.w.h.cells,pending17::INF);for(auto& p:tr.parents){int c=g.w.cell[tr.sample*g.w.h.nodes+p.node];if(g.w.node[p.node].type==1&&c>=0)expected[c]=std::min(expected[c],p.label);}require(target==expected,"target output differential");
 }
 template<class A>static void array(std::ostream&o,const A&a){o<<'[';bool comma=false;for(auto x:a){if(comma)o<<',';comma=true;o<<x;}o<<']';}
 void save(const char* path){std::ofstream o(path);o<<"{\"variant\":\""<<variant<<"\",\"scope\":\"finite frontend-only schedule, valid POP environment, ideal candidate sink; not RTL calibrated\",\"cycles\":"<<t<<",\"parents\":"<<parents_done<<",\"candidates\":"<<emitted<<",\"row_requests\":"<<row_req<<",\"edge_requests\":"<<edge_req<<",\"metadata_requests\":"<<meta_req<<",\"target_events\":"<<outputs<<",\"first_seen\":"<<first_seen<<",\"all_operand_candidates_and_target_outputs_exact\":true,\"H_E_M_slots_fork_ready_peaks\":";array(o,peaks);o<<",\"return_write_conflict_output_bank_slot_ready_E_fork_full_ready_empty_stalls\":";array(o,stalls);o<<",\"lane_emit\":";array(o,lane_emit);o<<",\"lane_empty\":";array(o,lane_empty);o<<",\"traffic_by_kind_port\":[";for(unsigned k=0;k<3;++k){if(k)o<<',';array(o,traffic[k]);}o<<"],\"lane_downstream_backpressure\":";array(o,lane_block);
  o<<",\"first_beat_wait_descriptor_cycles\":"<<first_wait<<",\"continuation_wait_descriptor_cycles\":"<<continuation_wait;
  o<<",\"last_input_parent_candidate_meta_response_cycles\":["<<last_input<<','<<last_parent<<','<<last_candidate<<','<<last_meta<<','<<last_response<<']';
  o<<",\"occupancy_H_E_M_slots_fork_ready_histograms\":[";for(unsigned i=0;i<6;++i){if(i)o<<',';array(o,occupancy[i]);}o<<']';
  o<<",\"port_credit_stall_attempts\":";array(o,credit_stall);o<<",\"port_queue_stall_attempts\":";array(o,queue_stall);o<<",\"port_response_full_cycles\":";array(o,return_full);
  o<<",\"port_queue_flight_credit_return_histograms\":[";for(unsigned b=0;b<32;++b){if(b)o<<',';o<<'[';array(o,queue_hist[b]);o<<',';array(o,flight_hist[b]);o<<',';array(o,credit_hist[b]);o<<',';array(o,return_hist[b]);o<<']';}
  o<<"],\"allocation_mode\":\""<<(balanced?"LANE_RR":"FIRST_FREE")<<"\",\"dispatch_width\":"<<dispatch<<",\"grouped_one_allocation_per_eight_lane_group\":"<<(grouped?"true":"false")<<",\"lane_allocations\":";array(o,lane_alloc);o<<",\"lane_occupancy_context_cycles\":";array(o,lane_occupancy);o<<",\"lane_slot_denied_attempts\":";array(o,lane_slot_pressure);o<<",\"lane_credit_denied_attempts\":";array(o,lane_credit_denied);o<<",\"lane_waiting_for_payload_context_cycles\":";array(o,lane_queue_wait);o<<",\"lane_slot_occupancy_beat_cycles\":";array(o,lane_slot_occupancy);o<<",\"lane_slot_occupancy_histograms\":[";for(unsigned l=0;l<L;++l){if(l)o<<',';array(o,lane_slot_hist[l]);}o<<"],\"fpga_seconds\":null,\"board_measured\":false}\n";}
};
int main(int argc,char**argv){try{require(argc>=5,"workload trace A/B/C out [jitter]");Graph g(argv[1]);Trace t(argv[2]);FrontModel m(g,t,argv[3][0],argc>5&&std::string(argv[5])=="jitter");m.balanced=argc>6&&std::string(argv[6])=="LANE_RR";m.dispatch=argc>7?std::stoul(argv[7]):0;m.grouped=argc>8&&std::string(argv[8])=="grouped";m.run();m.save(argv[4]);std::cout<<"FRONT_PASS cycles="<<m.t<<" candidates="<<m.emitted<<'\n';}catch(std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
