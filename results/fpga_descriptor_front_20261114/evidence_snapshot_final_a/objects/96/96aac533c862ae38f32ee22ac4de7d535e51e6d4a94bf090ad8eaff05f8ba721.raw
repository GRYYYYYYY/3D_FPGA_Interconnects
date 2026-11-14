#include "packed.hpp"
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <set>
template<class T>void read(std::ifstream&f,T&v){la::read(f,&v,1);}
struct Parent{uint32_t node;uint64_t pair;std::vector<std::pair<uint32_t,uint64_t>>expected;};
static std::string hex(const uint8_t*p,unsigned n){std::ostringstream s;for(unsigned k=n;k;--k)s<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(p[k-1]);return s.str();}
int main(int argc,char**argv){try{
 dfdesc::require(argc==5||argc==6,"usage project_native workload frozen_trace output_json count [first_parent_index]");Graph g(argv[1]);dfdesc::Admission a(g);dfdesc::require(a.formatbytes==8,"NATIVE_PROJECTION_EXPECTED8");std::ifstream f(argv[2],std::ios::binary);uint64_t h[8];la::read(f,h,8);dfdesc::require(h[0]==0x5053545241434531ull,"TRACE_MAGIC");f.seekg(h[4]*32,std::ios::cur);std::vector<Parent>parents;unsigned limit=std::stoul(argv[4]);uint64_t first=argc==6?std::stoull(argv[5]):0;dfdesc::require(first<h[5],"PROJECTION_WINDOW");
 // Keep the original contiguous prefix, including zero-degree and target entries.
 for(uint64_t i=0;i<h[5];++i){uint32_t node,count;uint64_t pair;read(f,node);read(f,count);read(f,pair);Parent p{node,pair,{}};bool keep=i>=first&&i-first<limit;for(unsigned j=0;j<count;++j){uint32_t n;uint64_t v;read(f,n);read(f,v);if(keep)p.expected.push_back({n,v});}if(keep)parents.push_back(p);}
 dfdesc::Image image(g,h[1],a),fallback(g,h[1],a,16);std::set<uint64_t>beats;
 std::ofstream o(argv[3]);o<<"{\"sample\":"<<h[1]<<",\"wave\":"<<h[2]<<",\"bucket\":"<<h[3]<<",\"source_parent_count\":"<<h[5]<<",\"first_parent_index\":"<<first<<",\"selection\":\"contiguous native window; frozen native workload, not full performance input\",\"format_bytes\":"<<a.formatbytes<<",\"descriptor_base_line\":"<<image.base_line<<",\"descriptor_stride_lines\":"<<image.stride_lines<<",\"edge_base_line\":"<<g.edgebase<<",\"cost_bits\":[";
 for(unsigned c=0;c<g.w.h.costs;++c){if(c)o<<',';o<<'"'<<std::hex<<std::setw(16)<<std::setfill('0')<<Graph::packed(g.w.cost[c])<<std::dec<<'"';}o<<"],\"parents\":[";
 for(unsigned i=0;i<parents.size();++i){const auto&p=parents[i];auto d=image.decode(p.node);dfdesc::require(d.end-d.begin==p.expected.size(),"NATIVE_DEGREE");if(i)o<<',';
  o<<"{\"node\":"<<p.node<<",\"parent_pair_bits\":\""<<std::hex<<std::setw(16)<<std::setfill('0')<<p.pair<<std::dec<<"\",\"begin\":"<<d.begin<<",\"end\":"<<d.end<<",\"target_valid\":"<<(d.valid?"true":"false")<<",\"target_cell\":"<<d.cell<<",\"desc8_hex\":\""<<hex(image.bytes.data()+uint64_t(p.node)*a.formatbytes,8)<<"\",\"desc16_hex\":\""<<hex(fallback.bytes.data()+uint64_t(p.node)*16,16)<<"\",\"descriptor_line\":"<<image.line(p.node)<<",\"descriptor_word_in_beat\":"<<p.node%4<<",\"candidates\":[";
  for(uint64_t e=d.begin;e<d.end;++e){auto desc=g.edge[e];uint64_t value=g.pair(p.pair,desc);const auto&expected=p.expected[e-d.begin];dfdesc::require(expected.first==(desc&0xfffffff)&&expected.second==value,"ACTUAL_FP32_VS_FROZEN_NATIVE");if(e!=d.begin)o<<',';o<<"{\"edge_offset\":"<<e<<",\"dst\":"<<(desc&0xfffffff)<<",\"cost_index\":"<<(desc>>28)<<",\"pair_bits\":\""<<std::hex<<std::setw(16)<<std::setfill('0')<<value<<std::dec<<"\"}";beats.insert(e/8);}
  o<<"]}";
 }o<<"],\"edge_beats\":[";bool comma=false;
 for(auto b:beats){if(comma)o<<',';comma=true;o<<"{\"physical_line\":"<<g.edgebase+b<<",\"relative_beat\":"<<b<<",\"words\":[";for(unsigned k=0;k<8;++k){if(k)o<<',';uint64_t e=b*8+k;o<<(e<g.edge.size()?g.edge[e]:0);}o<<"]}";}o<<"]}\n";
 std::cout<<"NATIVE_PROJECTION_PASS parents="<<parents.size()<<" edgebeats="<<beats.size()<<std::endl;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
