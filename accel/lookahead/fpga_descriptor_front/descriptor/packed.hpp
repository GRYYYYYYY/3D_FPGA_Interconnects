#pragma once
#include "../../fpga_decoupled_front/graph.hpp"
#include <algorithm>
#include <limits>

namespace dfdesc {
inline void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
inline uint64_t add64(uint64_t a,uint64_t b){require(b<=UINT64_MAX-a,"ADDRESS_ADD_OVERFLOW");return a+b;}
inline uint64_t mul64(uint64_t a,uint64_t b){require(!a||b<=UINT64_MAX/a,"ADDRESS_MULTIPLY_OVERFLOW");return a*b;}
inline uint64_t align(uint64_t a,uint64_t n=1024){require(n&&!(n&(n-1)),"ADDRESS_ALIGNMENT");return add64(a,n-1)&~(n-1);}
struct Decoded {uint32_t begin,end,cell;bool valid;};
inline void check_record(uint64_t begin,uint64_t end,int64_t cell,bool valid,uint64_t edges,uint64_t cells){
 require(begin<=end&&end<=edges&&end<=UINT32_MAX,"OFFSET32_DOMAIN");
 require(cells<=32768,"CELL_CAPACITY");
 require(!valid||(cell>=0&&uint64_t(cell)<cells&&cell<=32767),"TARGET_DOMAIN");
}
inline void put32(uint8_t* p,uint32_t x){for(unsigned b=0;b<4;++b)p[b]=uint8_t(x>>(8*b));}
inline uint32_t get32(const uint8_t* p){return uint32_t(p[0])|uint32_t(p[1])<<8|uint32_t(p[2])<<16|uint32_t(p[3])<<24;}
inline void encode_record(uint8_t* p,unsigned format,uint64_t begin,uint64_t end,int64_t cell,bool valid,uint64_t edges,uint64_t cells){
 check_record(begin,end,cell,valid,edges,cells);
 require(format==8||format==16,"DESCRIPTOR_FORMAT");
 if(format==8){require(end-begin<=65535,"DEGREE16_OVERFLOW");uint64_t bits=begin|((end-begin)<<32)|(uint64_t(valid?cell:0)<<48)|(uint64_t(valid)<<63);for(unsigned b=0;b<8;++b)p[b]=uint8_t(bits>>(8*b));}
 else {put32(p,uint32_t(begin));put32(p+4,uint32_t(end));put32(p+8,valid?uint32_t(cell):0);put32(p+12,valid?1:0);}
}
// Independent byte-wise decoder: no encoder helper or graph metadata access.
inline Decoded decode_record(const uint8_t* p,unsigned format,uint64_t edges,uint64_t cells){
 uint64_t begin=get32(p),end,cell;bool valid;
 if(format==8){uint64_t degree=uint32_t(p[4])|uint32_t(p[5])<<8;end=begin+degree;cell=uint32_t(p[6])|(uint32_t(p[7]&127)<<8);valid=(p[7]&128)!=0;}
 else {require(format==16,"DESCRIPTOR_FORMAT");end=get32(p+4);cell=get32(p+8);uint32_t flags=get32(p+12);require((flags&~1u)==0,"DESCRIPTOR_FLAGS");valid=flags&1;}
 check_record(begin,end,cell,valid,edges,cells);require(valid||cell==0,"INVALID_CELL_NOT_NORMALIZED");
 return {uint32_t(begin),uint32_t(end),uint32_t(cell),valid};
}
struct Layout {
 uint64_t base_bytes,nodes,jobs,stride_bytes,total_bytes,end_bytes;unsigned formatbytes;
 Layout(uint64_t base,uint64_t n,uint64_t j,unsigned format):base_bytes(base),nodes(n),jobs(j),formatbytes(format){
  require(format==8||format==16,"DESCRIPTOR_FORMAT");require(base%1024==0,"DESCRIPTOR_BASE_ALIGNMENT");
  stride_bytes=align(mul64(n,format));total_bytes=mul64(stride_bytes,j);end_bytes=add64(base,total_bytes);
 }
 uint64_t address(uint64_t sample,uint64_t node)const{require(sample<jobs&&node<nodes,"DESCRIPTOR_INDEX");return add64(base_bytes,add64(mul64(sample,stride_bytes),mul64(node,formatbytes)));}
 uint64_t line(uint64_t sample,uint64_t node)const{return address(sample,node)/32;}
};
struct Admission {
 uint64_t nodes=0,edges=0,jobs=0,cells=0,max_degree=0,zero_degree_nodes=0,prepared_cost_mask=0;
 unsigned formatbytes=8;std::vector<uint32_t>targets;std::vector<uint64_t>valid_nodes,zero_degree_targets;std::vector<int32_t>max_cell;
 explicit Admission(const Graph& g){const auto&w=g.w;nodes=w.h.nodes;edges=g.edge.size();jobs=w.h.jobs;cells=w.h.cells;
  require(nodes&&nodes<=4194304&&nodes<(1u<<28),"NODE_CAPACITY");require(cells<=32768,"CELL_CAPACITY");require(w.h.costs<=16,"EDGE_COST_INDEX_DOMAIN");
  require(g.row.size()==nodes+1&&g.row.front()==0&&g.row.back()==edges&&edges<=UINT32_MAX,"PREPARED_CSR");
  for(uint64_t n=0;n<nodes;++n){require(g.row[n]<=g.row[n+1]&&g.row[n+1]<=edges,"PREPARED_ROW");max_degree=std::max(max_degree,g.row[n+1]-g.row[n]);zero_degree_nodes+=g.row[n]==g.row[n+1];}
  formatbytes=max_degree<=65535?8:16;
  for(auto e:g.edge){unsigned dst=e&0xfffffff,c=e>>28;require(dst<nodes&&c<w.h.costs&&c==w.node[dst].cost,"PREPARED_EDGE_DOMAIN");require(la::numeric(w.cost[c].delay)&&la::numeric(w.cost[c].congestion),"UNSUPPORTED_NUMERIC");prepared_cost_mask|=1ull<<c;}
  targets.resize(jobs);valid_nodes.resize(jobs);zero_degree_targets.resize(jobs);max_cell.assign(jobs,-1);std::vector<bool>seen(cells);
  for(uint64_t q=0;q<jobs;++q){std::fill(seen.begin(),seen.end(),false);for(uint64_t n=0;n<nodes;++n){int c=w.cell[q*nodes+n];require(c>=-1&&c<int64_t(cells),"NATIVE_CELL_DOMAIN");bool valid=w.node[n].type==1&&c>=0;
    if(valid){require(c<=32767,"TARGET_DOMAIN");++valid_nodes[q];zero_degree_targets[q]+=g.row[n]==g.row[n+1];max_cell[q]=std::max(max_cell[q],c);if(!seen[c]){seen[c]=true;++targets[q];}}
  }}
 }
};
// Actual per-sample backing. All samples occupy disjoint reserved device ranges;
// independent simulator processes materialize only the sample they execute.
struct PackedDescriptors {
 unsigned formatbytes;uint64_t stride_lines,base_line,sample,nodes,edges,cells;Layout layout;std::vector<uint8_t>bytes;
 PackedDescriptors(const Graph&g,unsigned q):PackedDescriptors(g,q,Admission(g)){}
 PackedDescriptors(const Graph&g,unsigned q,const Admission&a,unsigned forced_format=0):
  formatbytes(forced_format?forced_format:a.formatbytes),sample(q),nodes(a.nodes),edges(a.edges),cells(a.cells),
  layout(mul64(Graph::align(add64(g.metabase,mul64(g.w.h.jobs,g.metastride))),32),a.nodes,a.jobs,formatbytes){
  require(q<a.jobs,"SAMPLE_RANGE");require(formatbytes>=a.formatbytes,"DEGREE_REQUIRES_FALLBACK");
  stride_lines=layout.stride_bytes/32;base_line=layout.base_bytes/32;bytes.resize(layout.stride_bytes,0);
  for(uint64_t n=0;n<nodes;++n){int c=g.w.cell[uint64_t(q)*nodes+n];encode_record(bytes.data()+n*formatbytes,formatbytes,g.row[n],g.row[n+1],c,g.w.node[n].type==1&&c>=0,edges,cells);}
 }
 Decoded decode(uint64_t node)const{require(node<nodes,"DESCRIPTOR_INDEX");return decode_record(bytes.data()+node*formatbytes,formatbytes,edges,cells);}
 Decoded get(uint64_t node)const{return decode(node);}
 uint64_t line(uint64_t node)const{return layout.line(sample,node);}
};
using Image=PackedDescriptors;
}
