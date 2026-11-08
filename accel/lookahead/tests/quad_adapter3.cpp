#include "kernel.hpp"
#include "quad_kernel3.hpp"
#include <vector>
#include <algorithm>
extern "C" void lookahead_top(const uint64_t* row,const la::Node* nodes,const la::Edge* edges,const la::Cost* costs,const la::Job* jobs,const int32_t* cells,float* visited,uint32_t* expanded,la::Entry* heap,la::Cost* output,la::Stats* stats,uint32_t n,uint32_t nj,uint32_t nc,uint32_t capacity,uint64_t budget) {
 unsigned chunk=(nj+3)/4,begin[4],count[4];
 std::vector<float> v[4];std::vector<uint32_t> e[4];std::vector<la::Entry> h[4];
 const la::Job* j[4];const int32_t* c[4];la::Cost* o[4];la::Stats* st[4];
 for(unsigned i=0;i<4;++i){begin[i]=std::min(i*chunk,nj);count[i]=std::min(chunk,nj-begin[i]);v[i].resize(n);e[i].resize(n);h[i].resize(capacity);j[i]=nj?jobs+begin[i]:jobs;c[i]=nj?cells+uint64_t(begin[i])*n:cells;o[i]=nj?output+uint64_t(begin[i])*nc:output;st[i]=nj?stats+begin[i]:stats;}
 lookahead_quad(
  row,nodes,edges,costs,j[0],c[0],v[0].data(),e[0].data(),h[0].data(),o[0],st[0],
  row,nodes,edges,costs,j[1],c[1],v[1].data(),e[1].data(),h[1].data(),o[1],st[1],
  row,nodes,edges,costs,j[2],c[2],v[2].data(),e[2].data(),h[2].data(),o[2],st[2],
  row,nodes,edges,costs,j[3],c[3],v[3].data(),e[3].data(),h[3].data(),o[3],st[3],
  n,count[0],count[1],count[2],count[3],nc,capacity,budget);
}
