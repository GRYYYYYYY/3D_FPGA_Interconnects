#include "../descriptor/packed.hpp"
#include <omp.h>
#include <cfenv>
#include <filesystem>
#include <iomanip>
#include <iostream>
using Pair=uint64_t;
constexpr Pair INF=0x7f8000007f800000ull,MISSING=0x7fc000007fc00000ull;
using Clock=std::chrono::steady_clock;
static double sec(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
static Pair add(Pair a,Pair b){return Graph::packed({Graph::unpack(a).delay+Graph::unpack(b).delay,Graph::unpack(a).congestion+Graph::unpack(b).congestion});}
template<unsigned FORMAT> inline dfdesc::Decoded trusted(const uint8_t*p){
 // This hot decoder is used only after the entire persisted image has been
 // strictly decoded and compared to native input before resident execution.
 if constexpr(FORMAT==8){uint64_t v;memcpy(&v,p,8);uint32_t begin=v;return {begin,begin+uint32_t((v>>32)&65535),uint32_t((v>>48)&32767),bool(v>>63)};}
 else return {dfdesc::get32(p),dfdesc::get32(p+4),dfdesc::get32(p+8),bool(dfdesc::get32(p+12)&1)};
}
struct Counts {uint64_t parents=0,edges=0,zero=0,stale=0,updates=0,waves=0,members_peak=0;};
struct Scratch {
 static constexpr unsigned CAP=524288,NIL=~0u;
 struct Member{uint32_t node,version,next;};
 struct Active{uint32_t node,begin,end;};
 std::vector<Pair>label,proposal;std::vector<uint32_t>pending,version;std::vector<uint8_t>marked,seen;
 std::vector<Member>member;std::vector<uint32_t>free_ids,changed;std::vector<Active>active;
 std::array<uint32_t,32768>head,tail;std::array<uint64_t,64>bitmap;uint64_t groups=0;unsigned used=0;
 Scratch(unsigned nodes,unsigned cells):label(nodes),proposal(nodes),pending(nodes),version(nodes),marked(nodes),seen(cells),member(CAP),free_ids(CAP){active.reserve(CAP);changed.reserve(CAP);}
 unsigned minimum()const{unsigned g=__builtin_ctzll(groups);return g*64+__builtin_ctzll(bitmap[g]);}
 void append(unsigned key,unsigned n){dfdesc::require(key<4096&&used<CAP,"DIRECTORY_CAPACITY");unsigned p=free_ids[used++],h=key*8+((n>>2)&7);member[p]={n,++version[n],NIL};pending[n]=key;if(head[h]==NIL)head[h]=p;else member[tail[h]].next=p;tail[h]=p;bitmap[key/64]|=1ull<<(key%64);groups|=1ull<<(key/64);}
 template<unsigned FORMAT,bool PROFILE> Counts solve(const uint8_t*descs,const std::vector<uint32_t>&edge,const std::array<Pair,16>&cost,unsigned src,unsigned targets,Pair*out){
  Counts counts;
  std::fill(label.begin(),label.end(),INF);std::fill(proposal.begin(),proposal.end(),INF);std::fill(pending.begin(),pending.end(),NIL);std::fill(version.begin(),version.end(),0);std::fill(marked.begin(),marked.end(),0);std::fill(seen.begin(),seen.end(),0);std::fill(out,out+seen.size(),MISSING);
  head.fill(NIL);tail.fill(NIL);bitmap.fill(0);groups=0;used=0;for(unsigned i=0;i<CAP;++i)free_ids[i]=i;
  label[src]=proposal[src]=0;append(0,src);if(!targets)return counts;unsigned recorded=0,waves=0;
  while(groups){dfdesc::require(++waves<=1000000,"WAVE_BUDGET");unsigned key=minimum();active.clear();changed.clear();bitmap[key/64]&=~(1ull<<(key%64));if(!bitmap[key/64])groups&=~(1ull<<(key/64));
   for(unsigned bank=0;bank<8;++bank){unsigned h=key*8+bank,id=head[h];head[h]=tail[h]=NIL;
    while(id!=NIL){auto m=member[id];free_ids[--used]=id;id=m.next;if(pending[m.node]!=key||version[m.node]!=m.version){if(PROFILE)++counts.stale;continue;}
     unsigned n=m.node;pending[n]=NIL;dfdesc::require(active.size()<CAP,"ACTIVE_CAPACITY");auto d=trusted<FORMAT>(descs+uint64_t(n)*FORMAT);active.push_back({n,d.begin,d.end});
     if(PROFILE){++counts.parents;counts.zero+=d.begin==d.end;}
     if(d.valid){if(!seen[d.cell]||label[n]<out[d.cell])out[d.cell]=label[n];if(!seen[d.cell]){seen[d.cell]=1;++recorded;}}
   }}
   for(auto a:active){Pair parent=label[a.node];for(uint64_t e=a.begin;e<a.end;++e){uint32_t desc=edge[e],v=desc&0xfffffff;Pair candidate=add(parent,cost[desc>>28]);
     // Numeric admission does not eliminate arithmetic overflow at runtime.
     dfdesc::require((candidate&0x7f8000007f800000ull)!=0x7f8000007f800000ull&&((candidate>>32)&0x7f800000)!=0x7f800000&&(candidate&0x7f800000)!=0x7f800000,"FP32_OVERFLOW");
     if(PROFILE)++counts.edges;
     if(candidate<proposal[v]){proposal[v]=candidate;if(!marked[v]){dfdesc::require(changed.size()<CAP,"CHANGED_CAPACITY");marked[v]=1;changed.push_back(v);}}
   }}
   for(auto v:changed){label[v]=proposal[v];unsigned k=label[v]>>52;dfdesc::require(k>=key,"NONMONOTONE_BUCKET");if(pending[v]!=k)append(k,v);marked[v]=0;}
   if(PROFILE){counts.updates+=changed.size();counts.members_peak=std::max<uint64_t>(counts.members_peak,used);}
   if((!groups||minimum()!=key)&&recorded==targets)break;
  }counts.waves=waves;return counts;
 }
};
template<unsigned FORMAT,bool PROFILE> int run(Graph&g,const dfdesc::Admission&a,const std::vector<uint8_t>&image,const std::vector<uint32_t>&edge,const std::vector<Pair>&gold,unsigned threads,unsigned repeats,uint64_t stride,const std::string&out){
 std::vector<Scratch>scratch;for(unsigned t=0;t<threads;++t)scratch.emplace_back(a.nodes,a.cells);
 std::vector<Pair>output(a.jobs*a.cells);std::vector<Counts>counts(a.jobs);std::ofstream metrics(out+"/metrics.jsonl");metrics<<std::setprecision(12);
 for(unsigned rep=0;rep<repeats;++rep){int failures=0;auto start=Clock::now();std::array<Pair,16>cost{};for(unsigned c=0;c<g.w.h.costs;++c)cost[c]=Graph::packed(g.w.cost[c]);
  #pragma omp parallel for schedule(dynamic) num_threads(threads) reduction(max:failures)
  for(unsigned q=0;q<a.jobs;++q){try{counts[q]=scratch[omp_get_thread_num()].solve<FORMAT,PROFILE>(image.data()+q*stride,edge,cost,g.w.job[q].source,a.targets[q],output.data()+q*a.cells);}catch(const std::exception&e){failures=1;
   #pragma omp critical
   std::cerr<<"SAMPLE_ERROR q="<<q<<" "<<e.what()<<std::endl;
  }}double elapsed=sec(start);dfdesc::require(!failures&&output==gold,"FULL_BATCH_EXACT_MISMATCH");
  metrics<<"{\"scope\":\"RESIDENT_COMPLETE_BATCH_V2\",\"representation\":\"packed_descriptor\",\"format_bytes\":"<<FORMAT<<",\"threads\":"<<threads<<",\"rep\":"<<rep<<",\"warmup\":"<<(rep==0?"true":"false")<<",\"resident_seconds\":"<<elapsed<<",\"full_output_exact\":true,\"profile_enabled\":"<<(PROFILE?"true":"false")<<",\"timing_qualification\":\"external_run_receipt_required\"}\n"<<std::flush;
  std::cout<<"BATCH_PASS rep="<<rep<<" seconds="<<elapsed<<std::endl;
 }
 // Store native pair byte order (delay32,congestion32) for wire-map import.
 std::ofstream binary(out+"/output.bin",std::ios::binary);for(auto p:output){auto c=Graph::unpack(p);la::write(binary,&c,1);}binary.close();
 std::ofstream cs(out+"/samples.json");cs<<"[";for(unsigned q=0;q<a.jobs;++q){if(q)cs<<',';auto c=counts[q];cs<<"{\"sample\":"<<q<<",\"targets\":"<<a.targets[q]<<",\"parents\":"<<c.parents<<",\"candidates\":"<<c.edges<<",\"zero_degree\":"<<c.zero<<",\"stale\":"<<c.stale<<",\"updates\":"<<c.updates<<",\"waves\":"<<c.waves<<",\"member_peak\":"<<c.members_peak<<",\"output_exact\":true}";}cs<<"]\n";
 return 0;
}
int main(int argc,char**argv){try{
 dfdesc::require(argc==10,"usage cpu workload golden conversion_dir format threads repeats profile output_dir process_label");std::fesetround(FE_TONEAREST);
 uint32_t endian=1;dfdesc::require(*reinterpret_cast<uint8_t*>(&endian)==1,"CPU_REFERENCE_REQUIRES_LITTLE_ENDIAN");
 std::string path=argv[3],out=argv[8];unsigned format=std::stoul(argv[4]),threads=std::stoul(argv[5]),repeats=std::stoul(argv[6]);bool profile=std::stoul(argv[7]);
 dfdesc::require((format==8||format==16)&&threads>0&&threads<=16&&repeats>0,"CONFIGURATION");dfdesc::require(!std::filesystem::exists(out),"OUTPUT_EXISTS");std::filesystem::create_directories(out);
 auto start=Clock::now();Graph g(argv[1]);dfdesc::Admission a(g);uint64_t stride=dfdesc::align(a.nodes*format),bytes=dfdesc::mul64(stride,a.jobs);
 std::vector<uint8_t>image(bytes);std::vector<uint32_t>edge(a.edges);std::vector<la::Cost>rawgold(a.jobs*a.cells);std::vector<Pair>gold(rawgold.size());
 dfdesc::require(std::filesystem::file_size(path+"/descriptors.bin")==bytes&&std::filesystem::file_size(path+"/edges.bin")==a.edges*4,"BACKING_SIZE");
 std::ifstream f(path+"/descriptors.bin",std::ios::binary),e(path+"/edges.bin",std::ios::binary),r(argv[2],std::ios::binary);la::read(f,image.data(),image.size());la::read(e,edge.data(),edge.size());la::read(r,rawgold.data(),rawgold.size());dfdesc::require(edge==g.edge,"PREPARED_EDGE_IDENTITY");
 for(size_t i=0;i<gold.size();++i)gold[i]=Graph::packed(rawgold[i]);
 for(unsigned q=0;q<a.jobs;++q){for(uint64_t n=0;n<a.nodes;++n){auto d=dfdesc::decode_record(image.data()+q*stride+n*format,format,a.edges,a.cells);int cell=g.w.cell[uint64_t(q)*a.nodes+n];bool valid=g.w.node[n].type==1&&cell>=0;dfdesc::require(d.begin==g.row[n]&&d.end==g.row[n+1]&&d.valid==valid&&d.cell==unsigned(valid?cell:0),"PERSISTED_DESCRIPTOR_IDENTITY");
   auto fast=format==8?trusted<8>(image.data()+q*stride+n*format):trusted<16>(image.data()+q*stride+n*format);dfdesc::require(d.begin==fast.begin&&d.end==fast.end&&d.cell==fast.cell&&d.valid==fast.valid,"TRUSTED_DECODE_IDENTITY");
  }for(uint64_t b=a.nodes*format;b<stride;++b)dfdesc::require(image[q*stride+b]==0,"DESCRIPTOR_PADDING");}
 std::ofstream prep(out+"/preparation.json");prep<<std::setprecision(12)<<"{\"load_and_cache_validation_seconds\":"<<sec(start)<<",\"validated_descriptor_bytes\":"<<bytes<<",\"records\":"<<a.nodes*a.jobs<<",\"actual_persisted_backing\":true,\"free_descriptor_recompute_in_resident\":false,\"profile\":"<<(profile?"true":"false")<<"}\n";prep.close();
 if(format==8)return profile?run<8,true>(g,a,image,edge,gold,threads,repeats,stride,out):run<8,false>(g,a,image,edge,gold,threads,repeats,stride,out);
 return profile?run<16,true>(g,a,image,edge,gold,threads,repeats,stride,out):run<16,false>(g,a,image,edge,gold,threads,repeats,stride,out);
 }catch(const std::exception&e){std::cerr<<"CPU_FAIL "<<e.what()<<std::endl;return 1;}
}
