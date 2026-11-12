// Verilator4 legacy callback used only by assertion diagnostics; clocks are explicit.
double sc_time_stamp(){return 0;}
#include "Vr2_many_tile.h"
#include "verilated.h"
#include "io.hpp"
#include <array>
#include <vector>
#include <fstream>
#include <iostream>
#include <random>
#include <filesystem>
#include <set>
#include <map>
#include <chrono>
#include <cstdlib>
#include <type_traits>
#ifndef TILE_L
#define TILE_L 32
#define TILE_P 32
#endif
constexpr unsigned L=TILE_L,P=TILE_P,B=__builtin_ctz(L);
template<class W>static void setbits(W&w,unsigned at,unsigned width,uint64_t v){
 if constexpr(std::is_integral<W>::value){for(unsigned i=0;i<width;++i){uint64_t mask=uint64_t(1)<<(at+i);w=(w&~mask)|(((v>>i)&1)?mask:0);}}
 else for(unsigned i=0;i<width;++i){uint32_t mask=uint32_t(1)<<(at+i)%32;w[(at+i)/32]=(w[(at+i)/32]&~mask)|(((v>>i)&1)?mask:0);}
}
template<class W>static uint64_t getbits(const W&w,unsigned at,unsigned width){uint64_t v=0;
 if constexpr(std::is_integral<W>::value){for(unsigned i=0;i<width;++i)v|=uint64_t(w>>(at+i)&1)<<i;}
 else for(unsigned i=0;i<width;++i)v|=uint64_t(w[(at+i)/32]>>((at+i)%32)&1)<<i;return v;
}
using Line=std::array<uint64_t,4>;
struct Request{bool write;unsigned line,id;Line data;uint64_t due;};
int main(int argc,char**argv){try{
 if(argc<5)throw std::runtime_error("workload prepared reference outdir [latency] [seed] [gap]");
 Verilated::commandArgs(argc,argv);la::Workload w(argv[1]);std::ifstream prep(argv[2],std::ios::binary);uint64_t header[6];prep.read((char*)header,sizeof(header));
 if(header[0]!=0x5350415253455632ull)throw std::runtime_error("prepared magic");std::vector<uint64_t> row(header[1]+1);std::vector<uint32_t> edge(header[2]);la::read(prep,row.data(),row.size());la::read(prep,edge.data(),edge.size());
 unsigned latency=argc>5?std::stoul(argv[5]):16,seed=argc>6?std::stoul(argv[6]):1729,gap=argc>7?std::stoul(argv[7]):2;
 if(w.h.jobs>64||w.h.nodes>4194304||w.h.cells>32768||!w.h.cells||!w.h.jobs||!w.h.costs||w.h.costs>16)throw std::runtime_error("M4 external tile capacity admission");
 std::filesystem::create_directories(argv[4]);std::string out=argv[4];std::ofstream cycles(out+"/cycles.csv"),commits(out+"/commits.csv"),events(out+"/phases.csv");
 cycles<<"cycle,sample,wave,phase,issued,accepted,committed,outstanding\n";commits<<"sample,wave,node\n";events<<"cycle,sample,wave,phase\n";
 auto align=[](unsigned v){return (v+255)&~255u;};const unsigned SB=align((w.h.nodes+4*L-1)/(4*L)*L),RB=align(SB+(w.h.nodes+4*L-1)/(4*L)*2*L),EB=align(RB+(row.size()*8+31)/32),CB=align(EB+(edge.size()*4+31)/32),MB=align(CB+(w.h.costs*8+31)/32),CS=align((w.h.nodes*8+31)/32),JB=MB+w.h.jobs*CS,OB=align(JB+w.h.jobs),OS=(w.h.cells+3)/4;
 std::vector<Line> memory(OB+w.h.jobs*OS);memcpy(memory.data()+RB,row.data(),row.size()*8);memcpy(memory.data()+EB,edge.data(),edge.size()*4);
 for(unsigned i=0;i<w.h.costs;++i){uint32_t a,b;memcpy(&a,&w.cost[i].delay,4);memcpy(&b,&w.cost[i].congestion,4);memory[CB+i/4][i%4]=uint64_t(a)<<32|b;}
 for(unsigned q=0;q<w.h.jobs;++q){std::set<int> seen;for(unsigned n=0;n<w.h.nodes;++n){int cell=w.cell[q*w.h.nodes+n];bool target=w.node[n].type==1;if(cell>=int(w.h.cells))throw std::runtime_error("cell admission");memory[MB+q*CS+n/4][n%4]=uint64_t(target)<<32|uint32_t(cell);if(target&&cell>=0)seen.insert(cell);}
  memory[JB+q]={uint64_t(seen.size())<<32|w.job[q].source,uint64_t(OB+q*OS)<<32|(MB+q*CS),0,0};
 }
 std::vector<uint64_t> reference(w.h.jobs*w.h.cells),actual;std::ifstream ref(argv[3],std::ios::binary);ref.read((char*)reference.data(),reference.size()*8);if(size_t(ref.gcount())!=reference.size()*8)throw std::runtime_error("reference size");for(auto &v:reference)v=(v<<32)|(v>>32);
 Vr2_many_tile d;std::mt19937 rng(seed);std::array<std::vector<Request>,P> pending;std::array<int,P> response;response.fill(-1);std::array<uint64_t,P> next{},reads{},writes{};std::array<unsigned,P> high{};std::array<uint64_t,L+1> ih{},ah{},ch{};std::array<uint64_t,10> arrays{};std::array<uint64_t,64> phases{};
 uint64_t tick=0,checks=0;unsigned last_phase=255,last_qid=255;std::vector<uint64_t> snapshot(w.h.nodes);bool snap=false;unsigned mshr_peak=0,dirty_peak=0;
 auto state_line=[&](unsigned n){return SB+(((n>>(B+2))*2+((n>>1)&1))*L)+((n>>2)&(L-1));};
 auto label=[&](unsigned n)->uint64_t{return memory[state_line(n)][(n&1)*2];};
 auto marked=[&](unsigned n){return bool(memory[state_line(n)][(n&1)*2+1]>>32&1);};
 auto clock=[&](){d.clk=0;d.eval();d.clk=1;d.eval();++tick;};
 d.rst=1;d.start=0;d.physical_rsp_valid=0;d.physical_ready=0;clock();clock();d.rst=0;
 d.node_count=w.h.nodes;d.state_base=SB;d.row_base=RB;d.edge_base=EB;d.cost_base=CB;d.job_base=JB;d.jobs=w.h.jobs;d.cost_count=w.h.costs;d.cell_count=w.h.cells;
 uint64_t max_cycles=std::getenv("R2_MAX_CYCLES")?std::stoull(std::getenv("R2_MAX_CYCLES")):20000000ull;
 bool full_trace=!std::getenv("R2_COMPACT_TRACE");uint64_t trace_hash=1469598103934665603ull;
 const auto wall_start=std::chrono::steady_clock::now();
 uint64_t start=tick;d.start=1;clock();d.start=0;bool success=false;
 for(uint64_t steps=0;steps<max_cycles;++steps){
  d.clk=0;d.physical_ready=d.physical_rsp_valid=0;
  for(unsigned c=0;c<P;++c){if(pending[c].size()<64&&tick>=next[c]&&rng()%7)d.physical_ready|=1u<<c;
   if(response[c]<0)for(int i=int(pending[c].size())-1;i>=0;--i)if(pending[c][i].due<=tick){response[c]=i;break;}
   if(response[c]>=0){auto &p=pending[c][response[c]];d.physical_rsp_valid|=1u<<c;setbits(d.physical_rsp_id,6*c,6,p.id);
    for(unsigned s=0;s<4;++s){d.physical_rsp_data[c*8+s*2]=p.data[s];d.physical_rsp_data[c*8+s*2+1]=p.data[s]>>32;}}
  }
  d.eval();
  if(d.phase!=last_phase||d.qid!=last_qid){
   events<<tick<<','<<unsigned(d.qid)<<','<<d.wave<<','<<unsigned(d.phase)<<'\n';
   if(d.phase==12){for(unsigned n=0;n<w.h.nodes;++n){if(memory[n/4][n%4]!=label(n))throw std::runtime_error("wave home/label invariant");snapshot[n]=label(n);}snap=true;++checks;}
   if(d.phase==18&&snap){std::set<unsigned> improved,queued;for(unsigned n=0;n<w.h.nodes;++n){if(snapshot[n]!=label(n))throw std::runtime_error("wave-start label changed");if(memory[n/4][n%4]<label(n))improved.insert(n);if(memory[n/4][n%4]>label(n))throw std::runtime_error("proposal increased");}
    for(unsigned n=0;n<w.h.nodes;++n)if(marked(n))queued.insert(n);
    if(improved!=queued)throw std::runtime_error("changed queue != final improvement set");++checks;
   }
   if(d.qid!=last_qid)snap=false;last_phase=d.phase;last_qid=d.qid;
  }
  unsigned outstanding=0;
  for(unsigned c=0;c<P;++c){bool pop=response[c]>=0&&(d.physical_rsp_ready>>c&1);
   if(pop){auto &p=pending[c][response[c]];if(p.write)memory[p.line]=p.data;}
   if((d.physical_valid&d.physical_ready)>>c&1){unsigned addr=d.physical_line[c],id=getbits(d.physical_id,6*c,6);
    if(addr>=memory.size()||addr%P!=c)throw std::runtime_error("physical address/striping");for(auto &p:pending[c])if(p.id==id)throw std::runtime_error("duplicate physical ID");
    bool wr=d.physical_write>>c&1;Line data=memory[addr];unsigned a=addr<SB?(wr?0:1):addr<RB?(wr?8:9):addr<EB?2:addr<CB?3:addr<MB?4:addr<JB?5:addr<OB?6:7;++arrays[a];
    if(wr){++writes[c];for(unsigned s=0;s<4;++s)data[s]=uint64_t(d.physical_data[c*8+s*2+1])<<32|d.physical_data[c*8+s*2];}else ++reads[c];
    pending[c].push_back({wr,addr,id,data,tick+latency+rng()%13});next[c]=tick+gap;
   }
   if(pop){pending[c].erase(pending[c].begin()+response[c]);response[c]=-1;}
   high[c]=std::max<unsigned>(high[c],pending[c].size());outstanding+=pending[c].size();
  }
  auto a=__builtin_popcount(d.issued),b=__builtin_popcount(d.accepted),c=__builtin_popcount(d.committed);++ih[a];++ah[b];++ch[c];++phases[d.phase];
  if(full_trace)cycles<<tick<<','<<unsigned(d.qid)<<','<<d.wave<<','<<unsigned(d.phase)<<','<<a<<','<<b<<','<<c<<','<<outstanding<<'\n';
  for(unsigned k=0;k<L;++k){if(d.committed>>k&1)commits<<unsigned(d.qid)<<','<<d.wave<<','<<d.commit_nodes[k]<<'\n';mshr_peak=std::max(mshr_peak,unsigned(getbits(d.mshr_peaks,k*6,6)));dirty_peak=std::max(dirty_peak,unsigned(getbits(d.dirty_peaks,k*5,5)));}
  for(uint64_t v:{tick,uint64_t(d.qid),uint64_t(d.wave),uint64_t(d.phase),uint64_t(a),uint64_t(b),uint64_t(c),uint64_t(outstanding)}){trace_hash^=v;trace_hash*=1099511628211ull;}
  if(steps%1000000==0){auto seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-wall_start).count();std::ofstream progress(out+"/progress.json");progress<<"{\"cycles\":"<<steps<<",\"sample\":"<<unsigned(d.qid)<<",\"wave\":"<<d.wave<<",\"phase\":"<<unsigned(d.phase)<<",\"host_elapsed_s\":"<<seconds<<"}\n";}
  d.clk=1;d.eval();++tick;
  if(d.error){std::cerr<<"bank="<<unsigned(d.r2_many_tile__DOT__bank_error)<<" meta="<<unsigned(d.r2_many_tile__DOT__meta_error)<<" reduce="<<unsigned(d.r2_many_tile__DOT__reduce_error)<<" front="<<unsigned(d.r2_many_tile__DOT__front_error)<<" queue="<<unsigned(d.r2_many_tile__DOT__queue_error)<<'\n';throw std::runtime_error("DUT error sample="+std::to_string(d.qid)+" wave="+std::to_string(d.wave)+" phase="+std::to_string(d.phase)+" owner="+std::to_string(d.owner_error));}
  if(d.done){if(outstanding)throw std::runtime_error("done before physical drain");success=true;break;}
 }
 if(!success)throw std::runtime_error("watchdog phase="+std::to_string(d.phase)+" qid="+std::to_string(d.qid)+" wave="+std::to_string(d.wave));
 for(unsigned q=0;q<w.h.jobs;++q)for(unsigned c=0;c<w.h.cells;++c){auto v=memory[OB+q*OS+c/4][c%4];actual.push_back(v);if(v!=reference[q*w.h.cells+c])throw std::runtime_error("output mismatch q="+std::to_string(q)+" cell="+std::to_string(c)+" got="+std::to_string(v)+" expected="+std::to_string(reference[q*w.h.cells+c]));}
 std::ofstream summary(out+"/summary.json");summary<<"{\"scope\":\"RTL functional cycles; hypothetical bounded physical memory; no qualified clock\",\"all_outputs_exact\":true,\"batch_starts\":1,\"jobs\":"<<w.h.jobs<<",\"resident_cycles\":"<<tick-start<<",\"wave_invariant_checks\":"<<checks<<",\"latency_cycles\":"<<latency<<",\"service_gap_cycles\":"<<gap<<",\"seed\":"<<seed<<",\"physical_channels\":"<<P<<",\"lanes\":"<<L<<",\"physical_outstanding_cap\":64,\"mshr_peak\":"<<mshr_peak<<",\"dirty_peak\":"<<dirty_peak<<",\"array_beats_prop_write_prop_read_row_edge_cost_cell_job_output_state_write_state_read\":[";
 for(unsigned i=0;i<10;++i)summary<<(i?",":"")<<arrays[i];summary<<"],\"issue_histogram\":[";for(unsigned i=0;i<L+1;++i)summary<<(i?",":"")<<ih[i];summary<<"],\"accept_histogram\":[";for(unsigned i=0;i<L+1;++i)summary<<(i?",":"")<<ah[i];summary<<"],\"commit_histogram\":[";for(unsigned i=0;i<L+1;++i)summary<<(i?",":"")<<ch[i];summary<<"],\"phase_cycles\":[";for(unsigned i=0;i<64;++i)summary<<(i?",":"")<<phases[i];summary<<"],\"channels\":[";for(unsigned i=0;i<P;++i)summary<<(i?",":"")<<"{\"reads\":"<<reads[i]<<",\"writes\":"<<writes[i]<<",\"peak\":"<<high[i]<<"}";summary<<"]}\n";
 std::ofstream trace(out+"/trace_mode.json");trace<<"{\"cycle_rows\":"<<tick-start-1<<",\"full_cycle_csv\":"<<(full_trace?"true":"false")<<",\"trace_fnv64_integer_stream\":"<<trace_hash<<",\"exact_clock_evaluation\":true,\"event_skipping\":false,\"max_cycles\":"<<max_cycles<<"}\n";
#ifdef R2_ARCH_MODEL
 d.write_metrics(out);
#endif
 std::ofstream binary(out+"/output.bin",std::ios::binary);for(auto v:actual){uint64_t native=(v<<32)|(v>>32);binary.write((char*)&native,8);}std::cout<<"BATCH_PASS cycles="<<tick-start<<" jobs="<<w.h.jobs<<" checks="<<checks<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
