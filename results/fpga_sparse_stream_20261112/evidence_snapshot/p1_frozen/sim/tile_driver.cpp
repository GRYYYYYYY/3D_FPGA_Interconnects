#ifdef SPARSE_TILE_MODEL
#include "tile_model.hpp"
using Vsparse_tile=sparse_model::TileModel;
struct Verilated{static void commandArgs(int,char**) {}};
#else
#include "Vsparse_tile.h"
#include "verilated.h"
#endif
#include "io.hpp"
#include <array>
#include <vector>
#include <fstream>
#include <iostream>
#include <random>
#include <filesystem>
#include <iomanip>
#include <set>
#include <map>
using Line=std::array<uint64_t,4>;
struct Request{bool write;unsigned line,id;Line data;uint64_t due;};
int main(int argc,char**argv){try{
 if(argc<5)throw std::runtime_error("workload prepared.bin reference.bin outdir [latency]");Verilated::commandArgs(argc,argv);la::Workload w(argv[1]);std::ifstream prep(argv[2],std::ios::binary);uint64_t header[6];prep.read((char*)header,sizeof(header));if(header[0]!=0x5350415253455632ull)throw std::runtime_error("prepared magic");std::vector<uint64_t> row(header[1]+1);std::vector<uint32_t> edge(header[2]);la::read(prep,row.data(),row.size());la::read(prep,edge.data(),edge.size());unsigned latency=argc>5?std::stoul(argv[5]):16;
 if(w.h.nodes>4096||w.h.cells>64)throw std::runtime_error("tile capacity admission");
 std::filesystem::create_directories(argv[4]);std::string output=argv[4];std::ofstream cycles(output+"/cycles.csv"),commits(output+"/commits.csv");cycles<<"cycle,sample,wave,phase,issued,accepted,committed,outstanding\n";commits<<"sample,wave,node\n";
 auto align=[](unsigned v){return (v+255)&~255u;};const unsigned RB=1024,EB=align(RB+(row.size()*8+31)/32),CB=align(EB+(edge.size()*4+31)/32),MB=align(CB+(w.h.costs*8+31)/32);std::vector<Line> memory(MB+(w.h.nodes*8+31)/32+64);memcpy(memory.data()+RB,row.data(),row.size()*8);memcpy(memory.data()+EB,edge.data(),edge.size()*4);
 for(unsigned i=0;i<w.h.costs;++i){uint32_t a,b;memcpy(&a,&w.cost[i].delay,4);memcpy(&b,&w.cost[i].congestion,4);memory[CB+i/4][i%4]=uint64_t(a)<<32|b;}
 std::vector<uint64_t> reference(w.h.jobs*w.h.cells),actual;std::ifstream ref(argv[3],std::ios::binary);ref.read((char*)reference.data(),reference.size()*8);
 // Reference binaries use native Cost {delay,congestion}, not packed lexical order.
 for(auto &v:reference)v=(v<<32)|(v>>32);
 Vsparse_tile d;std::mt19937 rng(1729);std::array<std::vector<Request>,25> pending;std::array<int,25> response;response.fill(-1);std::array<uint64_t,25> next{};std::array<unsigned,25> high{};std::array<uint64_t,25> reads{},writes{};std::array<uint64_t,9> ih{},ah{},ch{};std::array<uint64_t,32> phases{};std::map<unsigned,uint64_t> rh;unsigned last_retired=0,request_peak=0,response_peak=0,contexts_peak=0,changed_peak=0,member_peak=0;uint64_t starved=0,downstream=0;std::array<uint64_t,6> arrays{};uint64_t tick=0,resident=2,invariant_checks=0;
 std::vector<uint64_t> snapshot(w.h.nodes);unsigned last_phase=0;
 auto label=[&](unsigned n)->uint64_t{unsigned idx=((n>>5)<<2)|(n&3);switch((n>>2)&7){case 0:return d.sparse_tile__DOT__banks__BRA__0__KET____DOT__bank__DOT__labels[idx];case 1:return d.sparse_tile__DOT__banks__BRA__1__KET____DOT__bank__DOT__labels[idx];case 2:return d.sparse_tile__DOT__banks__BRA__2__KET____DOT__bank__DOT__labels[idx];case 3:return d.sparse_tile__DOT__banks__BRA__3__KET____DOT__bank__DOT__labels[idx];case 4:return d.sparse_tile__DOT__banks__BRA__4__KET____DOT__bank__DOT__labels[idx];case 5:return d.sparse_tile__DOT__banks__BRA__5__KET____DOT__bank__DOT__labels[idx];case 6:return d.sparse_tile__DOT__banks__BRA__6__KET____DOT__bank__DOT__labels[idx];case 7:return d.sparse_tile__DOT__banks__BRA__7__KET____DOT__bank__DOT__labels[idx];}return 0;};
 auto clock=[&](){d.clk=0;d.eval();d.clk=1;d.eval();++tick;};d.rst=1;d.start=0;d.rsp_valid=0;d.mem_ready=0;clock();clock();d.rst=0;d.row_base=RB;d.edge_base=EB;d.cost_base=CB;d.cell_base=MB;d.cost_count=w.h.costs;d.cell_count=w.h.cells;
 for(unsigned q=0;q<w.h.jobs;++q){
  unsigned targets=0;std::vector<bool> seen(w.h.cells);for(unsigned n=0;n<w.h.nodes;++n){int cell=w.cell[q*w.h.nodes+n];bool is_target=w.node[n].type==1;memory[MB+n/4][n%4]=uint64_t(is_target)<<32|uint32_t(cell);if(is_target&&cell>=0&&!seen[cell]){seen[cell]=true;++targets;}}
  uint64_t sample_start=tick;last_retired=0;d.source=w.job[q].source;d.targets=targets;d.start=1;clock();d.start=0;bool success=false;
  for(unsigned steps=0;steps<2000000;++steps){
   d.clk=0;d.mem_ready=d.rsp_valid=0;
   for(unsigned c=0;c<25;++c){if(pending[c].size()<64&&tick>=next[c]&&rng()%7)d.mem_ready|=1u<<c;
    if(response[c]<0)for(int i=int(pending[c].size())-1;i>=0;--i)if(pending[c][i].due<=tick){response[c]=i;break;}
    if(response[c]>=0){auto &p=pending[c][response[c]];d.rsp_valid|=1u<<c;unsigned bit=c*6,word=bit/32,shift=bit%32;d.rsp_id[word]=(d.rsp_id[word]&~(uint32_t(63)<<shift))|(uint32_t(p.id)<<shift);if(shift>26)d.rsp_id[word+1]=(d.rsp_id[word+1]&~((1u<<(shift-26))-1))|(p.id>>(32-shift));for(unsigned s=0;s<4;++s){d.rsp_data[c*8+s*2]=p.data[s];d.rsp_data[c*8+s*2+1]=p.data[s]>>32;}}
   }
   d.eval();
   if(d.phase!=last_phase){
    if(d.phase==7||d.phase==12){for(unsigned n=0;n<w.h.nodes;++n)if(memory[n/4][n%4]!=label(n))throw std::runtime_error("wave home/label invariant");++invariant_checks;}
    if(d.phase==8)for(unsigned n=0;n<w.h.nodes;++n)snapshot[n]=label(n);
    if(d.phase==11){
     std::set<unsigned> improved,queued;
     for(unsigned n=0;n<w.h.nodes;++n){if(snapshot[n]!=label(n))throw std::runtime_error("wave snapshot changed during expansion");if(memory[n/4][n%4]<label(n))improved.insert(n);if(memory[n/4][n%4]>label(n))throw std::runtime_error("proposal increased");}
     for(unsigned k=0;k<d.sparse_tile__DOT__banks__BRA__0__KET____DOT__changes__DOT__wr;++k){unsigned idx=d.sparse_tile__DOT__banks__BRA__0__KET____DOT__changes__DOT__ids[k];unsigned n=((idx>>2)<<5)|(0<<2)|(idx&3);if(!queued.insert(n).second)throw std::runtime_error("duplicate changed ID");}
     for(unsigned k=0;k<d.sparse_tile__DOT__banks__BRA__1__KET____DOT__changes__DOT__wr;++k){unsigned idx=d.sparse_tile__DOT__banks__BRA__1__KET____DOT__changes__DOT__ids[k];unsigned n=((idx>>2)<<5)|(1<<2)|(idx&3);if(!queued.insert(n).second)throw std::runtime_error("duplicate changed ID");}
     for(unsigned k=0;k<d.sparse_tile__DOT__banks__BRA__2__KET____DOT__changes__DOT__wr;++k){unsigned idx=d.sparse_tile__DOT__banks__BRA__2__KET____DOT__changes__DOT__ids[k];unsigned n=((idx>>2)<<5)|(2<<2)|(idx&3);if(!queued.insert(n).second)throw std::runtime_error("duplicate changed ID");}
     for(unsigned k=0;k<d.sparse_tile__DOT__banks__BRA__3__KET____DOT__changes__DOT__wr;++k){unsigned idx=d.sparse_tile__DOT__banks__BRA__3__KET____DOT__changes__DOT__ids[k];unsigned n=((idx>>2)<<5)|(3<<2)|(idx&3);if(!queued.insert(n).second)throw std::runtime_error("duplicate changed ID");}
     for(unsigned k=0;k<d.sparse_tile__DOT__banks__BRA__4__KET____DOT__changes__DOT__wr;++k){unsigned idx=d.sparse_tile__DOT__banks__BRA__4__KET____DOT__changes__DOT__ids[k];unsigned n=((idx>>2)<<5)|(4<<2)|(idx&3);if(!queued.insert(n).second)throw std::runtime_error("duplicate changed ID");}
     for(unsigned k=0;k<d.sparse_tile__DOT__banks__BRA__5__KET____DOT__changes__DOT__wr;++k){unsigned idx=d.sparse_tile__DOT__banks__BRA__5__KET____DOT__changes__DOT__ids[k];unsigned n=((idx>>2)<<5)|(5<<2)|(idx&3);if(!queued.insert(n).second)throw std::runtime_error("duplicate changed ID");}
     for(unsigned k=0;k<d.sparse_tile__DOT__banks__BRA__6__KET____DOT__changes__DOT__wr;++k){unsigned idx=d.sparse_tile__DOT__banks__BRA__6__KET____DOT__changes__DOT__ids[k];unsigned n=((idx>>2)<<5)|(6<<2)|(idx&3);if(!queued.insert(n).second)throw std::runtime_error("duplicate changed ID");}
     for(unsigned k=0;k<d.sparse_tile__DOT__banks__BRA__7__KET____DOT__changes__DOT__wr;++k){unsigned idx=d.sparse_tile__DOT__banks__BRA__7__KET____DOT__changes__DOT__ids[k];unsigned n=((idx>>2)<<5)|(7<<2)|(idx&3);if(!queued.insert(n).second)throw std::runtime_error("duplicate changed ID");}
     if(improved!=queued)throw std::runtime_error("changed queue vs final improvement set");++invariant_checks;
    }
    last_phase=d.phase;
   }
   unsigned outstanding=0;
   for(unsigned c=0;c<25;++c){bool pop=response[c]>=0&&(d.rsp_ready>>c&1);if(pop){auto p=pending[c][response[c]];if(p.write)memory[p.line]=p.data;}
    if((d.mem_valid&d.mem_ready)>>c&1){unsigned addr=d.mem_line[c];if(addr>=memory.size())throw std::runtime_error("memory address");bool wr=d.mem_write>>c&1;Line data=memory[addr];unsigned bit=c*6,word=bit/32,shift=bit%32,id=(d.mem_id[word]>>shift);if(shift>26)id|=d.mem_id[word+1]<<(32-shift);id&=63;++arrays[addr<RB?(wr?0:1):addr<EB?2:addr<CB?3:addr<MB?4:5];if(wr){++writes[c];for(unsigned s=0;s<4;++s)data[s]=uint64_t(d.mem_data[c*8+s*2+1])<<32|d.mem_data[c*8+s*2];}else ++reads[c];pending[c].push_back({wr,addr,id,data,tick+latency+rng()%7});next[c]=tick+2;}
    if(pop){pending[c].erase(pending[c].begin()+response[c]);response[c]=-1;}high[c]=std::max<unsigned>(high[c],pending[c].size());outstanding+=pending[c].size();
   }
   unsigned total_retired=0;
   total_retired+=d.sparse_tile__DOT__banks__BRA__0__KET____DOT__dummy1;
   request_peak=std::max<unsigned>(request_peak,d.sparse_tile__DOT__banks__BRA__0__KET____DOT__owner__DOT__qc);response_peak=std::max<unsigned>(response_peak,d.sparse_tile__DOT__banks__BRA__0__KET____DOT__owner__DOT__rc);changed_peak=std::max<unsigned>(changed_peak,d.sparse_tile__DOT__banks__BRA__0__KET____DOT__changed_peak);
#ifndef SPARSE_SMALL_MEMBER
member_peak=std::max<unsigned>(member_peak,d.sparse_tile__DOT__banks__BRA__0__KET____DOT__member_peak);
#endif

   {unsigned count=0;for(unsigned k=0;k<4;++k)count+=d.sparse_tile__DOT__banks__BRA__0__KET____DOT__front__DOT__state[k]!=0;contexts_peak=std::max(contexts_peak,count);if((d.phase==8||d.phase==9)&&!count)++starved;}
   if(d.sparse_tile__DOT__banks__BRA__0__KET____DOT__owner__DOT__qc==64)++downstream;
   total_retired+=d.sparse_tile__DOT__banks__BRA__1__KET____DOT__dummy1;
   request_peak=std::max<unsigned>(request_peak,d.sparse_tile__DOT__banks__BRA__1__KET____DOT__owner__DOT__qc);response_peak=std::max<unsigned>(response_peak,d.sparse_tile__DOT__banks__BRA__1__KET____DOT__owner__DOT__rc);changed_peak=std::max<unsigned>(changed_peak,d.sparse_tile__DOT__banks__BRA__1__KET____DOT__changed_peak);
#ifndef SPARSE_SMALL_MEMBER
member_peak=std::max<unsigned>(member_peak,d.sparse_tile__DOT__banks__BRA__1__KET____DOT__member_peak);
#endif

   {unsigned count=0;for(unsigned k=0;k<4;++k)count+=d.sparse_tile__DOT__banks__BRA__1__KET____DOT__front__DOT__state[k]!=0;contexts_peak=std::max(contexts_peak,count);if((d.phase==8||d.phase==9)&&!count)++starved;}
   if(d.sparse_tile__DOT__banks__BRA__1__KET____DOT__owner__DOT__qc==64)++downstream;
   total_retired+=d.sparse_tile__DOT__banks__BRA__2__KET____DOT__dummy1;
   request_peak=std::max<unsigned>(request_peak,d.sparse_tile__DOT__banks__BRA__2__KET____DOT__owner__DOT__qc);response_peak=std::max<unsigned>(response_peak,d.sparse_tile__DOT__banks__BRA__2__KET____DOT__owner__DOT__rc);changed_peak=std::max<unsigned>(changed_peak,d.sparse_tile__DOT__banks__BRA__2__KET____DOT__changed_peak);
#ifndef SPARSE_SMALL_MEMBER
member_peak=std::max<unsigned>(member_peak,d.sparse_tile__DOT__banks__BRA__2__KET____DOT__member_peak);
#endif

   {unsigned count=0;for(unsigned k=0;k<4;++k)count+=d.sparse_tile__DOT__banks__BRA__2__KET____DOT__front__DOT__state[k]!=0;contexts_peak=std::max(contexts_peak,count);if((d.phase==8||d.phase==9)&&!count)++starved;}
   if(d.sparse_tile__DOT__banks__BRA__2__KET____DOT__owner__DOT__qc==64)++downstream;
   total_retired+=d.sparse_tile__DOT__banks__BRA__3__KET____DOT__dummy1;
   request_peak=std::max<unsigned>(request_peak,d.sparse_tile__DOT__banks__BRA__3__KET____DOT__owner__DOT__qc);response_peak=std::max<unsigned>(response_peak,d.sparse_tile__DOT__banks__BRA__3__KET____DOT__owner__DOT__rc);changed_peak=std::max<unsigned>(changed_peak,d.sparse_tile__DOT__banks__BRA__3__KET____DOT__changed_peak);
#ifndef SPARSE_SMALL_MEMBER
member_peak=std::max<unsigned>(member_peak,d.sparse_tile__DOT__banks__BRA__3__KET____DOT__member_peak);
#endif

   {unsigned count=0;for(unsigned k=0;k<4;++k)count+=d.sparse_tile__DOT__banks__BRA__3__KET____DOT__front__DOT__state[k]!=0;contexts_peak=std::max(contexts_peak,count);if((d.phase==8||d.phase==9)&&!count)++starved;}
   if(d.sparse_tile__DOT__banks__BRA__3__KET____DOT__owner__DOT__qc==64)++downstream;
   total_retired+=d.sparse_tile__DOT__banks__BRA__4__KET____DOT__dummy1;
   request_peak=std::max<unsigned>(request_peak,d.sparse_tile__DOT__banks__BRA__4__KET____DOT__owner__DOT__qc);response_peak=std::max<unsigned>(response_peak,d.sparse_tile__DOT__banks__BRA__4__KET____DOT__owner__DOT__rc);changed_peak=std::max<unsigned>(changed_peak,d.sparse_tile__DOT__banks__BRA__4__KET____DOT__changed_peak);
#ifndef SPARSE_SMALL_MEMBER
member_peak=std::max<unsigned>(member_peak,d.sparse_tile__DOT__banks__BRA__4__KET____DOT__member_peak);
#endif

   {unsigned count=0;for(unsigned k=0;k<4;++k)count+=d.sparse_tile__DOT__banks__BRA__4__KET____DOT__front__DOT__state[k]!=0;contexts_peak=std::max(contexts_peak,count);if((d.phase==8||d.phase==9)&&!count)++starved;}
   if(d.sparse_tile__DOT__banks__BRA__4__KET____DOT__owner__DOT__qc==64)++downstream;
   total_retired+=d.sparse_tile__DOT__banks__BRA__5__KET____DOT__dummy1;
   request_peak=std::max<unsigned>(request_peak,d.sparse_tile__DOT__banks__BRA__5__KET____DOT__owner__DOT__qc);response_peak=std::max<unsigned>(response_peak,d.sparse_tile__DOT__banks__BRA__5__KET____DOT__owner__DOT__rc);changed_peak=std::max<unsigned>(changed_peak,d.sparse_tile__DOT__banks__BRA__5__KET____DOT__changed_peak);
#ifndef SPARSE_SMALL_MEMBER
member_peak=std::max<unsigned>(member_peak,d.sparse_tile__DOT__banks__BRA__5__KET____DOT__member_peak);
#endif

   {unsigned count=0;for(unsigned k=0;k<4;++k)count+=d.sparse_tile__DOT__banks__BRA__5__KET____DOT__front__DOT__state[k]!=0;contexts_peak=std::max(contexts_peak,count);if((d.phase==8||d.phase==9)&&!count)++starved;}
   if(d.sparse_tile__DOT__banks__BRA__5__KET____DOT__owner__DOT__qc==64)++downstream;
   total_retired+=d.sparse_tile__DOT__banks__BRA__6__KET____DOT__dummy1;
   request_peak=std::max<unsigned>(request_peak,d.sparse_tile__DOT__banks__BRA__6__KET____DOT__owner__DOT__qc);response_peak=std::max<unsigned>(response_peak,d.sparse_tile__DOT__banks__BRA__6__KET____DOT__owner__DOT__rc);changed_peak=std::max<unsigned>(changed_peak,d.sparse_tile__DOT__banks__BRA__6__KET____DOT__changed_peak);
#ifndef SPARSE_SMALL_MEMBER
member_peak=std::max<unsigned>(member_peak,d.sparse_tile__DOT__banks__BRA__6__KET____DOT__member_peak);
#endif

   {unsigned count=0;for(unsigned k=0;k<4;++k)count+=d.sparse_tile__DOT__banks__BRA__6__KET____DOT__front__DOT__state[k]!=0;contexts_peak=std::max(contexts_peak,count);if((d.phase==8||d.phase==9)&&!count)++starved;}
   if(d.sparse_tile__DOT__banks__BRA__6__KET____DOT__owner__DOT__qc==64)++downstream;
   total_retired+=d.sparse_tile__DOT__banks__BRA__7__KET____DOT__dummy1;
   request_peak=std::max<unsigned>(request_peak,d.sparse_tile__DOT__banks__BRA__7__KET____DOT__owner__DOT__qc);response_peak=std::max<unsigned>(response_peak,d.sparse_tile__DOT__banks__BRA__7__KET____DOT__owner__DOT__rc);changed_peak=std::max<unsigned>(changed_peak,d.sparse_tile__DOT__banks__BRA__7__KET____DOT__changed_peak);
#ifndef SPARSE_SMALL_MEMBER
member_peak=std::max<unsigned>(member_peak,d.sparse_tile__DOT__banks__BRA__7__KET____DOT__member_peak);
#endif

   {unsigned count=0;for(unsigned k=0;k<4;++k)count+=d.sparse_tile__DOT__banks__BRA__7__KET____DOT__front__DOT__state[k]!=0;contexts_peak=std::max(contexts_peak,count);if((d.phase==8||d.phase==9)&&!count)++starved;}
   if(d.sparse_tile__DOT__banks__BRA__7__KET____DOT__owner__DOT__qc==64)++downstream;
if(d.phase!=1){if(total_retired>=last_retired)++rh[total_retired-last_retired];last_retired=total_retired;}else last_retired=0;
   auto a=__builtin_popcount(d.issued),b=__builtin_popcount(d.accepted),c=__builtin_popcount(d.committed);++ih[a];++ah[b];++ch[c];++phases[d.phase];
   cycles<<tick<<','<<q<<','<<d.wave<<','<<unsigned(d.phase)<<','<<a<<','<<b<<','<<c<<','<<outstanding<<'\n';
   for(unsigned k=0;k<8;++k)if(d.committed>>k&1)commits<<q<<','<<d.wave<<','<<d.commit_nodes[k]<<'\n';
   d.clk=1;d.eval();++tick;
   if(d.error)throw std::runtime_error("DUT error sample="+std::to_string(q)+" wave="+std::to_string(d.wave)+" phase="+std::to_string(d.phase)+" owner="+std::to_string(d.owner_error));
   if(d.done){if(outstanding)throw std::runtime_error("done before drain");success=true;break;}
  }
  resident+=tick-sample_start;
  if(!success)throw std::runtime_error("watchdog phase="+std::to_string(d.phase)+" wave="+std::to_string(d.wave));
  for(unsigned c=0;c<w.h.cells;++c){d.output_index=c;clock();clock();auto v=d.output_pair;actual.push_back(v);if(v!=reference[q*w.h.cells+c])throw std::runtime_error("output mismatch sample="+std::to_string(q)+" cell="+std::to_string(c)+" got="+std::to_string(v)+" expected="+std::to_string(reference[q*w.h.cells+c]));}
  std::cout<<"SAMPLE_PASS "<<q<<" cycles="<<tick<<" waves="<<d.wave<<std::endl;
 }
 std::ofstream summary(output+"/summary.json");summary<<"{\"all_outputs_exact\":true,\"cycles_with_output_readback\":"<<tick<<",\"resident_cycles\":"<<resident<<",\"invariant_checks\":"<<invariant_checks<<",\"latency_cycles\":"<<latency<<",\"jobs\":"<<w.h.jobs<<",\"issue_histogram\":[";for(unsigned i=0;i<9;++i)summary<<(i?",":"")<<ih[i];summary<<"],\"accept_histogram\":[";for(unsigned i=0;i<9;++i)summary<<(i?",":"")<<ah[i];summary<<"],\"commit_histogram\":[";for(unsigned i=0;i<9;++i)summary<<(i?",":"")<<ch[i];summary<<"],\"channels\":[";for(unsigned i=0;i<25;++i)summary<<(i?",":"")<<"{\"reads\":"<<reads[i]<<",\"writes\":"<<writes[i]<<",\"outstanding_peak\":"<<high[i]<<"}";summary<<"],\"phase_cycles\":[";for(unsigned i=0;i<32;++i)summary<<(i?",":"")<<phases[i];summary<<"],\"request_FIFO_peak\":"<<request_peak<<",\"response_FIFO_peak\":"<<response_peak<<",\"parent_contexts_per_lane_peak\":"<<contexts_peak<<",\"changed_per_bank_peak\":"<<changed_peak<<",\"member_per_bank_peak\":"<<member_peak<<",\"front_empty_lane_cycles\":"<<starved<<",\"request_full_lane_cycles\":"<<downstream<<",\"array_beats_prop_write_prop_read_row_edge_cost_cell\":[";for(unsigned i=0;i<6;++i)summary<<(i?",":"")<<arrays[i];summary<<"],\"retire_histogram\":{";bool first=true;for(auto x:rh){summary<<(first?"":",")<<'"'<<x.first<<"\":"<<x.second;first=false;}summary<<"}}\n";
 std::ofstream binary(output+"/output.bin",std::ios::binary);for(auto v:actual){uint64_t native=(v<<32)|(v>>32);binary.write((char*)&native,8);}std::cout<<"TILE_PASS cycles="<<tick<<'\n';
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
