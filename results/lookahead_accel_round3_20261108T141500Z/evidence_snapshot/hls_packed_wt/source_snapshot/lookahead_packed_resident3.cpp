#ifndef LA_DEPTH_ROW
#define LA_DEPTH_ROW 65
#endif
#ifndef LA_DEPTH_NODES
#define LA_DEPTH_NODES 64
#endif
#ifndef LA_DEPTH_EDGES
#define LA_DEPTH_EDGES 256
#endif
#ifndef LA_DEPTH_COSTS
#define LA_DEPTH_COSTS 64
#endif
#ifndef LA_DEPTH_JOBS
#define LA_DEPTH_JOBS 8
#endif
#ifndef LA_DEPTH_CELLS
#define LA_DEPTH_CELLS 512
#endif
#ifndef LA_DEPTH_VISITED
#define LA_DEPTH_VISITED 64
#endif
#ifndef LA_DEPTH_EXPANDED
#define LA_DEPTH_EXPANDED 64
#endif
#ifndef LA_DEPTH_HEAP
#define LA_DEPTH_HEAP 257
#endif
#ifndef LA_DEPTH_OUTPUT
#define LA_DEPTH_OUTPUT 512
#endif
#ifndef LA_DEPTH_STATS
#define LA_DEPTH_STATS 8
#endif
#include "packed_engine3.hpp"
extern "C" void lookahead_packed(const uint64_t* row,const la::Node* nodes,const la::Edge* edges,const la::Cost* costs,const la::Job* jobs,const int32_t* cells,uint64_t* label,la::Entry* heap,la::Cost* output,la::Stats* stats,uint32_t n,uint32_t nj,uint32_t nc,uint32_t capacity,uint64_t budget) {
#if LA_SHARED_PORT
#define LA_GRAPH graph
#endif
#pragma HLS INTERFACE m_axi port=row bundle=graph depth=LA_DEPTH_ROW
#pragma HLS INTERFACE m_axi port=nodes bundle=graph depth=LA_DEPTH_NODES
#pragma HLS INTERFACE m_axi port=edges bundle=graph depth=LA_DEPTH_EDGES
#pragma HLS INTERFACE m_axi port=costs bundle=graph depth=LA_DEPTH_COSTS
#pragma HLS INTERFACE m_axi port=jobs bundle=graph depth=LA_DEPTH_JOBS
#pragma HLS INTERFACE m_axi port=cells bundle=graph depth=LA_DEPTH_CELLS
#pragma HLS INTERFACE m_axi port=label bundle=state depth=LA_DEPTH_VISITED
#if LA_SHARED_PORT
#pragma HLS INTERFACE m_axi port=heap bundle=graph depth=LA_DEPTH_HEAP
#else
#pragma HLS INTERFACE m_axi port=heap bundle=queue depth=LA_DEPTH_HEAP
#endif
#if LA_SHARED_PORT
#pragma HLS INTERFACE m_axi port=output bundle=graph depth=LA_DEPTH_OUTPUT
#else
#pragma HLS INTERFACE m_axi port=output bundle=result depth=LA_DEPTH_OUTPUT
#endif
#if LA_SHARED_PORT
#pragma HLS INTERFACE m_axi port=stats bundle=graph depth=LA_DEPTH_STATS
#else
#pragma HLS INTERFACE m_axi port=stats bundle=result depth=LA_DEPTH_STATS
#endif
#pragma HLS INTERFACE s_axilite port=return bundle=control
 packed_engine<0>(row,nodes,edges,costs,jobs,cells,label,heap,output,stats,n,nj,nc,capacity,budget);
}
