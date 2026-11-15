#include "../../fpga_descriptor_front/descriptor/packed.hpp"
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
using Line=std::array<uint64_t,4>;
void need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
int main(int argc,char**argv){try{
 need(argc==4,"usage fixture_directory workload golden");std::filesystem::path d(argv[1]);Graph g(argv[2]);dfdesc::Admission a(g);need(a.formatbytes==8,"expected8B");
 std::array<uint32_t,22>cfg{};std::ifstream cf(d/"config.hex");for(auto&v:cfg)need(bool(cf>>std::hex>>v),"config read");need(cfg[0]==0x43504631&&cfg[1]==1,"config ABI");
 dfdesc::Image first(g,0,a);uint64_t label=Graph::align(first.layout.end_bytes/32),scratch=Graph::align(label+(g.w.h.nodes+3)/4),output=Graph::align(scratch+(g.w.h.nodes+3)/4),stride=Graph::align((g.w.h.cells+3)/4),cost=Graph::align(output+g.w.h.jobs*stride);
 std::array<uint64_t,22>want={0x43504631,1,g.w.h.nodes,g.edge.size(),g.w.h.costs,g.w.h.cells,g.w.h.jobs,g.w.h.groups,g.rowbase,g.edgebase,g.metabase,g.metastride,first.base_line,first.stride_lines,label,scratch,output,stride,cost,cost+(g.w.h.costs+3)/4-1,(cost+(g.w.h.costs+3)/4-1)/32+1,8};
 for(unsigned i=0;i<22;++i)need(cfg[i]==want[i],"config vs production layout");
 std::map<uint32_t,Line>mem,expected;std::ifstream in(d/"input/lines.txt");uint64_t address;std::string hex;
 while(in>>std::hex>>address>>hex){need(address<=UINT32_MAX&&hex.size()==64,"line parse");Line v;for(unsigned i=0;i<4;++i)v[i]=std::stoull(hex.substr((3-i)*16,16),nullptr,16);need(mem.emplace(address,v).second,"duplicate memory line");}
 auto put=[&](uint64_t base,const std::vector<uint64_t>&v){for(unsigned i=0;i<v.size();++i)expected[base+i/4][i%4]=v[i];};
 put(g.rowbase,g.row);std::vector<uint64_t>packededge((g.edge.size()+1)/2);for(unsigned i=0;i<g.edge.size();++i)packededge[i/2]|=uint64_t(g.edge[i])<<((i%2)*32);put(g.edgebase,packededge);
 std::vector<uint64_t>costs;for(auto v:g.w.cost)costs.push_back(Graph::packed(v));put(cost,costs);
 std::ifstream samples(d/"samples.hex");unsigned targets_total=0;
 for(unsigned q=0;q<g.w.h.jobs;++q){dfdesc::Image im(g,q,a);std::vector<uint64_t>desc(g.w.h.nodes);for(unsigned n=0;n<g.w.h.nodes;++n){uint64_t v=0;for(unsigned b=0;b<8;++b)v|=uint64_t(im.bytes[8*n+b])<<(8*b);desc[n]=v;auto dec=im.decode(n);need(dec.begin==g.row[n]&&dec.end==g.row[n+1],"descriptor decode");}put(im.base_line+q*im.stride_lines,desc);
  std::string s;need(bool(samples>>s)&&s.size()==32,"sample parse");need(std::stoul(s.substr(0,8),nullptr,16)==q&&std::stoul(s.substr(8,8),nullptr,16)==a.targets[q]&&std::stoul(s.substr(16,8),nullptr,16)==g.w.job[q].source&&std::stoul(s.substr(24,8),nullptr,16)==bool(a.targets[q]),"sample fields");targets_total+=a.targets[q];
 }
 need(mem==expected,"all external-memory bytes must match production graph/descriptor");
 // Verify the sparse readmemh form independently from the flat loader form.
 for(unsigned p=0;p<32;++p){std::ifstream f(d/("input/port_"+(p<10?std::string("0"):std::string())+std::to_string(p)+".hex"));std::string index,value;unsigned count=0;while(f>>index>>value){need(index[0]=='@'&&value.size()==64,"sparse syntax");uint64_t la=std::stoull(index.substr(1),nullptr,16);need(la<cfg[20],"port array bound");auto it=mem.find(la*32+p);need(it!=mem.end(),"sparse unknown line");for(unsigned lane=0;lane<4;++lane)need(std::stoull(value.substr((3-lane)*16,16),nullptr,16)==it->second[lane],"sparse value");++count;}unsigned actual=0;for(auto&kv:mem)actual+=(kv.first&31)==p;need(count==actual,"sparse coverage");}
 std::ifstream gold(argv[3],std::ios::binary),vh(d/"validation/all_pairs.hex");unsigned pairs=0;
 for(unsigned q=0;q<g.w.h.jobs;++q){std::ifstream beats(d/("validation/sample_"+std::to_string(q)+"_beats.hex"));for(unsigned line=0;line<(g.w.h.cells+3)/4;++line){std::string b;need(bool(beats>>b)&&b.size()==64,"output beat parse");for(unsigned k=0;k<4;++k){uint64_t wantpair=0x7fc000007fc00000ull;if(line*4+k<g.w.h.cells){la::Cost v;la::read(gold,&v,1);wantpair=Graph::packed(v);uint64_t h;need(bool(vh>>std::hex>>h)&&h==wantpair,"golden pair conversion");++pairs;}need(std::stoull(b.substr((3-k)*16,16),nullptr,16)==wantpair,"full output beat or padding");}}}
 std::cout<<"FIXTURE_VALIDATION_PASS jobs="<<g.w.h.jobs<<" input_lines="<<mem.size()<<" output_pairs="<<pairs<<" unique_targets_sum="<<targets_total<<" ports=32\n";
}catch(const std::exception&e){std::cerr<<"FIXTURE_VALIDATION_FAIL "<<e.what()<<'\n';return 1;}}
