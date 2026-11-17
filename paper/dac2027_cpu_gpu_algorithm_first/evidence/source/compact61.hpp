#pragma once
#include "io.hpp"
#include "backend.hpp"
#include <cstring>
#include <stdexcept>
namespace la61 {
template<class T>struct Span {const T* p;size_t n;const T* data()const{return p;}const T* begin()const{return p;}const T* end()const{return p+n;}const T& operator[](size_t i)const{return p[i];}};
struct View {la::Header h;Span<uint64_t> row;Span<la::Node> node;Span<la::Edge> edge;Span<la::Cost> cost;Span<la::Job> job;Span<int32_t> cell;};
inline View view(const la::BackendInput& a){return {{la::MAGIC,a.n,a.ne,a.nj,a.nk,a.nc,0},{a.row,a.n+1},{a.nodes,a.n},{a.edges,a.ne},{a.costs,a.nk},{a.jobs,a.nj},{a.cells,size_t(a.n)*a.nj}};}
// COMPACT_RRG_V1: type[1:0], inter[2], segment+1[4:3], cost[15:5].
LA_HD inline la::Node decode(uint16_t x){return {unsigned(x&3),unsigned(x>>5),unsigned((x>>2)&1),int((x>>3)&3)-1};}
LA_HD inline la::Node decode(la::Node x){return x;}
LA_HD inline unsigned destination(uint32_t x){return x;}
LA_HD inline unsigned destination(la::Edge x){return x.dst;}
struct Nodes {std::vector<uint16_t> data;la::Node operator[](size_t i)const{return decode(data[i]);}struct Iter {const uint16_t* p;la::Node operator*()const{return decode(*p);}Iter& operator++(){++p;return *this;}bool operator!=(Iter x)const{return p!=x.p;}};Iter begin()const{return {data.data()};}Iter end()const{return {data.data()+data.size()};}};
struct Edges {std::vector<uint32_t> data;la::Edge operator[](size_t i)const{return {data[i],0};}};
struct Compact {
 la::Header h;Span<uint64_t> row;Nodes node;Edges edge;Span<la::Cost> cost;Span<la::Job> job;Span<int32_t> cell;
 template<class W>explicit Compact(const W& w):h(w.h),row{w.row.data(),size_t(w.h.nodes+1)},cost{w.cost.data(),size_t(w.h.costs)},job{w.job.data(),size_t(w.h.jobs)},cell{w.cell.data(),size_t(w.h.nodes*w.h.jobs)}{
  node.data.reserve(h.nodes);edge.data.reserve(h.edges);
  for(auto n:w.node){if(n.type>2||n.inter>1||n.segment_kind< -1||n.segment_kind>1||n.cost>=2048||n.cost>=h.costs)throw std::runtime_error("COMPACT_RRG_V1 field admission");node.data.push_back(uint16_t(n.type|(n.inter<<2)|((n.segment_kind+1)<<3)|(n.cost<<5)));}
  if(w.row[0]||w.row[h.nodes]!=h.edges)throw std::runtime_error("bad CSR");
  for(size_t u=0;u<h.nodes;++u)if(w.row[u]>w.row[u+1])throw std::runtime_error("bad row");
  for(size_t e=0;e<h.edges;++e){auto v=w.edge[e].dst;if(v>=h.nodes)throw std::runtime_error("bad dst");edge.data.push_back(v);}
 }
 size_t graph_bytes()const{return 8*(h.nodes+1)+2*h.nodes+4*h.edges+8*h.costs;}
};
inline uint64_t hash_bytes(const void* p,size_t bytes){uint64_t h=14695981039346656037ULL;auto b=static_cast<const unsigned char*>(p);for(size_t i=0;i<bytes;++i){h^=b[i];h*=1099511628211ULL;}return h;}
}
