#include "kernel.hpp"
#include "packed_kernel3.hpp"
#include <vector>
#include <cstring>
#include <cassert>
// Host-only coherence check against the uncached kernel. Neither this oracle nor
// its allocations are compiled into the HLS top or the real-workload RTL TB.
#define lookahead_top reference_coherence3
#include "../hls/lookahead_top.cpp"
#undef lookahead_top
extern "C" void lookahead_top(const uint64_t* row,const la::Node* nodes,const la::Edge* edges,const la::Cost* costs,const la::Job* jobs,const int32_t* cells,float* visited,uint32_t* expanded,la::Entry* heap,la::Cost* output,la::Stats* stats,uint32_t n,uint32_t nj,uint32_t nc,uint32_t capacity,uint64_t budget) {
 std::vector<uint64_t> label(n);
 std::vector<float> ref_visited(visited,visited+n);std::vector<uint32_t> ref_expanded(expanded,expanded+n);
 std::vector<la::Entry> ref_heap(capacity);std::vector<la::Cost> ref_out(uint64_t(nj)*nc);std::vector<la::Stats> ref_stats(nj);
 for(uint32_t i=0;i<n;++i){union {uint32_t u;float f;} bits;bits.f=visited[i];label[i]=(uint64_t(expanded[i])<<32)|bits.u;}
 reference_coherence3(row,nodes,edges,costs,jobs,cells,ref_visited.data(),ref_expanded.data(),ref_heap.data(),ref_out.data(),ref_stats.data(),n,nj,nc,capacity,budget);
 lookahead_packed(row,nodes,edges,costs,jobs,cells,label.data(),heap,output,stats,n,nj,nc,capacity,budget);
 for(uint32_t i=0;i<n;++i){union {uint32_t u;float f;} bits;bits.u=uint32_t(label[i]);visited[i]=bits.f;expanded[i]=label[i]>>32;}
 assert(!std::memcmp(visited,ref_visited.data(),n*sizeof(float)));
 assert(!std::memcmp(expanded,ref_expanded.data(),n*sizeof(uint32_t)));
}
