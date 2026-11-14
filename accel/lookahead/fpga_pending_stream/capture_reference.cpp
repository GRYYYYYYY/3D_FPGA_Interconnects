// Derived from a64c934 pending17_reference.cpp; only trace hooks added.
#include "bucket61.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <filesystem>
using namespace la61;
struct Failure:std::runtime_error{using std::runtime_error::runtime_error;};
static unsigned owner(unsigned n){return (n>>2)&7;}
struct BankCounts {
 std::array<size_t,8> used8{},peak8{};std::array<size_t,64> used64{},peak64{};
 void clear(){used8.fill(0);used64.fill(0);}
 void add(unsigned n){auto b=(n>>2)&63;peak8[b&7]=std::max(peak8[b&7],++used8[b&7]);peak64[b]=std::max(peak64[b],++used64[b]);}
 void remove(unsigned n){auto b=(n>>2)&63;if(!used8[b&7]||!used64[b])throw Failure("BANK_ACCOUNTING_UNDERFLOW");--used8[b&7];--used64[b];}
 void write(std::ostream&o)const{o<<"{\"line_hash_8_peak\":[";for(unsigned i=0;i<8;++i)o<<(i?",":"")<<peak8[i];o<<"],\"line_hash_64_peak\":[";for(unsigned i=0;i<64;++i)o<<(i?",":"")<<peak64[i];o<<"]}";}
};
struct List {
 std::vector<uint32_t> a;size_t size=0,peak=0;BankCounts banks;
 explicit List(size_t cap):a(cap){}
 void push(uint32_t x){if(size==a.size())throw Failure("LIST_OVERFLOW");a[size++]=x;banks.add(x);peak=std::max(peak,size);}
 void clear(){size=0;banks.clear();}
};
// Fixed physical member pool; stale entries occupy slots until popped. No vector per bucket.
struct Directory {
 struct Member{uint32_t node,version,next;};
 static constexpr uint32_t nil=~0u;
 std::vector<Member> pool;std::vector<uint32_t> free;
 std::array<uint32_t,4096*8> head,tail;
 BankCounts banks;std::array<uint64_t,64> bits{};uint64_t upper=0;size_t used=0,peak=0;
 explicit Directory(size_t cap):pool(cap),free(cap){clear();}
 void clear(){banks.clear();head.fill(nil);tail.fill(nil);bits.fill(0);upper=used=0;for(size_t i=0;i<free.size();++i)free[i]=i;}
 unsigned min()const{unsigned g=__builtin_ctzll(upper);return g*64+__builtin_ctzll(bits[g]);}
 void put(unsigned key,unsigned node,unsigned version){
  if(key>=4096)throw Failure("KEY_OVERFLOW");if(used==pool.size())throw Failure("MEMBER_OVERFLOW");
  banks.add(node);auto p=free[used++];peak=std::max(peak,used);pool[p]={node,version,nil};unsigned h=key*8+owner(node);
  if(head[h]==nil)head[h]=p;else pool[tail[h]].next=p;tail[h]=p;bits[key/64]|=1ull<<(key%64);upper|=1ull<<(key/64);
 }
 template<class Fn>void pop(unsigned key,Fn fn){
  bits[key/64]&=~(1ull<<(key%64));if(!bits[key/64])upper&=~(1ull<<(key/64));
  for(unsigned b=0;b<8;++b){unsigned h=key*8+b,p=head[h];head[h]=tail[h]=nil;while(p!=nil){auto m=pool[p];free[--used]=p;banks.remove(m.node);fn(m.node,m.version);p=m.next;}}
 }
};
static uint64_t pack(la::Cost c){return (uint64_t(bits(c.delay))<<32)|bits(c.congestion);}
#include "pending17.hpp"
struct WaveAccumulatorProfile {WaveAccumulatorProfile(unsigned,const std::string&){} void begin(){} void candidate(unsigned,uint64_t){} template<class...T>void finish(T&&...){}void save(){}};
struct PreparedCSR {
 std::vector<uint64_t> row;std::vector<uint32_t> edge;uint64_t raw=0,skips=0,breaks=0;double seconds=0;
 explicit PreparedCSR(const la::Workload& w){auto t=std::chrono::steady_clock::now();if(w.h.nodes>=(1ull<<28)||w.h.costs>16)throw Failure("UNSUPPORTED_DESCRIPTOR");row.reserve(w.h.nodes+1);edge.reserve(w.h.edges);
  for(unsigned u=0;u<w.h.nodes;++u){row.push_back(edge.size());for(uint64_t k=w.row[u];k<w.row[u+1];++k){++raw;auto v=w.edge[k].dst;if(v>=w.h.nodes||w.node[v].cost>=w.h.costs)throw Failure("BAD_INPUT");int e=la::eligible(w.node[u],w.node[v]);if(e<0){++breaks;break;}if(!e){++skips;continue;}edge.push_back(v|(w.node[v].cost<<28));}}
  row.push_back(edge.size());seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();
 }
};
#include "trace_capture.hpp"
int main(int argc,char**argv){try{
 if(argc<4)throw Failure("usage workload reference.bin outdir [member_cap] [list_cap]");la::Workload w(argv[1]);Prepared counts(w);PreparedCSR p(w);std::filesystem::create_directories(argv[3]);std::string d=argv[3];size_t cap=argc>4?std::stoull(argv[4]):524288,lc=argc>5?std::stoull(argv[5]):524288;
 if(w.h.nodes>(1u<<22))throw Failure("MAX_N_REJECT");std::vector<pending17::Old> old_state(w.h.nodes);std::vector<pending17::Packed> packed_state(w.h.nodes);uint64_t checked_ops=0;
 Directory dir(cap);List active(lc),changed(lc),closed(lc),touched(w.h.nodes); // closed is a verification-only R1 oracle; it never drives candidate search/output // touched is independent oracle only, not a hardware list
 const la::Cost inf={INFINITY,INFINITY};std::vector<la::Cost> label(w.h.nodes),prop(w.h.nodes),out(w.h.jobs*w.h.cells);
 std::vector<uint32_t> pending(w.h.nodes),version(w.h.nodes),mark(w.h.nodes),touch(w.h.nodes);std::vector<uint8_t> in_closed(w.h.nodes),output_seen(w.h.cells),pop_seen(w.h.nodes);
 std::vector<la::Cost> oracle(w.h.cells);
 std::vector<uint32_t> cell_epoch(w.h.cells),meta_epoch((w.h.nodes+3)/4);
 std::array<uint64_t,8> target_banks{};
 uint32_t epoch=1;uint64_t target_pops=0,repeated_target_pops=0,output_improvements=0,closures_checked=0;
 uint64_t bucket_targets=0,bucket_unique_cells=0,bucket_metadata_lines=0;
 std::ofstream closures(d+"/closures.csv");closures<<"sample,bucket,recorded,target_pop_events,unique_target_cells,metadata_line_working_set,output_hash\n";
 auto mix=[](uint64_t h,uint64_t v){return (h^v)*1099511628211ull;};
 std::ofstream waves(d+"/waves.csv");waves<<"sample,wave,bucket,active,candidates,touched,changed,changed_lines,closed,member_slots,stale,active_snapshot_hash,commit_hash,target_pop_events\n";
 WaveAccumulatorProfile profile(w.h.nodes,d);TraceCapture capture(d);
 uint64_t total_edges=0,total_changed=0,total_touched=0,total_active=0,total_waves=0,stale=0;auto begin=std::chrono::steady_clock::now();
 for(unsigned q=0;q<w.h.jobs;++q){std::fill(old_state.begin(),old_state.end(),pending17::Old{});std::fill(packed_state.begin(),packed_state.end(),pending17::Packed{});std::fill(label.begin(),label.end(),inf);std::fill(prop.begin(),prop.end(),inf);std::fill(pending.begin(),pending.end(),~0u);std::fill(version.begin(),version.end(),0);std::fill(mark.begin(),mark.end(),0);std::fill(touch.begin(),touch.end(),0);std::fill(in_closed.begin(),in_closed.end(),0);dir.clear();closed.clear();std::fill(output_seen.begin(),output_seen.end(),0);std::fill(pop_seen.begin(),pop_seen.end(),0);unsigned pop_recorded=0;bucket_targets=bucket_unique_cells=bucket_metadata_lines=0;++epoch;auto output=out.data()+q*w.h.cells;for(unsigned c=0;c<w.h.cells;++c)output[c]=oracle[c]={la::missing(),la::missing()};if(!counts.targets[q])continue;
  auto src=w.job[q].source;label[src]=prop[src]={0,0};pending17::both(old_state[src],packed_state[src],5,0,0);++checked_ops;pending[src]=0;dir.put(0,src,++version[src]);unsigned wave=0,recorded=0;
  while(dir.upper){unsigned bucket=dir.min();if(++wave>=1000000)throw Failure("WAVE_LIMIT");active.clear();changed.clear();touched.clear();profile.begin();capture.begin(q,wave,bucket);uint64_t ah=14695981039346656037ull,ch=ah,wave_targets=0;
   dir.pop(bucket,[&](unsigned u,unsigned v){unsigned old_pv=packed_state[u].pv;unsigned success=pending17::both(old_state[u],packed_state[u],2,0,((v&65535)<<12)|bucket);++checked_ops;capture.pop(u,((v&65535)<<12)|bucket,old_pv,success,success&&w.node[u].type==1&&w.cell[q*w.h.nodes+u]>=0,pack(label[u]));if(bool(success)!=(pending[u]==bucket&&version[u]==v))throw Failure("POP_DIVERGENCE");if(!success){++stale;return;}pending[u]=~0u;version[u]=0;active.push(u);
    // Capture the parent before any relaxation/commit in this wave. Every valid
    // POP generates an event, even for zero outdegree; stale members return above.
    const auto parent=label[u];if(!la::numeric(parent.delay)||!la::numeric(parent.congestion))throw Failure("INVALID_POP_PAIR");
    if((bits(parent.delay)>>20)!=bucket)throw Failure("POP_KEY_MISMATCH");
    ah=mix(mix(ah,u),pack(parent));
    if(meta_epoch[u/4]!=epoch){meta_epoch[u/4]=epoch;++bucket_metadata_lines;}
    const int c=w.cell[q*w.h.nodes+u];
    if(w.node[u].type==1&&c>=0){
      ++target_pops;++wave_targets;++bucket_targets;++target_banks[c&7];
      if(pop_seen[u])++repeated_target_pops;pop_seen[u]=1;
      if(cell_epoch[c]!=epoch){cell_epoch[c]=epoch;++bucket_unique_cells;}
      if(!output_seen[c]||less(parent,output[c])){output[c]=parent;++output_improvements;}
      if(!output_seen[c]){output_seen[c]=1;++pop_recorded;}
    }
    if(!in_closed[u]){closed.push(u);in_closed[u]=1;}});
   uint64_t edges=0;
   for(size_t a=0;a<active.size;++a){auto u=active.a[a];const auto parent=label[u];capture.parent(u,pack(parent));for(uint64_t e=p.row[u];e<p.row[u+1];++e){auto desc=p.edge[e];auto v=desc&0xfffffff;auto cost=w.cost[desc>>28];la::Cost cand={parent.delay+cost.delay,parent.congestion+cost.congestion};if(!la::numeric(cand.delay)||!la::numeric(cand.congestion))throw Failure("NUMERIC");++edges;profile.candidate(v,pack(cand));capture.candidate(v,pack(cand));
    if(touch[v]!=wave){touched.push(v);touch[v]=wave;
#ifdef PROFILE_PRIVATE_INF
      prop[v]=inf;
#endif
    }
    if(less(cand,prop[v])){
#ifndef PROFILE_PRIVATE_INF
     if(mark[v]!=wave){changed.push(v);mark[v]=wave;}
#endif
     prop[v]=cand;}
   }}
#ifdef PROFILE_PRIVATE_INF
   changed.clear();
   for(size_t i=0;i<touched.size;++i){auto v=touched.a[i];if(less(prop[v],label[v])){changed.push(v);mark[v]=wave;}else{mark[v]=0;prop[v]=label[v];}}
#endif
   profile.finish(q,wave,bucket,changed,label,prop);capture.finish(label,prop,packed_state);
   // Independent touched reference set checks changed-only equality before commits.
   size_t improved=0;for(size_t i=0;i<touched.size;++i){auto v=touched.a[i];bool c=less(prop[v],label[v]);if(c)++improved;if(c!=(mark[v]==wave))throw Failure("CHANGED_SET_MISMATCH");}if(improved!=changed.size)throw Failure("DUPLICATE_CHANGED");
   std::vector<uint32_t> lines;lines.reserve(changed.size);
   for(size_t i=0;i<changed.size;++i){auto v=changed.a[i];if(!less(prop[v],label[v]))throw Failure("COMMIT_NO_IMPROVEMENT");unsigned append=pending17::both(old_state[v],packed_state[v],3,pack(prop[v]),0);++checked_ops;if(old_state[v].label!=pack(prop[v]))throw Failure("LABEL_MISMATCH");label[v]=prop[v];ch=mix(mix(ch,v),pack(label[v]));lines.push_back(v>>2);unsigned key=bits(label[v].delay)>>20;if(key<bucket)throw Failure("NONMONOTONE");if(bool(append)!=(pending[v]!=key))throw Failure("APPEND_DIVERGENCE");if(append){version[v]=(version[v]+1)&65535;dir.put(key,v,version[v]);pending[v]=key;}if(packed_state[v].pv!=(65536|version[v]))throw Failure("PV_VERSION");}
   std::sort(lines.begin(),lines.end());size_t nl=std::unique(lines.begin(),lines.end())-lines.begin();
   // Small graph exhaustive wave-start/home invariant; not counted as hardware work.
   if(w.h.nodes<10000)for(unsigned v=0;v<w.h.nodes;++v)if(pack(prop[v])!=pack(label[v]))throw Failure("HOME_LABEL_INVARIANT");
   waves<<q<<','<<wave<<','<<bucket<<','<<active.size<<','<<edges<<','<<touched.size<<','<<changed.size<<','<<nl<<','<<closed.size<<','<<dir.used<<','<<stale<<','<<ah<<','<<ch<<','<<wave_targets<<'\n';
   total_edges+=edges;total_changed+=changed.size;total_touched+=touched.size;total_active+=active.size;++total_waves;
   if(!dir.upper||dir.min()!=bucket){
    // Verification only: old closed-at-bucket-end observer, isolated from output.
    for(size_t i=0;i<closed.size;++i){auto u=closed.a[i];auto c=w.cell[q*w.h.nodes+u];if(w.node[u].type==1&&c>=0){bool first=std::isnan(oracle[c].delay);if(first||less(label[u],oracle[c]))oracle[c]=label[u];recorded+=first;}in_closed[u]=0;}closed.clear();
    if(pop_recorded!=recorded||memcmp(output,oracle.data(),w.h.cells*8))throw Failure("BUCKET_OUTPUT_OR_RECORDED_MISMATCH");
    ++closures_checked;uint64_t oh=14695981039346656037ull;for(unsigned c=0;c<w.h.cells;++c)oh=mix(oh,pack(output[c]));
    closures<<q<<','<<bucket<<','<<pop_recorded<<','<<bucket_targets<<','<<bucket_unique_cells<<','<<bucket_metadata_lines<<','<<oh<<'\n';
    bucket_targets=bucket_unique_cells=bucket_metadata_lines=0;++epoch;
    // Completion is deliberately here, never when an online event finds a target.
    if(pop_recorded==counts.targets[q])break;
   }
  }
 }
 profile.save();std::ofstream(d+"/pending17_invariant.json")<<"{\"all_pass\":true,\"checked_operations\":"<<checked_ops<<",\"MAX_N\":4194304,\"scope\":\"functional operation/state equivalence, no cycle claim\"}\n";
 double resident=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();std::vector<la::Cost> ref(out.size());std::ifstream f(argv[2],std::ios::binary);la::read(f,ref.data(),ref.size());if(memcmp(out.data(),ref.data(),out.size()*8))throw Failure("OUTPUT_MISMATCH");std::ofstream result(d+"/output.bin",std::ios::binary);la::write(result,out.data(),out.size());
 std::ofstream meta(d+"/summary.json");meta<<std::setprecision(12)<<"{\"output_exact\":true,\"jobs\":"<<w.h.jobs<<",\"nodes\":"<<w.h.nodes<<",\"prepared_edges\":"<<p.edge.size()<<",\"original_edges\":"<<w.h.edges<<",\"prepare_seconds\":"<<p.seconds<<",\"eligible_break_rows\":"<<p.breaks<<",\"prepared_bytes\":"<<p.row.size()*8+p.edge.size()*4<<",\"functional_instrumented_wall_s\":"<<resident<<",\"waves\":"<<total_waves<<",\"candidates\":"<<total_edges<<",\"active\":"<<total_active<<",\"touched\":"<<total_touched<<",\"changed\":"<<total_changed<<",\"member_peak\":"<<dir.peak<<",\"active_peak\":"<<active.peak<<",\"changed_peak\":"<<changed.peak<<",\"closed_peak\":"<<closed.peak<<",\"stale\":"<<stale<<"}\n";
 std::ofstream popmeta(d+"/pop_reduction.json");popmeta<<"{\"scope\":\"functional transform with closed verification oracle; not performance\",\"all_bucket_outputs_and_recorded_exact\":true,\"closures_checked\":"<<closures_checked<<",\"valid_target_pop_events\":"<<target_pops<<",\"repeated_target_pop_events\":"<<repeated_target_pops<<",\"output_improvements\":"<<output_improvements<<",\"cell_banks\":[";for(unsigned i=0;i<8;++i)popmeta<<(i?",":"")<<target_banks[i];popmeta<<"]}\n";
 std::ofstream caps(d+"/capacity.json");caps<<"{\"physical_member_pool\":"<<cap<<",\"each_list_capacity\":"<<lc<<",\"member\":";dir.banks.write(caps);caps<<",\"active\":";active.banks.write(caps);caps<<",\"changed\":";changed.banks.write(caps);caps<<",\"closed\":";closed.banks.write(caps);caps<<"}\n";
 if(argc>6&&std::string(argv[6])=="--no-prepared-export"){std::cout<<"POP_REDUCE_NATIVE_PASS capacity audit waves="<<total_waves<<'\n';return 0;}
 // Runtime binary prepared graph; includes no golden/frontier/changed lists.
 std::ofstream b(d+"/prepared.bin",std::ios::binary);uint64_t h[]={0x5350415253455632ull,w.h.nodes,p.edge.size(),w.h.jobs,w.h.costs,w.h.cells};b.write((char*)h,sizeof(h));la::write(b,p.row.data(),p.row.size());la::write(b,p.edge.data(),p.edge.size());la::write(b,w.node.data(),w.node.size());la::write(b,w.cost.data(),w.cost.size());la::write(b,w.cell.data(),w.cell.size());la::write(b,w.job.data(),w.job.size());la::write(b,counts.targets.data(),counts.targets.size());
 std::cout<<"POP_REDUCE_NATIVE_PASS waves="<<total_waves<<" changed="<<total_changed<<" touched="<<total_touched<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
