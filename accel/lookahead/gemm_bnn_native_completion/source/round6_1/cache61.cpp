#include "replay61.hpp"
#include <list>
#include <unordered_map>
#include <iostream>
#include <iomanip>
struct Entry {uint32_t dst;la::Cost pair;bool dirty;};
struct Cache {
 unsigned capacity;std::list<Entry> lru;std::unordered_map<uint32_t,std::list<Entry>::iterator> index;
 explicit Cache(unsigned c):capacity(c){index.reserve(2*c);}
};
struct Observer {
 unsigned q,capacity;bool sample;uint64_t limit=5000000,events=0,hits=0,misses=0,evictions=0,dirty_writes=0,improved=0,member_writes=0,publishes=0,empty_transitions=0,min_select=0,chunk_peak=0,member_peak=0,pool_chunks=0,selected=0;
 std::array<uint64_t,32> read_channels{},write_channels{};std::array<uint64_t,65> reuse_gap_bins{},distinct_distance_bins{};std::vector<unsigned> fenwick;unsigned distinct=0;
 std::vector<la::Cost> home;std::vector<uint64_t> last;std::vector<Cache> caches;
 std::unordered_map<uint32_t,uint32_t> chunks;std::array<uint32_t,4096> bucket_members{};std::vector<std::array<uint64_t,5>> waves;uint32_t current=0;bool selected_wave=false;
 Observer(size_t n,unsigned c,unsigned qid,bool sm):q(qid),capacity(c),sample(sm),home(n,{INFINITY,INFINITY}),last(n,0){if(sample)fenwick.resize(5000002);for(unsigned b=0;b<64;++b)caches.emplace_back(c);}
 void member(uint32_t b,uint32_t v){++member_writes;if(!bucket_members[b]++)++empty_transitions;uint32_t key=b*64+v%64;auto& count=chunks[key];if(count%32==0){++publishes;++pool_chunks;chunk_peak=std::max(chunk_peak,pool_chunks);if(pool_chunks>16384)throw std::runtime_error("finite chunk pool overflow");}++count;}
 void begin_wave(uint32_t b,uint64_t wave,const std::vector<uint32_t>& active,const std::vector<la::Cost>& labels){current=b;++min_select;selected_wave=!sample||(q==0&&(wave==1||wave==10||wave==30||wave==50||wave==59));if(sample&&selected_wave){home=labels;std::fill(last.begin(),last.end(),0);std::fill(fenwick.begin(),fenwick.end(),0);distinct=0;}waves.push_back({b,wave,active.size(),events,pool_chunks});}
 void write(Entry& e){if(e.dirty){home[e.dst]=e.pair;++dirty_writes;write_channels[(e.dst/4)%32]+=32;}}
 void edge(size_t qid,uint32_t v,la::Cost cand,uint64_t wave){
  if(!selected_wave||(sample&&selected>=limit))return;++selected;++events;
  if(sample){auto prefix=[&](unsigned k){unsigned sum=0;for(;k;k-=k&-k)sum+=fenwick[k];return sum;};auto update=[&](unsigned k,int value){for(;k<fenwick.size();k+=k&-k)fenwick[k]+=value;};if(last[v]){unsigned distance=distinct-prefix(last[v]);unsigned b=distance?32-__builtin_clz(distance):0;++distinct_distance_bins[b];update(last[v],-1);}else ++distinct;update(events,1);}
  if(last[v]){uint64_t gap=events-last[v];unsigned bin=gap?64-__builtin_clzll(gap):0;++reuse_gap_bins[bin];}last[v]=events;
  auto& c=caches[v%64];auto hit=c.index.find(v);
  if(hit!=c.index.end()){++hits;c.lru.splice(c.lru.begin(),c.lru,hit->second);}
  else{++misses;read_channels[(v/4)%32]+=32;if(c.lru.size()==capacity){auto& old=c.lru.back();write(old);c.index.erase(old.dst);c.lru.pop_back();++evictions;}c.lru.push_front({v,home[v],false});c.index[v]=c.lru.begin();}
  auto& e=c.lru.front();if(la61::less(cand,e.pair)){e.pair=cand;e.dirty=true;++improved;}
 }
 void flush(){for(auto& c:caches){for(auto& e:c.lru)write(e);c.lru.clear();c.index.clear();}
  // Snapshot fully consumed and all proposal writes visible before commit/publish.
  for(unsigned bank=0;bank<64;++bank){auto i=chunks.find(current*64+bank);if(i!=chunks.end()){pool_chunks-=(i->second+31)/32;chunks.erase(i);}}bucket_members[current]=0;
 }
 void end_wave(uint64_t entries,uint64_t buckets){member_peak=std::max(member_peak,entries);waves.back()[3]=events-waves.back()[3];}
 void print(const la61::Profile& p,bool equal){std::cout<<"{\"qid\":"<<q<<",\"capacity_per_bank\":"<<capacity<<",\"sample\":"<<(sample?"true":"false")<<",\"events\":"<<events<<",\"fp32_additions\":"<<events*2<<",\"cache_hits\":"<<hits<<",\"cache_misses\":"<<misses<<",\"evictions\":"<<evictions<<",\"dirty_pair_writebacks\":"<<dirty_writes<<",\"improving_cache_updates\":"<<improved<<",\"member_enqueue\":"<<member_writes<<",\"pending_writes\":"<<member_writes<<",\"chunk_publish\":"<<publishes<<",\"empty_to_nonempty\":"<<empty_transitions<<",\"min_selection\":"<<min_select<<",\"chunk_pool_peak\":"<<chunk_peak<<",\"member_peak\":"<<member_peak<<",\"status\":"<<p.status<<",\"whole_pair_home_equal\":"<<(equal?"true":"false")<<",\"proposal_read_bytes_channels\":[";for(unsigned i=0;i<32;++i){if(i)std::cout<<',';std::cout<<read_channels[i];}std::cout<<"],\"proposal_write_bytes_channels\":[";for(unsigned i=0;i<32;++i){if(i)std::cout<<',';std::cout<<write_channels[i];}std::cout<<"],\"reuse_reference_gap_log2_histogram\":[";for(unsigned i=0;i<65;++i){if(i)std::cout<<',';std::cout<<reuse_gap_bins[i];}std::cout<<"],\"sample_within_wave_distinct_reuse_distance_log2\":[";for(unsigned i=0;i<65;++i){if(i)std::cout<<',';std::cout<<distinct_distance_bins[i];}std::cout<<"],\"waves_bucket_ordinal_width_candidates_chunks\":[";for(size_t i=0;i<waves.size();++i){if(i)std::cout<<',';auto x=waves[i];std::cout<<'['<<x[0]<<','<<x[1]<<','<<x[2]<<','<<x[3]<<','<<x[4]<<']';}std::cout<<"]}\n"<<std::flush;}
};
int main(int argc,char** argv){try{if(argc!=4)throw std::runtime_error("cache61 workload entries sample|full");la::Workload w(argv[1]);la61::Compact c(w);la61::Prepared prep(c);unsigned capacity=std::stoul(argv[2]);if(capacity!=16&&capacity!=32&&capacity!=64&&capacity!=128)throw std::runtime_error("bad cache capacity");bool sample=std::string(argv[3])=="sample";la61::ScratchT<la61::DirectDirectory> s(w.h.nodes);std::vector<la::Cost> output(w.h.cells);
 for(unsigned q=0;q<(sample?std::min<uint64_t>(1,w.h.jobs):w.h.jobs);++q){Observer obs(w.h.nodes,capacity,q,sample);if(prep.targets[q])obs.home[w.job[q].source]={0,0};auto p=la61::search_replay<true>(c,q,prep.targets[q],20,s,output.data(),false,500000000,524288,obs);bool equal=sample||!memcmp(obs.home.data(),s.label.data(),w.h.nodes*8);obs.print(p,equal);if(p.status||!equal)return 3;}
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 10;}}
